# Receipt PDF API

API สำหรับสร้างและเสิร์ฟ PDF ใบเสร็จ (พร้อม QR code) และรองรับปริ้นคู่

## วิธีติดตั้งและใช้งาน

1. ติดตั้ง dependency

```bash
pip install -r requirements.txt
```

2. ติดตั้ง wkhtmltopdf (จำเป็นสำหรับ pdfkit)

- Ubuntu:
  ```bash
  sudo apt-get install wkhtmltopdf
  ```
- Mac:
  ```bash
  brew install Caskroom/cask/wkhtmltopdf
  ```

3. รัน Flask app

```bash
python app.py
```

4. เรียกใช้งาน
- PDF ใบเดียว:  
  `GET /generate-receipt/<request_number>`
- PDF คู่:  
  `GET /generate-receipt-pair/<request_number1>/<request_number2>`

## Deploy บน Render
- สร้าง Web Service ใหม่ เลือก Python 3, ใส่ build command: `pip install -r requirements.txt`
- Start command: `python app.py`
- เพิ่ม environment variable: `PYTHONUNBUFFERED=1`
- ติดตั้ง wkhtmltopdf ใน shell ของ Render ด้วยคำสั่ง:
  ```bash
  apt-get update && apt-get install -y wkhtmltopdf
  ```

## หมายเหตุ
- ถ้าต้องการเปลี่ยน template หรือข้อมูล สามารถแก้ไขไฟล์ `receipt_template.html` และข้อมูลใน app.py ได้