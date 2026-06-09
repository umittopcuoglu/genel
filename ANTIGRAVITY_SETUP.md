# Antigravity IDE Setup Guide

## 🚀 Quick Start

### 1. Open Antigravity
- Launch Antigravity IDE

### 2. Open Project Folder
- File → Open Folder
- Navigate to: `C:\Users\umit.topcuoglu\Desktop\geneL`
- Select and Open

### 3. All AI Services Configured
Everything is pre-configured in `.antigravityrc`:

```
✅ Deepseek
✅ Claude Pro #1 (Koray)
✅ Claude Pro #2 (Umit)
✅ Gemini Pro
```

---

## 📋 AI Providers Available

### Deepseek
- **API Key:** sk-5e9a1781e51240b6afb635abff65bcc1
- **Model:** deepseek-chat
- **Status:** ✅ Ready
- **Usage:** Terminal → `deepseek`

### Claude Pro #1 - Koray
- **Email:** korayumit@gmail.com
- **Model:** claude-opus-4-1
- **Status:** ✅ Ready
- **Usage:** Terminal → `koray`

### Claude Pro #2 - Umit
- **Email:** birumit@yandex.com.tr
- **Model:** claude-opus-4-1
- **Status:** ✅ Ready
- **Usage:** Terminal → `umit`

### Gemini Pro
- **API Key:** AQ.Ab8RN6KUbRU8ip8N3lSXhJ8WWJFtZQLaT5CrMWI4bkecCQXBLw
- **Model:** gemini-2.0-flash
- **Status:** ⚡ Ready (quota may needed)
- **Usage:** Terminal → `gemini`

---

## 🔧 Configuration Files

### `.antigravityrc`
Main configuration file with all AI providers:
- Default language: Python
- Auto-format: Enabled
- Extensions: Python, JavaScript, Git
- Terminal environment variables: Pre-set

### `.env`
Secure file (not in git) containing:
- All API keys
- Credentials
- Environment variables

---

## 💻 Terminal Integration

### In Antigravity Terminal:

```bash
# Launch AI CLI with different providers
umit                    # Claude Pro #2 (Umit)
koray                   # Claude Pro #1 (Koray)
deepseek                # Deepseek
gemini                  # Gemini Pro
menu                    # Interactive menu
python ai_cli.py        # Direct Python CLI

# Run applications
cd openclaw             # Open openclaw app
cd claudex              # Open claudex app
```

---

## 🎯 Environment Variables

Auto-loaded when Antigravity starts:

```bash
DEEPSEEK_API_KEY=sk-5e9a1781e51240b6afb635abff65bcc1
GEMINI_API_KEY=AQ.Ab8RN6KUbRU8ip8N3lSXhJ8WWJFtZQLaT5CrMWI4bkecCQXBLw
CLAUDE_EMAIL_1=korayumit@gmail.com
CLAUDE_EMAIL_2=birumit@yandex.com.tr
```

Access in code:
```python
import os
deepseek_key = os.getenv('DEEPSEEK_API_KEY')
claude_email = os.getenv('CLAUDE_EMAIL_1')
```

---

## 📂 Project Structure

```
genel/
├── openclaw/           # OpenClaw application
├── claudex/            # ClaudeX application
├── loveable/           # Loveable application
├── whisper-flow/       # Whisper Flow application
├── manus/              # Manus application
├── ai_cli.py           # CLI for all AI services
├── ai_control_panel.py # Web dashboard
├── .antigravityrc      # Antigravity config
├── .vscode/            # VS Code config
├── .env                # Environment variables
├── templates/          # Web templates
├── static/             # Web assets
└── README.md           # Documentation
```

---

## 🚀 Run AI Services

### Option 1: Quick Launch
```bash
umit              # Opens Claude Pro #2 immediately
koray             # Opens Claude Pro #1 immediately
deepseek          # Opens Deepseek immediately
```

### Option 2: Interactive Menu
```bash
menu              # Shows menu to select AI service
```

### Option 3: Web Dashboard
```bash
python ai_control_panel.py
# Then open: http://localhost:5000
```

---

## 🔐 Security Notes

- `.env` file is gitignored (not in GitHub)
- API keys are only stored locally
- Each provider credentials are separate
- Use `.env.example` as template

---

## ✨ Features in Antigravity

- ✅ Python syntax highlighting
- ✅ Git integration
- ✅ Auto-formatting
- ✅ Terminal access
- ✅ Multi-language support
- ✅ Environment variables pre-loaded
- ✅ All 4 AI services configured

---

## 🆘 Troubleshooting

**Commands not found in terminal?**
- Restart Antigravity
- Check `.antigravityrc` is in project root
- Verify Python venv is initialized

**API errors?**
- Check `.env` file has all keys
- Verify API keys are correct
- Test with: `python ai_cli.py --api deepseek`

**Configuration not loading?**
- Reload Antigravity
- Check file permissions on `.antigravityrc`
- Verify folder path is correct

---

## 📚 Next Steps

1. Open folder in Antigravity
2. Try: `umit` or `koray` in terminal
3. Or run: `python ai_control_panel.py` for web UI
4. Start developing with all AI services available!

---

**All ready! Happy coding with Antigravity!** 🎉
