# api/index.py

import httpx
import base64
import io
import random
from fastapi import FastAPI, Query
from fastapi.responses import Response
from PIL import Image, ImageDraw, ImageFont

CREART_AI_BASE_URL = "https://api.creartai.com/api/v1"
DEVELOPER_TAG = "@lakshitpatidar"

app = FastAPI(title="Image Render API")

# ---------- WATERMARK ----------

def add_watermark(image_bytes: bytes) -> bytes:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")

    layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(layer)

    font = ImageFont.load_default()
    text = DEVELOPER_TAG

    w, h = img.size
    tw, th = draw.textsize(text, font)

    x = w - tw - 15
    y = h - th - 15

    draw.text((x, y), text, fill=(255, 255, 255, 120), font=font)

    final = Image.alpha_composite(img, layer)
    buf = io.BytesIO()
    final.convert("RGB").save(buf, format="PNG")

    return buf.getvalue()

# ---------- IMAGE RENDER ROUTE ----------

@app.get("/image")
async def render_image(
    prompt: str = Query(..., description="Image prompt"),
    width: int = 512,
    height: int = 512
):
    seed = random.randint(1, 9999999)

    payload = {
        "prompt": prompt,
        "width": width,
        "height": height,
        "seed": seed
    }

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            f"{CREART_AI_BASE_URL}/text-to-image",
            json=payload
        )
        r.raise_for_status()
        data = r.json()

    image_base64 = data.get("image")
    if not image_base64:
        return Response("Image generation failed", status_code=500)

    image_bytes = base64.b64decode(image_base64)

    # watermark
    final_image = add_watermark(image_bytes)

    return Response(
        content=final_image,
        media_type="image/png"
    )

# ---------- HEALTH ----------

@app.get("/")
async def root():
    return {
        "status": "running",
        "developer": DEVELOPER_TAG
  }
