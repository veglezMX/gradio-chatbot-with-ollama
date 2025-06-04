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
- Windows PowerShell (for Windows users)

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

3. **Choose how to run the application:**

   We provide two launch scripts:

   **Option A: Full-featured script (`run-full-windows.ps1`)**
   - Automatically starts Ollama if not running
   - Checks and installs models if needed
   - May trigger antivirus warnings (see [Antivirus Issues](#antivirus-issues) section)
   
   ```powershell
   .\run-full-windows.ps1
   ```

   **Option B: Simple script (`run-windows.ps1`)**
   - No automatic Ollama management
   - You must ensure Ollama is running before starting
   - Less likely to trigger antivirus warnings
   
   ```powershell
   .\run-windows.ps1
   ```

4. **Create a desktop shortcut (recommended):**
   
   **Method 1: Using File Explorer**
   - Navigate to your ollama-chat folder in File Explorer
   - Right-click on your preferred script (`run-windows.ps1` or `run-full-windows.ps1`)
   - Select "Send to" → "Desktop (create shortcut)"
   - Rename the shortcut to "Ollama Chat"
   
   **Method 2: Create a batch launcher**
   Create a new file `OllamaChat.bat` on your desktop with:
   ```batch
   @echo off
   cd /d "C:\path\to\ollama-chat"
   powershell -ExecutionPolicy Bypass -File ".\run-windows.ps1"
   pause
   ```
   
   **Optional: Customize the shortcut icon**
   - Right-click the desktop shortcut and select "Properties"
   - Click "Change Icon..." button
   - Browse to `C:\Windows\System32\shell32.dll` and select an appropriate icon
   - Click "OK" to apply

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

## Antivirus Issues

### Full-featured Script Warnings

The `run-full-windows.ps1` script may trigger antivirus warnings because it:
- Starts external processes (Ollama)
- Makes network requests
- Downloads models automatically

**Solutions:**

1. **Add to Antivirus Exclusions (if you trust the script):**
   - **Windows Defender:** Windows Security → Virus & threat protection → Manage settings → Add or remove exclusions → Add an exclusion → File → Select `run-full-windows.ps1`
   - **Other Antivirus:** Check your antivirus documentation for adding file exclusions

2. **Use the Simple Script:** If you prefer not to modify antivirus settings, use `run-windows.ps1` instead and manually ensure Ollama is running

3. **Run with Bypass:** Execute the script with bypass policy:
   ```powershell
   powershell -ExecutionPolicy Bypass -File ".\run-full-windows.ps1"
   ```

### PowerShell Execution Policy

If you get execution policy errors, run PowerShell as Administrator and execute:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Manual Installation

If you prefer to set up manually:

1. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   ```

2. **Activate the virtual environment:**
   
   Windows (PowerShell):
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   
   Windows (Command Prompt):
   ```cmd
   .venv\Scripts\activate.bat
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
   python main.py
   ```

## Configuration

The application runs on `http://localhost:7860` by default. You can modify the port by editing the last line in `main.py`:

```python
demo.launch(server_name="localhost", server_port=7860)
```

## Troubleshooting

### Ollama not found
- Ensure Ollama is installed and running
- Check if Ollama is accessible at `http://localhost:11434`
- Try running `ollama list` in your terminal
- If using `run-windows.ps1`, manually start Ollama with `ollama serve`

### No models available
- Pull at least one model: `ollama pull llama3.2`
- Recommended models: `ollama pull deepseek-r1:8b` and `ollama pull gemma3:12b`
- Restart the application after pulling new models

### PowerShell script errors
- Ensure you're using PowerShell (not Command Prompt)
- Check execution policy: `Get-ExecutionPolicy`
- Try running with bypass: `powershell -ExecutionPolicy Bypass -File ".\script.ps1"`

### Unicode character errors
- The scripts use ASCII characters to avoid encoding issues
- If you see strange characters, ensure your terminal supports UTF-8

### Permission denied on Linux
- Make scripts executable: `chmod +x *.sh`
- Run with proper permissions

## Script Differences

### `run-full-windows.ps1`
- **Pros:** Fully automated, starts Ollama, installs models
- **Cons:** May trigger antivirus, requires more permissions
- **Use when:** You want a one-click solution

### `run-windows.ps1`
- **Pros:** Simple, less likely to trigger antivirus
- **Cons:** Manual Ollama management required
- **Use when:** You prefer manual control or have antivirus concerns

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Ollama](https://ollama.ai) for the amazing local LLM runtime
- [Gradio](https://gradio.app) for the web interface framework
- The open-source community for inspiration and support