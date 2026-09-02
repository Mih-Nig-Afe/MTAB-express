"""Thermal sticker assets: Code128 barcode + QR (track URL) as SVG."""
from __future__ import annotations

import io

import qrcode
import qrcode.image.svg
from barcode import Code128
from barcode.writer import SVGWriter

from app.config import settings
from app.core.brand import brand_name, brand_short


def track_url(tracking_code: str) -> str:
    base = settings.public_portal_url.rstrip("/")
    return f"{base}/track/{tracking_code}"


def barcode_svg(tracking_code: str) -> str:
    writer = SVGWriter()
    writer.set_options({"module_width": 0.35, "module_height": 12, "quiet_zone": 2})
    code = Code128(tracking_code.upper(), writer=writer)
    buf = io.BytesIO()
    code.write(buf, options={"write_text": False})
    return buf.getvalue().decode("utf-8")


def qr_svg(url: str) -> str:
    factory = qrcode.image.svg.SvgPathImage
    img = qrcode.make(url, image_factory=factory, box_size=4, border=2)
    buf = io.BytesIO()
    img.save(buf)
    return buf.getvalue().decode("utf-8")


def sticker_html(parcel_data: dict) -> str:
    """4×6\" thermal layout with scannable codes for printer drivers."""
    tracking = parcel_data["tracking_code"]
    url = track_url(tracking)
    bc = barcode_svg(tracking)
    qr = qr_svg(url)
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{tracking}</title>
<style>
  @page {{ size: 4in 6in; margin: 0.12in; }}
  body {{ font-family: Arial, sans-serif; margin: 0; color: #000; }}
  .box {{ border: 3px solid #000; padding: 10px; height: 5.7in; box-sizing: border-box; }}
  .hdr {{ display: flex; justify-content: space-between; border-bottom: 2px solid #000; padding-bottom: 6px; }}
  .hdr h1 {{ margin: 0; font-size: 18px; letter-spacing: -0.5px; }}
  .route {{ display: grid; grid-template-columns: 1fr 1fr; border-bottom: 2px solid #000; text-align: center; padding: 6px 0; }}
  .route div:first-child {{ border-right: 2px solid #000; }}
  .lbl {{ font-size: 8px; font-weight: bold; color: #444; text-transform: uppercase; }}
  .val {{ font-size: 16px; font-weight: 900; }}
  .codes {{ text-align: center; border-bottom: 2px solid #000; padding: 8px 0; }}
  .codes svg {{ max-width: 100%; height: auto; }}
  .track {{ font-size: 16px; font-weight: 900; letter-spacing: 2px; font-family: monospace; }}
  .meta {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 10px; padding-top: 6px; }}
  .foot {{ display: flex; justify-content: space-between; font-size: 10px; margin-top: 8px; border-top: 2px solid #000; padding-top: 6px; }}
  .badge {{ border: 1px solid #000; padding: 2px 6px; font-size: 9px; font-weight: bold; }}
</style></head><body>
<div class="box">
  <div class="hdr">
    <div><h1>{brand_name() or brand_short()}</h1><small>Scan at every checkpoint</small></div>
    <div style="text-align:right"><div class="badge">{parcel_data.get('payment_badge', 'PAY')}</div>
    <div style="font-size:9px;margin-top:4px">{parcel_data.get('created_at', '')}</div></div>
  </div>
  <div class="route">
    <div><div class="lbl">From</div><div class="val">{parcel_data.get('origin_branch', '')}</div></div>
    <div><div class="lbl">To</div><div class="val">{parcel_data.get('destination_branch', '')}</div></div>
  </div>
  <div class="codes">{bc}<div class="track">{tracking}</div></div>
  <div style="text-align:center;padding:6px 0;border-bottom:2px solid #000">{qr}</div>
  <div class="meta">
    <div><div class="lbl">Sender</div>{parcel_data.get('sender_phone', '')}</div>
    <div><div class="lbl">Receiver</div><strong>{parcel_data.get('receiver_name', '')}</strong><br>{parcel_data.get('receiver_phone', '')}</div>
    <div><div class="lbl">Size</div>{parcel_data.get('size_category', '—')}</div>
    <div><div class="lbl">Billable kg</div>{parcel_data.get('chargeable_weight_kg', parcel_data.get('weight_kg', '—'))}</div>
  </div>
  <div class="foot">
    <span>Fee: {parcel_data.get('price', '')}</span>
    <span>{parcel_data.get('content_category', '')}</span>
  </div>
</div></body></html>"""
