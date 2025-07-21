from flask import Blueprint, jsonify, request, send_file
from werkzeug.utils import secure_filename
from datetime import datetime
import json
import os
import tempfile
import qrcode
from io import BytesIO
import base64

receipt_bp = Blueprint('receipt', __name__)

# ข้อมูลตัวอย่างสำหรับใบเสร็จ (ใช้ JSON ในหน่วยความจำ)
sample_data = [
    {
        "requestNumber": "WP-67-009630",
        "englishName": "MISS EI YE PYAN",
        "profileImage": "",
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
        "profileImage": "",
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

# Template สำหรับใบเสร็จ (เพิ่ม QR Code)
RECEIPT_TEMPLATE = """<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <title>ใบเสร็จรับเงิน</title>
    <style>
        @font-face {
            font-family: 'TH Sarabun New';
            src: url('/static/font/subset-THSarabunNew.woff2') format('woff2'),
                 url('/static/font/subset-THSarabunNew.woff') format('woff');
            font-weight: normal;
            font-style: normal;
        }
        @font-face {
            font-family: 'TH Sarabun New';
            src: url('/static/font/subset-THSarabunNew-Bold.woff2') format('woff2'),
                 url('/static/font/subset-THSarabunNew-Bold.woff') format('woff');
            font-weight: bold;
            font-style: normal;
        }
        p { margin: 0; padding: 0; }
        .ft10 { font-size: 17px; font-family: 'TH Sarabun New', Times; color: #000000; }
        .ft11 { font-size: 23px; font-family: 'TH Sarabun New', Times; color: #000000; }
        .ft12 { font-size: 20px; font-family: 'TH Sarabun New', Times; color: #000000; }
        .ft13 { font-size: 20px; font-family: 'TH Sarabun New', Times; color: #000000; }
        .ft14 { font-size: 12px; font-family: 'TH Sarabun New', Times; color: #000000; }
        .ft15 { font-size: 12px; line-height: 17px; font-family: 'TH Sarabun New', Times; color: #000000; }
    </style>
</head>
<body bgcolor="#A0A0A0" vlink="blue" link="blue">
    <div id="page1-div" style="position: relative; width: 892px; height: 1262px;">
        <img width="892" height="1262" src="/static/bg.svg" alt="background image"/>
        <p style="position: absolute; top: 148px; left: 86px; white-space: nowrap" class="ft10">กรมการจัดหางาน</p>
        <p style="position: absolute; top: 171px; left: 88px; white-space: nowrap" class="ft10">กระทรวงแรงงาน</p>
        <p style="position: absolute; top: 91px; left: 397px; white-space: nowrap" class="ft11"><b>ใบเสร็จรับเงิน</b></p>
        <p style="position: absolute; top: 121px; left: 418px; white-space: nowrap" class="ft11"><b>ต้นฉบับ</b></p>
        <p style="position: absolute; top: 61px; left: 597px; white-space: nowrap" class="ft10">เลขที่ {{เลขที่บนขวาใบเสร็จ}}</p>
        <p style="position: absolute; top: 150px; left: 582px; white-space: nowrap" class="ft10">ที่ทำการ สำนักบริหารแรงงานต่างด้าว</p>
        <p style="position: absolute; top: 189px; left: 601px; white-space: nowrap" class="ft10">วันที่ {{current_date}}</p>
        <p style="position: absolute; top: 228px; left: 539px; white-space: nowrap" class="ft10">เลขที่ใบชำระเงิน {{หมายเลขชำระเงิน}}</p>
        <p style="position: absolute; top: 272px; left: 60px; white-space: nowrap" class="ft10">เลขรับคำขอที่</p>
        <p style="position: absolute; top: 272px; left: 184px; white-space: nowrap" class="ft10">{{requestNumber}}</p>
        <p style="position: absolute; top: 311px; left: 60px; white-space: nowrap" class="ft10">ชื่อผู้ชำระเงิน</p>
        <p style="position: absolute; top: 311px; left: 184px; white-space: nowrap" class="ft10">{{englishName}}</p>
        <p style="position: absolute; top: 311px; left: 471px; white-space: nowrap" class="ft10">สัญชาติ {{nationality}}</p>
        <p style="position: absolute; top: 356px; left: 60px; white-space: nowrap" class="ft10">เลขอ้างอิงคนต่างด้าว {{alienReferenceNumber}}</p>
        <p style="position: absolute; top: 356px; left: 432px; white-space: nowrap" class="ft10">หมายเลขประจำตัวคนต่างด้าว {{personalID}}</p>
        <p style="position: absolute; top: 400px; left: 60px; white-space: nowrap" class="ft10">ชื่อนายจ้าง / สถานประกอบการ {{employerName}}</p>
        <p style="position: absolute; top: 439px; left: 60px; white-space: nowrap" class="ft10">เลขประจำตัวนายจ้าง</p>
        <p style="position: absolute; top: 438px; left: 231px; white-space: nowrap" class="ft10">{{employerId}}</p>
        <p style="position: absolute; top: 527px; left: 345px; white-space: nowrap" class="ft12"><b>รายการ</b></p>
        <p style="position: absolute; top: 527px; left: 688px; white-space: nowrap" class="ft12"><b>จำนวนเงิน</b></p>
        <p style="position: absolute; top: 573px; left: 118px; white-space: nowrap" class="ft13">1. ค่าธรรมเนียมในการยื่นคำขอ ฉบับละ 100 บาท</p>
        <p style="position: absolute; top: 573px; left: 736px; white-space: nowrap" class="ft13">100.00</p>
        <p style="position: absolute; top: 617px; left: 118px; white-space: nowrap" class="ft13">2. ค่าธรรมเนียมใบอนุญาตทำงาน</p>
        <p style="position: absolute; top: 617px; left: 736px; white-space: nowrap" class="ft13">900.00</p>
        <p style="position: absolute; top: 695px; left: 97px; white-space: nowrap" class="ft13"></p>
        <p style="position: absolute; top: 695px; left: 648px; white-space: nowrap" class="ft13"></p>
        <p style="position: absolute; top: 773px; left: 174px; white-space: nowrap" class="ft12"><b>รวมเป็นเงินทั้งสิ้น (บาท)</b></p>
        <p style="position: absolute; top: 800px; left: 188px; white-space: nowrap" class="ft12"><b>( หนึ่งพันบาทถ้วน )</b></p>
        <p style="position: absolute; top: 787px; left: 385px; white-space: nowrap" class="ft13"></p>
        <p style="position: absolute; top: 776px; left: 722px; white-space: nowrap" class="ft12"><b>1,000.00</b></p>
        <p style="position: absolute; top: 895px; left: 93px; white-space: nowrap" class="ft10">ได้รับเงินไว้เป็นการถูกต้องแล้ว</p>
        <p style="position: absolute; top: 979px; left: 481px; white-space: nowrap" class="ft10">(ลงชื่อ)</p>
        <p style="position: absolute; top: 978px; left: 564px; white-space: nowrap" class="ft10">นางสาวอารีวรรณ โพธิ์นิ่มแดง</p>
        <p style="position: absolute; top: 979px; left: 762px; white-space: nowrap" class="ft10">(ผู้รับเงิน)</p>
        <p style="position: absolute; top: 1018px; left: 473px; white-space: nowrap" class="ft10">ตำแหน่ง</p>
        <p style="position: absolute; top: 1017px; left: 562px; white-space: nowrap" class="ft10">นักวิชาการแรงงานชำนาญการ</p>
        <div style="position: absolute; top: 1050px; left: 396px; width: 100px; height: 100px;">
            <img src="{{qr_code}}" style="width: 100px; height: 100px;" />
        </div>
        <p style="position: absolute; top: 1135px; left: 55px; white-space: nowrap" class="ft15">เอกสารอิเล็กทรอนิกส์ฉบับนี้ถูกสร้างจากระบบอนุญาตทำงานคนต่างด้าวที่มีสถานะการทำงานไม่ถูกต้องตามกฎหมาย ตามมติคณะรัฐมนตรีเมื่อวันที่ 24 กันยายน 2567<br/>โดยกรมการจัดหางาน กระทรวงแรงงาน</p>
        <p style="position: absolute; top: 1178px; left: 55px; white-space: nowrap" class="ft14">พิมพ์เอกสาร วันที่ {{print_date}}</p>
    </div>
</body>
</html>"""

# API routes
@receipt_bp.route('/worker-data', methods=['GET'])
def get_worker_data():
    """API สำหรับดึงข้อมูลคนงานทั้งหมด"""
    return jsonify(sample_data)

@receipt_bp.route('/worker-data/<request_number>', methods=['GET'])
def get_worker_by_request_number(request_number):
    """API สำหรับดึงข้อมูลคนงานตามเลขคำขอ"""
    worker = next((item for item in sample_data if item["requestNumber"] == request_number), None)
    if worker:
        return jsonify(worker)
    return jsonify({"error": "ไม่พบข้อมูลสำหรับเลขคำขอที่ระบุ"}), 404

@receipt_bp.route('/add-worker', methods=['POST'])
def add_worker():
    """API สำหรับเพิ่มข้อมูลคนงานใหม่"""
    try:
        data = request.get_json()
        if not data or 'requestNumber' not in data:
            return jsonify({"error": "ข้อมูล requestNumber เป็นข้อมูลที่จำเป็น"}), 400
        
        if any(item["requestNumber"] == data["requestNumber"] for item in sample_data):
            return jsonify({"error": "เลขคำขอนี้มีอยู่แล้ว"}), 400
        
        sample_data.append(data)
        return jsonify({"message": "เพิ่มข้อมูลสำเร็จ", "data": data}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@receipt_bp.route('/update-worker/<request_number>', methods=['PUT'])
def update_worker(request_number):
    """API สำหรับอัปเดตข้อมูลคนงาน"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "ไม่พบข้อมูลที่ส่งมา"}), 400
        
        worker_index = next((i for i, item in enumerate(sample_data) if item["requestNumber"] == request_number), None)
        if worker_index is None:
            return jsonify({"error": "ไม่พบข้อมูลสำหรับเลขคำขอที่ระบุ"}), 404
        
        sample_data[worker_index].update(data)
        return jsonify({"message": "อัปเดตข้อมูลสำเร็จ", "data": sample_data[worker_index]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@receipt_bp.route('/delete-worker/<request_number>', methods=['DELETE'])
def delete_worker(request_number):
    """API สำหรับลบข้อมูลคนงาน"""
    try:
        worker_index = next((i for i, item in enumerate(sample_data) if item["requestNumber"] == request_number), None)
        if worker_index is None:
            return jsonify({"error": "ไม่พบข้อมูลสำหรับเลขคำขอที่ระบุ"}), 404
        
        deleted_worker = sample_data.pop(worker_index)
        return jsonify({"message": "ลบข้อมูลสำเร็จ", "data": deleted_worker})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@receipt_bp.route('/current-date', methods=['GET'])
def get_current_date():
    """API สำหรับดึงวันที่ปัจจุบันในรูปแบบไทย"""
    try:
        today = datetime.now()
        day = str(today.day).zfill(2)
        month = today.month
        year = today.year + 543
        hours = str(today.hour).zfill(2)
        minutes = str(today.minute).zfill(2)
        
        thai_months = ['มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน', 'พฤษภาคม', 'มิถุนายน',
                       'กรกฎาคม', 'สิงหาคม', 'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม']
        
        formatted_date = f"{day} {thai_months[month-1]} {year}"
        print_date = f"{day}/{str(month).zfill(2)}/{str(year)[2:]} {hours}:{minutes} น."
        
        return jsonify({
            "date": formatted_date,
            "datetime": print_date,
            "timestamp": today.isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@receipt_bp.route('/upload-json', methods=['POST'])
def upload_json():
    """API สำหรับอัปโหลดไฟล์ JSON"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "ไม่พบไฟล์ที่อัปโหลด"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "ไม่ได้เลือกไฟล์"}), 400
        
        if file and file.filename.lower().endswith('.json'):
            try:
                content = file.read().decode('utf-8')
                data = json.loads(content)
                
                if not isinstance(data, list):
                    return jsonify({"error": "ไฟล์ JSON ต้องเป็น array ของ objects"}), 400
                
                global sample_data
                sample_data = data
                return jsonify({
                    "message": f"อัปโหลดไฟล์ JSON สำเร็จ โหลดข้อมูล {len(data)} รายการ",
                    "count": len(data),
                    "data": data
                })
            except json.JSONDecodeError:
                return jsonify({"error": "ไฟล์ JSON มีรูปแบบไม่ถูกต้อง"}), 400
            except UnicodeDecodeError:
                return jsonify({"error": "ไม่สามารถอ่านไฟล์ได้ กรุณาตรวจสอบ encoding"}), 400
        else:
            return jsonify({"error": "กรุณาอัปโหลดไฟล์ .json เท่านั้น"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@receipt_bp.route('/download-json', methods=['GET'])
def download_json():
    """API สำหรับดาวน์โหลดข้อมูลปัจจุบันเป็นไฟล์ JSON"""
    try:
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
        json.dump(sample_data, temp_file, ensure_ascii=False, indent=2)
        temp_file.close()
        
        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name='worker_data.json',
            mimetype='application/json'
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@receipt_bp.route('/reset-data', methods=['POST'])
def reset_data():
    """API สำหรับรีเซ็ตข้อมูลกลับเป็นค่าเริ่มต้น"""
    try:
        global sample_data
        sample_data = [
            {
                "requestNumber": "WP-67-009630",
                "englishName": "MISS EI YE PYAN",
                "profileImage": "",
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
                "profileImage": "",
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
        return jsonify({
            "message": "รีเซ็ตข้อมูลสำเร็จ",
            "count": len(sample_data),
            "data": sample_data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@receipt_bp.route('/backup-document-style', methods=['GET'])
def backup_document_style():
    """API สำหรับ backup รูปลักษณ์หน้าตาเอกสาร"""
    try:
        document_style_config = {
            "template": RECEIPT_TEMPLATE,
            "fonts": {
                "primary": "TH Sarabun New",
                "fallback": "Times"
            },
            "font_sizes": {
                "ft10": "17px",
                "ft11": "23px",
                "ft12": "20px",
                "ft13": "20px",
                "ft14": "12px",
                "ft15": "12px"
            },
            "colors": {
                "text": "#000000",
                "background": "#A0A0A0",
                "link": "blue"
            },
            "layout": {
                "page_width": "892px",
                "page_height": "1262px",
                "background_image": "bg.svg"
            },
            "field_mappings": {
                "เลขที่บนขวาใบเสร็จ": "top:61px;left:597px",
                "หมายเลขชำระเงิน": "top:228px;left:539px",
                "requestNumber": "top:272px;left:184px",
                "englishName": "top:311px;left:184px",
                "nationality": "top:311px;left:471px",
                "alienReferenceNumber": "top:356px;left:60px",
                "personalID": "top:356px;left:432px"
            }
        }
        
        # บันทึกเป็นไฟล์ใน src/database/
        os.makedirs('src/database', exist_ok=True)
        backup_file = f"src/database/backup_document_style_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(document_style_config, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            "message": f"Backup รูปลักษณ์หน้าตาเอกสารสำเร็จ บันทึกเป็น {backup_file}",
            "document_style": document_style_config,
            "backup_timestamp": datetime.now().isoformat()  # Metadata สำหรับบันทึกเวลา backup
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@receipt_bp.route('/restore-document-style', methods=['POST'])
def restore_document_style():
    """API สำหรับ restore รูปลักษณ์หน้าตาเอกสาร"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "ไม่พบไฟล์ที่อัปโหลด"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "ไม่ได้เลือกไฟล์"}), 400
        
        if file and file.filename.lower().endswith('.json'):
            try:
                content = file.read().decode('utf-8')
                data = json.loads(content)
                
                if 'template' not in data:
                    return jsonify({"error": "ไฟล์ backup ต้องมี field 'template'"}), 400
                
                global RECEIPT_TEMPLATE
                RECEIPT_TEMPLATE = data['template']
                
                return jsonify({
                    "message": "Restore รูปลักษณ์หน้าตาเอกสารสำเร็จ",
                    "restored_style": data,
                    "restore_timestamp": datetime.now().isoformat()  # Metadata สำหรับบันทึกเวลา restore
                })
            except json.JSONDecodeError:
                return jsonify({"error": "ไฟล์ JSON มีรูปแบบไม่ถูกต้อง"}), 400
            except UnicodeDecodeError:
                return jsonify({"error": "ไม่สามารถอ่านไฟล์ได้ กรุณาตรวจสอบ encoding"}), 400
        else:
            return jsonify({"error": "กรุณาอัปโหลดไฟล์ .json เท่านั้น"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@receipt_bp.route('/generate-receipt/<request_number>', methods=['GET'])
def generate_receipt(request_number):
    """API สำหรับสร้างใบเสร็จพร้อม QR Code"""
    try:
        # ตรวจสอบไฟล์
        if not os.path.exists('src/static/font/subset-THSarabunNew.woff') or not os.path.exists('src/static/bg.svg'):
            return jsonify({"error": "ไฟล์ฟอนต์หรือ background ไม่พบ"}), 500
        
        worker = next((item for item in sample_data if item["requestNumber"] == request_number), None)
        if not worker:
            return jsonify({"error": "ไม่พบข้อมูลสำหรับเลขคำขอที่ระบุ"}), 404
        
        # สร้าง QR Code
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
        
        receipt_html = RECEIPT_TEMPLATE
        for key, value in template_data.items():
            receipt_html = receipt_html.replace(f"{{{{{key}}}}}", str(value))
        
        return receipt_html, 200, {'Content-Type': 'text/html; charset=utf-8'}
    except Exception as e:
        return jsonify({"error": str(e)}), 500