#!/bin/bash
# Ollama Chat Run Script for Linux/macOS
# This script activates the virtual environment and runs the application

# Get the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "\033[36m=== Starting Ollama Chat ===\033[0m"
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "\033[31mVirtual environment not found!\033[0m"
    echo -e "\033[33mPlease run ./setup-linux.sh first\033[0m"
    exit 1
fi

# Check if ollama_chat.py exists
if [ ! -f "ollama_chat.py" ]; then
    echo -e "\033[31mollama_chat.py not found!\033[0m"
    echo -e "\033[33mPlease ensure you're in the correct directory\033[0m"
    exit 1
fi

# Activate virtual environment
echo -e "\033[33mActivating virtual environment...\033[0m"
source .venv/bin/activate

# Check if Ollama is running
echo -e "\033[33mChecking Ollama status...\033[0m"
if curl -s -f -m 3 http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo -e "\033[32m✓ Ollama is running\033[0m"
else
    echo -e "\033[33m! Warning: Ollama appears to be offline\033[0m"
    echo -e "\033[33mThe app will start but won't work without Ollama running\033[0m"
    echo ""
fi

# Function to open URL in default browser
open_browser() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        open "$1"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v xdg-open >/dev/null 2>&1; then
            xdg-open "$1"
        elif command -v gnome-open >/dev/null 2>&1; then
            gnome-open "$1"
        fi
    fi
}

# Run the application
echo ""
echo -e "\033[32mStarting application...\033[0m"
echo -e "\033[36mOpening browser at http://localhost:7860\033[0m"
echo ""
echo -e "\033[33mPress Ctrl+C to stop the server\033[0m"
echo ""

# Try to open browser after a short delay
(sleep 2 && open_browser "http://localhost:7860") &

# Run the Python application
python ollama_chat.py

# Check exit code
if [ $? -ne 0 ]; then
    echo ""
    echo -e "\033[31mApplication exited with error\033[0m"
    read -p "Press Enter to exit..."
fi