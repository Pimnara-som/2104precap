import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
import hashlib
import os
import numpy as np
import base64 
import pywt

ctk.set_appearance_mode("Dark")  
ctk.set_default_color_theme("blue")

class WatermarkApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Evidence Watermarking System (DWT LH-Band Additive)")
        self.geometry("950x700")
        self.resizable(False, False)

        self.current_watermarked_img = None
        self.embed_file_path = None
        self.extract_file_path = None
        
        # ตัวแปรสำหรับเก็บค่า Original Image ไว้ใช้ตอนแกะ (Non-blind Extraction)
        self.original_img_for_extraction = None 

        # ค่าขยายสัญญาณ เพื่อไม่ให้ Alpha 0.1-0.9 ถูกปัดเศษทิ้งตอนเซฟเป็น PNG (uint8)
        self.STRENGTH_MULTIPLIER = 50.0 

        self.setup_ui()

    def setup_ui(self):
        self.left_frame = ctk.CTkFrame(self, width=350, corner_radius=10)
        self.left_frame.pack(side="left", fill="y", padx=20, pady=20)

        self.right_frame = ctk.CTkFrame(self, width=550, corner_radius=10)
        self.right_frame.pack(side="right", fill="both", expand=True, padx=(0, 20), pady=20)

        # ================= ส่วนซ้าย =================
        ctk.CTkLabel(self.left_frame, text="ตั้งค่าข้อมูลหลักฐาน", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 10))

        ctk.CTkLabel(self.left_frame, text="ชื่อ-นามสกุล ผู้ฝังหลักฐาน:").pack(anchor="w", padx=20)
        self.entry_name = ctk.CTkEntry(self.left_frame, width=250)
        self.entry_name.pack(padx=20, pady=(0, 10))

        ctk.CTkLabel(self.left_frame, text="รหัสพนักงาน:").pack(anchor="w", padx=20)
        self.entry_emp_id = ctk.CTkEntry(self.left_frame, width=250)
        self.entry_emp_id.pack(padx=20, pady=(0, 10))

        # เพิ่ม Slider สำหรับปรับค่า Alpha
        ctk.CTkLabel(self.left_frame, text="ความแรงลายน้ำ (Alpha 0.1 - 0.9):").pack(anchor="w", padx=20)
        self.slider_alpha = ctk.CTkSlider(self.left_frame, from_=0.1, to=0.9, number_of_steps=8)
        self.slider_alpha.set(0.5)
        self.slider_alpha.pack(padx=20, pady=(0, 20), fill="x")

        ctk.CTkLabel(self.left_frame, text="--- โหมดฝังลายน้ำ ---", text_color="#28a745").pack(pady=(10, 5))
        
        self.btn_select_embed = ctk.CTkButton(self.left_frame, text="📁 เลือกรูปต้นฉบับ", command=self.select_embed_file, fg_color="#555555", hover_color="#333333")
        self.btn_select_embed.pack(pady=5, padx=20, fill="x")
        
        self.lbl_embed_file = ctk.CTkLabel(self.left_frame, text="ยังไม่ได้เลือกรูปภาพ", text_color="gray", font=("Arial", 12))
        self.lbl_embed_file.pack(pady=(0, 10))

        self.btn_embed = ctk.CTkButton(self.left_frame, text="แยก DWT & เริ่มฝังลายน้ำ (LH)", fg_color="#28a745", hover_color="#218838", command=self.embed_watermark)
        self.btn_embed.pack(pady=(0, 20), padx=20, fill="x")

        ctk.CTkLabel(self.left_frame, text="--- โหมดถอดลายน้ำ ---", text_color="#dc3545").pack(pady=(10, 5))
        
        self.btn_select_extract = ctk.CTkButton(self.left_frame, text="📁 เลือกรูปที่มีลายน้ำ", command=self.select_extract_file, fg_color="#555555", hover_color="#333333")
        self.btn_select_extract.pack(pady=5, padx=20, fill="x")
        
        self.lbl_extract_file = ctk.CTkLabel(self.left_frame, text="ยังไม่ได้เลือกรูปภาพ", text_color="gray", font=("Arial", 12))
        self.lbl_extract_file.pack(pady=(0, 10))

        self.btn_extract = ctk.CTkButton(self.left_frame, text="ถอดลายน้ำจาก LH ย้อนกลับ", fg_color="#dc3545", hover_color="#c82333", command=self.extract_watermark)
        self.btn_extract.pack(pady=5, padx=20, fill="x")

        # ================= ส่วนขวา =================
        self.preview_label = ctk.CTkLabel(self.right_frame, text="พื้นที่แสดงรูปภาพ (Preview)", text_color="gray", width=400, height=350)
        self.preview_label.pack(pady=(20, 10))

        self.info_textbox = ctk.CTkTextbox(self.right_frame, height=120, width=450)
        self.info_textbox.pack(pady=10)
        self.info_textbox.insert("0.0", "ระบบพร้อมทำงาน...")
        self.info_textbox.configure(state="disabled")

        self.btn_save = ctk.CTkButton(self.right_frame, text="💾 ดาวน์โหลดรูปลงเครื่อง", command=self.save_image)
        self.btn_save.pack(pady=10)
        self.btn_save.pack_forget()

    def generate_mock_hash(self):
        mock_log = "Access_Log_TimeBased"
        return hashlib.sha256(mock_log.encode()).hexdigest()[:16]

    def display_image(self, pil_image):
        img_copy = pil_image.copy()
        img_copy.thumbnail((450, 350), Image.LANCZOS)
        ctk_img = ctk.CTkImage(light_image=img_copy, dark_image=img_copy, size=img_copy.size)
        self.preview_label.configure(image=ctk_img, text="")
        self.preview_label.image = ctk_img

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
            # เก็บรูปต้นฉบับไว้สำหรับการถอดลายน้ำ (Non-blind)
            self.original_img_for_extraction = Image.open(path).convert("RGB")

    def select_extract_file(self):
        path = filedialog.askopenfilename(title="เลือกรูปภาพที่ฝังลายน้ำแล้ว", filetypes=[("PNG Files", "*.png")])
        if path:
            self.extract_file_path = path
            filename = os.path.basename(path)
            self.lbl_extract_file.configure(text=filename[:27]+"..." if len(filename)>30 else filename, text_color="white")

    # ================= Core Logic: Data to Binary =================
    def text_to_binary_array(self, text, shape):
        """ แปลงข้อความให้เป็น Array ของ 1 และ -1 ให้ขนาดเท่ากับ DWT Band """
        binary_str = ''.join(format(ord(char), '08b') for char in text)
        bits = np.array([1 if b == '1' else -1 for b in binary_str], dtype=np.float32)
        
        total_pixels = shape[0] * shape[1]
        if len(bits) < total_pixels:
            # ถ้าข้อมูลสั้นกว่าขนาดแบนด์ ให้เติม Padding ด้วย -1
            bits = np.pad(bits, (0, total_pixels - len(bits)), constant_values=-1)
        else:
            bits = bits[:total_pixels] # ตัดทิ้งถ้าเกิน
            
        return bits.reshape(shape)

    def binary_array_to_text(self, array):
        """ แปลง Array ของ 1 และ -1 กลับเป็นข้อความ """
        flat = array.flatten()
        # ทำ Thresholding: ค่ามากกว่า 0 เป็น 1, น้อยกว่า/เท่ากับ 0 เป็น 0
        binary_str = ''.join(['1' if val > 0 else '0' for val in flat])
        
        chars = []
        for i in range(0, len(binary_str), 8):
            byte = binary_str[i:i+8]
            # หยุดเมื่อเจอ Padding (-1 ล้วน หรือ 00000000)
            if byte == '00000000' or byte == '11111111' or len(byte) < 8: 
                break
            try:
                chars.append(chr(int(byte, 2)))
            except:
                break
        return ''.join(chars)

    def embed_watermark(self):
        name = self.entry_name.get().strip()
        emp_id = self.entry_emp_id.get().strip()

        if not name or not emp_id:
            messagebox.showwarning("แจ้งเตือน", "กรุณากรอกข้อมูลให้ครบ")
            return
        if not self.embed_file_path:
            messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกรูปภาพต้นฉบับ")
            return

        try:
            # 1. เตรียมรูปภาพ แยก Channel RGB
            image = Image.open(self.embed_file_path).convert("RGB")
            r, g, b = image.split()
            
            # ใช้เฉพาะ Channel B (Blue) เพื่อซ่อนให้เนียนที่สุด
            arr_b = np.float32(b) 

            # 2. แยก DWT (Haar Level 1)
            coeffs = pywt.dwt2(arr_b, 'haar')
            LL, (LH, HL, HH) = coeffs

            # 3. เตรียมข้อมูลและสร้าง Binary Watermark
            access_hash = self.generate_mock_hash()
            raw_data = f"Name:{name}|ID:{emp_id}|Hash:{access_hash}"
            
            W = self.text_to_binary_array(raw_data, LH.shape)

            # 4. สมการการฝัง (Embedding Equation) -> LH' = LH + (alpha * W)
            alpha_input = self.slider_alpha.get()
            effective_alpha = alpha_input * self.STRENGTH_MULTIPLIER
            LH_new = LH + (effective_alpha * W)

            # 5. ประกอบกลับด้วย Inverse DWT (IDWT)
            coeffs_new = (LL, (LH_new, HL, HH))
            watermarked_b_arr = pywt.idwt2(coeffs_new, 'haar')
            
            # แปลงกลับเป็นค่าสี 0-255
            watermarked_b_arr = np.clip(watermarked_b_arr, 0, 255).astype(np.uint8)
            b_new = Image.fromarray(watermarked_b_arr, mode='L')

            # รวม RGB กลับเป็นภาพสี
            self.current_watermarked_img = Image.merge("RGB", (r, g, b_new))

            self.display_image(self.current_watermarked_img)
            self.update_info_box(f"✅ ฝังลายน้ำลงในแบนด์ LH สำเร็จ!\nAlpha (UI): {alpha_input:.2f} | Alpha (คำนวณจริง): {effective_alpha:.2f}\nข้อมูล: {raw_data}")
            self.btn_save.pack(pady=10) 

        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", str(e))

    def save_image(self):
        if self.current_watermarked_img:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG Files", "*.png")],
                title="บันทึกรูปภาพหลักฐาน"
            )
            if file_path:
                self.current_watermarked_img.save(file_path, "PNG")
                messagebox.showinfo("สำเร็จ", "บันทึกรูปภาพเรียบร้อยแล้ว!")
                self.btn_save.pack_forget()

    # ================= ฟังก์ชันใหม่: แสดงหน้าต่างเปรียบเทียบผลลัพธ์ =================
    def show_extraction_report(self, wm_img, orig_img, W_extracted):
        top = ctk.CTkToplevel(self)
        top.title("รายงานวิเคราะห์การถอดลายน้ำ (Extraction Analysis)")
        top.geometry("900x400")
        top.resizable(False, False)

        # สร้าง Frame จัด Layout 3 ช่อง
        frame_imgs = ctk.CTkFrame(top, fg_color="transparent")
        frame_imgs.pack(pady=20, fill="x")

        # ---------------- ช่องที่ 1: ภาพหลักฐาน ----------------
        frame1 = ctk.CTkFrame(frame_imgs, fg_color="transparent")
        frame1.pack(side="left", expand=True)
        ctk.CTkLabel(frame1, text="1. ภาพหลักฐาน (มองด้วยตาเปล่า)", font=("Arial", 14, "bold")).pack(pady=(0, 10))
        
        img1 = wm_img.copy()
        img1.thumbnail((250, 250), Image.LANCZOS)
        ctk_img1 = ctk.CTkImage(light_image=img1, dark_image=img1, size=img1.size)
        ctk.CTkLabel(frame1, image=ctk_img1, text="").pack()

        # ---------------- ช่องที่ 2: รูปร่างของลายน้ำ Binary ----------------
        frame2 = ctk.CTkFrame(frame_imgs, fg_color="transparent")
        frame2.pack(side="left", expand=True)
        ctk.CTkLabel(frame2, text="2. ลายน้ำที่ดึงได้จากแบนด์ LH", font=("Arial", 14, "bold"), text_color="#28a745").pack(pady=(0, 10))
        
        # แปลง Array ของ Watermark (1, -1) ให้เป็นภาพขาวดำ (255, 0)
        wm_pattern_array = np.where(W_extracted > 0, 255, 0).astype(np.uint8)
        wm_pattern_img = Image.fromarray(wm_pattern_array, mode='L')
        
        # ขยายภาพให้เห็นชัดๆ (เพราะขนาดมันเท่ากับแค่ครึ่งนึงของภาพจริงตามหลัก DWT Level 1)
        wm_pattern_img = wm_pattern_img.resize((250, 250), Image.NEAREST) 
        ctk_img2 = ctk.CTkImage(light_image=wm_pattern_img, dark_image=wm_pattern_img, size=wm_pattern_img.size)
        ctk.CTkLabel(frame2, image=ctk_img2, text="").pack()

        # ---------------- ช่องที่ 3: ภาพแสดงส่วนต่าง (Difference Map) ----------------
        frame3 = ctk.CTkFrame(frame_imgs, fg_color="transparent")
        frame3.pack(side="left", expand=True)
        ctk.CTkLabel(frame3, text="3. จุดที่พิกเซลถูกเปลี่ยน (Diff Map)", font=("Arial", 14, "bold"), text_color="#ffc107").pack(pady=(0, 10))
        
        # นำภาพมาลบกันเพื่อหาความต่าง และคูณเร่งสัญญาณให้สว่างขึ้นเพื่อให้ตาเปล่ามองเห็น
        arr_wm = np.array(wm_img, dtype=np.int16)
        arr_orig = np.array(orig_img, dtype=np.int16)
        diff_array = np.abs(arr_wm - arr_orig)
        
        diff_amplified = np.clip(diff_array * 15, 0, 255).astype(np.uint8) # เร่งแสง 15 เท่า
        diff_img = Image.fromarray(diff_amplified, mode='RGB')
        
        diff_img.thumbnail((250, 250), Image.LANCZOS)
        ctk_img3 = ctk.CTkImage(light_image=diff_img, dark_image=diff_img, size=diff_img.size)
        ctk.CTkLabel(frame3, image=ctk_img3, text="").pack()

    # ================= ฟังก์ชันถอดลายน้ำที่ถูกอัปเดตแล้ว =================
    def extract_watermark(self):
        if not self.extract_file_path:
            messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกรูปลายน้ำ")
            return
        if not self.original_img_for_extraction:
            messagebox.showerror("ข้อมูลไม่ครบ", "การถอดลายน้ำแบบ Additive ต้องใช้ Original Image เป็นฐาน\n(ในหน้าทดสอบนี้ กรุณาอัปโหลดรูปต้นฉบับในช่อง 'ฝังลายน้ำ' ค้างไว้ด้วย)")
            return

        try:
            wm_img = Image.open(self.extract_file_path).convert("RGB")
            orig_img = self.original_img_for_extraction
            
            if wm_img.size != orig_img.size:
                messagebox.showerror("ล้มเหลว", "ขนาดภาพที่นำมาตรวจสอบ ไม่เท่ากับภาพต้นฉบับ")
                return

            _, _, b_wm = wm_img.split()
            _, _, b_orig = orig_img.split()

            coeffs_wm = pywt.dwt2(np.float32(b_wm), 'haar')
            coeffs_orig = pywt.dwt2(np.float32(b_orig), 'haar')

            LH_wm = coeffs_wm[1][0]
            LH_orig = coeffs_orig[1][0]

            alpha_input = self.slider_alpha.get()
            effective_alpha = alpha_input * self.STRENGTH_MULTIPLIER
            
            W_extracted = (LH_wm - LH_orig) / effective_alpha

            decoded_str = self.binary_array_to_text(W_extracted)

            if "Name:" in decoded_str and "|ID:" in decoded_str:
                self.display_image(wm_img)
                self.update_info_box(f"🔍 [ ถอดลายน้ำสำเร็จ ] 🔍\n{decoded_str}")
                
                # --- เรียกใช้งานหน้าต่างเปรียบเทียบที่นี่ ---
                self.show_extraction_report(wm_img, orig_img, W_extracted)
                
            else:
                self.update_info_box("❌ ไม่สามารถถอดลายน้ำได้ หรือรูปภาพมีการถูกดัดแปลงเกินไป\n(อาจจะเกิดจากตั้งค่า Alpha ต่ำเกินไป ทำให้ข้อมูลสูญหายตอนเซฟไฟล์)")

            self.extract_file_path = None
            self.lbl_extract_file.configure(text="ยังไม่ได้เลือกรูปภาพ", text_color="gray")

        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"เกิดปัญหา: {str(e)}")

if __name__ == "__main__":
    app = WatermarkApp()
    app.mainloop()