import os

from dotenv import load_dotenv
from flask import Flask

from routes.chat_routes import chat_bp

load_dotenv()

app = Flask(__name__)
app.register_blueprint(chat_bp)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 12345))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
