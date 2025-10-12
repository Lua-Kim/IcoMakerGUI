import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
import os
from ico_generator import ICOGenerator  # ico_generator.py에서 가져옴

class ICOMakerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ICO Maker GUI v0.1")
        self.root.geometry("800x600")
        self.image = None
        self.ico_gen = ICOGenerator()  # 추가: ICOGenerator 인스턴스 생성
        self.setup_ui()

    def setup_ui(self):
        # 이미지 선택 버튼 (기존 코드)
        self.select_btn = tk.Button(
            self.root, text="이미지 선택 (256x256 이상)", 
            command=self.load_image, font=("Arial", 12)
        )
        self.select_btn.pack(pady=20)
        
        # 상태 라벨 (기존 코드) - generate_frame 전에 배치
        self.status_label = tk.Label(self.root, text="이미지를 선택해주세요.", font=("Arial", 10))
        self.status_label.pack(pady=10)
        
        # === 추가: ICO 생성 버튼과 체크박스 UI (중복 제거, 여기로 이동) ===
        self.generate_frame = tk.Frame(self.root)
        self.generate_frame.pack(pady=20)

        # 해상도 체크박스 (임시: 모든 해상도)
        self.all_sizes_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            self.generate_frame, 
            text="모든 해상도 (256~16)", 
            variable=self.all_sizes_var,
            font=("Arial", 10)
        ).pack()

        self.generate_btn = tk.Button(
            self.generate_frame, 
            text="ICO 생성", 
            command=self.generate_ico,
            state="disabled",  # 초기 비활성화
            bg="lightgreen",
            font=("Arial", 12)
        )
        self.generate_btn.pack(pady=10)
        # === 추가 끝 ===

    def load_image(self):
        filetypes = [
            ("이미지 파일", "*.jpg *.jpeg *.png *.bmp *.gif"),
            ("PNG", "*.png"),
            ("JPG", "*.jpg *.jpeg"),
            ("All files", "*.*")
        ]
        
        file_path = filedialog.askopenfilename(
            title="256x256 이상 이미지를 선택하세요",
            filetypes=filetypes
        )
        
        if file_path:
            try:
                self.image = Image.open(file_path)
                width, height = self.image.size
                
                # 해상도 검증
                if width < 256 or height < 256:
                    messagebox.showerror(
                        "해상도 오류", 
                        f"이미지 해상도: {width}x{height}\n"
                        "256x256 픽셀 이상의 이미지만 지원합니다."
                    )
                    self.image = None
                    return
                
                self.status_label.config(
                    text=f"로드 완료: {width}x{height} ({os.path.basename(file_path)})"
                )
                messagebox.showinfo("성공", "이미지가 로드되었습니다!")
                
                # === 추가: 이미지 로드 성공 시 ICO 생성 버튼 활성화 ===
                self.generate_btn.config(state="normal")
                # === 추가 끝 ===
                
            except Exception as e:
                messagebox.showerror("오류", f"이미지 로드 실패: {str(e)}")
    
    # === 추가: ICO 생성 메서드 ===
    def generate_ico(self):
        if not self.image:
            messagebox.showwarning("경고", "먼저 이미지를 선택하세요.")
            return
        
        # 저장 경로 선택
        output_path = filedialog.asksaveasfilename(
            defaultextension=".ico",
            filetypes=[("ICO 파일", "*.ico")],
            title="ICO 파일 저장 위치"
        )
        
        if output_path:
            selected_sizes = self.ico_gen.RESOLUTIONS if self.all_sizes_var.get() else []
            success, message = self.ico_gen.create_ico(self.image, selected_sizes, output_path)
            
            if success:
                messagebox.showinfo("성공", message)
            else:
                messagebox.showerror("오류", message)
    # === 추가 끝 ===
    
    # run 메서드: 클래스 수준으로 이동 (들여쓰기 수정)
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = ICOMakerGUI(root)
    app.run()