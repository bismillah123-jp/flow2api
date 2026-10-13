# Flow2API

<div align="center">

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.119.0-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://www.docker.com/)

**Layanan API yang kompatibel penuh dengan OpenAI, menyediakan satu interface terpadu untuk Flow**

</div>

## ❤️ Sponsor

<table>
<tr>
<td width="180" align="center" valign="middle">
  <a href="https://useapi.net/docs/articles/google-flow-api-zh?utm_source=flow2api&utm_medium=referral&utm_campaign=flow2api-sponsor">
    <img src="https://useapi.net/assets/images/sponsor/useapi-banner.png" alt="useapi.net" width="150">
  </a>
</td>
<td valign="top">
  Terima kasih kepada <strong>useapi.net</strong> yang telah mensponsori proyek ini! <strong>Satu langganan, semua API</strong>: useapi.net menyediakan API terkelola untuk akun Googlemu sendiri: <strong>Google Flow</strong> (Veo 3.1, Omni 1.1 Flash dengan audio native, Nano Banana Pro), <strong>Google Vids</strong> (Gemini Omni 1.1 Flash dengan avatar manusia digital berdubbing, <strong>tanpa captcha</strong>, kuota terpisah dari Flow — memakai Flow dan Vids bersamaan di satu akun kira-kira melipatgandakan kapasitas Omni), <strong>Google Flow Music</strong> (lagu utuh dengan Lyria 3.5) dan <strong>Gemini Notebook</strong> (NotebookLM). Baru: <strong>Meta Muse</strong> (muse.ai): buat gambar dan video sekitar 10 detik dengan dialog bersuara memakai akun Musemu sendiri, akun gratis pun bisa. Tidak perlu self-host. Langganan yang sama juga mencakup API Dreamina, Kling, PixVerse, MiniMax, Mureka, Runway, dan lainnya, dengan tarif flat $15/bulan.<a href="https://useapi.net/docs/articles/google-flow-api-zh?utm_source=flow2api&utm_medium=referral&utm_campaign=flow2api-sponsor">Tutorial Flow (Mandarin)</a> · <a href="https://useapi.net/docs/articles/google-vids-api-zh?utm_source=flow2api&utm_medium=referral&utm_campaign=flow2api-sponsor">Tutorial Vids (Mandarin)</a> · <a href="https://useapi.net/docs/articles/muse-api-zh?utm_source=flow2api&utm_medium=referral&utm_campaign=flow2api-sponsor">Tutorial Muse (Mandarin)</a> · <a href="https://buy.stripe.com/8x2aEX4Bd8Vh9PMg4qeUU03?client_reference_id=flow2api">Berlangganan</a><br><br>
  Thanks to <strong>useapi.net</strong> for sponsoring this project! <strong>One subscription, every API</strong>: useapi.net runs hosted APIs on your own Google account: <strong>Google Flow</strong> (Veo 3.1, audio-native Omni 1.1 Flash, Nano Banana Pro), <strong>Google Vids</strong> (Gemini Omni 1.1 Flash with voiced avatars, <strong>no captcha</strong>, an allowance separate from Flow, so using both on one account roughly doubles your Omni capacity), <strong>Google Flow Music</strong> (full songs with Lyria 3.5) and <strong>Gemini Notebook</strong> (NotebookLM). New: <strong>Meta Muse</strong> (muse.ai): images and about 10-second videos with spoken dialogue on your own Muse account, free plan included. Nothing to self-host. The same flat $15/month also covers Dreamina, Kling, PixVerse, MiniMax, Mureka, Runway and more. <a href="https://useapi.net/docs/api-google-flow-v1?utm_source=flow2api&utm_medium=referral&utm_campaign=flow2api-sponsor">Flow docs</a> · <a href="https://useapi.net/docs/api-google-vids-v1?utm_source=flow2api&utm_medium=referral&utm_campaign=flow2api-sponsor">Vids docs</a> · <a href="https://useapi.net/docs/api-muse-v1?utm_source=flow2api&utm_medium=referral&utm_campaign=flow2api-sponsor">Muse docs</a> · <a href="https://buy.stripe.com/8x2aEX4Bd8Vh9PMg4qeUU03?client_reference_id=flow2api">Subscribe</a>
</td>
</tr>
</table>

<table>
<tr>
<td width="180" align="center" valign="middle">
  <a href="https://proxylane.dev/?utm_source=flow2api&utm_medium=partnership&utm_campaign=flow2api_sponsor_202610&utm_content=github_readme">
    <img src="static/sponsors/proxylane-flow2api.png" alt="ProxyLane" width="150">
  </a>
