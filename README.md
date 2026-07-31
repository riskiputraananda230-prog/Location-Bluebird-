# 🚖 Bot Telegram Bluebird — Rekomendasi Lokasi Driver

Bot Telegram untuk driver Bluebird yang memberikan rekomendasi lokasi jemput berdasarkan posisi GPS dan jam saat ini. Koordinat diverifikasi otomatis via **Google Maps Geocoding API**.

---

## Fitur
- Kirim lokasi → dapat rekomendasi dalam **7 km** sesuai slot waktu
- Jika tidak ada → tombol **Perluas ke 10 km**
- Link **Google Maps** langsung untuk setiap lokasi
- Koordinat **akurat** dari Google Maps (bukan estimasi)
- Hasil di-**cache** → tidak bolak-balik hit API

---

## Cara Deploy ke Railway

### 1. Buat Bot Telegram
1. Buka Telegram, cari **@BotFather**
2. Kirim `/newbot` → ikuti instruksi
3. Simpan **TOKEN** (contoh: `123456:ABCdef...`)

### 2. Buat Google Maps API Key
1. Buka [console.cloud.google.com](https://console.cloud.google.com)
2. Buat project baru
3. Enable **Geocoding API**
4. Buat **API Key** di menu Credentials

### 3. Upload ke GitHub
1. Buat repository baru di [github.com](https://github.com)
2. Upload semua file ini ke repo

### 4. Deploy ke Railway
1. Buka [railway.app](https://railway.app) → Login dengan GitHub
2. **New Project** → **Deploy from GitHub repo** → pilih repo
3. Masuk tab **Variables**, tambahkan 2 variable:
   ```
   BOT_TOKEN    = token_dari_botfather
   GMAPS_API_KEY = api_key_dari_google
   ```
4. Railway otomatis deploy. Cek log di tab **Deployments**

---

## Struktur File
```
bluebird-bot/
├── bot.py           ← Kode utama bot
├── locations.py     ← Data semua lokasi + koordinat fallback
├── geocode.py       ← Verifikasi koordinat via Google Maps API
├── requirements.txt
├── Procfile
├── runtime.txt
└── README.md
```

## Update Lokasi
Edit `locations.py`, lalu hapus `geocache.json` di Railway agar koordinat baru ikut di-geocode ulang.
