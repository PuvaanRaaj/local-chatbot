from flask import Blueprint, jsonify, request, send_from_directory

from config.prompts import SYSTEM_PROMPTS
from services.llama_runner import run_chat

chat_bp = Blueprint("chat_bp", __name__)


@chat_bp.route("/")
def index():
    return send_from_directory("templates", "index.html")


@chat_bp.route("/chat.html")
def chat_ui():
    return send_from_directory("templates", "chat.html")


@chat_bp.route("/models", methods=["GET"])
def list_models():
    import requests

    try:
        response = requests.get(
            "http://host.docker.internal:12434/engines/llama.cpp/v1/models", timeout=10
        )
        response.raise_for_status()
        return jsonify(response.json()), 200
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500


def extract_payload(data):
    return (
        data.get("prompt", ""),
        data.get("model", "ai/llama3.2"),
        data.get("format", "json"),
    )


@chat_bp.route("/chat/<mode>", methods=["POST"])
def dynamic_chat_handler(mode):
    if mode not in SYSTEM_PROMPTS:
        return jsonify({"error": "Invalid mode"}), 400

    data = request.json
    prompt, model, fmt = extract_payload(data)
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    return run_chat(prompt, SYSTEM_PROMPTS[mode], model, fmt)
