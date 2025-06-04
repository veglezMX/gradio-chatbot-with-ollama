# Ollama Chat Interface

A modern, feature-rich chat interface for Ollama with real-time streaming, model management, and beautiful UI.

## Features

- 🚀 Real-time streaming responses
- 🎨 Beautiful dark theme UI
- 📊 Live model information display
- 🔄 Easy model switching
- 💾 Chat history during session
- 🖼️ Support for vision models
- ⚡ Fast and responsive

## Prerequisites

- Python 3.8 or higher
- Ollama installed and running (download from [ollama.ai](https://ollama.ai))
- At least one Ollama model pulled (e.g., `ollama pull llama3.2`)

## Quick Start

### Windows

1. **Clone the repository:**
   ```powershell
   git clone https://github.com/yourusername/ollama-chat.git
   cd ollama-chat
   ```

2. **Run the setup script (first time only):**
   ```powershell
   .\setup-windows.ps1
   ```

3. **Run the application:**
   ```powershell
   .\run-windows.ps1
   ```

4. **Create a desktop shortcut (optional):**
   - Right-click on `run-windows.ps1`
   - Select "Create shortcut"
   - Move the shortcut to your desktop
   - Rename it to "Ollama Chat"

### Linux/macOS

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/ollama-chat.git
   cd ollama-chat
   ```

2. **Run the setup script (first time only):**
   ```bash
   chmod +x setup-linux.sh
   ./setup-linux.sh
   ```

3. **Run the application:**
   ```bash
   chmod +x run-linux.sh
   ./run-linux.sh
   ```

4. **Create a desktop shortcut (optional):**
   
   For Linux with GNOME:
   ```bash
   ./create-desktop-shortcut.sh
   ```

## Manual Installation

If you prefer to set up manually:

1. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   ```

2. **Activate the virtual environment:**
   
   Windows:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   
   Linux/macOS:
   ```bash
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python ollama_chat.py
   ```

## Configuration

The application runs on `http://localhost:7860` by default. You can modify the port by editing the last line in `ollama_chat.py`:

```python
demo.launch(server_name="localhost", server_port=7860)
```

## Troubleshooting

### Ollama not found
- Ensure Ollama is installed and running
- Check if Ollama is accessible at `http://localhost:11434`
- Try running `ollama list` in your terminal

### No models available
- Pull at least one model: `ollama pull llama3.2`
- Restart the application after pulling new models

### Permission denied on Linux
- Make scripts executable: `chmod +x *.sh`
- Run with proper permissions

### PowerShell execution policy (Windows)
If you get an execution policy error, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Ollama](https://ollama.ai) for the amazing local LLM runtime
- [Gradio](https://gradio.app) for the web interface framework
- The open-source community for inspiration and support