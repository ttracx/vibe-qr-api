# 🔲 Vibe QR API

Fast, simple QR code generation API built with FastAPI. Generate QR codes as PNG or SVG with customizable options.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/ttracx/vibe-qr-api)

## Features

- 🖼️ **PNG & SVG Output** - Choose your format
- ⚡ **Fast** - Built on FastAPI with async support
- 🎛️ **Customizable** - Size, border, error correction
- 🚦 **Rate Limited** - Fair use with Pro tier upgrade
- 🐳 **Docker Ready** - Easy deployment anywhere
- 📚 **Auto-documented** - OpenAPI/Swagger docs included

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | API information |
| `GET` | `/health` | Health check |
| `POST` | `/generate` | Generate QR code as PNG |
| `POST` | `/generate-svg` | Generate QR code as SVG |

## Quick Start

### Generate a QR Code (PNG)

```bash
curl -X POST https://your-api.onrender.com/generate \
  -H "Content-Type: application/json" \
  -d '{"data": "https://example.com"}' \
  --output qr.png
```

### Generate a QR Code (SVG)

```bash
curl -X POST https://your-api.onrender.com/generate-svg \
  -H "Content-Type: application/json" \
  -d '{"data": "Hello World"}' \
  --output qr.svg
```

### With Options

```bash
curl -X POST https://your-api.onrender.com/generate \
  -H "Content-Type: application/json" \
  -d '{
    "data": "https://example.com",
    "size": 10,
    "border": 2,
    "error_correction": "H"
  }' \
  --output qr.png
```

## Request Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data` | string | required | Text or URL to encode (max 4296 chars) |
| `size` | int | 10 | QR code version/size (1-40) |
| `border` | int | 4 | Border size (0-10) |
| `error_correction` | string | "M" | Error correction: L (7%), M (15%), Q (25%), H (30%) |

## Rate Limits

| Tier | Limit | How to Access |
|------|-------|---------------|
| **Free** | 20 requests/day | Default |
| **Pro** | Unlimited | Include `X-API-Key` header |

### Pro Tier Usage

```bash
curl -X POST https://your-api.onrender.com/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-pro-api-key" \
  -d '{"data": "https://example.com"}' \
  --output qr.png
```

Rate limit headers are included in responses:
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Limit`: Total limit (or "unlimited" for Pro)

## Local Development

### With Docker

```bash
docker build -t vibe-qr-api .
docker run -p 8000:8000 vibe-qr-api
```

### Without Docker

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then visit: http://localhost:8000/docs

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FREE_TIER_LIMIT` | 20 | Requests per day for free tier |
| `PRO_API_KEY` | "" | API key for Pro tier access |

## Deployment

### Render (Recommended)

1. Click "Deploy to Render" button above, or
2. Create new Web Service → Connect this repo → Deploy

The `render.yaml` blueprint handles configuration automatically.

### Docker (Anywhere)

```bash
docker pull ghcr.io/ttracx/vibe-qr-api:latest
docker run -p 8000:8000 \
  -e PRO_API_KEY=your-secret-key \
  ghcr.io/ttracx/vibe-qr-api:latest
```

## API Documentation

Once deployed, visit:
- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
- **OpenAPI JSON**: `/openapi.json`

## License

MIT

---

Built with ⚡ by [ttracx](https://github.com/ttracx)
