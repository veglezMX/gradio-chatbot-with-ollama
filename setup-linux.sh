#!/bin/bash
# Ollama Chat Setup Script for Linux/macOS
# This script creates a virtual environment and installs dependencies

echo -e "\033[36m=== Ollama Chat Setup for Linux/macOS ===\033[0m"
echo ""

# Function to check command existence
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if Python is installed
if command_exists python3; then
    PYTHON_CMD="python3"
elif command_exists python; then
    PYTHON_CMD="python"
else
    echo -e "\033[31m✗ Python not found. Please install Python 3.8 or higher\033[0m"
    echo -e "\033[33mUbuntu/Debian: sudo apt-get install python3 python3-venv python3-pip\033[0m"
    echo -e "\033[33mFedora: sudo dnf install python3 python3-pip\033[0m"
    echo -e "\033[33mmacOS: brew install python3\033[0m"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
MAJOR_VERSION=$(echo $PYTHON_VERSION | cut -d. -f1)
MINOR_VERSION=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$MAJOR_VERSION" -eq 3 ] && [ "$MINOR_VERSION" -ge 8 ]; then
    echo -e "\033[32m✓ Python $PYTHON_VERSION found\033[0m"
else
    echo -e "\033[31m✗ Python 3.8 or higher required. Found: $PYTHON_VERSION\033[0m"
    exit 1
fi

# Check if pip is installed
if ! $PYTHON_CMD -m pip --version >/dev/null 2>&1; then
    echo -e "\033[31m✗ pip not found. Installing pip...\033[0m"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        $PYTHON_CMD -m ensurepip
    else
        # Linux
        echo -e "\033[33mPlease install pip:\033[0m"
        echo -e "\033[33mUbuntu/Debian: sudo apt-get install python3-pip\033[0m"
        echo -e "\033[33mFedora: sudo dnf install python3-pip\033[0m"
        exit 1
    fi
fi

# Check if venv module is available
if ! $PYTHON_CMD -m venv --help >/dev/null 2>&1; then
    echo -e "\033[31m✗ venv module not found\033[0m"
    echo -e "\033[33mUbuntu/Debian: sudo apt-get install python3-venv\033[0m"
    echo -e "\033[33mFedora: sudo dnf install python3-venv\033[0m"
    exit 1
fi

# Check if virtual environment already exists
if [ -d ".venv" ]; then
    echo -e "\033[33mVirtual environment already exists. Removing old environment...\033[0m"
    rm -rf .venv
fi

# Create virtual environment
echo ""
echo -e "\033[33mCreating virtual environment...\033[0m"
$PYTHON_CMD -m venv .venv
if [ $? -eq 0 ]; then
    echo -e "\033[32m✓ Virtual environment created\033[0m"
else
    echo -e "\033[31m✗ Failed to create virtual environment\033[0m"
    exit 1
fi

# Activate virtual environment
echo ""
echo -e "\033[33mActivating virtual environment...\033[0m"
source .venv/bin/activate

# Upgrade pip
echo ""
echo -e "\033[33mUpgrading pip...\033[0m"
python -m pip install --upgrade pip

# Install requirements
echo ""
echo -e "\033[33mInstalling requirements...\033[0m"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo -e "\033[32m✓ Requirements installed\033[0m"
else
    echo -e "\033[31m✗ requirements.txt not found!\033[0m"
    exit 1
fi

# Check if Ollama is accessible
echo ""
echo -e "\033[33mChecking Ollama connection...\033[0m"
if curl -s -f -m 5 http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo -e "\033[32m✓ Ollama is running\033[0m"
    
    # Check for available models
    MODEL_COUNT=$(curl -s http://localhost:11434/api/tags | grep -o '"name"' | wc -l)
    if [ "$MODEL_COUNT" -gt 0 ]; then
        echo -e "\033[32m✓ Found $MODEL_COUNT model(s) available\033[0m"
    else
        echo -e "\033[33m! No models found. Run 'ollama pull llama3.2' to download a model\033[0m"
    fi
else
    echo -e "\033[33m! Ollama not found or not running\033[0m"
    echo -e "\033[33mPlease ensure Ollama is installed and running (http://localhost:11434)\033[0m"
    echo -e "\033[36mDownload from: https://ollama.ai\033[0m"
fi

echo ""
echo -e "\033[32m=== Setup Complete! ===\033[0m"
echo ""
echo -e "\033[36mTo run the application, use:\033[0m"
echo -e "\033[37m  ./run-linux.sh\033[0m"
echo ""
echo -e "\033[36mDon't forget to make the run script executable:\033[0m"
echo -e "\033[37m  chmod +x run-linux.sh\033[0m"
echo ""