import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw, PngImagePlugin, ImageFont
import hashlib
import os
import numpy as np
import base64 

# ตั้งค่า Theme ของ UI
ctk.set_appearance_mode("Dark")  
ctk.set_default_color_theme("blue")

class WatermarkApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Evidence Watermarking System (Fragile / Destructive)")
        self.geometry("900x650")
        self.resizable(False, False)

        # ตัวแปรเก็บสถานะ
        self.current_watermarked_img = None
        self.current_metadata = None
        self.embed_file_path = None
        self.extract_file_path = None

        self.setup_ui()

    def setup_ui(self):
        self.left_frame = ctk.CTkFrame(self, width=320, corner_radius=10)
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
        self.entry_emp_id.pack(padx=20, pady=(0, 20))

        ctk.CTkLabel(self.left_frame, text="--- โหมดฝังลายน้ำ ---", text_color="#28a745").pack(pady=(10, 5))
        
        self.btn_select_embed = ctk.CTkButton(self.left_frame, text="📁 เลือกรูปต้นฉบับ", command=self.select_embed_file, fg_color="#555555", hover_color="#333333")
        self.btn_select_embed.pack(pady=5, padx=20, fill="x")
        
        self.lbl_embed_file = ctk.CTkLabel(self.left_frame, text="ยังไม่ได้เลือกรูปภาพ", text_color="gray", font=("Arial", 12))
        self.lbl_embed_file.pack(pady=(0, 10))

        self.btn_embed = ctk.CTkButton(self.left_frame, text="เริ่มฝังลายน้ำ (Invisible)", fg_color="#28a745", hover_color="#218838", command=self.embed_watermark)
        self.btn_embed.pack(pady=(0, 20), padx=20, fill="x")

        ctk.CTkLabel(self.left_frame, text="--- โหมดถอดลายน้ำ ---", text_color="#dc3545").pack(pady=(10, 5))
        
        self.btn_select_extract = ctk.CTkButton(self.left_frame, text="📁 เลือกรูปที่มีลายน้ำ", command=self.select_extract_file, fg_color="#555555", hover_color="#333333")
        self.btn_select_extract.pack(pady=5, padx=20, fill="x")
        
        self.lbl_extract_file = ctk.CTkLabel(self.left_frame, text="ยังไม่ได้เลือกรูปภาพ", text_color="gray", font=("Arial", 12))
        self.lbl_extract_file.pack(pady=(0, 10))

        self.btn_extract = ctk.CTkButton(self.left_frame, text="ถอดลายน้ำ (ทำลายหลักฐาน)", fg_color="#dc3545", hover_color="#c82333", command=self.extract_and_destroy)
        self.btn_extract.pack(pady=5, padx=20, fill="x")

        # ================= ส่วนขวา =================
        self.preview_label = ctk.CTkLabel(self.right_frame, text="พื้นที่แสดงรูปภาพ (Preview)", text_color="gray", width=400, height=350)
        self.preview_label.pack(pady=(20, 10))

        self.info_textbox = ctk.CTkTextbox(self.right_frame, height=120, width=450)
        self.info_textbox.pack(pady=10)
        self.info_textbox.insert("0.0", "ข้อมูลที่ถอดได้ หรือสถานะระบบ จะแสดงที่นี่...")
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
            if len(filename) > 30: filename = filename[:27] + "..."
            self.lbl_embed_file.configure(text=filename, text_color="white")

    def select_extract_file(self):
        path = filedialog.askopenfilename(title="เลือกรูปภาพที่ฝังลายน้ำแล้ว", filetypes=[("PNG Files", "*.png")])
        if path:
            self.extract_file_path = path
            filename = os.path.basename(path)
            if len(filename) > 30: filename = filename[:27] + "..."
            self.lbl_extract_file.configure(text=filename, text_color="white")

    def embed_watermark(self):
        name = self.entry_name.get().strip()
        emp_id = self.entry_emp_id.get().strip()

        if not name or not emp_id:
            messagebox.showwarning("แจ้งเตือน", "กรุณากรอก ชื่อ-นามสกุล และ รหัสพนักงาน ให้ครบถ้วน")
            return
        if not self.embed_file_path:
            messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกรูปภาพต้นฉบับก่อนกดฝังลายน้ำ")
            return

        try:
            access_hash = self.generate_mock_hash()
            
            raw_data = f"Name:{name}|ID:{emp_id}|Hash:{access_hash}"
            encoded_bytes = base64.b64encode(raw_data.encode('utf-8'))
            encoded_str = encoded_bytes.decode('utf-8') 

            image = Image.open(self.embed_file_path).convert("RGBA")
            width, height = image.size
            
            txt_layer = Image.new("RGBA", image.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(txt_layer)
            
            # วาดด้วย Alpha = 3 (กลืนไปกับรูป)
            watermark_color = (255, 255, 255, 3) 
            
            bbox = draw.textbbox((0, 0), encoded_str)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            x = (width - text_w) // 2
            y = (height - text_h) // 2
            
            draw.text((x, y), encoded_str, fill=watermark_color)
            
            watermarked_image = Image.alpha_composite(image, txt_layer).convert("RGB")

            meta_info = PngImagePlugin.PngInfo()
            meta_info.add_text("SecuredData", encoded_str)

            self.current_watermarked_img = watermarked_image
            self.current_metadata = meta_info

            self.display_image(self.current_watermarked_img)
            self.update_info_box(f"✅ ฝังลายน้ำแบบมองไม่เห็นเสร็จสิ้น!\n\nข้อมูลที่ถูกเข้ารหัสฝังลงไป: {encoded_str}\n(ตรวจสอบรูปด้านบน หากถูกต้องให้กดดาวน์โหลด)")
            self.btn_save.pack(pady=10) 

        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", str(e))

    def save_image(self):
        if self.current_watermarked_img and self.current_metadata:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG Files", "*.png")],
                title="บันทึกรูปภาพหลักฐาน"
            )
            if file_path:
                self.current_watermarked_img.save(file_path, "PNG", pnginfo=self.current_metadata)
                messagebox.showinfo("สำเร็จ", "บันทึกรูปภาพหลักฐานเรียบร้อยแล้ว!")
                self.btn_save.pack_forget()

    def extract_and_destroy(self):
        if not self.extract_file_path:
            messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกรูปภาพที่ฝังลายน้ำก่อนกดถอดลายน้ำ")
            return

        try:
            image = Image.open(self.extract_file_path)
            info = image.info
            
            encoded_str = info.get("SecuredData", "ไม่พบข้อมูล")

            if encoded_str == "ไม่พบข้อมูล":
                messagebox.showwarning("ล้มเหลว", "รูปภาพนี้ไม่มีลายน้ำระบบหลักฐาน หรือไม่ใช่ไฟล์ที่ถูกเข้ารหัสไว้")
                return

            # ถอดรหัส (Decode) ข้อความ
            try:
                decoded_bytes = base64.b64decode(encoded_str.encode('utf-8'))
                decoded_str = decoded_bytes.decode('utf-8')
                
                parts = decoded_str.split("|")
                name_part = parts[0].replace("Name:", "")
                id_part = parts[1].replace("ID:", "")
                hash_part = parts[2].replace("Hash:", "")
            except Exception:
                messagebox.showerror("ล้มเหลว", "ข้อมูลถูกบิดเบือน ไม่สามารถถอดรหัสได้")
                return

            # ==============================================================
            # 2. ถอดลายน้ำแบบ Destructive (ดึงข้อมูลพิกเซลจนภาพพัง)
            # ==============================================================
            image_rgb = image.convert("RGB")
            
            # แปลงภาพเป็นชุดตัวเลขเพื่อคำนวณทางคณิตศาสตร์ (ใช้ float เพื่อไม่ให้ค่าตันที่ 255 ตอนคูณ)
            img_array = np.array(image_rgb, dtype=np.float32)
            
            # เร่งสัญญาณพิกเซลขึ้น 50 เท่า เพื่อจำลองการเค้นหาลายน้ำที่ซ่อนอยู่
            # ใช้ modulo 255 (% 255) เพื่อให้ค่าสีที่ล้นกรอบวนลูปกลับมา ทำให้สีเพี้ยนแตกทั้งภาพ
            distorted_array = (img_array * 50) % 255
            
            # แปลงชุดตัวเลขที่บิดเบี้ยวแล้วกลับเป็นรูปภาพ
            destroyed_image = Image.fromarray(distorted_array.astype(np.uint8))

            # แสดงผล
            self.display_image(destroyed_image)
            extracted_text = f"🚨 [ ข้อมูลหลักฐานถูกเปิดเผย ] 🚨\nเจ้าหน้าที่: {name_part}\nรหัสพนักงาน: {id_part}\nHash: {hash_part}\n\n*สถานะ: รูปหลักฐานเสียหาย (Distorted) จากกระบวนการเร่งสัญญาณเพื่อดึงข้อมูล*"
            self.update_info_box(extracted_text)
            
            self.btn_save.pack_forget()

            # บันทึกรูปที่พังแล้วทับไฟล์เดิมทันทีเพื่อป้องกันการนำไปใช้ต่อ
            destroyed_image.save(self.extract_file_path)
            
            self.extract_file_path = None
            self.lbl_extract_file.configure(text="ยังไม่ได้เลือกรูปภาพ", text_color="gray")

        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"เกิดปัญหาในการอ่านไฟล์: {str(e)}")

if __name__ == "__main__":
    app = WatermarkApp()
    app.mainloop()