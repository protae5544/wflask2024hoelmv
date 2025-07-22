import os
from flask import Flask, send_file, request, jsonify
import pdfkit
import tempfile
from datetime import datetime
import qrcode
from io import BytesIO
import base64
import json

app = Flask(__name__)

# ตัวอย่างข้อมูลใบเสร็จ
SAMPLE_DATA = [
    {
        "requestNumber": "WP-67-009630",
        "englishName": "MISS EI YE PYAN",
        "thaiName": "นางสาวเอ ยี เปียน",
        "age": "25",
        "alienReferenceNumber": "2492100646840",
        "personalID": "6682190049543",
        "nationality": "เมียนมา",
        "workPermitNumber": "WP-67-009630",
        "birthDate": "15/03/1999",
        "เลขที่บนขวาใบเสร็จ": "2100680001130",
        "หมายเลขชำระเงิน": "IV680106/001176"
    },
    {
        "requestNumber": "WP-67-009631",
        "englishName": "MR. JOHN SMITH",
        "thaiName": "นายจอห์น สมิธ",
        "age": "30",
        "alienReferenceNumber": "2492100646841",
        "personalID": "6682190049544",
        "nationality": "อเมริกัน",
        "workPermitNumber": "WP-67-009631",
        "birthDate": "20/05/1994",
        "เลขที่บนขวาใบเสร็จ": "2100680001131",
        "หมายเลขชำระเงิน": "IV680106/001177"
    }
]

# โหลด template
with open('receipt_template.html', encoding='utf-8') as f:
    RECEIPT_TEMPLATE = f.read()

def render_receipt_html(worker):
    # สร้าง QR code
    qr_data = f"Receipt: {worker['เลขที่บนขวาใบเสร็จ']}\nName: {worker['englishName']}\nRequest: {worker['requestNumber']}"
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode('utf-8')

    today = datetime.now()
    day = str(today.day).zfill(2)
    month = today.month
    year = today.year + 543
    hours = str(today.hour).zfill(2)
    minutes = str(today.minute).zfill(2)
    thai_months = ['มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน', 'พฤษภาคม', 'มิถุนายน',
                   'กรกฎาคม', 'สิงหาคม', 'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม']
    current_date = f"{day} {thai_months[month-1]} {year}"
    print_date = f"{day}/{str(month).zfill(2)}/{str(year)[2:]} {hours}:{minutes} น."

    template_data = {
        **worker,
        "current_date": current_date,
        "print_date": print_date,
        "employerName": worker.get("employerName", "บริษัท ธัชชัย คอนกรีต 2022 จำกัด"),
        "employerId": worker.get("employerId", "0255565000295"),
        "qr_code": f"data:image/png;base64,{qr_base64}"
    }
    html = RECEIPT_TEMPLATE
    for key, value in template_data.items():
        html = html.replace(f"{{{{{key}}}}}", str(value))
    return html

@app.route('/generate-receipt/<request_number>')
def generate_receipt(request_number):
    worker = next((item for item in SAMPLE_DATA if item["requestNumber"] == request_number), None)
    if not worker:
        return jsonify({"error": "ไม่พบข้อมูลสำหรับเลขคำขอที่ระบุ"}), 404
    html = render_receipt_html(worker)
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        pdfkit.from_string(html, f.name)
        return send_file(f.name, as_attachment=True, download_name=f'receipt_{request_number}.pdf', mimetype='application/pdf')

@app.route('/generate-receipt-pair/<request_number1>/<request_number2>')
def generate_receipt_pair(request_number1, request_number2):
    worker1 = next((item for item in SAMPLE_DATA if item["requestNumber"] == request_number1), None)
    worker2 = next((item for item in SAMPLE_DATA if item["requestNumber"] == request_number2), None)
    if not worker1 or not worker2:
        return jsonify({"error": "ไม่พบข้อมูลสำหรับเลขคำขอที่ระบุ"}), 404
    html1 = render_receipt_html(worker1)
    html2 = render_receipt_html(worker2)
    html_pair = f"""
    <html><head><meta charset='utf-8'></head><body>
    <div style='page-break-after: always'>{html1}</div>
    <div>{html2}</div>
    </body></html>
    """
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        pdfkit.from_string(html_pair, f.name)
        return send_file(f.name, as_attachment=True, download_name=f'receipt_pair_{request_number1}_{request_number2}.pdf', mimetype='application/pdf')

@app.route('/')
def index():
    return '<h2>Receipt PDF API พร้อมใช้งาน</h2>'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)