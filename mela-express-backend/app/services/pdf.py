import jinja2
from weasyprint import HTML

WAYBILL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Waybill</title>
    <style>
        body { font-family: Arial, sans-serif; }
        .container { border: 2px solid #000; padding: 20px; width: 600px; margin: 0 auto; }
        .header { text-align: center; border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 10px; }
        .barcode { text-align: center; font-family: 'Courier New', Courier, monospace; font-size: 24px; font-weight: bold; margin: 20px 0; }
        .details { width: 100%; border-collapse: collapse; }
        .details th, .details td { border: 1px solid #000; padding: 8px; text-align: left; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>MELA EXPRESS</h1>
            <h2>Waybill Label</h2>
        </div>
        
        <div class="barcode">
            *{{ tracking_code }}*
        </div>
        
        <table class="details">
            <tr>
                <th>Sender</th>
                <td>{{ sender_name }}</td>
            </tr>
            <tr>
                <th>Receiver</th>
                <td>{{ receiver_name }}</td>
            </tr>
            <tr>
                <th>Origin</th>
                <td>{{ origin_branch }}</td>
            </tr>
            <tr>
                <th>Destination</th>
                <td>{{ destination_branch }}</td>
            </tr>
            <tr>
                <th>Weight (kg)</th>
                <td>{{ weight_kg }}</td>
            </tr>
            <tr>
                <th>Description</th>
                <td>{{ description }}</td>
            </tr>
        </table>
    </div>
</body>
</html>
"""

def render_waybill_html(parcel_data: dict) -> str:
    """Renders the waybill HTML template with parcel data."""
    template = jinja2.Template(WAYBILL_TEMPLATE)
    return template.render(**parcel_data)

def generate_pdf_bytes(html: str) -> bytes:
    """Generates PDF bytes from an HTML string using WeasyPrint."""
    return HTML(string=html).write_pdf()