</td>
<td valign="top">
  Terima kasih kepada <strong>ProxyLane</strong> yang telah mensponsori proyek ini! ProxyLane adalah layanan residential proxy yang mencakup 195 negara, 95%+ IP berpredikat risiko rendah oleh Scamalytics, mendukung autentikasi HTTP / SOCKS5 dan username–password. Masukkan proxy ke kolom "proxy protokol" / "proxy captcha" di Token, atau ke "alamat proxy request" global — tulis kota dan nama sesi di username: setiap Token memakai satu IP residential yang sama hingga 72 jam, dan IP pengganti pun tetap di kota yang sama. Antarmuka berbahasa Mandarin, mendukung pembayaran USDT, pembelian pertama dapat diskon 30% dengan kode <strong>FLOW2API30</strong> — daftar lewat <a href="https://proxylane.dev/?utm_source=flow2api&utm_medium=partnership&utm_campaign=flow2api_sponsor_202610&utm_content=github_readme">link ini</a>.<br><br>
  Thanks to <strong>ProxyLane</strong> for sponsoring this project! ProxyLane is a residential proxy service in 195 countries, with 95%+ of IPs rated low risk by Scamalytics and HTTP / SOCKS5 with username and password. Put the proxy into a Token's protocol or captcha proxy, or into the global request proxy, with a city and a session name in the username: each Token keeps one residential IP for up to 72 hours, and a replacement IP stays in the same city. New customers get 30% off the first purchase with code <strong>FLOW2API30</strong>. <a href="https://proxylane.dev/?utm_source=flow2api&utm_medium=partnership&utm_campaign=flow2api_sponsor_202610&utm_content=github_readme_en">Sign up here</a> to get started.
</td>
</tr>
</table>

## ✨ Fitur Utama

- 🎨 **Text-to-image** / **Image-to-image**
- 🎬 **Text-to-video** / **Image-to-video**
- 🎞️ **Video frame awal–akhir**
- 🔄 **Refresh Cookie otomatis** - me-refresh Cookie Google/Flow lengkap secara berkala dan memverifikasi status login, dengan fallback browser `browser`/`personal`; jika login kedaluwarsa, Cookie harus disinkronkan ulang
- 📊 **Tampilan saldo** - query dan tampilkan VideoFX Credits secara real-time
- 🚀 **Load balancing** - round-robin multi-Token dan kontrol konkurensi
- 🌐 **Dukungan proxy** - mendukung proxy HTTP/SOCKS5
- 📱 **Antarmuka web admin** - manajemen Token dan konfigurasi yang intuitif
- 🎨 **Percakapan berkelanjutan untuk pembuatan gambar**
- 🧩 **Kompatibel dengan request body resmi Gemini** - mendukung `generateContent` / `streamGenerateContent`, `systemInstruction`, `contents.parts.text/inlineData/fileData`
- ✅ **Format resmi Gemini sudah diuji menghasilkan gambar** - sudah diverifikasi dengan Token asli bahwa `/models/{model}:generateContent` mengembalikan `candidates[].content.parts[].inlineData` resmi dengan normal

## 🚀 Mulai Cepat

### Persyaratan

- Docker dan Docker Compose (direkomendasikan)
- atau Python 3.8+

