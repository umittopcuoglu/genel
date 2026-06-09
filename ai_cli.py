#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI CLI - Terminal interface for Deepseek, Claude Pro #1, Claude Pro #2, and Gemini Pro
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import argparse

# Fix Windows encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
load_dotenv()

class AICLI:
    def __init__(self):
        self.apis = {
            'deepseek': {
                'name': 'Deepseek',
                'key': os.getenv('DEEPSEEK_API_KEY', ''),
                'client': None
            },
            'claude1': {
                'name': 'Koray',
                'email': os.getenv('CLAUDE_EMAIL_1', ''),
                'key': os.getenv('CLAUDE_API_KEY_1', ''),
                'client': None
            },
            'claude2': {
                'name': 'Umit',
                'email': os.getenv('CLAUDE_EMAIL_2', ''),
                'key': os.getenv('CLAUDE_API_KEY_2', ''),
                'client': None
            },
            'gemini': {
                'name': 'Gemini Pro',
                'key': os.getenv('GEMINI_API_KEY', ''),
                'client': None
            },
            'openrouter': {
                'name': 'OpenRouter',
                'key': os.getenv('OPENROUTER_API_KEY', ''),
                'client': None
            }
        }
        self.current_api = None
        self._init_clients()

    def _init_clients(self):
        """Initialize API clients"""
        try:
            import anthropic
            if self.apis['claude1']['key']:
                self.apis['claude1']['client'] = anthropic.Anthropic(
                    api_key=self.apis['claude1']['key']
                )
            if self.apis['claude2']['key']:
                self.apis['claude2']['client'] = anthropic.Anthropic(
                    api_key=self.apis['claude2']['key']
                )
        except ImportError:
            pass

        try:
            import google.generativeai as genai
            if self.apis['gemini']['key']:
                genai.configure(api_key=self.apis['gemini']['key'])
                self.apis['gemini']['client'] = genai
        except ImportError:
            pass

        try:
            from deepseek import Deepseek
            if self.apis['deepseek']['key']:
                self.apis['deepseek']['client'] = Deepseek(
                    api_key=self.apis['deepseek']['key']
                )
        except ImportError:
            pass

    def show_menu(self):
        """Display available APIs"""
        print("\n" + "="*50)
        print("🤖 AI CLI - Select an AI Service")
        print("="*50)

        for i, (key, api) in enumerate(self.apis.items(), 1):
            status = "✓" if api['key'] else "✗"
            if 'email' in api:
                print(f"{i}. [{status}] {api['name']} ({api['email']})")
            else:
                print(f"{i}. [{status}] {api['name']}")

        print(f"{len(self.apis)+1}. Exit")
        print("="*50)

    def get_user_input(self):
        """Get user choice"""
        while True:
            try:
                choice = input("\nSelect service (1-5): ").strip()
                choice_num = int(choice)

                if choice_num == len(self.apis) + 1:
                    return None

                if 1 <= choice_num <= len(self.apis):
                    api_key = list(self.apis.keys())[choice_num - 1]
                    return api_key

                print(f"❌ Invalid choice. Please enter 1-{len(self.apis)+1}")
            except ValueError:
                print("❌ Please enter a valid number")

    def send_message(self, api_key, message):
        """Send message to selected API"""
        api = self.apis[api_key]

        if not api['key']:
            print(f"❌ {api['name']} API key not configured")
            return

        print(f"\n🔄 Sending to {api['name']}...")
        print("-" * 50)

        try:
            if api_key == 'deepseek':
                response = self._query_deepseek(message)
            elif api_key.startswith('claude'):
                response = self._query_claude(api_key, message)
            elif api_key == 'gemini':
                response = self._query_gemini(message)
            elif api_key == 'openrouter':
                response = self._query_openrouter(message)

            if response:
                print(f"\n✅ {api['name']} Response:\n")
                print(response)
                print("\n" + "-" * 50)
        except Exception as e:
            print(f"❌ Error: {str(e)}")

    def _query_claude(self, api_key, message):
        """Query Claude API"""
        client = self.apis[api_key]['client']
        if not client:
            return "Claude client not initialized"

        try:
            response = client.messages.create(
                model="claude-opus-4-1",
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": message}
                ]
            )
            return response.content[0].text
        except Exception as e:
            return f"Error: {str(e)}"

    def _query_gemini(self, message):
        """Query Gemini API"""
        try:
            genai = self.apis['gemini']['client']

            # Try newer models first
            models_to_try = ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-pro']

            for model_name in models_to_try:
                try:
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(message)
                    return response.text
                except Exception as model_error:
                    error_str = str(model_error)
                    if "quota" in error_str.lower():
                        return (
                            "Gemini API quota exceeded. Please upgrade:\n"
                            "1. Go to: https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com\n"
                            "2. Enable Generative AI API\n"
                            "3. Set up billing in Google Cloud Console\n"
                            "4. Try again after quota refresh"
                        )
                    continue

            return "Gemini API: No available models. Please check your API key and quota."

        except Exception as e:
            return f"Gemini Error: {str(e)}"

    def _query_deepseek(self, message):
        """Query Deepseek API"""
        try:
            import requests
            api_key = self.apis['deepseek']['key']

            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }

            data = {
                'model': 'deepseek-chat',
                'messages': [
                    {'role': 'user', 'content': message}
                ],
                'stream': False
            }

            response = requests.post(
                'https://api.deepseek.com/chat/completions',
                headers=headers,
                json=data
            )

            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error: {str(e)}"

    def _query_openrouter(self, message):
        """Query OpenRouter API"""
        try:
            import requests
            api_key = self.apis['openrouter']['key']

            headers = {
                'Authorization': f'Bearer {api_key}',
                'HTTP-Referer': 'https://github.com/umittopcuoglu/genel',
                'X-Title': 'Genel AI CLI',
                'Content-Type': 'application/json'
            }

            data = {
                'model': 'openrouter/auto',
                'messages': [
                    {'role': 'user', 'content': message}
                ],
                'max_tokens': 1024
            }

            response = requests.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers=headers,
                json=data
            )

            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error: {str(e)}"

    def interactive_mode(self):
        """Interactive CLI mode"""
        print("\n🚀 AI CLI - Interactive Mode")

        while True:
            self.show_menu()
            api_key = self.get_user_input()

            if not api_key:
                print("\n👋 Goodbye!")
                break

            api = self.apis[api_key]
            print(f"\n✅ Selected: {api['name']}")

            while True:
                try:
                    message = input(f"\n📝 Enter your prompt (or 'back' to change API):\n> ").strip()

                    if message.lower() == 'back':
                        break

                    if not message:
                        print("❌ Please enter a valid prompt")
                        continue

                    self.send_message(api_key, message)

                except KeyboardInterrupt:
                    print("\n\n⚠️ Interrupted by user")
                    return

def main():
    parser = argparse.ArgumentParser(
        description='AI CLI - Terminal interface for multiple AI services'
    )
    parser.add_argument(
        '--api',
        choices=['deepseek', 'claude1', 'claude2', 'gemini', 'openrouter'],
        help='Specify API directly'
    )
    parser.add_argument(
        '--message', '-m',
        help='Message to send'
    )

    args = parser.parse_args()

    cli = AICLI()

    # Direct mode with --api and --message
    if args.api and args.message:
        cli.send_message(args.api, args.message)
    # Direct mode with just --api
    elif args.api:
        print(f"Selected: {cli.apis[args.api]['name']}")
        while True:
            try:
                message = input("\n📝 Enter your prompt (or 'exit' to quit):\n> ").strip()
                if message.lower() == 'exit':
                    break
                if message:
                    cli.send_message(args.api, message)
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
    # Interactive mode
    else:
        cli.interactive_mode()

if __name__ == '__main__':
    main()
