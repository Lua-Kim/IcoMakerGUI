import tkinter as tk
from tkinter import filedialog, messagebox, ttk  # ttk 추가: 스크롤바
from PIL import Image
import os
from ico_generator import ICOGenerator

class ICOMakerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ICO Maker GUI v0.2")  # 버전 업
        self.root.geometry("800x600")
        self.image = None
        self.ico_gen = ICOGenerator()
        self.resolution_vars = {}  # 추가: 각 해상도 체크 상태 저장 (dict)
        self.setup_ui()

    def setup_ui(self):
        # 이미지 선택 버튼
        self.select_btn = tk.Button(
            self.root, text="이미지 선택 (256x256 이상)", 
            command=self.load_image, font=("Arial", 12)
        )
        self.select_btn.pack(pady=20)
        
        # 상태 라벨
        self.status_label = tk.Label(self.root, text="이미지를 선택해주세요.", font=("Arial", 10))
        self.status_label.pack(pady=10)
        
        # === 개선: 해상도 선택 프레임 (개별 체크박스 + 스크롤) ===
        self.res_frame = tk.Frame(self.root)
        self.res_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        # 스크롤 가능한 캔버스
        canvas = tk.Canvas(self.res_frame)
        scrollbar = ttk.Scrollbar(self.res_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # 해상도 리스트
        self.resolutions = [256, 128, 64, 48, 40, 32, 24, 20, 16]
        for res in self.resolutions:
            var = tk.BooleanVar(value=True)  # 기본: 모두 체크
            self.resolution_vars[res] = var
            tk.Checkbutton(
                scrollable_frame, 
                text=f"{res}x{res} pixels", 
                variable=var,
                font=("Arial", 10)
            ).pack(anchor="w")

        # 전체 선택/해제 버튼
        control_frame = tk.Frame(self.res_frame)
        control_frame.pack(pady=5)
        tk.Button(control_frame, text="전체 선택", command=self.select_all).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="전체 해제", command=self.deselect_all).pack(side=tk.LEFT, padx=5)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        # === 개선 끝 ===

        # ICO 생성 버튼
        self.generate_btn = tk.Button(
            self.root, 
            text="ICO 생성", 
            command=self.generate_ico,
            state="disabled",
            bg="lightgreen",
            font=("Arial", 12)
        )
        self.generate_btn.pack(pady=20)

    # 추가: 전체 선택/해제 메서드
    def select_all(self):
        for var in self.resolution_vars.values():
            var.set(True)

    def deselect_all(self):
        for var in self.resolution_vars.values():
            var.set(False)

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
                
                if width < 256 or height < 256:
                    messagebox.showerror(
                        "해상도 오류", 
                        f"이미지 해상도: {width}x{height}\n256x256 픽셀 이상만 지원."
                    )
                    self.image = None
                    return
                
                self.status_label.config(
                    text=f"로드 완료: {width}x{height} ({os.path.basename(file_path)})"
                )
                messagebox.showinfo("성공", "이미지가 로드되었습니다!")
                self.generate_btn.config(state="normal")
                
            except Exception as e:
                messagebox.showerror("오류", f"이미지 로드 실패: {str(e)}")

    def generate_ico(self):
        if not self.image:
            messagebox.showwarning("경고", "먼저 이미지를 선택하세요.")
            return
        
        if not any(self.resolution_vars[res].get() for res in self.resolutions):
            messagebox.showwarning("경고", "적어도 하나의 해상도를 선택하세요.")
            return
        
        output_path = filedialog.asksaveasfilename(
            defaultextension=".ico",
            filetypes=[("ICO 파일", "*.ico")],
            title="ICO 파일 저장 위치"
        )
        
        if output_path:
            # 선택된 해상도만 필터링
            selected_sizes = [res for res in self.resolutions if self.resolution_vars[res].get()]
            success, message = self.ico_gen.create_ico(self.image, selected_sizes, output_path)
            
            if success:
                messagebox.showinfo("성공", f"{message} ({', '.join(map(str, selected_sizes))} 선택)")
            else:
                messagebox.showerror("오류", message)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = ICOMakerGUI(root)
    app.run()