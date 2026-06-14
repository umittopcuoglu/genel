# HotelOps — Firebase Deploy Rehberi

## Gereksinimler
- Node.js 18+
- Firebase CLI: `npm install -g firebase-tools`
- Google Cloud hesabi (Firebase projesi icin)
- (Opsiyonel) Docker — backend icin Cloud Run kullanacaksan

---

## Adim 1: Firebase Projesi Olustur

```bash
firebase login
firebase projects:create hotelops-demo
firebase init hosting
```

Sorulara su cevaplari verin:
- Public directory: `frontend/out`
- Single-page app: **Yes**
- GitHub auto deploy: **No** (sonra ekleyebilirsiniz)

---

## Adim 2: Frontend Build (Static Export)

```bash
cd hotel/frontend
npm install
npx next build
```

Bu `out/` klasorunu olusturur — tum sayfalar static HTML.

---

## Adim 3: Sadece Frontend Deploy (Backend olmadan)

```bash
cd hotel
firebase deploy --only hosting
```

Demo URL: `https://hotelops-demo.web.app`

Tum sayfalar mock veriyle calisir, tema secici ve dil degistirici aktif.

---

## Adim 4: Backend Deploy (Cloud Run — opsiyonel)

Backend'i de istiyorsan:

```bash
# Google Cloud CLI gerekli
gcloud auth login
gcloud config set project hotelops-demo

# Docker imaji olustur ve push et
cd hotel
gcloud builds submit --tag gcr.io/hotelops-demo/hotelops-api -f Dockerfile.cloudrun .

# Cloud Run'a deploy et
gcloud run deploy hotelops-api \
  --image gcr.io/hotelops-demo/hotelops-api \
  --region europe-west1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --set-env-vars="DATABASE_URL=sqlite+aiosqlite:///./dev.db"
```

Cloud Run URL'ini alinca frontend'e baglama:

```bash
cd hotel/frontend
echo "NEXT_PUBLIC_API_URL=https://hotelops-api-xxxxx-ew.a.run.app" > .env.local
npx next build
cd ..
firebase deploy --only hosting
```

---

## Hizli Baslangiç (sadece frontend demo)

```powershell
cd C:\Users\umit\Desktop\genel\hotel\frontend
npm install
npx next build
cd ..
firebase deploy --only hosting
```

Bu kadar! Tum 33 sayfa mock veriyle calisir.

---

## Notlar
- Firebase Hosting ucretsiz (Spark plan, 10 GB/ay bandwidth)
- Cloud Run ucretsiz katman: 2M istek/ay
- SQLite Cloud Run'da gecici — production icin Cloud SQL (PostgreSQL) oneriyoruz
- `firebase.json` API isteklerini Cloud Run'a yonlendirir (`/api/**` -> Cloud Run)
