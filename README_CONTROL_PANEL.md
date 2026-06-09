# AI Control Panel

Manage all your AI services in one place:
- **Gemini Pro** (Business Account)
- **Claude Pro** (x2 Accounts)
- **Deepseek** (API)

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Keys:**
   Edit `.env` file with your API keys:
   ```
   GEMINI_API_KEY=your_key
   CLAUDE_API_KEY_1=your_key
   CLAUDE_API_KEY_2=your_key
   DEEPSEEK_API_KEY=your_key
   ```

3. **Run the Control Panel:**
   ```bash
   python ai_control_panel.py
   ```

4. **Access Dashboard:**
   Open your browser: `http://localhost:5000`

## Features

- ✅ Centralized API management
- ✅ Configure/test all AI services
- ✅ Manage applications (GitHub sync)
- ✅ Real-time status monitoring
- ✅ Easy onboarding for new APIs

## Environment Variables

```
DEEPSEEK_API_KEY     - Deepseek API key
GEMINI_API_KEY       - Google Gemini Pro API key
CLAUDE_API_KEY_1     - First Claude Pro API key
CLAUDE_API_KEY_2     - Second Claude Pro API key
GITHUB_PAT           - GitHub Personal Access Token
```

## API Endpoints

- `GET /api/status` - Get system status
- `GET /api/apps` - List all applications
- `POST /api/config/<api_name>` - Configure API
- `POST /api/apps/sync` - Sync applications with GitHub

## Applications

All your applications are automatically discovered:
- openclaw
- claudex
- loveable
- whisper-flow
- manus

Each application is synchronized with its GitHub repository.
