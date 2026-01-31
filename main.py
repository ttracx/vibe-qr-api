"""
Vibe QR API - Fast, Beautiful QR Code Generation
"""
import io
import base64
from typing import Optional, List
from enum import Enum

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, HttpUrl
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import (
    SquareModuleDrawer,
    RoundedModuleDrawer,
    CircleModuleDrawer,
)
from PIL import Image
import requests

app = FastAPI(
    title="Vibe QR API",
    description="Generate beautiful QR codes with custom colors, logos, and styles",
    version="1.0.0",
    docs_url="/",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ErrorCorrection(str, Enum):
    LOW = "L"       # 7% recovery
    MEDIUM = "M"    # 15% recovery
    QUARTILE = "Q"  # 25% recovery
    HIGH = "H"      # 30% recovery


class ModuleStyle(str, Enum):
    SQUARE = "square"
    ROUNDED = "rounded"
    CIRCLE = "circle"


ERROR_CORRECTION_MAP = {
    ErrorCorrection.LOW: qrcode.constants.ERROR_CORRECT_L,
    ErrorCorrection.MEDIUM: qrcode.constants.ERROR_CORRECT_M,
    ErrorCorrection.QUARTILE: qrcode.constants.ERROR_CORRECT_Q,
    ErrorCorrection.HIGH: qrcode.constants.ERROR_CORRECT_H,
}

MODULE_DRAWER_MAP = {
    ModuleStyle.SQUARE: SquareModuleDrawer(),
    ModuleStyle.ROUNDED: RoundedModuleDrawer(),
    ModuleStyle.CIRCLE: CircleModuleDrawer(),
}


class QRRequest(BaseModel):
    data: str = Field(..., description="Data to encode in QR code", max_length=4296)
    size: int = Field(default=300, ge=50, le=2000, description="Image size in pixels")
    foreground: str = Field(default="#000000", description="Foreground color (hex)")
    background: str = Field(default="#FFFFFF", description="Background color (hex)")
    error_correction: ErrorCorrection = Field(
        default=ErrorCorrection.MEDIUM,
        description="Error correction level"
    )
    logo_url: Optional[HttpUrl] = Field(default=None, description="URL of logo to embed")
    logo_size_ratio: float = Field(
        default=0.25, ge=0.1, le=0.4,
        description="Logo size as ratio of QR code"
    )
    module_style: ModuleStyle = Field(
        default=ModuleStyle.SQUARE,
        description="Style of QR modules"
    )


class QRResponse(BaseModel):
    success: bool
    image_base64: str
    format: str
    size: int


class BulkQRRequest(BaseModel):
    items: List[QRRequest] = Field(..., max_length=50, description="List of QR requests")


class BulkQRResponse(BaseModel):
    success: bool
    results: List[QRResponse]
    count: int


class SVGRequest(BaseModel):
    data: str = Field(..., description="Data to encode in QR code", max_length=4296)
    size: int = Field(default=300, ge=50, le=2000, description="Image size in pixels")
    foreground: str = Field(default="#000000", description="Foreground color (hex)")
    background: str = Field(default="#FFFFFF", description="Background color (hex)")
    error_correction: ErrorCorrection = Field(
        default=ErrorCorrection.MEDIUM,
        description="Error correction level"
    )


class SVGResponse(BaseModel):
    success: bool
    svg: str
    format: str


def hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def generate_qr_image(req: QRRequest) -> bytes:
    """Generate a QR code image and return as PNG bytes."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECTION_MAP[req.error_correction],
        box_size=10,
        border=4,
    )
    qr.add_data(req.data)
    qr.make(fit=True)
    
    fg_color = hex_to_rgb(req.foreground)
    bg_color = hex_to_rgb(req.background)
    
    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=MODULE_DRAWER_MAP[req.module_style],
        fill_color=fg_color,
        back_color=bg_color,
    )
    
    # Convert to PIL Image for resizing
    if hasattr(img, 'get_image'):
        pil_img = img.get_image()
    else:
        pil_img = img
    
    # Embed logo if provided
    if req.logo_url:
        try:
            response = requests.get(str(req.logo_url), timeout=5)
            response.raise_for_status()
            logo = Image.open(io.BytesIO(response.content))
            
            # Calculate logo size
            logo_max_size = int(pil_img.size[0] * req.logo_size_ratio)
            logo.thumbnail((logo_max_size, logo_max_size), Image.Resampling.LANCZOS)
            
            # Convert logo to RGBA if needed
            if logo.mode != 'RGBA':
                logo = logo.convert('RGBA')
            
            # Convert base image to RGBA
            if pil_img.mode != 'RGBA':
                pil_img = pil_img.convert('RGBA')
            
            # Calculate position to center logo
            logo_pos = (
                (pil_img.size[0] - logo.size[0]) // 2,
                (pil_img.size[1] - logo.size[1]) // 2,
            )
            
            # Paste logo onto QR code
            pil_img.paste(logo, logo_pos, logo)
        except Exception:
            pass  # Continue without logo on error
    
    # Resize to requested size
    pil_img = pil_img.resize((req.size, req.size), Image.Resampling.LANCZOS)
    
    # Convert to RGB for PNG output
    if pil_img.mode == 'RGBA':
        rgb_img = Image.new('RGB', pil_img.size, bg_color)
        rgb_img.paste(pil_img, mask=pil_img.split()[3])
        pil_img = rgb_img
    
    # Save to bytes
    buffer = io.BytesIO()
    pil_img.save(buffer, format='PNG', optimize=True)
    return buffer.getvalue()


def generate_qr_svg(req: SVGRequest) -> str:
    """Generate a QR code as SVG string."""
    import qrcode.image.svg
    
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECTION_MAP[req.error_correction],
        box_size=10,
        border=4,
    )
    qr.add_data(req.data)
    qr.make(fit=True)
    
    factory = qrcode.image.svg.SvgPathImage
    img = qr.make_image(image_factory=factory)
    
    buffer = io.BytesIO()
    img.save(buffer)
    svg_string = buffer.getvalue().decode('utf-8')
    
    # Replace default colors with custom colors
    svg_string = svg_string.replace('fill="#000000"', f'fill="{req.foreground}"')
    svg_string = svg_string.replace('fill:black', f'fill:{req.foreground}')
    
    # Add background
    if req.background.upper() != "#FFFFFF":
        # Insert background rect after opening svg tag
        svg_parts = svg_string.split('>', 1)
        if len(svg_parts) == 2:
            svg_string = f'{svg_parts[0]}><rect width="100%" height="100%" fill="{req.background}"/>{svg_parts[1]}'
    
    return svg_string


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "vibe-qr-api",
        "version": "1.0.0"
    }


@app.post("/generate", response_model=QRResponse)
async def generate_qr(request: QRRequest):
    """
    Generate a QR code image.
    
    Returns PNG image as base64 encoded string.
    """
    try:
        image_bytes = generate_qr_image(request)
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        return QRResponse(
            success=True,
            image_base64=image_base64,
            format="png",
            size=request.size
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/generate-svg", response_model=SVGResponse)
async def generate_qr_svg_endpoint(request: SVGRequest):
    """
    Generate a QR code as SVG.
    
    Returns SVG markup as string.
    """
    try:
        svg_string = generate_qr_svg(request)
        
        return SVGResponse(
            success=True,
            svg=svg_string,
            format="svg"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/bulk", response_model=BulkQRResponse)
async def generate_bulk_qr(request: BulkQRRequest):
    """
    Generate multiple QR codes in a single request.
    
    Maximum 50 QR codes per request.
    """
    try:
        results = []
        for item in request.items:
            image_bytes = generate_qr_image(item)
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            results.append(QRResponse(
                success=True,
                image_base64=image_base64,
                format="png",
                size=item.size
            ))
        
        return BulkQRResponse(
            success=True,
            results=results,
            count=len(results)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
