# Evidence Watermarking System (QR + Arnold Transform)

แอปพลิเคชันสำหรับฝังและถอดรหัสลายน้ำดิจิทัล (Digital Image Watermarking) สำหรับระบบจัดการหลักฐานดิจิทัล (Digital Evidence Repository) พัฒนาด้วยภาษา Python พร้อม GUI ที่ใช้งานง่าย

ระบบนี้ใช้เทคนิค **Discrete Wavelet Transform (DWT)** ในการฝังลายน้ำแบบมองไม่เห็น (Invisible Watermark) ลงในแชนเนลสี Blue ของภาพ ผสานกับการทำ **Arnold Transform** เพื่อสลับพิกเซลของ QR Code เพิ่มความปลอดภัยและการป้องกันข้อมูลหลักฐานจากการถูกดัดแปลง

## ✨ คุณสมบัติหลัก (Features)

- **Metadata to QR Code**: แปลงข้อมูลสำคัญ (รหัสประจำตัว, ชื่อ, ยศ, หน่วยงาน, บทบาท) พร้อมค่า Hash (SHA-256) เป็น QR Code เพื่อใช้เป็นลายน้ำ
- **Arnold Scrambling**: เข้ารหัสรูปภาพลายน้ำ (QR Code) ด้วย Arnold Transform ก่อนทำการฝัง เพื่อไม่ให้ผู้ไม่หวังดีสามารถดึงข้อมูลลายน้ำไปอ่านได้โดยตรง
- **DWT Embedding**: ฝังลายน้ำลงในคลื่นความถี่ต่ำ-สูง (LH sub-band) ของภาพผ่าน Haar Wavelet Transform ทำให้ภาพหลักฐานแทบไม่สูญเสียความคมชัด
- **Adjustable Strength**: สามารถปรับระดับความเข้มของการฝังลายน้ำ (Alpha) ได้ผ่าน UI
- **Extraction & Verification**: ถอดรหัสลายน้ำกลับมาเป็น QR Code และอ่านค่าเพื่อยืนยันความถูกต้องของหลักฐาน
- **Modern UI**: หน้าต่างแอปพลิเคชันแบบ Dark Mode ใช้งานง่าย แบ่งสัดส่วนชัดเจนด้วย CustomTkinter

## 🛠 เทคโนโลยีที่ใช้ (Tech Stack)

- **Python 3.x**
- **GUI**: `customtkinter`
- **Image Processing**: `Pillow` (PIL), `numpy`
- **Watermarking**: `PyWavelets` (pywt) สำหรับการทำ DWT
- **QR Code**: `qrcode` (สร้าง) และ `pyzbar` (อ่าน)
- **Security**: `hashlib` (SHA-256)

## ⚙️ การติดตั้ง (Installation)

1. Clone repository นี้ลงมาที่เครื่อง
2. ติดตั้งไลบรารีพื้นฐานของ Python ผ่าน pip:
   ```bash
   pip install customtkinter Pillow numpy PyWavelets qrcode pyzbar
