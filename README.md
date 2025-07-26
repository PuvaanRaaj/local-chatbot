# LLM Chatbot (Code Review, Generation, Debugging, and More)

This project is a lightweight, developer-friendly chatbot powered by **Docker Model Runner** (e.g. LLaMA 3.2 or other local models), styled like ChatGPT, with support for:

* **Code Review**
* **Code Generation**
* **General Q\&A**
* **Debugging**
* **Optimization**

It runs fully locally via **Docker + Flask**, with markdown rendering, streaming response, copy buttons, and multiple modes.

---

## Features

* Dark-mode responsive UI with Tailwind
* Markdown + code block rendering
* Upload file support (+ icon)
* Streamed assistant typing effect
* Multiple endpoints and prompts (review, generate, debug...)
* Runs entirely on Docker (LLM + app)

---

## Project Structure

```
llm-chatbot/
├── app.py                # Flask entry
├── routes/              # Route handlers
│   └── chat_routes.py
├── services/            # Chat logic
│   └── llama_runner.py
├── templates/
│   ├── index.html       # Mode selector
│   └── chat.html        # Chat UI
├── .env                 # Copied from .env.example
├── .env.example         # Sample environment file
├── requirements.txt
└── demo/
    └── <your-screenshots-here>.png
```

---

## Getting Started

### 1. Prerequisites

* Docker Desktop
* Docker Model Runner plugin

### 2. Clone This Repo

```bash
git clone https://github.com/yourname/llm-chatbot
cd llm-chatbot
cp .env.example .env
```

### 3. Install Docker Model Runner (Only Once)

```bash
docker extension install docker/model:latest
```

Then enable TCP support:

```bash
docker model install-runner --tcp 12434
```

Or in Docker Desktop:

1. Go to **Settings > Features in Development**
2. Enable **Model Runner TCP support**

![Docker Model Runner Enable](demo/docker-model-runner-enable.png)

### 4. Pull Your Model

```bash
docker model pull ai/llama3.2:latest
```

You may use any compatible model such as `ai/qwen3:latest`, `llama3.3:latest`, or  `unsloth/DeepSeek-R1-0528-Qwen3-8B-GGUF`.

---

## 🛠 Run It (Local Dev)

Use Docker to start the chatbot container:

```bash
docker compose up -d
```

Then visit: [http://localhost:12345](http://localhost:12345)

---

## 🔧 .env

Copy it:

```bash
cp .env.example .env
```

---

## 📄 requirements.txt

```txt
flask
requests
python-dotenv
```

---

## ✅ Features to Explore

* [ ] Add Chat History (localStorage?)
* [ ] Auth or Login (JWT, sessions)
* [ ] Save/Share prompts

---

## 🧠 Credits

* Powered by Docker Model Runner

---

## 📜 License

MIT. Use freely. Attribution appreciated.
