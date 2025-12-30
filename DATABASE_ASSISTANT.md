# Database Assistant Feature

## Overview

A new database assistant has been added to help you query your local MySQL database using natural language. The assistant connects to your MySQL container (`rds_test`) running in the `vpc_test_1network` Docker network.

## Setup

### 1. Database Configuration

Your MySQL database setup:
- **Container name:** `rds_test`
- **Port:** 3306
- **Network:** `vpc_test_1network`
- **Databases:** test1, test2, test3
- **Host:** rds_test (within Docker network)

### 2. Environment Variables

You can configure MySQL credentials via environment variables:

```bash
export MYSQL_USER=root
export MYSQL_PASSWORD=your_password
```

### 3. Update Requirements

Install the new dependency:

```bash
pip install -r requirements.txt
```

This will install `pymysql` (MySQL connector for Python).

### 4. Restart Services

If running in Docker, rebuild and restart:

```bash
docker-compose down
docker-compose up --build
```

## Usage

### In the UI

1. Open the chat interface: `http://localhost:12345/chat.html`
2. Select **"Database Query"** mode from the dropdown
3. Enter your natural language query

### Example Queries

- "Show me all tables in test1 database"
- "What columns are in the users table in test1?"
- "Get all records from the users table in test1"
- "Show the first 10 customers from test2"
- "Describe the products table in test3"

### Response Format

The assistant will:
1. Convert your natural language to SQL
2. Execute the query against your MySQL database
3. Display the results in a formatted table
4. Show the generated SQL for reference

**Example response:**
```
Query Executed Successfully

Generated SQL:
USE test1; SELECT * FROM users LIMIT 100;

Result: 15 row(s) returned

| id | username | email |
|---|---|---|
| 1 | john | john@example.com |
...
```

## Architecture

### New Files Created

1. **`services/database_service.py`** - Handles MySQL connections and query execution
2. **`config/prompts.py`** - Added "database" mode system prompt
3. **`routes/chat_routes.py`** - Added database route handling
4. **`templates/chat.html`** - Added database mode to UI

### How It Works

1. User enters natural language query
2. LLM converts query to SQL using specialized prompt
3. Generated SQL is cleaned and executed against MySQL
4. Results are formatted as a markdown table
5. Response includes both the SQL and results

### Network Configuration

The `docker-compose.yml` has been updated to connect the chatbot to the `vpc_test_1network`:

```yaml
networks:
  - vpc_test_1network
```

This allows the chatbot container to communicate with the `rds_test` MySQL container.

## Troubleshooting

### Cannot Connect to Database

If you see connection errors:

1. Ensure the MySQL container is running:
   ```bash
   docker ps | grep rds_test
   ```

2. Check network connectivity:
   ```bash
   docker network inspect vpc_test_1network
   ```

3. Verify the chatbot is on the same network:
   ```bash
   docker inspect chatbot | grep NetworkMode
   ```

### Connection Test

Test the database connection manually:

```bash
# From the host
mysql -h 127.0.0.1 -P 3306 -u root

# From within the chatbot container
docker exec -it chatbot python -c "from services.database_service import get_db_connection; conn = get_db_connection(); print('Connected!')"
```

## Security Notes

- Default configuration assumes no password for root user
- For production, set strong `MYSQL_PASSWORD` environment variable
- Consider restricting database access to specific IPs
- The assistant automatically limits SELECT queries to 100 rows by default

## API Endpoints

### Python/Flask Server

- `POST /chat/database` - Execute database query
  ```json
  {
    "prompt": "Show tables in test1",
    "model": "ai/llama3.2",
    "format": "json"
  }
  ```

### Go Server

- Supports the same database mode via `/go/chat/database`
- Note: Go server forwards to LLM only, doesn't execute queries

