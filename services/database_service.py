import pymysql
import re
from flask import jsonify
import requests


def get_db_connection():
    """Create a connection to the MySQL database running in Docker.
    
    The database container is named 'rds_payment' and runs on port 3306 in the 'vpc_test_1network' network.
    """
    import os
    
    # Try to connect from within Docker network first
    docker_hosts = ['rds_payment', 'localhost', 'host.docker.internal']
    
    last_error = None
    for host in docker_hosts:
        try:
            connection = pymysql.connect(
                host=host,
                port=3306,
                user=os.getenv('MYSQL_USER', 'root'),
                password=os.getenv('MYSQL_PASSWORD', 'mysqlroot'),
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=5
            )
            return connection
        except Exception as e:
            last_error = e
            continue
    
    raise Exception(f"Failed to connect to database after trying hosts: {docker_hosts}. Last error: {str(last_error)}")


def execute_query(sql):
    """Execute SQL query and return results."""
    connection = None
    try:
        # Clean up SQL - remove markdown code blocks if present
        sql = re.sub(r'```sql\s*', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'```\s*$', '', sql, flags=re.MULTILINE)
        sql = sql.strip()
        
        connection = get_db_connection()
        
        with connection.cursor() as cursor:
            # Split multiple statements if present
            statements = [s.strip() for s in sql.split(';') if s.strip()]
            
            results = []
            for statement in statements:
                if not statement:
                    continue
                    
                cursor.execute(statement)
                
                # If it's a SELECT, SHOW, or DESCRIBE statement, fetch results
                if statement.strip().upper().startswith(('SELECT', 'SHOW', 'DESCRIBE', 'DESC', 'EXPLAIN')):
                    result = cursor.fetchall()
                    results.append({
                        'query': statement,
                        'columns': list(result[0].keys()) if result and isinstance(result[0], dict) else None,
                        'rows': result,
                        'row_count': len(result)
                    })
                else:
                    # For INSERT, UPDATE, DELETE, etc.
                    connection.commit()
                    results.append({
                        'query': statement,
                        'affected_rows': cursor.rowcount,
                        'message': 'Query executed successfully'
                    })
            
            # Return the result with data if available, otherwise return the last result
            # If we have multiple results, prefer the one with columns/rows
            import sys
            print(f"DEBUG: Total results: {len(results)}", file=sys.stderr)
            for i, result in enumerate(results):
                print(f"DEBUG: Result {i}: {result}", file=sys.stderr)
            sys.stderr.flush()
            
            for result in results:
                if 'columns' in result and result['columns']:
                    print(f"DEBUG: Returning result with columns", file=sys.stderr)
                    sys.stderr.flush()
                    return result
            
            # Return the last result if no data results
            print(f"DEBUG: Returning last result", file=sys.stderr)
            sys.stderr.flush()
            return results[-1] if results else {'message': 'Query executed successfully'}
            
    except Exception as e:
        import sys
        print(f"DEBUG: Exception in execute_query: {e}", file=sys.stderr)
        sys.stderr.flush()
        return {'error': str(e), 'query': sql}
    finally:
        if connection:
            connection.close()


