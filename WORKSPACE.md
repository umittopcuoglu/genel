# Çalışma Alanı Kuralı (VS Code + Antigravity) — TEK DOĞRU KAYNAK

> Bu dosya, projenin **nerede** ve **hangi branch'te** geliştirileceğinin tek
> referansıdır. İki farklı yerde (VS Code / Antigravity) ve iki Claude oturumunda
> çalışırken karışıklığı önlemek için **herkes buradaki kurala uyar.**

## 1. Tek repo, tek aktif branch

| | Değer |
|---|---|
| **Repo** | `umittopcuoglu/genel` |
| **Aktif geliştirme branch'i** | `claude/ecstatic-gates-paa35d` ← **birleştirilmiş, tek doğru branch** |
| **Aktif proje dizini** | `genel/hotel/` (HotelOps PMS) |
| **`main`** | korunur — doğrudan push YOK |

> ⚠️ **Eski `claude/wonderful-gates-cahvpv` branch'i artık KULLANILMAZ.** İçeriği
> 2026-06-13'te `claude/ecstatic-gates-paa35d`'ye birleştirildi. Yeni iş bu branch'e.
> **Yeni paralel branch AÇMAYIN** — yoksa tekrar iki kol oluşur ve birleştirme gerekir.

## 2. Açılış — her zaman aynı yer

**VS Code:**
```
File → Open Workspace from File… → genel/genel.code-workspace
```
İlk klasör **★ hotel (AKTİF PROJE)**. Backend/frontend ayrı kök olarak da görünür.

**Antigravity:**
```
Open Folder → genel/   (kök; .antigravityrc otomatik okunur)
```

> Her iki araç da **aynı `genel/` klonunu** açar. Makinende projeyi **tek bir yere**
> klonla ve hep orayı aç — farklı kopyalar karışıklığın kaynağıdır.

## 3. İki Claude oturumu / iki cihaz için senkron akışı

Aynı anda iki yerde çalışıyorsan **her oturuma başlamadan önce çek, bitince it:**

```bash
# Başlarken (her zaman):
git checkout claude/ecstatic-gates-paa35d
git pull origin claude/ecstatic-gates-paa35d

# ... değişiklik yap ...

# Bitirince (her zaman):
git add -A
git commit -m "açıklayıcı mesaj"
git push origin claude/ecstatic-gates-paa35d
```

**Kural:** Diğer hesaba/cihaza geçmeden önce **mutlaka push et.** Diğer tarafta
**mutlaka pull et.** Böylece iki kol asla ayrışmaz.

## 4. Hızlı çalıştırma (hotel/)

```bash
# Backend
cd hotel/backend && python -m uvicorn app.main:app --reload     # :8000
# Frontend
cd hotel/frontend && npm run dev                                 # :3000
# Testler
cd hotel/backend && pytest tests/ -q                             # 356 yeşil
# Görsel QA (ekran görüntüleri)
cd hotel/frontend && npx next start -p 3000
cd hotel/qa/e2e && PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers \
  npx playwright test screenshots.spec.ts --project=chromium-light
```

## 5. Durum

- Test: **356 yeşil** · Frontend: **33 route** · Migration: tek head `022`
- Detaylı durum: `hotel/PROJECT_STATUS.md` · Sürüm: `hotel/RELEASE_NOTES.md`
