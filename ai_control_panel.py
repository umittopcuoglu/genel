#!/usr/bin/env python3
"""
AI Control Panel - Manage Gemini Pro, Claude Pro, and Deepseek APIs
"""

import os
import json
from pathlib import Path
from typing import Dict, List
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import subprocess

# Load environment variables
load_dotenv()

app = Flask(__name__)
PROJECT_DIR = Path(__file__).parent

class AIControlPanel:
    def __init__(self):
        self.config = self.load_config()
        self.apps = self.discover_apps()

    def load_config(self) -> Dict:
        """Load AI credentials from environment"""
        return {
            'gemini_pro': {
                'name': 'Gemini Pro',
                'type': 'business',
                'api_key': os.getenv('GEMINI_API_KEY', ''),
                'status': 'configured' if os.getenv('GEMINI_API_KEY') else 'pending'
            },
            'claude_pro_1': {
                'name': 'Claude Pro #1',
                'type': 'subscription',
                'email': os.getenv('CLAUDE_EMAIL_1', ''),
                'api_key': os.getenv('CLAUDE_API_KEY_1', ''),
                'status': 'configured' if os.getenv('CLAUDE_API_KEY_1') else 'pending'
            },
            'claude_pro_2': {
                'name': 'Claude Pro #2',
                'type': 'subscription',
                'email': os.getenv('CLAUDE_EMAIL_2', ''),
                'api_key': os.getenv('CLAUDE_API_KEY_2', ''),
                'status': 'configured' if os.getenv('CLAUDE_API_KEY_2') else 'pending'
            },
            'deepseek': {
                'name': 'Deepseek',
                'type': 'api',
                'api_key': os.getenv('DEEPSEEK_API_KEY', ''),
                'status': 'configured' if os.getenv('DEEPSEEK_API_KEY') else 'pending'
            }
        }

    def discover_apps(self) -> List[Dict]:
        """Discover applications in the repository"""
        apps = []
        app_dirs = ['openclaw', 'claudex', 'loveable', 'whisper-flow', 'manus']

        for app_name in app_dirs:
            app_path = PROJECT_DIR / app_name
            if app_path.exists():
                git_url = self.get_git_url(app_path)
                apps.append({
                    'name': app_name,
                    'path': str(app_path),
                    'git_url': git_url,
                    'status': 'cloned' if git_url else 'local'
                })

        return apps

    def get_git_url(self, app_path: Path) -> str:
        """Get git remote URL for an application"""
        try:
            result = subprocess.run(
                ['git', 'config', '--get', 'remote.origin.url'],
                cwd=app_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip() if result.returncode == 0 else ''
        except:
            return ''

    def get_status(self) -> Dict:
        """Get overall system status"""
        configured_apis = sum(
            1 for api in self.config.values()
            if api['status'] == 'configured'
        )

        return {
            'total_apis': len(self.config),
            'configured_apis': configured_apis,
            'total_apps': len(self.apps),
            'apis': self.config,
            'apps': self.apps
        }

# Initialize control panel
panel = AIControlPanel()

@app.route('/')
def dashboard():
    """Main dashboard"""
    status = panel.get_status()
    return render_template('dashboard.html', **status)

@app.route('/api/status')
def api_status():
    """API status endpoint"""
    return jsonify(panel.get_status())

@app.route('/api/apps')
def api_apps():
    """Get all applications"""
    return jsonify({'apps': panel.apps})

@app.route('/api/config/<api_name>', methods=['GET', 'POST'])
def api_config(api_name):
    """Get/Set API configuration"""
    if api_name not in panel.config:
        return jsonify({'error': 'API not found'}), 404

    if request.method == 'POST':
        api_key = request.json.get('api_key')
        env_var = api_name.upper()

        # Update .env file
        env_file = PROJECT_DIR / '.env'
        env_content = env_file.read_text() if env_file.exists() else ''

        if f'{env_var}=' in env_content:
            env_content = env_content.replace(
                f'{env_var}={os.getenv(env_var, "")}',
                f'{env_var}={api_key}'
            )
        else:
            env_content += f'\n{env_var}={api_key}\n'

        env_file.write_text(env_content)
        os.environ[env_var] = api_key
        panel.config[api_name]['api_key'] = api_key
        panel.config[api_name]['status'] = 'configured'

        return jsonify({'status': 'success', 'message': f'{api_name} configured'})

    return jsonify(panel.config[api_name])

@app.route('/api/apps/sync', methods=['POST'])
def sync_apps():
    """Sync applications with GitHub"""
    results = []

    for app in panel.apps:
        try:
            app_path = Path(app['path'])
            result = subprocess.run(
                ['git', 'pull'],
                cwd=app_path,
                capture_output=True,
                text=True,
                timeout=30
            )

            results.append({
                'app': app['name'],
                'status': 'success' if result.returncode == 0 else 'failed',
                'message': result.stdout or result.stderr
            })
        except Exception as e:
            results.append({
                'app': app['name'],
                'status': 'error',
                'message': str(e)
            })

    return jsonify({'results': results})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
