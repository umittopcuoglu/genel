#!/bin/bash
# Load environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ Environment variables loaded from .env"
else
    echo "⚠️  .env file not found"
    echo "Please create .env file with DEEPSEEK_API_KEY and GITHUB_PAT"
fi
