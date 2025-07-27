import os

from dotenv import load_dotenv
from flask import Flask

from routes.chat_routes import chat_bp

load_dotenv()

app = Flask(__name__)
app.register_blueprint(chat_bp)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 12345))
    host = os.getenv("HOST")
    debug = os.getenv("DEBUG", "false").lower() == "true"

    app.run(host=host, port=port, debug=debug)
