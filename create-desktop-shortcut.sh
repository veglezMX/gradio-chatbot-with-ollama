#!/bin/bash
# Create Desktop Shortcut for Ollama Chat (Linux)

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DESKTOP_FILE="$HOME/.local/share/applications/ollama-chat.desktop"

echo -e "\033[36m=== Creating Desktop Shortcut ===\033[0m"
echo ""

# Create .desktop file
cat > "$DESKTOP_FILE" << EOL
[Desktop Entry]
Version=1.0
Type=Application
Name=Ollama Chat
Comment=Modern chat interface for Ollama
Icon=utilities-terminal
Exec=bash -c "cd '$SCRIPT_DIR' && ./run-linux.sh"
Terminal=true
Categories=Development;Utility;
EOL

# Make it executable
chmod +x "$DESKTOP_FILE"

# Copy to desktop if it exists
if [ -d "$HOME/Desktop" ]; then
    cp "$DESKTOP_FILE" "$HOME/Desktop/"
    chmod +x "$HOME/Desktop/ollama-chat.desktop"
    echo -e "\033[32m✓ Desktop shortcut created on Desktop\033[0m"
fi

echo -e "\033[32m✓ Application shortcut created in Applications menu\033[0m"
echo ""
echo -e "\033[36mYou can now launch Ollama Chat from:\033[0m"
echo -e "  - Your desktop (if available)"
echo -e "  - The applications menu"
echo -e "  - By running: ./run-linux.sh"
echo ""