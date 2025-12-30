// main.go
package main

import (
	"encoding/json"
	"io"
	"log"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/joho/godotenv"
	"github.com/rs/cors"
)

type Message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type RequestPayload struct {
	Prompt   string    `json:"prompt"`
	Messages []Message `json:"messages"`
	Model    string    `json:"model"`
	Format   string    `json:"format"`
}

type ChatResponse struct {
	Choices []struct {
		Message struct {
			Content string `json:"content"`
		} `json:"message"`
	} `json:"choices"`
}

var systemPrompts = map[string]string{
	"review":   "You are a senior code reviewer. Give structured feedback.",
	"generate": "You are a code generator. Output clean, runnable code.",
	"ask":      "You are a helpful assistant. Answer clearly and concisely.",
	"debug":    "You are a debugging expert. Explain bugs and fixes.",
	"optimize": "You are a performance engineer. Suggest optimizations.",
	"database": "You are an intelligent database assistant that helps users query MySQL databases using natural language.\n\nYour task is to:\n1. Understand the user's natural language query\n2. Generate appropriate SQL queries\n3. The user has access to 3 databases: onlinepayment1, onlinepayment2, and onlinepayment3\n4. Each database contains many tables\n\nImportant rules:\n- ALWAYS generate ONLY valid SQL queries without any explanation or markdown formatting\n- Do NOT wrap the SQL in code blocks or markdown\n- Return ONLY the SQL query that can be executed directly\n- If you need to show tables in a database, use: SHOW TABLES\n- If you need to describe a table, use: DESCRIBE table_name\n- If you need to see databases, use: SHOW DATABASES\n- Use appropriate database names (onlinepayment1, onlinepayment2, or onlinepayment3) in your queries\n- Be careful with SELECT queries - always specify a LIMIT for large tables (default LIMIT 100 unless specified)\n\nAlways prefix your SQL with the appropriate USE database statement.",
}

func main() {
	_ = godotenv.Load()

	port := os.Getenv("PORT")
	if port == "" {
		port = "12345"
	}

	http.HandleFunc("/go", serveIndex)
	http.HandleFunc("/go/chat.html", serveChat)
	http.HandleFunc("/go/models", handleModels)
	http.HandleFunc("/go/chat/", handleChat)

	handler := cors.AllowAll().Handler(http.DefaultServeMux)
	log.Printf("Go server running on http://localhost:%s/go", port)
	log.Fatal(http.ListenAndServe(":"+port, handler))
}

func serveIndex(w http.ResponseWriter, r *http.Request) {
	http.ServeFile(w, r, "templates/index.html")
}

func serveChat(w http.ResponseWriter, r *http.Request) {
	http.ServeFile(w, r, "templates/chat.html")
}

func handleModels(w http.ResponseWriter, r *http.Request) {
	resp, err := http.Get("http://host.docker.internal:12434/engines/llama.cpp/v1/models")
	if err != nil {
		http.Error(w, "Failed to fetch models", 500)
		return
	}
	defer resp.Body.Close()
	w.Header().Set("Content-Type", "application/json")
	io.Copy(w, resp.Body)
}

func handleChat(w http.ResponseWriter, r *http.Request) {
	mode := strings.TrimPrefix(r.URL.Path, "/go/chat/")
	if _, ok := systemPrompts[mode]; !ok {
		http.Error(w, "Invalid mode", 400)
		return
	}

	var payload RequestPayload
	if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
		http.Error(w, "Bad request", 400)
		return
	}

	if payload.Prompt == "" && len(payload.Messages) == 0 {
		http.Error(w, "Prompt is required", 400)
		return
	}

	messages := []Message{{Role: "system", Content: systemPrompts[mode]}}
	if len(payload.Messages) > 0 {
		messages = append(messages, payload.Messages...)
	} else {
		messages = append(messages, Message{Role: "user", Content: payload.Prompt})
	}

	bodyMap := map[string]interface{}{
		"model":    payload.Model,
		"messages": messages,
	}
	bodyBytes, _ := json.Marshal(bodyMap)

	req, err := http.NewRequest("POST", "http://host.docker.internal:12434/engines/llama.cpp/v1/chat/completions", strings.NewReader(string(bodyBytes)))
	if err != nil {
		http.Error(w, "Request error", 500)
		return
	}
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{Timeout: 120 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		http.Error(w, "Chat error", 500)
		return
	}
	defer resp.Body.Close()

	w.Header().Set("Content-Type", "application/json")
	io.Copy(w, resp.Body)
}
