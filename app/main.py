"""
Vibe QR API - FastAPI service for QR code generation
"""
import io
import os
from datetime import datetime, timedelta
from typing import Optional
from collections import defaultdict

import qrcode
import qrcode.image.svg
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.responses import Response, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(
    title="Vibe QR API",
    description="Generate QR codes as PNG or SVG",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting storage (in-memory, resets on restart)
# In production, use Redis for persistence
rate_limit_store: dict[str, list[datetime]] = defaultdict(list)

# Configuration
FREE_TIER_LIMIT = int(os.getenv("FREE_TIER_LIMIT", "20"))
PRO_API_KEY = os.getenv("PRO_API_KEY", "")
RATE_LIMIT_WINDOW = timedelta(days=1)


class QRRequest(BaseModel):
    """Request model for QR code generation"""
    data: str = Field(..., description="Text or URL to encode", min_length=1, max_length=4296)
    size: int = Field(default=10, ge=1, le=40, description="QR code size (1-40)")
    border: int = Field(default=4, ge=0, le=10, description="Border size")
    error_correction: str = Field(default="M", description="Error correction level: L, M, Q, H")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: str


def get_error_correction(level: str):
    """Map error correction string to qrcode constant"""
    levels = {
        "L": qrcode.constants.ERROR_CORRECT_L,
        "M": qrcode.constants.ERROR_CORRECT_M,
        "Q": qrcode.constants.ERROR_CORRECT_Q,
        "H": qrcode.constants.ERROR_CORRECT_H,
    }
    return levels.get(level.upper(), qrcode.constants.ERROR_CORRECT_M)


def get_client_ip(request: Request) -> str:
    """Get client IP from request, handling proxies"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check_rate_limit(client_id: str, is_pro: bool) -> bool:
    """Check if client has exceeded rate limit. Returns True if allowed."""
    if is_pro:
        return True
    
    now = datetime.utcnow()
    cutoff = now - RATE_LIMIT_WINDOW
    
    # Clean old entries
    rate_limit_store[client_id] = [
        ts for ts in rate_limit_store[client_id] if ts > cutoff
    ]
    
    # Check limit
    if len(rate_limit_store[client_id]) >= FREE_TIER_LIMIT:
        return False
    
    # Record this request
    rate_limit_store[client_id].append(now)
    return True


def get_remaining_requests(client_id: str, is_pro: bool) -> int:
    """Get remaining requests for client"""
    if is_pro:
        return -1  # Unlimited
    
    now = datetime.utcnow()
    cutoff = now - RATE_LIMIT_WINDOW
    
    recent = [ts for ts in rate_limit_store[client_id] if ts > cutoff]
    return max(0, FREE_TIER_LIMIT - len(recent))


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat(),
    )


@app.post("/generate", tags=["QR Code"])
async def generate_qr_png(
    request: Request,
    qr_request: QRRequest,
    x_api_key: Optional[str] = Header(None),
):
    """
    Generate a QR code as PNG image.
    
    - **data**: Text or URL to encode (required)
    - **size**: QR code size 1-40 (default: 10)
    - **border**: Border size 0-10 (default: 4)
    - **error_correction**: L, M, Q, or H (default: M)
    
    Free tier: 20 requests/day. Pro tier (with API key): unlimited.
    """
    client_id = get_client_ip(request)
    is_pro = bool(x_api_key and PRO_API_KEY and x_api_key == PRO_API_KEY)
    
    if not check_rate_limit(client_id, is_pro):
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Free tier allows {FREE_TIER_LIMIT} requests per day. Upgrade to Pro for unlimited access.",
        )
    
    try:
        qr = qrcode.QRCode(
            version=qr_request.size,
            error_correction=get_error_correction(qr_request.error_correction),
            box_size=10,
            border=qr_request.border,
        )
        qr.add_data(qr_request.data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        remaining = get_remaining_requests(client_id, is_pro)
        headers = {
            "X-RateLimit-Remaining": str(remaining) if remaining >= 0 else "unlimited",
            "X-RateLimit-Limit": str(FREE_TIER_LIMIT) if not is_pro else "unlimited",
        }
        
        return Response(
            content=buffer.getvalue(),
            media_type="image/png",
            headers=headers,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to generate QR code: {str(e)}")


@app.post("/generate-svg", tags=["QR Code"])
async def generate_qr_svg(
    request: Request,
    qr_request: QRRequest,
    x_api_key: Optional[str] = Header(None),
):
    """
    Generate a QR code as SVG image.
    
    - **data**: Text or URL to encode (required)
    - **size**: QR code size 1-40 (default: 10)
    - **border**: Border size 0-10 (default: 4)
    - **error_correction**: L, M, Q, or H (default: M)
    
    Free tier: 20 requests/day. Pro tier (with API key): unlimited.
    """
    client_id = get_client_ip(request)
    is_pro = bool(x_api_key and PRO_API_KEY and x_api_key == PRO_API_KEY)
    
    if not check_rate_limit(client_id, is_pro):
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Free tier allows {FREE_TIER_LIMIT} requests per day. Upgrade to Pro for unlimited access.",
        )
    
    try:
        qr = qrcode.QRCode(
            version=qr_request.size,
            error_correction=get_error_correction(qr_request.error_correction),
            box_size=10,
            border=qr_request.border,
        )
        qr.add_data(qr_request.data)
        qr.make(fit=True)
        
        factory = qrcode.image.svg.SvgImage
        img = qr.make_image(image_factory=factory)
        
        buffer = io.BytesIO()
        img.save(buffer)
        buffer.seek(0)
        
        remaining = get_remaining_requests(client_id, is_pro)
        headers = {
            "X-RateLimit-Remaining": str(remaining) if remaining >= 0 else "unlimited",
            "X-RateLimit-Limit": str(FREE_TIER_LIMIT) if not is_pro else "unlimited",
        }
        
        return Response(
            content=buffer.getvalue(),
            media_type="image/svg+xml",
            headers=headers,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to generate QR code: {str(e)}")


@app.get("/", tags=["Info"])
async def root():
    """API information"""
    return {
        "name": "Vibe QR API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "POST /generate": "Generate QR code as PNG",
            "POST /generate-svg": "Generate QR code as SVG",
            "GET /health": "Health check",
        },
        "rate_limits": {
            "free": f"{FREE_TIER_LIMIT} requests/day",
            "pro": "Unlimited (requires X-API-Key header)",
        },
    }
