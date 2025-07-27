# Dockerfile

FROM python:3.12-slim AS python-api

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Build Go binary
FROM golang:1.22-alpine AS go-builder

WORKDIR /goapp
COPY . .
RUN go build -o /go-server main.go

# Final combined container
FROM python:3.12-slim

WORKDIR /app
COPY --from=python-api /app /app
COPY --from=go-builder /go-server /go-server

RUN apt update && apt install -y curl

EXPOSE 12345

CMD ["sh", "-c", "python app.py & ./go-server"]
