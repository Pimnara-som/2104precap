import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageOps
import hashlib
import os
import numpy as np
import pywt
import qrcode
from pyzbar.pyzbar import decode

ctk.set_appearance_mode("Dark")  
ctk.set_default_color_theme("blue")

class WatermarkApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Evidence Watermarking System (QR + Arnold)")
        # ปรับความกว้างและสูงเพิ่มขึ้นเล็กน้อยเพื่อให้มีพื้นที่แสดงหลายรูปในหน้าเดียว
        self.geometry("1150x800")
        
        # เพิ่ม minsize บังคับขนาดขั้นต่ำ เพื่อป้องกันหน้าต่างหดตัวบน macOS
        self.minsize(1150, 800) 
        # ปิดคำสั่ง resizable ทิ้งไป เพื่อไม่ให้ขัดแย้งกับระบบของ Mac
        # self.resizable(False, False)

        self.current_watermarked_img = None
        self.embed_file_path = None
        self.extract_file_path = None
        
        self.original_img_for_extraction = None 
        self.STRENGTH_MULTIPLIER = 50.0 
        self.ARNOLD_ITERATIONS = 5

        self.setup_ui()

    def setup_ui(self):
        # ================= ส่วนซ้าย (Input) =================
        self.left_frame = ctk.CTkScrollableFrame(self, width=350, corner_radius=10)
        self.left_frame.pack(side="left", fill="y", padx=20, pady=20)

        self.right_frame = ctk.CTkFrame(self, width=750, corner_radius=10)
        self.right_frame.pack(side="right", fill="both", expand=True, padx=(0, 20), pady=20)

        ctk.CTkLabel(self.left_frame, text="ตั้งค่าข้อมูลหลักฐาน", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(10, 10))

        # Inputs...
        ctk.CTkLabel(self.left_frame, text="1. รหัสประจำตัว (Badge Number):").pack(anchor="w", padx=10)
        self.entry_badge = ctk.CTkEntry(self.left_frame, width=300)
        self.entry_badge.pack(padx=10, pady=(0, 10))

        ctk.CTkLabel(self.left_frame, text="2. ชื่อ-นามสกุลจริง:").pack(anchor="w", padx=10)
        self.entry_fullname = ctk.CTkEntry(self.left_frame, width=300)
        self.entry_fullname.pack(padx=10, pady=(0, 10))

        ctk.CTkLabel(self.left_frame, text="3. ยศ/ตำแหน่ง (Rank):").pack(anchor="w", padx=10)
        self.entry_rank = ctk.CTkEntry(self.left_frame, width=300)
        self.entry_rank.pack(padx=10, pady=(0, 10))

        ctk.CTkLabel(self.left_frame, text="4. หน่วยงาน/สังกัด (Dept):").pack(anchor="w", padx=10)
        self.entry_dept = ctk.CTkEntry(self.left_frame, width=300)
        self.entry_dept.pack(padx=10, pady=(0, 10))

        ctk.CTkLabel(self.left_frame, text="5. บทบาท (Role):").pack(anchor="w", padx=10)
        self.entry_role = ctk.CTkEntry(self.left_frame, width=300)
        self.entry_role.pack(padx=10, pady=(0, 10))

        ctk.CTkLabel(self.left_frame, text="ความแรงลายน้ำ (Alpha 0.1 - 0.9):").pack(anchor="w", padx=10)
        self.slider_alpha = ctk.CTkSlider(self.left_frame, from_=0.1, to=0.9, number_of_steps=8)
        self.slider_alpha.set(0.5)
        self.slider_alpha.pack(padx=10, pady=(0, 20), fill="x")

        # Buttons - Embed
        ctk.CTkLabel(self.left_frame, text="--- โหมดฝังลายน้ำ ---", text_color="#28a745").pack(pady=(5, 5))
        self.btn_select_embed = ctk.CTkButton(self.left_frame, text="📁 เลือกรูปต้นฉบับ", command=self.select_embed_file, fg_color="#555555", hover_color="#333333")
        self.btn_select_embed.pack(pady=5, padx=10, fill="x")
        self.lbl_embed_file = ctk.CTkLabel(self.left_frame, text="ยังไม่ได้เลือกรูปภาพ", text_color="gray", font=("Arial", 12))
        self.lbl_embed_file.pack(pady=(0, 10))
        self.btn_embed = ctk.CTkButton(self.left_frame, text="สลับพิกเซล & ฝัง QR", fg_color="#28a745", hover_color="#218838", command=self.embed_watermark)
        self.btn_embed.pack(pady=(0, 20), padx=10, fill="x")

        # Buttons - Extract
        ctk.CTkLabel(self.left_frame, text="--- โหมดถอดลายน้ำ ---", text_color="#dc3545").pack(pady=(5, 5))
        self.btn_select_extract = ctk.CTkButton(self.left_frame, text="📁 เลือกรูปที่มีลายน้ำ", command=self.select_extract_file, fg_color="#555555", hover_color="#333333")
        self.btn_select_extract.pack(pady=5, padx=10, fill="x")
        self.lbl_extract_file = ctk.CTkLabel(self.left_frame, text="ยังไม่ได้เลือกรูปภาพ", text_color="gray", font=("Arial", 12))
        self.lbl_extract_file.pack(pady=(0, 10))
        self.btn_extract = ctk.CTkButton(self.left_frame, text="แกะลายน้ำ & อ่านข้อมูล", fg_color="#dc3545", hover_color="#c82333", command=self.extract_watermark)
        self.btn_extract.pack(pady=5, padx=10, fill="x")

        # ================= ส่วนขวา (Preview Area: 2 Pages) =================
        self.tabview = ctk.CTkTabview(self.right_frame, width=700, height=550)
        self.tabview.pack(pady=10, padx=10, fill="both", expand=True)

        self.tab_embed = self.tabview.add("หน้า 1: ฝังลายน้ำ")
        self.tab_extract = self.tabview.add("หน้า 2: แกะลายน้ำ")

        # ---- สร้างหน้า 1 (ฝังลายน้ำ) ----
        # แถวบน: รูปต้นฉบับ กับ QR
        self.frame_embed_top = ctk.CTkFrame(self.tab_embed, fg_color="transparent")
        self.frame_embed_top.pack(fill="x", pady=5)
        
        self.frame_orig, self.lbl_img_orig = self.create_image_frame(self.frame_embed_top, "1. ภาพก่อนฝัง")
        self.frame_orig.pack(side="left", expand=True, fill="both", padx=5)

        self.frame_qr, self.lbl_img_qr = self.create_image_frame(self.frame_embed_top, "2. QR ที่จะนำไปฝัง")
        self.frame_qr.pack(side="right", expand=True, fill="both", padx=5)

        # แถวล่าง: รูปหลังฝัง
        self.frame_embed_bottom = ctk.CTkFrame(self.tab_embed, fg_color="transparent")
        self.frame_embed_bottom.pack(fill="both", expand=True, pady=10)
        self.frame_wm, self.lbl_img_wm = self.create_image_frame(self.frame_embed_bottom, "3. ภาพหลังฝัง")
        self.frame_wm.pack(expand=True, fill="both")

        # ---- สร้างหน้า 2 (แกะลายน้ำ) ----
        self.frame_extract_main = ctk.CTkFrame(self.tab_extract, fg_color="transparent")
        self.frame_extract_main.pack(fill="both", expand=True, pady=10)

        self.frame_ext_source, self.lbl_img_ext_source = self.create_image_frame(self.frame_extract_main, "1. ภาพที่นำมาถอดลายน้ำ")
        self.frame_ext_source.pack(side="left", expand=True, fill="both", padx=5)

        self.frame_ext_qr, self.lbl_img_ext_qr = self.create_image_frame(self.frame_extract_main, "2. QR ที่ถอดออกมาได้")
        self.frame_ext_qr.pack(side="right", expand=True, fill="both", padx=5)

        # ---- กล่องข้อความ และ ปุ่มเซฟรูป ----
        self.info_textbox = ctk.CTkTextbox(self.right_frame, height=120, width=700)
        self.info_textbox.pack(pady=10, padx=10)
        self.info_textbox.insert("0.0", "ระบบพร้อมทำงาน...")
        self.info_textbox.configure(state="disabled")

        self.btn_save = ctk.CTkButton(self.right_frame, text="💾 บันทึกรูปภาพที่ฝังลายน้ำแล้ว", command=self.save_image)
        self.btn_save.pack(pady=10)
        self.btn_save.pack_forget()

    # ================= UI Utils =================
    def create_image_frame(self, parent, title):
        """ ฟังก์ชันช่วยสร้าง Frame ที่มี Title และ Label สำหรับใส่รูป """
        frame = ctk.CTkFrame(parent, fg_color="#2b2b2b")
        lbl_title = ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(weight="bold"))
        lbl_title.pack(pady=(5, 0))
        lbl_img = ctk.CTkLabel(frame, text="ยังไม่มีรูปภาพ", text_color="gray")
        lbl_img.pack(expand=True, pady=5)
        return frame, lbl_img

    def display_image_in_tab(self, pil_image, label_widget, max_size=(300, 300)):
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

    # ================= Arnold Scrambling Methods =================
    def arnold_transform(self, img_array, iterations):
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

    # ================= File Selection =================
    def select_embed_file(self):
        path = filedialog.askopenfilename(title="เลือกรูปภาพต้นฉบับ", filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
        if path:
            self.embed_file_path = path
            filename = os.path.basename(path)
            self.lbl_embed_file.configure(text=filename[:27]+"..." if len(filename)>30 else filename, text_color="white")
            self.original_img_for_extraction = Image.open(path).convert("RGB")
            
            # โชว์รูปลงในช่อง 'ภาพก่อนฝัง'
            self.display_image_in_tab(self.original_img_for_extraction, self.lbl_img_orig, max_size=(250, 200))
            self.tabview.set("หน้า 1: ฝังลายน้ำ")

    def select_extract_file(self):
        path = filedialog.askopenfilename(title="เลือกรูปภาพที่ฝังลายน้ำแล้ว", filetypes=[("PNG Files", "*.png")])
        if path:
            self.extract_file_path = path
            filename = os.path.basename(path)
            self.lbl_extract_file.configure(text=filename[:27]+"..." if len(filename)>30 else filename, text_color="white")
            
            # นำรูปมาพรีวิวในหน้า 2 (ภาพที่นำมาถอดลายน้ำ)
            ext_preview = Image.open(path).convert("RGB")
            self.display_image_in_tab(ext_preview, self.lbl_img_ext_source, max_size=(320, 320))
            self.tabview.set("หน้า 2: แกะลายน้ำ")

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

            # 2. สร้าง QR Code
            qr_payload = f"Badge: {badge} | Hash: {data_hash}"
            qr = qrcode.make(qr_payload.encode('utf-8'))  
            qr_64 = qr.resize((64, 64), Image.NEAREST) 
            self.display_image_in_tab(qr_64, self.lbl_img_qr, max_size=(150, 150))

            # 3. แปลงเป็นอาร์เรย์ 
            qr_arr = np.array(qr_64.convert("L"))
            W = np.where(qr_arr > 128, 1, -1).astype(np.float32)

            # 4. สลับพิกเซล (Arnold Transform)
            W_scrambled = self.arnold_transform(W, self.ARNOLD_ITERATIONS)

            # 5. แยก DWT
            image = Image.open(self.embed_file_path).convert("RGB")
            r, g, b = image.split()
            arr_b = np.float32(b) 
            coeffs = pywt.dwt2(arr_b, 'haar')
            LL, (LH, HL, HH) = coeffs

            if LH.shape[0] < 64 or LH.shape[1] < 64:
                messagebox.showerror("Error", "รูปภาพเล็กเกินไป ต้องมีขนาดอย่างน้อย 128x128 พิกเซล")
                return

            # 6. สมการฝัง
            alpha_input = self.slider_alpha.get()
            effective_alpha = alpha_input * self.STRENGTH_MULTIPLIER
            
            LH_new = np.copy(LH)
            LH_new[:64, :64] = LH[:64, :64] + (effective_alpha * W_scrambled)

            # 7. IDWT คืนค่า
            coeffs_new = (LL, (LH_new, HL, HH))
            watermarked_b_arr = pywt.idwt2(coeffs_new, 'haar')
            watermarked_b_arr = np.clip(watermarked_b_arr, 0, 255).astype(np.uint8)
            b_new = Image.fromarray(watermarked_b_arr, mode='L')

            # รวมสีและโชว์ภาพหลังฝัง
            self.current_watermarked_img = Image.merge("RGB", (r, g, b_new))
            self.display_image_in_tab(self.current_watermarked_img, self.lbl_img_wm, max_size=(350, 250))

            self.update_info_box("✅ ฝังลายน้ำสำเร็จ! ภาพเปรียบเทียบแสดงอยู่ใน 'หน้า 1: ฝังลายน้ำ'\nสามารถกดปุ่มบันทึกด้านล่างเพื่อเซฟไฟล์ได้ทันที")
            self.tabview.set("หน้า 1: ฝังลายน้ำ")
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

    # ================= Extraction Process =================
    def extract_watermark(self):
        if not self.extract_file_path:
            messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกรูปภาพที่ต้องการถอดลายน้ำ")
            return
        if not self.original_img_for_extraction:
            messagebox.showerror("ข้อมูลไม่ครบ", "ระบบต้องการ Original Image (รูปต้นฉบับ) เพื่อเปรียบเทียบ\nกรุณาอัปโหลดรูปต้นฉบับที่ช่องฝังลายน้ำทิ้งไว้")
            return

        try:
            wm_img = Image.open(self.extract_file_path)
            orig_img = self.original_img_for_extraction
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
            
            W_ext_scrambled = (LH_wm[:64, :64] - LH_orig[:64, :64]) / effective_alpha
            W_ext_binary = np.where(W_ext_scrambled > 0, 1, -1)
            W_extracted = self.inverse_arnold_transform(W_ext_binary, self.ARNOLD_ITERATIONS)

            wm_pattern_array = np.where(W_extracted > 0, 255, 0).astype(np.uint8)
            ext_qr_img = Image.fromarray(wm_pattern_array, mode='L')
            
            # แสดง QR ที่ถอดได้
            self.display_image_in_tab(ext_qr_img, self.lbl_img_ext_qr, max_size=(320, 320))
            self.tabview.set("หน้า 2: แกะลายน้ำ")

            # อ่าน QR
            qr_img_resized = ext_qr_img.resize((300, 300), Image.NEAREST)
            qr_img_bordered = ImageOps.expand(qr_img_resized, border=40, fill=255)
            decoded_objects = decode(qr_img_bordered)
            
            if decoded_objects:
                qr_text = decoded_objects[0].data.decode("utf-8")
                extracted_text = f"✅ อ่านได้สำเร็จ:\n{qr_text}"
            else:
                extracted_text = "❌ ไม่สามารถอ่านข้อความได้ (รูปร่าง QR อาจบิดเบี้ยวเกินไป หรือบันทึกผิด format)"

            report = (
                "🔍 [ แกะลายน้ำเสร็จสิ้น ] 🔍\n"
                "----------------------------------------\n"
                "📌 ข้อมูลที่ถอดรหัสได้จากลายน้ำ (QR Code):\n\n"
                f"{extracted_text}\n\n"
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