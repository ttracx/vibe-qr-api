# 🎨 Vibe QR API

Fast, beautiful QR code generation API. Built with FastAPI.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://dashboard.render.com/select-repo?type=web&search=vibe-qr-api)

**Live API:** https://vibe-qr-api.onrender.com

## ✨ Features

- **Custom Colors** - Set foreground/background colors
- **Logo Embedding** - Add your brand logo to QR codes
- **Multiple Styles** - Square, rounded, or circle modules
- **SVG Support** - Vector output for print quality
- **Bulk Generation** - Up to 50 QR codes per request
- **Error Correction** - L/M/Q/H levels

## 🚀 Quick Start

### Generate a QR Code

```bash
curl -X POST https://vibe-qr-api.onrender.com/generate \
  -H "Content-Type: application/json" \
  -d '{"data": "https://example.com"}' | jq -r .image_base64 | base64 -d > qr.png
```

### With Custom Colors

```bash
curl -X POST https://vibe-qr-api.onrender.com/generate \
  -H "Content-Type: application/json" \
  -d '{
    "data": "https://example.com",
    "foreground": "#6366F1",
    "background": "#F0F9FF",
    "size": 400
  }'
```

### With Logo

```bash
curl -X POST https://vibe-qr-api.onrender.com/generate \
  -H "Content-Type: application/json" \
  -d '{
    "data": "https://example.com",
    "logo_url": "https://example.com/logo.png",
    "error_correction": "H"
  }'
```

### Generate SVG

```bash
curl -X POST https://vibe-qr-api.onrender.com/generate-svg \
  -H "Content-Type: application/json" \
  -d '{"data": "https://example.com"}'
```

### Bulk Generation

```bash
curl -X POST https://vibe-qr-api.onrender.com/bulk \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"data": "https://example1.com"},
      {"data": "https://example2.com"},
      {"data": "https://example3.com"}
    ]
  }'
```

## 📖 API Reference

### `POST /generate`

Generate a PNG QR code.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data` | string | required | Data to encode (max 4296 chars) |
| `size` | integer | 300 | Image size in pixels (50-2000) |
| `foreground` | string | #000000 | Foreground color (hex) |
| `background` | string | #FFFFFF | Background color (hex) |
| `error_correction` | string | M | L/M/Q/H |
| `logo_url` | string | null | URL of logo to embed |
| `logo_size_ratio` | float | 0.25 | Logo size ratio (0.1-0.4) |
| `module_style` | string | square | square/rounded/circle |

**Response:**
```json
{
  "success": true,
  "image_base64": "iVBORw0KGgo...",
  "format": "png",
  "size": 300
}
```

### `POST /generate-svg`

Generate an SVG QR code.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data` | string | required | Data to encode |
| `size` | integer | 300 | Image size |
| `foreground` | string | #000000 | Foreground color |
| `background` | string | #FFFFFF | Background color |
| `error_correction` | string | M | Error correction level |

### `POST /bulk`

Generate multiple QR codes (max 50).

```json
{
  "items": [
    {"data": "https://example1.com", "size": 200},
    {"data": "https://example2.com", "foreground": "#FF0000"}
  ]
}
```

### `GET /health`

Health check endpoint.

## 💰 Pricing

| Plan | Price | Requests |
|------|-------|----------|
| **Free** | $0/mo | 50/day |
| **Pro** | $9/mo | Unlimited |

## 🛠️ Self-Host

```bash
# Clone
git clone https://github.com/ttracx/vibe-qr-api.git
cd vibe-qr-api

# Run with Docker
docker build -t vibe-qr-api .
docker run -p 8000:8000 vibe-qr-api

# Or run directly
pip install -r requirements.txt
uvicorn main:app --reload
```

## 📝 License

MIT

---

Built with ❤️ by [ttracx](https://github.com/ttracx)
