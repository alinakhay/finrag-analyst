#!/usr/bin/env sh
set -eu

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker Desktop is required for the full local stack."
  echo "Install it, start it, then run this script again."
  exit 1
fi

docker compose up --build -d
echo "FinRAG Analyst: http://localhost:8080"
echo "API documentation: http://localhost:8000/docs"
echo "First startup may take several minutes while the local model downloads."
