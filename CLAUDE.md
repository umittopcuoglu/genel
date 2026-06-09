# Genel Project - Claude Code Configuration

## Project Structure

```
genel/
├── openclaw/        # OpenClaw application
├── claudex/         # ClaudeX application
├── loveable/        # Loveable application
├── whisper-flow/    # Whisper Flow application
├── manus/           # Manus application
├── .env             # Environment variables (API keys)
├── README.md        # Project documentation
└── CLAUDE.md        # This file
```

## Environment Variables

### Deepseek API
- **Key**: `DEEPSEEK_API_KEY`
- **Location**: `.env` file
- **Value**: `sk-928b49e165f44517b815b69b98a2ab07`

### GitHub PAT
- **Key**: `GITHUB_PAT`
- **Location**: `.env` file
- **User**: `umit.topcuoglu`

## Applications

1. **openclaw** - OpenClaw application
   - Location: `~/Desktop/geneL/openclaw`
   - Git: https://github.com/openclaw/openclaw.git

2. **claudex** - ClaudeX application
   - Location: `~/Desktop/geneL/claudex`
   - Git: https://github.com/tct68/claudex.git

3. **loveable** - Loveable application
   - Location: `~/Desktop/geneL/loveable`

4. **whisper-flow** - Whisper Flow application
   - Location: `~/Desktop/geneL/whisper-flow`

5. **manus** - Manus application
   - Location: `~/Desktop/geneL/manus`

## Claude Code Access

All applications are accessible via Claude Code:
- Working directory: `~/Desktop/geneL`
- Git repository: Initialized and configured
- API keys: Available via `.env` file
- All applications: Available for development and testing

## VS Code Configuration

VS Code workspace file: `genel.code-workspace`

Open with:
```powershell
code ~/Desktop/geneL
```

## Antigravity Access

The project is configured for Antigravity IDE access:
- Open: Antigravity → Open Folder → `~/Desktop/geneL`
- API Key: Available in `.env`
- All applications: Ready for development

## Development Notes

- All applications are in the same git repository
- Use `.env` for sensitive configuration
- API keys are gitignored
- Each application can be developed independently