- Karena Flow menambahkan captcha tambahan, kamu bisa memilih memakai captcha browser atau captcha pihak ketiga:
  - Daftar [YesCaptcha](https://yescaptcha.com/i/13Xd8K) dan dapatkan API Key, lalu isi di kolom `YesCaptcha API Key` pada halaman konfigurasi sistem.
  - Daftar [CapSolver](https://dashboard.capsolver.com/passport/register?inviteCode=z95yVf1HvixI) dan dapatkan API Key, lalu isi di kolom `CapSolver API Key` pada halaman konfigurasi sistem.
  - Daftar [Captcha.run](https://captcha.run/sso?inviter=36179602-dbd1-4227-8ec8-98f8c0170c59) dan dapatkan API Key, lalu isi di kolom `Captcha.run API Key` pada halaman konfigurasi sistem.
  - Daftar [2Captcha](https://2captcha.com/auth/register/?from=24953866) dan dapatkan API Key, lalu isi di kolom `2Captcha API Key` pada halaman konfigurasi sistem.
- YesCaptcha mendukung pergantian `type` di halaman admin: `RecaptchaV3TaskProxyless`, `RecaptchaV3TaskProxylessM1`, `RecaptchaV3TaskProxylessM1S7`, `RecaptchaV3TaskProxylessM1S9`; default yang direkomendasikan saat ini adalah `M1S9`, S7/S9 akan memaksa submit `minScore` 0.7/0.9.
- `docker-compose.yml` default disarankan dipakai bersama captcha pihak ketiga (yescaptcha/captcharun/twocaptcha/capmonster/ezcaptcha/capsolver).
- Jika butuh captcha headed di dalam Docker (browser/personal), gunakan `docker-compose.headed.yml` di bawah.

- Ekstensi browser yang otomatis mendorong status login Flow terbaru: [Flow2API-Token-Updater](https://github.com/TheSmallHanCat/Flow2API-Token-Updater).

### Cara 1: Deploy Docker (direkomendasikan)

#### Mode standar (tanpa proxy)

```bash
# Clone proyek
git clone https://github.com/TheSmallHanCat/flow2api.git
cd flow2api

# Jalankan layanan
docker-compose up -d

# Lihat log
docker-compose logs -f
```

> Catatan: Compose secara default mem-mount `./tmp:/app/tmp`. Jika timeout cache diset ke `0`, artinya "tidak otomatis dihapus saat kedaluwarsa"; jika ingin file cache tetap ada setelah container dibangun ulang, mount `tmp` ini juga harus dipertahankan.

#### Mode WARP (dengan proxy)

```bash
# Jalankan dengan proxy WARP
docker-compose -f docker-compose.proxy.yml up -d

# Lihat log
docker-compose -f docker-compose.proxy.yml logs -f
```

#### Mode captcha headed di Docker (browser / personal)

> Cocok untuk skenario di mana kamu butuh desktop virtual dan ingin mengaktifkan captcha via browser headed di dalam container.
> Mode ini secara default menjalankan `Xvfb + Fluxbox` untuk visualisasi di dalam container, dan mengatur `ALLOW_DOCKER_HEADED_CAPTCHA=true`.
> Hanya port aplikasi yang dibuka; tidak ada port koneksi remote desktop.
> Browser bawaan `personal` kini berjalan dalam mode headed secara default; untuk sementara beralih kembali ke headless, set environment variable `PERSONAL_BROWSER_HEADLESS=true`.

```bash
# Jalankan mode headed (disarankan pakai --build saat pertama kali)
docker compose -f docker-compose.headed.yml up -d --build

# Lihat log
docker compose -f docker-compose.headed.yml logs -f
```

- Port API: `8000`
- Setelah masuk ke panel admin, set metode captcha ke `browser` atau `personal`

### Cara 2: Deploy lokal

```bash
# Clone proyek
git clone https://github.com/TheSmallHanCat/flow2api.git
cd flow2api

# Buat virtual environment
python -m venv venv

# Aktifkan virtual environment
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Instal dependensi
pip install -r requirements.txt

# Jalankan layanan
python main.py
```

### Akses Pertama

Setelah layanan berjalan, buka panel admin: **http://localhost:8000**, dan segera ganti password setelah login pertama!

- **Username**: `admin`
- **Password**: `admin`

## 📈 Endpoint Pemantauan

- `GET /health`: health check publik, mengembalikan ringkasan — apakah layanan hidup, jumlah Token aktif, Token yang akan kedaluwarsa, Token yang sudah kedaluwarsa, jumlah disable karena 429, dll
- `GET /metrics`: endpoint metrik Prometheus
- `GET /api/tokens`: endpoint admin, mengembalikan status Token `at_expires`, `at_expired`, `at_expiring_within_1h`, `ban_reason`, `consecutive_error_count`, dll

Prometheus bisa langsung scrape `/metrics`. Jika deploy ke Kubernetes, disarankan hanya scrape dari dalam cluster, dan batasi akses eksternal `/metrics` di layer Ingress/Gateway.

### Halaman Uji Model

Buka **http://localhost:8000/test** untuk membuka halaman uji model bawaan, yang mendukung:

- Jelajahi semua model yang tersedia berdasarkan kategori (pembuatan gambar, video dari teks/gambar, video multi-gambar, upscaling video, dll)
- Uji dengan satu klik setelah memasukkan prompt, progres pembuatan ditampilkan secara streaming
- Skenario image-to-image / image-to-video mendukung upload gambar
- Pratinjau gambar atau video langsung setelah pembuatan selesai

## 📋 Model yang Didukung

### Pembuatan Gambar

Saat ini `/v1/models` dan Gemini `/models` mempublikasikan dua seri gambar Nano Banana 2.1 dan Nano Banana 2 Lite, total 30 varian rasio dan resolusi. Nama `gemini-3.1-flash-image-*` yang sudah ada tetap dipertahankan, memanggil Nano Banana 2.1 baru (`BELUGA`). Nama Pro lama `gemini-3.0-pro-image-*` tetap memanggil Nano Banana Pro (`GEM_PIX_2`), tetapi tidak tampil di daftar model. Model Imagen lama sudah tidak didukung; jika model tidak ada, tidak ada fallback ke field upstream lama.

| Nama publik saat ini | Resolusi | Rasio |
|---|---:|---:|
| `gemini-3.1-flash-image-landscape` | Default | Landscape |
| `gemini-3.1-flash-image-portrait` | Default | Portrait |
| `gemini-3.1-flash-image-square` | Default | Square |
| `gemini-3.1-flash-image-four-three` | Default | Landscape 4:3 |
| `gemini-3.1-flash-image-three-four` | Default | Portrait 3:4 |
| `gemini-3.1-flash-image-landscape-2k` | 2K | Landscape |
| `gemini-3.1-flash-image-portrait-2k` | 2K | Portrait |
| `gemini-3.1-flash-image-square-2k` | 2K | Square |
| `gemini-3.1-flash-image-four-three-2k` | 2K | Landscape 4:3 |
| `gemini-3.1-flash-image-three-four-2k` | 2K | Portrait 3:4 |
| `gemini-3.1-flash-image-landscape-4k` | 4K | Landscape |
| `gemini-3.1-flash-image-portrait-4k` | 4K | Portrait |
| `gemini-3.1-flash-image-square-4k` | 4K | Square |
| `gemini-3.1-flash-image-four-three-4k` | 4K | Landscape 4:3 |
| `gemini-3.1-flash-image-three-four-4k` | 4K | Portrait 3:4 |

Nano Banana 2 Lite memakai `gemini-3.1-flash-lite-image-*`, dengan sufiks rasio dan resolusi yang sama seperti tabel di atas, misalnya `gemini-3.1-flash-lite-image-landscape`, `gemini-3.1-flash-lite-image-portrait-2k`, `gemini-3.1-flash-lite-image-square-4k`. Nama sederhana `gemini-3.1-flash-lite-image` juga didukung, dikombinasikan dengan parameter `aspectRatio` / `imageSize`.

Varian 2K/4K diwujudkan lewat upscaling HD setelah pembuatan, bukan berarti Lite secara native mengeluarkan resolusi tersebut. Program utama mengirimkan model, rasio, dan gambar referensi secara eksplisit lewat RPC gambar; captcha browser maupun pihak ketiga hanya menyediakan token captcha. Mode `browser` / `personal` tidak membutuhkan kunci captcha pihak ketiga; request gambar, upload, upscaling, dan video memperoleh captcha sesuai action yang dibutuhkan. Lite tidak otomatis fallback ke model gambar lain.

### Pembuatan Video

Saat ini `/v1/models` dan Gemini `/models` hanya mempublikasikan keluarga model Flow yang aktif. Nama model lama bergaris bawah tetap kompatibel, tetapi tidak lagi tampil di daftar model.

| Nama publik saat ini | Keluarga model upstream | Kemampuan |
|---|---|---|
| `veo-3.1-lite` / `veo-3.1-fast` / `veo-3.1-quality` / `omni-1.1-flash` | Model default saat ini | Video text-to-video landscape 8 detik |
| `veo-3.1-lite-{4,6,8}s-{landscape,portrait}` | Veo 3.1 - Lite | Text-to-video |
| `veo-3.1-fast-{4,6,8}s-{landscape,portrait}` | Veo 3.1 - Fast | Text-to-video |
| `veo-3.1-quality-{4,6,8}s-{landscape,portrait}` | Veo 3.1 - Quality | Text-to-video |
| `omni-1.1-flash-{4,6,8,10}s-{landscape,portrait}` | Omni 1.1 Flash (`abra`) | Text-to-video / video gambar referensi |
| `veo-3.1-{lite,fast,quality}-i2v-{4,6}s-{landscape,portrait}` | Veo 3.1 | Video frame awal / frame awal–akhir |
| `veo-3.1-{lite,fast}-r2v-8s-{landscape,portrait}` | Veo 3.1 | Video multi gambar referensi |
| `veo-3.1-{lite,fast,quality}-extend-8s-{landscape,portrait}` | Veo 3.1 | Lanjutan video |

Kurung kurawal di tabel berarti pilih salah satu nilai. Misalnya `veo-3.1-fast-{4,6,8}s-{landscape,portrait}` mencakup kombinasi 4/6/8 detik dengan landscape/portrait.

#### Omni 1.1 Flash

`Omni 1.1 Flash` mendukung text-to-video maupun video gambar referensi. Caller memakai nama model yang sama, layanan otomatis memilih mode pembuatan berdasarkan apakah request memuat gambar:

- `omni-1.1-flash` adalah alias default dari `omni-1.1-flash-8s-landscape`.
- Nama model lengkapnya `omni-1.1-flash-{4,6,8,10}s-{landscape,portrait}`, bisa memilih 4, 6, 8, atau 10 detik serta landscape atau portrait.
- Jika hanya teks yang dikirim, dipakai mode text-to-video; jika 1–3 gambar `image_url` dikirim, dipakai mode video gambar referensi.
- Durasi dan orientasi frame ditentukan oleh nama model, tidak perlu mengirim parameter bernama sama secara terpisah.

Contoh request video gambar referensi:

```json
{
  "model": "omni-1.1-flash-8s-landscape",
  "messages": [
    {
      "role": "user",
      "content": [
        { "type": "text", "text": "Biarkan orang di dalam frame berbalik dengan alami dan menatap kamera" },
        {
          "type": "image_url",
          "image_url": {
            "url": "data:image/jpeg;base64,<gambar_referensi_base64>"
          }
        }
      ]
    }
  ],
  "stream": true
}
```

#### Nama lama (kompatibilitas): Text-to-video (T2V - Text to Video)
⚠️ **Tidak mendukung upload gambar**

| Nama model | Keterangan| Ukuran |
|---------|---------|--------|
| `veo_3_1_t2v_fast_portrait` | Text-to-video | Portrait |
| `veo_3_1_t2v_fast_landscape` | Text-to-video | Landscape |
| `veo_3_1_t2v_fast_portrait_ultra` | Text-to-video | Portrait |
| `veo_3_1_t2v_fast_ultra` | Text-to-video | Landscape |
| `veo_3_1_t2v_fast_portrait_ultra_relaxed` | Text-to-video | Portrait |
| `veo_3_1_t2v_fast_ultra_relaxed` | Text-to-video | Landscape |
| `veo_3_1_t2v_portrait` | Text-to-video | Portrait |
| `veo_3_1_t2v_landscape` | Text-to-video | Landscape |
| `veo_3_1_t2v_landscape_4s` | Text-to-video 4 detik | Landscape |
| `veo_3_1_t2v_portrait_4s` | Text-to-video 4 detik | Portrait |
| `veo_3_1_t2v_landscape_6s` | Text-to-video 6 detik | Landscape |
| `veo_3_1_t2v_portrait_6s` | Text-to-video 6 detik | Portrait |
| `veo_3_1_t2v_fast_landscape_4s` | Text-to-video Fast 4 detik | Landscape |
| `veo_3_1_t2v_fast_portrait_4s` | Text-to-video Fast 4 detik | Portrait |
| `veo_3_1_t2v_fast_landscape_6s` | Text-to-video Fast 6 detik | Landscape |
| `veo_3_1_t2v_fast_portrait_6s` | Text-to-video Fast 6 detik | Portrait |
| `veo_3_1_t2v_lite_portrait` | Text-to-video Lite | Portrait |
| `veo_3_1_t2v_lite_landscape` | Text-to-video Lite | Landscape |
| `veo_3_1_t2v_lite_4s_portrait` | Text-to-video Lite 4 detik | Portrait |
| `veo_3_1_t2v_lite_4s_landscape` | Text-to-video Lite 4 detik | Landscape |
| `veo_3_1_t2v_lite_6s_portrait` | Text-to-video Lite 6 detik | Portrait |
| `veo_3_1_t2v_lite_6s_landscape` | Text-to-video Lite 6 detik | Landscape |

#### Nama lama (kompatibilitas): Model frame awal–akhir (I2V - Image to Video)
📸 **Mendukung 1–2 gambar: 1 gambar sebagai frame awal, 2 gambar sebagai frame awal dan akhir**

> 💡 **Adaptasi otomatis**: sistem otomatis memilih `model_key` yang sesuai berdasarkan jumlah gambar
> - **Mode satu frame** (1 gambar): membuat video dari frame awal
> - **Mode dua frame** (2 gambar): membuat video transisi dari frame awal + frame akhir
> - `veo_3_1_i2v_lite_*` hanya mendukung **1** gambar frame awal
> - `veo_3_1_interpolation_lite_*` hanya mendukung **2** gambar frame awal–akhir

| Nama model | Keterangan| Ukuran |
|---------|---------|--------|
| `veo_3_1_i2v_s_fast_portrait_fl` | Image-to-video | Portrait |
| `veo_3_1_i2v_s_fast_fl` | Image-to-video | Landscape |
| `veo_3_1_i2v_s_fast_portrait_ultra_fl` | Image-to-video | Portrait |
| `veo_3_1_i2v_s_fast_ultra_fl` | Image-to-video | Landscape |
| `veo_3_1_i2v_s_fast_portrait_ultra_relaxed` | Image-to-video | Portrait |
| `veo_3_1_i2v_s_fast_ultra_relaxed` | Image-to-video | Landscape |
| `veo_3_1_i2v_s_portrait` | Image-to-video | Portrait |
| `veo_3_1_i2v_s_landscape` | Image-to-video | Landscape |
| `veo_3_1_i2v_s_landscape_4s` | Image-to-video 4 detik | Landscape |
| `veo_3_1_i2v_s_portrait_4s` | Image-to-video 4 detik | Portrait |
| `veo_3_1_i2v_s_landscape_6s` | Image-to-video 6 detik | Landscape |
| `veo_3_1_i2v_s_portrait_6s` | Image-to-video 6 detik | Portrait |
| `veo_3_1_i2v_s_fast_landscape_4s_fl` | Image-to-video Fast 4 detik | Landscape |
| `veo_3_1_i2v_s_fast_portrait_4s_fl` | Image-to-video Fast 4 detik | Portrait |
| `veo_3_1_i2v_s_fast_landscape_6s_fl` | Image-to-video Fast 6 detik | Landscape |
| `veo_3_1_i2v_s_fast_portrait_6s_fl` | Image-to-video Fast 6 detik | Portrait |
| `veo_3_1_i2v_lite_portrait` | Image-to-video Lite (hanya frame awal) | Portrait |
| `veo_3_1_i2v_lite_landscape` | Image-to-video Lite (hanya frame awal) | Landscape |
| `veo_3_1_i2v_lite_4s_portrait` | Image-to-video Lite 4 detik (hanya frame awal) | Portrait |
| `veo_3_1_i2v_lite_4s_landscape` | Image-to-video Lite 4 detik (hanya frame awal) | Landscape |
| `veo_3_1_i2v_lite_6s_portrait` | Image-to-video Lite 6 detik (hanya frame awal) | Portrait |
| `veo_3_1_i2v_lite_6s_landscape` | Image-to-video Lite 6 detik (hanya frame awal) | Landscape |
| `veo_3_1_interpolation_lite_portrait` | Image-to-video Lite (transisi frame awal–akhir) | Portrait |
| `veo_3_1_interpolation_lite_landscape` | Image-to-video Lite (transisi frame awal–akhir) | Landscape |
| `veo_3_1_interpolation_lite_4s_portrait` | Image-to-video Lite 4 detik (transisi frame awal–akhir) | Portrait |
| `veo_3_1_interpolation_lite_4s_landscape` | Image-to-video Lite 4 detik (transisi frame awal–akhir) | Landscape |
| `veo_3_1_interpolation_lite_6s_portrait` | Image-to-video Lite 6 detik (transisi frame awal–akhir) | Portrait |
| `veo_3_1_interpolation_lite_6s_landscape` | Image-to-video Lite 6 detik (transisi frame awal–akhir) | Landscape |

#### Nama lama (kompatibilitas): Pembuatan multi-gambar (R2V - Reference Images to Video)
🖼️ **Mendukung banyak gambar**

> **Pembaruan 2026-03-06**
>
> - Sudah disinkronkan dengan request body `R2V` versi terbaru dari upstream
> - `textInput` sudah beralih ke `structuredPrompt.parts`
> - Level teratas menambahkan `mediaGenerationContext.batchId`
> - Level teratas menambahkan `useV2ModelConfig: true`
> - Model `R2V` landscape / portrait berbagi satu request body versi baru yang sama
> - `videoModelKey` upstream untuk `R2V` landscape sudah beralih ke bentuk `*_landscape`
> - Sesuai protokol upstream saat ini, `referenceImages` maksimal **3** gambar

| Nama model | Keterangan| Ukuran |
|---------|---------|--------|
| `veo_3_1_r2v_fast_portrait` | Image-to-video | Portrait |
| `veo_3_1_r2v_fast_landscape` | Image-to-video | Landscape |
| `veo_3_1_r2v_fast_portrait_ultra` | Image-to-video | Portrait |
| `veo_3_1_r2v_fast_landscape_ultra` | Image-to-video | Landscape |
| `veo_3_1_r2v_fast_portrait_ultra_relaxed` | Image-to-video | Portrait |
| `veo_3_1_r2v_fast_landscape_ultra_relaxed` | Image-to-video | Landscape |

#### Nama lama (kompatibilitas): Model upscaling video (Upsample)

Model-model ini tidak langsung memanggil kunci upsampler upstream, melainkan membuat video dulu dengan model Veo 3.1 biasa yang sesuai, lalu mengirim request upscaling 1080P/4K.

| Nama model | Keterangan | Output |
|---------|---------|--------|
| `veo_3_1_t2v_landscape_4k` | Upscale text-to-video | 4K |
| `veo_3_1_t2v_portrait_4k` | Upscale text-to-video | 4K |
| `veo_3_1_t2v_landscape_1080p` | Upscale text-to-video | 1080P |
| `veo_3_1_t2v_portrait_1080p` | Upscale text-to-video | 1080P |
| `veo_3_1_t2v_landscape_4s_4k` | Upscale text-to-video 4 detik | 4K |
| `veo_3_1_t2v_portrait_4s_4k` | Upscale text-to-video 4 detik | 4K |
| `veo_3_1_t2v_landscape_4s_1080p` | Upscale text-to-video 4 detik | 1080P |
| `veo_3_1_t2v_portrait_4s_1080p` | Upscale text-to-video 4 detik | 1080P |
| `veo_3_1_t2v_landscape_6s_4k` | Upscale text-to-video 6 detik | 4K |
| `veo_3_1_t2v_portrait_6s_4k` | Upscale text-to-video 6 detik | 4K |
| `veo_3_1_t2v_landscape_6s_1080p` | Upscale text-to-video 6 detik | 1080P |
| `veo_3_1_t2v_portrait_6s_1080p` | Upscale text-to-video 6 detik | 1080P |
| `veo_3_1_t2v_fast_portrait_4k` | Upscale text-to-video | 4K |
| `veo_3_1_t2v_fast_4k` | Upscale text-to-video | 4K |
| `veo_3_1_t2v_fast_portrait_ultra_4k` | Upscale text-to-video | 4K |
| `veo_3_1_t2v_fast_ultra_4k` | Upscale text-to-video | 4K |
| `veo_3_1_t2v_fast_portrait_1080p` | Upscale text-to-video | 1080P |
| `veo_3_1_t2v_fast_1080p` | Upscale text-to-video | 1080P |
| `veo_3_1_t2v_fast_portrait_ultra_1080p` | Upscale text-to-video | 1080P |
| `veo_3_1_t2v_fast_ultra_1080p` | Upscale text-to-video | 1080P |
| `veo_3_1_i2v_s_fast_portrait_ultra_fl_4k` | Upscale image-to-video | 4K |
| `veo_3_1_i2v_s_fast_ultra_fl_4k` | Upscale image-to-video | 4K |
| `veo_3_1_i2v_s_fast_portrait_ultra_fl_1080p` | Upscale image-to-video | 1080P |
| `veo_3_1_i2v_s_fast_ultra_fl_1080p` | Upscale image-to-video | 1080P |
| `veo_3_1_i2v_s_landscape_4k` | Upscale image-to-video | 4K |
| `veo_3_1_i2v_s_portrait_4k` | Upscale image-to-video | 4K |
| `veo_3_1_i2v_s_landscape_1080p` | Upscale image-to-video | 1080P |
| `veo_3_1_i2v_s_portrait_1080p` | Upscale image-to-video | 1080P |
| `veo_3_1_i2v_s_landscape_4s_4k` | Upscale image-to-video 4 detik | 4K |
| `veo_3_1_i2v_s_portrait_4s_4k` | Upscale image-to-video 4 detik | 4K |
| `veo_3_1_i2v_s_landscape_4s_1080p` | Upscale image-to-video 4 detik | 1080P |
| `veo_3_1_i2v_s_portrait_4s_1080p` | Upscale image-to-video 4 detik | 1080P |
| `veo_3_1_i2v_s_landscape_6s_4k` | Upscale image-to-video 6 detik | 4K |
| `veo_3_1_i2v_s_portrait_6s_4k` | Upscale image-to-video 6 detik | 4K |
| `veo_3_1_i2v_s_landscape_6s_1080p` | Upscale image-to-video 6 detik | 1080P |
| `veo_3_1_i2v_s_portrait_6s_1080p` | Upscale image-to-video 6 detik | 1080P |
| `veo_3_1_r2v_fast_portrait_ultra_4k` | Upscale video multi-gambar | 4K |
| `veo_3_1_r2v_fast_landscape_ultra_4k` | Upscale video multi-gambar | 4K |
| `veo_3_1_r2v_fast_portrait_ultra_1080p` | Upscale video multi-gambar | 1080P |
| `veo_3_1_r2v_fast_landscape_ultra_1080p` | Upscale video multi-gambar | 1080P |

## 📡 Contoh Penggunaan API (wajib pakai streaming)

> Selain contoh `OpenAI-compatible` di bawah, layanan juga mendukung format resmi Gemini:
> - `POST /v1beta/models/{model}:generateContent`
> - `POST /models/{model}:generateContent`
> - `POST /v1beta/models/{model}:streamGenerateContent`
> - `POST /models/{model}:streamGenerateContent`
>
> Format resmi Gemini mendukung metode autentikasi berikut:
> - `Authorization: Bearer <api_key>`
> - `x-goog-api-key: <api_key>`
> - `?key=<api_key>`
>
> Request body gambar resmi Gemini sudah kompatibel:
> - `systemInstruction`
> - `contents[].parts[].text`
> - `contents[].parts[].inlineData`
> - `contents[].parts[].fileData.fileUri`
> - `generationConfig.responseModalities`
> - `generationConfig.imageConfig.aspectRatio`
> - `generationConfig.imageConfig.imageSize`

### generateContent resmi Gemini (text-to-image)

> Sudah diuji langsung dengan Token asli dan lolos.
> Untuk respons streaming, ganti path dengan `:streamGenerateContent?alt=sse`.

```bash
curl -X POST "http://localhost:8000/models/gemini-3.1-flash-image:generateContent" \
  -H "x-goog-api-key: han1234" \
  -H "Content-Type: application/json" \
  -d '{
    "systemInstruction": {
      "parts": [
        {
          "text": "Return an image only."
        }
      ]
    },
    "contents": [
      {
        "role": "user",
        "parts": [
          {
            "text": "Sebuah apel merah di atas meja kayu, pencahayaan studio, latar minimalis"
          }
        ]
      }
    ],
    "generationConfig": {
      "responseModalities": ["IMAGE"],
      "imageConfig": {
        "aspectRatio": "1:1",
        "imageSize": "1K"
      }
    }
  }'
```

### Text-to-image

```bash
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Authorization: Bearer han1234" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-3.1-flash-image-landscape",
    "messages": [
      {
        "role": "user",
        "content": "Seekor kucing lucu bermain di taman"
      }
    ],
    "stream": true
  }'
```

### Image-to-image

```bash
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Authorization: Bearer han1234" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-3.1-flash-image-landscape",
    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": "Ubah gambar ini menjadi gaya cat air"
          },
          {
            "type": "image_url",
            "image_url": {
              "url": "data:image/jpeg;base64,<base64_encoded_image>"
            }
          }
        ]
      }
    ],
    "stream": true
  }'
```

### Text-to-video

```bash
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Authorization: Bearer han1234" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "veo-3.1-fast-8s-landscape",
    "messages": [
      {
        "role": "user",
        "content": "Seekor anak kucing mengejar kupu-kupu di rumput"
      }
    ],
    "stream": true
  }'
```

### Membuat video dari frame awal–akhir

```bash
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Authorization: Bearer han1234" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "veo-3.1-fast-i2v-4s-landscape",
    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": "Transisi dari gambar pertama ke gambar kedua"
          },
          {
            "type": "image_url",
            "image_url": {
              "url": "data:image/jpeg;base64,<frame_awal_base64>"
            }
          },
          {
            "type": "image_url",
            "image_url": {
              "url": "data:image/jpeg;base64,<frame_akhir_base64>"
            }
          }
        ]
      }
    ],
    "stream": true
  }'
```

### Membuat video multi-gambar

> `R2V` dirakit otomatis oleh server menjadi request body video versi baru, caller cukup memakai input OpenAI-compatible.
> Server otomatis memetakan `R2V` landscape ke kunci model upstream `*_landscape` terbaru.
> Maksimal **3** gambar referensi saat ini.

```bash
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Authorization: Bearer han1234" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "veo-3.1-fast-r2v-8s-portrait",
    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": "Berdasarkan karakter dan adegan dari tiga gambar referensi, buat video portrait dengan gerakan kamera push-in yang mulus"
          },
          {
            "type": "image_url",
            "image_url": {
              "url": "data:image/jpeg;base64/<gambar_referensi1_base64>"
            }
          },
          {
            "type": "image_url",
            "image_url": {
              "url": "data:image/jpeg;base64/<gambar_referensi2_base64>"
            }
          },
          {
            "type": "image_url",
            "image_url": {
              "url": "data:image/jpeg;base64/<gambar_referensi3_base64>"
            }
          }
        ]
      }
    ],
    "stream": true
  }'
```

---

## 📄 Lisensi

Proyek ini memakai lisensi MIT. Lihat file [LICENSE](LICENSE) untuk detail.

---

## 🙏 Ucapan Terima Kasih

- [PearNoDec](https://github.com/PearNoDec) atas solusi captcha YesCaptcha
- [raomaiping](https://github.com/raomaiping) atas solusi captcha headless
Terima kasih atas dukungan semua kontributor dan pengguna!

---

## 📞 Kontak

- Laporkan Issue: [GitHub Issues](https://github.com/TheSmallHanCat/flow2api/issues)

---

**⭐ Jika proyek ini membantumu, beri Star!**

## Star History

[![Star History Chart](https://star-history.dera.page/svg?repos=TheSmallHanCat/flow2api&type=date&legend=top-left)](https://star-history.dera.page/#TheSmallHanCat/flow2api&type=date&legend=top-left)
