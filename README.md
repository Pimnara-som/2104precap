# Evidence Watermarking System (DWT Domain)

ตัวต้นแบบระบบฝังลายน้ำดิจิทัล (Digital Watermarking) สำหรับโปรเจกต์ Pre-CapStone ระบบจัดเก็บหลักฐานดิจิทัล เป้าหมายของโค้ดชุดนี้คือการซ่อนข้อมูลการเข้าถึง (ชื่อเจ้าหน้าที่, รหัสพนักงาน, Access Hash) ลงไปในไฟล์ภาพหลักฐาน โดยต้องรบกวนสายตาให้น้อยที่สุดและรักษาความสมบูรณ์ของภาพไว้

ระบบนี้ใช้เทคนิค **Discrete Wavelet Transform (DWT)** ร่วมกับสมการ Additive Embedding แบบ Non-blind

## ⚙️ Core Logic & Algorithm
- **Color Channel:** ดึงเฉพาะ **Blue Channel (B)** ของภาพมาใช้ฝังข้อมูล เนื่องจากสายตามนุษย์มีความไวต่อการเปลี่ยนแปลงของสีน้ำเงินน้อยที่สุด ทำให้รอยด่างของลายน้ำเนียนไปกับภาพ
- **DWT Decomposition:** ใช้ Haar Wavelet (Level 1) แยกความถี่ภาพออกมา ฝังข้อมูลลงในแบนด์ **LH (Vertical Details)** เพราะเป็นจุดสมดุลที่ดีระหว่างการซ่อนตัวจากสายตาและความทนทาน
- **Binary Array Transformation:** แปลงข้อมูล Text ให้เป็น Array ของ `1` และ `-1` เพื่อนำไปคำนวณทางคณิตศาสตร์
- **Additive Method:** นำ Array ข้อมูลไปบวกเข้ากับสัมประสิทธิ์ของแบนด์ LH โดยมีตัวแปร $\alpha$ (Alpha) เป็นตัวควบคุมความแรงของลายน้ำ
- **Non-blind Extraction:** การถอดลายน้ำต้องใช้ "ภาพหลักฐานที่ฝังลายน้ำ" ลบด้วย "ภาพต้นฉบับดั้งเดิม" เพื่อหาส่วนต่าง นำมาหารด้วย Alpha และแปลงกลับเป็นข้อความ

## 🛠 Dependencies
ติดตั้งไลบรารีที่จำเป็นก่อนรันโปรแกรม:
```bash
pip install customtkinter Pillow numpy PyWavelets
