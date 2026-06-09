# AI CLI - Terminal Interface

Terminal'den Deepseek, Claude Pro #1, Claude Pro #2, ve Gemini Pro API'lerini kullan!

## 🚀 Quick Start

```bash
cd ~/Desktop/geneL

# Interactive mode (menu'den seç)
python ai_cli.py

# Direkt mode (belirli API'yi seç)
python ai_cli.py --api deepseek
python ai_cli.py --api claude1
python ai_cli.py --api claude2
python ai_cli.py --api gemini

# Mesaj gönder (tek seferlik)
python ai_cli.py --api deepseek --message "Merhaba"
python ai_cli.py --api claude1 --message "Türkçe yazı yaz"
```

## 📡 Kullanılabilir API'ler

### 1. **Deepseek** (`deepseek`)
```bash
python ai_cli.py --api deepseek
```

### 2. **Claude Pro #1** (`claude1`)
```bash
python ai_cli.py --api claude1
```
Email: `korayumit@gmail.com`

### 3. **Claude Pro #2** (`claude2`)
```bash
python ai_cli.py --api claude2
```
Email: `birumit@yandex.com.tr`

### 4. **Gemini Pro** (`gemini`)
```bash
python ai_cli.py --api gemini
```

## 💬 Örnekler

### Interactive Mode
```
$ python ai_cli.py

==================================================
🤖 AI CLI - Select an AI Service
==================================================
1. [✓] Deepseek
2. [✓] Claude Pro #1 (korayumit@gmail.com)
3. [✓] Claude Pro #2 (birumit@yandex.com.tr)
4. [✓] Gemini Pro
5. Exit
==================================================

Select service (1-5): 1

✅ Selected: Deepseek

📝 Enter your prompt (or 'back' to change API):
> Türkçe bir şarkı yazabilir misin?

🔄 Sending to Deepseek...
--------------------------------------------------
✅ Deepseek Response:

[Response burada görülecek]
```

### Direct Mode (Deepseek)
```bash
$ python ai_cli.py --api deepseek

📝 Enter your prompt (or 'exit' to quit):
> Merhaba, nasılsın?

🔄 Sending to Deepseek...
--------------------------------------------------
✅ Deepseek Response:

Merhaba! Ben iyi durumdayım. Sana nasıl yardımcı olabilirim?
```

### One-Shot Mode
```bash
$ python ai_cli.py --api claude1 --message "Python'da Hello World yazı"

🔄 Sending to Claude Pro #1...
--------------------------------------------------
✅ Claude Pro #1 Response:

print("Hello World")
```

## 🔄 Terminal Commands

```bash
# Interactive mode'de API değiştirmek için:
> back

# Çıkmak için:
> exit
# veya Ctrl+C

# Farklı API test etmek
python ai_cli.py --api deepseek
python ai_cli.py --api claude1
python ai_cli.py --api claude2
python ai_cli.py --api gemini
```

## ✨ Features

- ✅ **4 farklı AI servisi** tek CLI'dan
- ✅ **Interactive mode** - API seçip devamlı sohbet
- ✅ **Direct mode** - Belirli API'yi direkt kullan
- ✅ **One-shot mode** - Tek mesaj gönder ve çık
- ✅ **Email gösterme** - Her Claude hesabının emaili visible
- ✅ **Error handling** - Hata durumunda bilgi ver
- ✅ **API key validation** - Kurmamış API'leri uyar

## 🛠️ Gerekli Kütüphaneler

```
anthropic>=0.25.0      # Claude API
google-generativeai>=0.3.0  # Gemini API
deepseek-api>=1.0.0    # Deepseek API
requests>=2.31.0       # HTTP requests
python-dotenv>=1.0.0   # .env dosya desteği
```

Yüklemek için:
```bash
pip install -r requirements.txt
```

## 📝 Tips

- Her API için farklı use case'ler var - hangisinin iyisi olduğunu dene
- `claude1` ve `claude2` aynı model'i kullanıyor, farklı hesaplar
- Deepseek'i hızlı cevap için dene
- Gemini Pro'yu karmaşık görevler için dene
- Back deyerek API'lar arasında switch yapabilirsin
- Ctrl+C ile anında çıkabilirsin

## 🔐 API Keys

Tüm API key'ler `.env` dosyasında saklanıyor (gitignore'da).

Kontrol et:
```bash
cat .env
```

---

**Enjoy! 🚀**
