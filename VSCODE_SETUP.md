# VS Code Setup Guide

## 🔧 Installation

### 1. Open VS Code Workspace
```bash
code genel.code-workspace
```

Or:
- File → Open Workspace from File
- Select: `C:\Users\umit.topcuoglu\Desktop\geneL\genel.code-workspace`

### 2. Install Claude Extension (Recommended)

1. **Extensions Panel** (Ctrl+Shift+X)
2. Search: **"Claude"**
3. Install official **Anthropic Claude** extension
4. Reload VS Code

### 3. Configure Claude Extension

1. Extensions → Claude → Settings (gear icon)
2. Or: Preferences → Settings → Claude
3. Add your API keys:

```json
"claude.apiKey": "sk-ant-api03-...",  // For Koray
```

Or for Umit:
```json
"claude.apiKey": "sk-ant-api03-...",  // For Umit
```

### 4. Environment Variables Auto-Loaded

All AI services are pre-configured in:
- `.vscode/settings.json` - Terminal environment vars
- `.antigravityrc` - Antigravity IDE config

**Auto-loaded variables:**
- `DEEPSEEK_API_KEY`
- `GEMINI_API_KEY`
- `CLAUDE_EMAIL_1` (Koray)
- `CLAUDE_EMAIL_2` (Umit)

---

## 🚀 Usage

### Terminal in VS Code (Ctrl+`)

```bash
# All commands work automatically with env vars
umit                    # Claude Pro #2 (Umit)
koray                   # Claude Pro #1 (Koray)
deepseek                # Deepseek
gemini                  # Gemini Pro
python ai_cli.py        # Interactive menu
```

### Claude Extension in VS Code

1. Open Claude Chat (sidebar or Ctrl+Shift+C)
2. Type your prompt
3. Claude responds using configured API key

**Tip:** Switch between Koray and Umit accounts by:
- Updating Claude extension settings
- Or using Claude's account switcher

---

## 📦 Multi-Root Workspace

Your workspace includes 6 folders:
1. **genel-main** - Main project
2. **openclaw** - OpenClaw app
3. **claudex** - ClaudeX app
4. **loveable** - Loveable app
5. **whisper-flow** - Whisper Flow app
6. **manus** - Manus app

Each can be developed independently.

---

## 🔑 AI Providers Configuration

All configured and ready:

| Provider | Status | Account |
|----------|--------|---------|
| Deepseek | ✅ Ready | API configured |
| Claude #1 | ✅ Ready | korayumit@gmail.com |
| Claude #2 | ✅ Ready | birumit@yandex.com.tr |
| Gemini | ⚡ Ready | Quota may needed |

---

## 🛠️ Recommended Extensions

VS Code → Extensions → Install:
- **Python** (Microsoft)
- **Pylance** (Microsoft)
- **Prettier** (Code formatter)
- **Claude** (Anthropic) - For AI assistance
- **Git Graph** - For Git visualization
- **REST Client** - For API testing

---

## 💡 Tips

1. **Switch Claude accounts:** Update Claude extension settings
2. **Use environment variables:** Terminal auto-loads all API keys
3. **Run AI CLI:** Use integrated terminal
4. **Debug:** Terminal shows all env vars loaded

---

## 🆘 Troubleshooting

**Claude extension not working?**
- Check API key in settings
- Reload VS Code (Ctrl+K Ctrl+R)
- Verify `.vscode/settings.json`

**Terminal not finding commands?**
- Restart VS Code
- Check PATH includes `C:\Users\umit.topcuoglu\Desktop\geneL`

**API keys not loaded?**
- Terminal reads from `.vscode/settings.json`
- Or manually: `$env:DEEPSEEK_API_KEY = "..."`

---

**Happy coding!** 🚀
