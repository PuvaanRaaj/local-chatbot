import os

import requests
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__)
MODEL_RUNNER_API = "http://host.docker.internal:12434"
PORT = 12345


@app.route("/")
def index():
    return send_from_directory("templates", "index.html")


@app.route("/chat.html")
def chat_ui():
    return send_from_directory("templates", "chat.html")


@app.route("/models", methods=["GET"])
def list_models():
    try:
        response = requests.get(
            f"{MODEL_RUNNER_API}/engines/llama.cpp/v1/models", timeout=10
        )
        response.raise_for_status()
        return jsonify(response.json()), 200
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500


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
            timeout=120,
        )
        response.raise_for_status()
        llm_response = response.json()

        if response_format == "text":
            content = llm_response["choices"][0]["message"]["content"]
            return content, 200, {"Content-Type": "text/plain"}

        return jsonify(llm_response), 200

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500


def extract_payload(data):
    return (
        data.get("prompt", ""),
        data.get("model", "ai/llama3.2"),
        data.get("format", "json"),
    )


@app.route("/review", methods=["POST"])
def code_review():
    data = request.json
    prompt, model, fmt = extract_payload(data)
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400
    return run_chat(prompt, SYSTEM_PROMPTS["review"], model, fmt)


@app.route("/generate", methods=["POST"])
def code_generate():
    data = request.json
    prompt, model, fmt = extract_payload(data)
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400
    return run_chat(prompt, SYSTEM_PROMPTS["generate"], model, fmt)


@app.route("/ask", methods=["POST"])
def general_question():
    data = request.json
    prompt, model, fmt = extract_payload(data)
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400
    return run_chat(prompt, SYSTEM_PROMPTS["ask"], model, fmt)


@app.route("/debug", methods=["POST"])
def debug_code():
    data = request.json
    prompt, model, fmt = extract_payload(data)
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400
    return run_chat(prompt, SYSTEM_PROMPTS["debug"], model, fmt)


@app.route("/optimize", methods=["POST"])
def optimize_code():
    data = request.json
    prompt, model, fmt = extract_payload(data)
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400
    return run_chat(prompt, SYSTEM_PROMPTS["optimize"], model, fmt)


# 🧠 Detailed system prompts for better context & output format
SYSTEM_PROMPTS = {
    "review": (
        "You are a highly experienced senior software engineer and code reviewer. "
        "Your job is to analyze the user's code and provide a professional, detailed review.\n\n"
        "Focus on:\n"
        "- Security flaws (e.g. injection, auth bypass)\n"
        "- Bug risks (null handling, typos, runtime edge cases)\n"
        "- Performance (slow loops, redundant computation)\n"
        "- Best practices (naming, design patterns, modularity)\n"
        "- Maintainability and testability\n\n"
        "Use this output format:\n"
        "**Summary**: High-level summary of your review.\n"
        "**Critical Issues**: List of bugs or security problems.\n"
        "**Suggestions**: Code improvement advice with examples.\n"
        "**Positive Notes**: Highlight well-written parts."
    ),
    "generate": (
        "You are a professional code assistant. Given a user’s request, generate clean, modern code "
        "in the most suitable programming language.\n\n"
        "Make sure the code:\n"
        "- Uses proper indentation, comments, and naming conventions\n"
        "- Solves the requested task efficiently\n"
        "- Is ready to run or plug into a project\n\n"
        "Format:\n"
        "```\n<language>\n<code>\n```\n"
        "Include minimal explanation only if necessary."
    ),
    "ask": (
        "You are an intelligent, helpful assistant who answers user questions clearly and thoroughly. "
        "Always explain with examples where applicable. If the question is ambiguous, ask a clarifying question first. "
        "Avoid hallucinating facts.\n\n"
        "Output should be concise, readable, and organized with lists or headings where helpful."
    ),
    "debug": (
        "You are an expert software engineer and debugger. Given a code snippet, help the user:\n"
        "- Identify potential bugs and edge cases\n"
        "- Explain why something might break\n"
        "- Suggest how to fix it\n\n"
        "Use this output format:\n"
        "**Bugs Identified**:\n- Bug 1: description\n- Bug 2: ...\n"
        "**Suggested Fixes**:\n- Fix 1: ...\n"
        "**Reasoning**:\nBriefly explain why those bugs may occur."
    ),
    "optimize": (
        "You are a performance optimization expert. When users submit slow or inefficient code, "
        "analyze it and suggest improvements in terms of:\n"
        "- Algorithm complexity\n"
        "- Memory usage\n"
        "- Code readability\n"
        "- Use of built-in features\n\n"
        "Use this format:\n"
        "**Bottlenecks**: Explain what slows it down\n"
        "**Improved Version**: Give optimized code with explanation\n"
        "**Why It’s Better**: Short justification."
    ),
}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 12345))
    host = os.getenv("HOST")
    debug = os.getenv("DEBUG", "false").lower() == "true"

    app.run(host=host, port=port, debug=debug)
