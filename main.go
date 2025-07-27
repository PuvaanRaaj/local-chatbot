// main.go
package main

import (
	"encoding/json"
	"fmt"
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