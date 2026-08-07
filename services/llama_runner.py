import requests
from flask import jsonify, make_response

MODEL_RUNNER_API = "http://host.docker.internal:12434"


def run_chat(prompt, system_prompt, model, response_format):
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
    }

    try:
        response = requests.post(
            f"{MODEL_RUNNER_API}/engines/llama.cpp/v1/chat/completions",
            json=payload,
            timeout=600,
        )
        response.raise_for_status()
        llm_response = response.json()

        if response_format == "text":
            content = llm_response["choices"][0]["message"]["content"]
            return make_response(content, 200, {"Content-Type": "text/plain"})

        return jsonify(llm_response), 200

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500