def run_database_chat(prompt, model, response_format):
    """Main function to process natural language database queries."""
    print(f"DEBUG: Starting database chat with prompt: {prompt}")
    MODEL_RUNNER_API = "http://host.docker.internal:12434"
    
    # First, use LLM to convert natural language to SQL
    # Use a very strict prompt to get only SQL
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "Generate SQL queries ONLY. Output format: USE database_name; SQL_QUERY;\n\nDatabases: onlinepayment1, onlinepayment2, onlinepayment3\n\nDo NOT output explanations, descriptions, or example data.\n\nOutput ONLY this format:\nUSE onlinepayment1; SELECT * FROM table LIMIT 100;"
            },
            {
                "role": "user", 
                "content": "Convert this to SQL (output only the SQL query, no explanations): " + prompt
            }
        ],
        "temperature": 0.1  # Lower temperature for more deterministic output
    }
    
    try:
        # Get SQL from LLM
        response = requests.post(
            f"{MODEL_RUNNER_API}/engines/llama.cpp/v1/chat/completions",
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        llm_response = response.json()
        
        # Extract SQL from LLM response
        raw_sql = llm_response["choices"][0]["message"]["content"].strip()
        
        # Debug: Print what we got from LLM
        import sys
        print(f"DEBUG: Raw LLM response: {raw_sql}", file=sys.stderr)
        sys.stderr.flush()
        
        # Extract SQL - look for SELECT statements first
        sql = None
        
        # Method 1: Look for SELECT statement with database.table format
        match = re.search(r'SELECT\s+.*\s+FROM\s+[\w\.`]+\s+WHERE\s+.*;', raw_sql, re.IGNORECASE | re.DOTALL)
        if match:
            sql = match.group(0)
            print(f"DEBUG: Found SQL via method 1: {sql}", file=sys.stderr)
            sys.stderr.flush()
        
        # Method 2: Look for full SELECT statement (with multi-line support)
        if not sql:
            # Match SELECT ... FROM ... (rest of query) until semicolon
            match = re.search(r'SELECT\s+[^;]+;', raw_sql, re.IGNORECASE | re.DOTALL)
            if match:
                sql = match.group(0)
                print(f"DEBUG: Found SQL via method 2: {sql}", file=sys.stderr)
                sys.stderr.flush()
        
        # Method 3: If still no SQL, try to extract from code blocks
        if not sql:
            # Look for content between ```sql and ```
            code_match = re.search(r'```sql\s*(.*?)\s*```', raw_sql, re.IGNORECASE | re.DOTALL)
            if code_match:
                sql = code_match.group(1).strip()
                print(f"DEBUG: Found SQL via method 3: {sql}")
        
        # Method 4: Last resort - find any line that looks like SQL
        if not sql:
            lines = raw_sql.split('\n')
            for line in lines:
                line = line.strip()
                if re.match(r'SELECT\s+.*?\s+FROM\s+', line, re.IGNORECASE):
                    sql = line
                    if not sql.endswith(';'):
                        sql += ';'
                    print(f"DEBUG: Found SQL via method 4: {sql}")
                    break
        
        # Clean up the SQL
        if sql:
            sql = sql.strip()
            # Check if USE statement is present in raw_sql and prepend it if not already in sql
            use_match = re.search(r'USE\s+\w+;', raw_sql, re.IGNORECASE)
            if use_match and 'USE' not in sql.upper():
                use_statement = use_match.group(0)
                sql = f"{use_statement} {sql}"
            elif 'onlinepayment1' in raw_sql.lower() and 'USE' not in sql.upper():
                sql = f"USE onlinepayment1; {sql}"
            elif 'onlinepayment2' in raw_sql.lower() and 'USE' not in sql.upper():
                sql = f"USE onlinepayment2; {sql}"
            elif 'onlinepayment3' in raw_sql.lower() and 'USE' not in sql.upper():
                sql = f"USE onlinepayment3; {sql}"
        
        print(f"DEBUG: Final SQL to execute: {sql}", file=sys.stderr)
        sys.stderr.flush()
        
        # Check if we found SQL
        if not sql:
            return jsonify({
                'choices': [{
                    'message': {
                        'content': f'**Error:** Could not extract SQL from LLM response.\n\n**Raw response:**\n```\n{raw_sql}\n```\n\nPlease try rephrasing your query.'
                    }
                }]
            }), 200
        
        # Execute the SQL query
        print(f"DEBUG: About to call execute_query", file=sys.stderr)
        sys.stderr.flush()
        query_result = execute_query(sql)
        print(f"DEBUG: Query result: {query_result}", file=sys.stderr)
        sys.stderr.flush()
        print(f"DEBUG: query_result keys: {query_result.keys() if isinstance(query_result, dict) else 'not a dict'}", file=sys.stderr)
        sys.stderr.flush()
        
        # Format the response
        if 'error' in query_result:
            error_message = f"**Database Query Error**\n\n**Generated SQL:**\n```sql\n{query_result.get('query', '')}\n```\n\n**Error:** {query_result['error']}"
            return jsonify({
                'choices': [{
                    'message': {
                        'content': error_message
                    }
                }]
            }), 200
        
        # Format successful response
        response_text = f"**Query Executed Successfully**\n\n**Generated SQL:**\n```sql\n{query_result.get('query', '')}\n```\n\n"
        
        if 'columns' in query_result and query_result['columns']:
            response_text += f"**Result:**\n{query_result.get('row_count', 0)} row(s) returned\n\n"
            
            # Format as table
            if query_result.get('rows'):
                response_text += "| " + " | ".join(query_result['columns']) + " |\n"
                response_text += "| " + " | ".join(["---"] * len(query_result['columns'])) + " |\n"
                for row in query_result['rows'][:50]:  # Limit to 50 rows for display
                    values = [str(row.get(col, '')) for col in query_result['columns']]
                    response_text += "| " + " | ".join(values) + " |\n"
                if len(query_result['rows']) > 50:
                    response_text += f"\n*Showing first 50 of {len(query_result['rows'])} rows*"
        elif 'affected_rows' in query_result:
            response_text += f"**Result:** {query_result.get('message', 'Query executed')} - {query_result.get('affected_rows', 0)} row(s) affected"
        
        return jsonify({
            'choices': [{
                'message': {
                    'content': response_text
                }
            }]
        }), 200
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            'choices': [{
                'message': {
                    'content': f'**Error:** Failed to communicate with LLM: {str(e)}'
                }
            }]
        }), 200
    except Exception as e:
        return jsonify({
            'choices': [{
                'message': {
                    'content': f'**Error:** Database query failed: {str(e)}\n\nMake sure the MySQL container (rds_payment) is running and the chatbot is connected to the aws_molpay network.'
                }
            }]
        }), 200

