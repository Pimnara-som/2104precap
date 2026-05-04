import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
from PIL.PngImagePlugin import PngInfo
import hashlib
import os
import numpy as np
import pywt
import qrcode

ctk.set_appearance_mode("Dark")  
ctk.set_default_color_theme("blue")

class WatermarkApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Evidence Watermarking System (QR + Arnold + EXIF)")
        self.geometry("1100x750")
        self.resizable(False, False)

        self.current_watermarked_img = None
        self.current_png_info = None # สำหรับเก็บ EXIF
        self.embed_file_path = None
        self.extract_file_path = None
        
        self.original_img_for_extraction = None 
        self.STRENGTH_MULTIPLIER = 50.0 
        self.ARNOLD_ITERATIONS = 5 # จำนวนรอบในการสลับพิกเซล

        self.setup_ui()

    def setup_ui(self):
        # ใช้ ScrollableFrame ด้านซ้ายเผื่อช่องกรอกข้อมูลเยอะ
        self.left_frame = ctk.CTkScrollableFrame(self, width=350, corner_radius=10)
        self.left_frame.pack(side="left", fill="y", padx=20, pady=20)

        self.right_frame = ctk.CTkFrame(self, width=650, corner_radius=10)
        self.right_frame.pack(side="right", fill="both", expand=True, padx=(0, 20), pady=20)

        # ================= ส่วนซ้าย (Input) =================
        ctk.CTkLabel(self.left_frame, text="ตั้งค่าข้อมูลหลักฐาน", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(10, 10))

        # 1. badge_number
        ctk.CTkLabel(self.left_frame, text="1. รหัสประจำตัว (Badge Number):").pack(anchor="w", padx=10)
        self.entry_badge = ctk.CTkEntry(self.left_frame, width=300)
        self.entry_badge.pack(padx=10, pady=(0, 10))

        # 2. full_name
        ctk.CTkLabel(self.left_frame, text="2. ชื่อ-นามสกุลจริง:").pack(anchor="w", padx=10)
        self.entry_fullname = ctk.CTkEntry(self.left_frame, width=300)
        self.entry_fullname.pack(padx=10, pady=(0, 10))

        # 3. Rank
        ctk.CTkLabel(self.left_frame, text="3. ยศ/ตำแหน่ง (Rank):").pack(anchor="w", padx=10)
        self.entry_rank = ctk.CTkEntry(self.left_frame, width=300)
        self.entry_rank.pack(padx=10, pady=(0, 10))

        # 4. Department
        ctk.CTkLabel(self.left_frame, text="4. หน่วยงาน/สังกัด (Dept):").pack(anchor="w", padx=10)
        self.entry_dept = ctk.CTkEntry(self.left_frame, width=300)
        self.entry_dept.pack(padx=10, pady=(0, 10))

        # 5. Role
        ctk.CTkLabel(self.left_frame, text="5. บทบาท (Role):").pack(anchor="w", padx=10)
        self.entry_role = ctk.CTkEntry(self.left_frame, width=300)
        self.entry_role.pack(padx=10, pady=(0, 10))

        # Slider สำหรับปรับค่า Alpha
        ctk.CTkLabel(self.left_frame, text="ความแรงลายน้ำ (Alpha 0.1 - 0.9):").pack(anchor="w", padx=10)
        self.slider_alpha = ctk.CTkSlider(self.left_frame, from_=0.1, to=0.9, number_of_steps=8)
        self.slider_alpha.set(0.5)
        self.slider_alpha.pack(padx=10, pady=(0, 20), fill="x")

        # ปุ่มอัปโหลดและฝัง
        ctk.CTkLabel(self.left_frame, text="--- โหมดฝังลายน้ำ ---", text_color="#28a745").pack(pady=(5, 5))
        self.btn_select_embed = ctk.CTkButton(self.left_frame, text="📁 เลือกรูปต้นฉบับ", command=self.select_embed_file, fg_color="#555555", hover_color="#333333")
        self.btn_select_embed.pack(pady=5, padx=10, fill="x")
        self.lbl_embed_file = ctk.CTkLabel(self.left_frame, text="ยังไม่ได้เลือกรูปภาพ", text_color="gray", font=("Arial", 12))
        self.lbl_embed_file.pack(pady=(0, 10))
        self.btn_embed = ctk.CTkButton(self.left_frame, text="สลับพิกเซล & ฝัง QR (LH Band)", fg_color="#28a745", hover_color="#218838", command=self.embed_watermark)
        self.btn_embed.pack(pady=(0, 20), padx=10, fill="x")

        # ปุ่มอัปโหลดและถอด
        ctk.CTkLabel(self.left_frame, text="--- โหมดถอดลายน้ำ ---", text_color="#dc3545").pack(pady=(5, 5))
        self.btn_select_extract = ctk.CTkButton(self.left_frame, text="📁 เลือกรูปที่มีลายน้ำ", command=self.select_extract_file, fg_color="#555555", hover_color="#333333")
        self.btn_select_extract.pack(pady=5, padx=10, fill="x")
        self.lbl_extract_file = ctk.CTkLabel(self.left_frame, text="ยังไม่ได้เลือกรูปภาพ", text_color="gray", font=("Arial", 12))
        self.lbl_extract_file.pack(pady=(0, 10))
        self.btn_extract = ctk.CTkButton(self.left_frame, text="แกะลายน้ำ & อ่าน EXIF", fg_color="#dc3545", hover_color="#c82333", command=self.extract_watermark)
        self.btn_extract.pack(pady=5, padx=10, fill="x")

        # ================= ส่วนขวา (Preview Area) =================
        self.tabview = ctk.CTkTabview(self.right_frame, width=600, height=450)
        self.tabview.pack(pady=10, padx=10, fill="both", expand=True)

        self.tab_orig = self.tabview.add("1. ภาพก่อนฝัง")
        self.tab_qr = self.tabview.add("2. QR ที่นำไปฝัง")
        self.tab_wm = self.tabview.add("3. ภาพหลังฝัง")
        self.tab_ext_qr = self.tabview.add("4. QR ที่ถอดได้")

        # สร้าง Label รับรูปในแต่ละ Tab
        self.lbl_img_orig = ctk.CTkLabel(self.tab_orig, text="ยังไม่มีรูปต้นฉบับ")
        self.lbl_img_orig.pack(expand=True)
        self.lbl_img_qr = ctk.CTkLabel(self.tab_qr, text="ยังไม่มี QR Code")
        self.lbl_img_qr.pack(expand=True)
        self.lbl_img_wm = ctk.CTkLabel(self.tab_wm, text="ยังไม่มีภาพหลักฐาน")
        self.lbl_img_wm.pack(expand=True)
        self.lbl_img_ext_qr = ctk.CTkLabel(self.tab_ext_qr, text="ยังไม่มีการถอดลายน้ำ")
        self.lbl_img_ext_qr.pack(expand=True)

        self.info_textbox = ctk.CTkTextbox(self.right_frame, height=120, width=600)
        self.info_textbox.pack(pady=10, padx=10)
        self.info_textbox.insert("0.0", "ระบบพร้อมทำงาน...\n(เมื่อถอดลายน้ำ ข้อมูล EXIF จะแสดงที่นี่)")
        self.info_textbox.configure(state="disabled")

        self.btn_save = ctk.CTkButton(self.right_frame, text="💾 บันทึกรูปภาพ + ฝัง EXIF", command=self.save_image)
        self.btn_save.pack(pady=10)
        self.btn_save.pack_forget()

    # ================= Arnold Scrambling Methods =================
    def arnold_transform(self, img_array, iterations):
        """ สลับพิกเซลเพื่อซ่อนรูปแบบ QR Code ด้วย Arnold Cat Map """
        N = img_array.shape[0]
        scrambled = np.zeros_like(img_array)
        for _ in range(iterations):
            for y in range(N):
                for x in range(N):
                    new_x = (x + y) % N
                    new_y = (x + 2*y) % N
                    scrambled[new_y, new_x] = img_array[y, x]
            img_array = scrambled.copy()
        return scrambled

    def inverse_arnold_transform(self, img_array, iterations):
        """ ย้อนกลับพิกเซลที่ถูกสลับ """
        N = img_array.shape[0]
        unscrambled = np.zeros_like(img_array)
        for _ in range(iterations):
            for y in range(N):
                for x in range(N):
                    orig_x = (2*x - y) % N
                    orig_y = (-x + y) % N
                    unscrambled[orig_y, orig_x] = img_array[y, x]
            img_array = unscrambled.copy()
        return unscrambled

    # ================= UI & Utility Methods =================
    def display_image_in_tab(self, pil_image, label_widget, max_size=(500, 400)):
        img_copy = pil_image.copy()
        img_copy.thumbnail(max_size, Image.LANCZOS)
        ctk_img = ctk.CTkImage(light_image=img_copy, dark_image=img_copy, size=img_copy.size)
        label_widget.configure(image=ctk_img, text="")
        label_widget.image = ctk_img

    def update_info_box(self, text):
        self.info_textbox.configure(state="normal")
        self.info_textbox.delete("0.0", "end")
        self.info_textbox.insert("0.0", text)
        self.info_textbox.configure(state="disabled")

    def select_embed_file(self):
        path = filedialog.askopenfilename(title="เลือกรูปภาพต้นฉบับ", filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
        if path:
            self.embed_file_path = path
            filename = os.path.basename(path)
            self.lbl_embed_file.configure(text=filename[:27]+"..." if len(filename)>30 else filename, text_color="white")
            self.original_img_for_extraction = Image.open(path).convert("RGB")
            self.display_image_in_tab(self.original_img_for_extraction, self.lbl_img_orig)
            self.tabview.set("1. ภาพก่อนฝัง")

    def select_extract_file(self):
        path = filedialog.askopenfilename(title="เลือกรูปภาพที่ฝังลายน้ำแล้ว", filetypes=[("PNG Files", "*.png")])
        if path:
            self.extract_file_path = path
            filename = os.path.basename(path)
            self.lbl_extract_file.configure(text=filename[:27]+"..." if len(filename)>30 else filename, text_color="white")

    # ================= Embedding Process =================
    def embed_watermark(self):
        badge = self.entry_badge.get().strip()
        fullname = self.entry_fullname.get().strip()
        rank = self.entry_rank.get().strip()
        dept = self.entry_dept.get().strip()
        role = self.entry_role.get().strip()

        if not badge or not fullname:
            messagebox.showwarning("แจ้งเตือน", "กรุณากรอกรหัสประจำตัวและชื่อให้ครบถ้วน")
            return
        if not self.embed_file_path:
            messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกรูปภาพต้นฉบับ")
            return

        try:
            # 1. รวมข้อมูลและทำ Hash
            raw_data = f"{badge}|{fullname}|{rank}|{dept}|{role}"
            data_hash = hashlib.sha256(raw_data.encode()).hexdigest()[:16]

            # 2. สร้าง QR Code (ข้อมูลหลักคือ Badge + Hash)
            qr_payload = f"Badge:{badge}\nHash:{data_hash}"
            qr = qrcode.make(qr_payload)
            # บังคับขนาดเป็น 64x64 ตามทฤษฎีที่ระบุ
            qr_64 = qr.resize((64, 64), Image.NEAREST) 
            self.display_image_in_tab(qr_64, self.lbl_img_qr)

            # 3. แปลงเป็นอาร์เรย์ (ดำ = 0 -> -1, ขาว = 255 -> 1)
            qr_arr = np.array(qr_64.convert("L"))
            W = np.where(qr_arr > 128, 1, -1).astype(np.float32)

            # 4. สลับพิกเซล (Arnold Transform)
            W_scrambled = self.arnold_transform(W, self.ARNOLD_ITERATIONS)

            # 5. แยก DWT Channel Blue
            image = Image.open(self.embed_file_path).convert("RGB")
            r, g, b = image.split()
            arr_b = np.float32(b) 
            coeffs = pywt.dwt2(arr_b, 'haar')
            LL, (LH, HL, HH) = coeffs

            # เช็คว่าภาพเล็กไปหรือไม่
            if LH.shape[0] < 64 or LH.shape[1] < 64:
                messagebox.showerror("Error", "รูปภาพเล็กเกินไป ต้องมีขนาดอย่างน้อย 128x128 พิกเซล")
                return

            # 6. สมการฝัง: ฝังมุมซ้ายบนของ LH-Band (ขนาด 64x64)
            alpha_input = self.slider_alpha.get()
            effective_alpha = alpha_input * self.STRENGTH_MULTIPLIER
            
            # คัดลอก LH เดิม เพื่อแก้ไขเฉพาะส่วน 64x64
            LH_new = np.copy(LH)
            LH_new[:64, :64] = LH[:64, :64] + (effective_alpha * W_scrambled)

            # 7. IDWT คืนค่า
            coeffs_new = (LL, (LH_new, HL, HH))
            watermarked_b_arr = pywt.idwt2(coeffs_new, 'haar')
            watermarked_b_arr = np.clip(watermarked_b_arr, 0, 255).astype(np.uint8)
            b_new = Image.fromarray(watermarked_b_arr, mode='L')

            # รวมสี
            self.current_watermarked_img = Image.merge("RGB", (r, g, b_new))
            self.display_image_in_tab(self.current_watermarked_img, self.lbl_img_wm)

            # 8. เตรียมฝังข้อมูลที่เหลือเป็น EXIF (PngInfo)
            metadata = PngInfo()
            metadata.add_text("full_name", fullname)
            metadata.add_text("Rank", rank)
            metadata.add_text("Department", dept)
            metadata.add_text("Role", role)
            self.current_png_info = metadata

            self.update_info_box(f"✅ ฝังสำเร็จ! (Arnold รอบ: {self.ARNOLD_ITERATIONS})\nEXIF Data Prepared: Name={fullname}, Dept={dept}\nไปที่แท็บ '3. ภาพหลังฝัง' เพื่อดูรูปหลักฐาน")
            self.tabview.set("3. ภาพหลังฝัง")
            self.btn_save.pack(pady=10) 

        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", str(e))

    def save_image(self):
        if self.current_watermarked_img and self.current_png_info:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG Files", "*.png")],
                title="บันทึกรูปภาพหลักฐาน"
            )
            if file_path:
                # เซฟรูปลงเครื่องพร้อมฝัง EXIF (PngInfo Header)
                self.current_watermarked_img.save(file_path, "PNG", pnginfo=self.current_png_info)
                messagebox.showinfo("สำเร็จ", "บันทึกรูปภาพพร้อมฝัง EXIF เรียบร้อยแล้ว!")
                self.btn_save.pack_forget()

    # ================= Extraction Process =================
    def extract_watermark(self):
        if not self.extract_file_path:
            messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกรูปภาพที่ต้องการถอดลายน้ำ")
            return
        if not self.original_img_for_extraction:
            messagebox.showerror("ข้อมูลไม่ครบ", "ระบบต้องการ Original Image (รูปต้นฉบับ) เพื่อเปรียบเทียบ\nกรุณาอัปโหลดรูปต้นฉบับที่ช่องฝังลายน้ำทิ้งไว้")
            return

        try:
            wm_img = Image.open(self.extract_file_path) # โหลดรูป PNG
            orig_img = self.original_img_for_extraction
            
            # ดึง EXIF (Header Metadata) จาก PNG
            img_info = wm_img.info
            ext_fullname = img_info.get("full_name", "N/A")
            ext_rank = img_info.get("Rank", "N/A")
            ext_dept = img_info.get("Department", "N/A")
            ext_role = img_info.get("Role", "N/A")

            wm_img_rgb = wm_img.convert("RGB")
            
            if wm_img_rgb.size != orig_img.size:
                messagebox.showerror("ล้มเหลว", "ขนาดภาพที่นำมาตรวจสอบ ไม่เท่ากับภาพต้นฉบับ")
                return

            _, _, b_wm = wm_img_rgb.split()
            _, _, b_orig = orig_img.split()

            coeffs_wm = pywt.dwt2(np.float32(b_wm), 'haar')
            coeffs_orig = pywt.dwt2(np.float32(b_orig), 'haar')

            LH_wm = coeffs_wm[1][0]
            LH_orig = coeffs_orig[1][0]

            alpha_input = self.slider_alpha.get()
            effective_alpha = alpha_input * self.STRENGTH_MULTIPLIER
            
            # 1. ดึงข้อมูลพิกเซลจากการลบ LH_wm - LH_orig
            W_ext_scrambled = (LH_wm[:64, :64] - LH_orig[:64, :64]) / effective_alpha

            # 2. Thresholding: มากกว่า 0 ให้เป็น 1 (ขาว), น้อยกว่าเท่ากับ 0 เป็น -1 (ดำ)
            # ตามเอกสาร: แปลง 1 เป็น 255 (สีขาว), 0 เป็น 0 (สีดำ)
            W_ext_binary = np.where(W_ext_scrambled > 0, 1, -1)

            # 3. ถอดรหัส Arnold Inverse เพื่อจัดเรียงพิกเซลกลับที่เดิม
            W_extracted = self.inverse_arnold_transform(W_ext_binary, self.ARNOLD_ITERATIONS)

            # 4. แปลงเป็นรูปภาพ ขาว-ดำ
            wm_pattern_array = np.where(W_extracted > 0, 255, 0).astype(np.uint8)
            ext_qr_img = Image.fromarray(wm_pattern_array, mode='L')
            
            self.display_image_in_tab(ext_qr_img, self.lbl_img_ext_qr)
            self.tabview.set("4. QR ที่ถอดได้")

            # แสดงผล EXIF ใน Textbox
            report = (
                "🔍 [ ถอดลายน้ำสำเร็จ ] 🔍\n"
                "----------------------------------------\n"
                "📌 ข้อมูล Header (EXIF / PngInfo):\n"
                f"   - Full Name : {ext_fullname}\n"
                f"   - Rank      : {ext_rank}\n"
                f"   - Dept      : {ext_dept}\n"
                f"   - Role      : {ext_role}\n\n"
                "📌 ข้อมูลในลายน้ำ (QR Code):\n"
                "   -> สแกนรูป QR ที่แท็บที่ 4 เพื่อดู Badge Number และ Hash\n"
                "----------------------------------------"
            )
            self.update_info_box(report)

            self.extract_file_path = None
            self.lbl_extract_file.configure(text="ยังไม่ได้เลือกรูปภาพ", text_color="gray")

        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"เกิดปัญหา: {str(e)}")

if __name__ == "__main__":
    app = WatermarkApp()
    app.mainloop()