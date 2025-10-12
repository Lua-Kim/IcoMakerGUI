import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import struct
import os
import io
from ico_generator import ICOGenerator

class ICOMakerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ICO Maker GUI v0.5")
        self.root.geometry("1000x700")
        self.image = None
        self.ico_gen = ICOGenerator()
        self.resolution_vars = {}
        self.last_ico_path = None
        self.resolutions = [256, 128, 64, 48, 40, 32, 24, 20, 16]
        self.ico_data = b''
        self.entries_data = []
        self.setup_ui()

    def setup_ui(self):
        # 상단 툴바
        toolbar = tk.Frame(self.root)
        toolbar.pack(pady=10, fill=tk.X)
        self.select_btn = tk.Button(toolbar, text="이미지 선택 (256x256 이상)", command=self.load_image, font=("Arial", 12))
        self.select_btn.pack(side=tk.LEFT, padx=5)
        self.generate_btn = tk.Button(toolbar, text="ICO 생성", command=self.generate_ico, state="disabled", bg="lightgreen", font=("Arial", 12))
        self.generate_btn.pack(side=tk.LEFT, padx=5)
        self.open_ico_btn = tk.Button(toolbar, text="ICO 열기", command=self.open_existing_ico, font=("Arial", 12))
        self.open_ico_btn.pack(side=tk.LEFT, padx=5)
        self.view_structure_btn = tk.Button(toolbar, text="ICO 구조 보기", command=self.view_ico_structure, state="disabled", font=("Arial", 12))
        self.view_structure_btn.pack(side=tk.LEFT, padx=5)

        # 본문: 3패널
        self.paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, pady=10)

        # 왼쪽: 입력 미리보기 (checkerboard 배경 추가)
        left_frame = tk.Frame(self.paned, bg="white", width=200)
        self.paned.add(left_frame, weight=1)
        tk.Label(left_frame, text="입력 이미지 미리보기", font=("Arial", 10)).pack(pady=5)
        self.preview_canvas = tk.Canvas(left_frame, width=200, height=200, bg="white")
        self.preview_canvas.pack(pady=5)
        self.create_checkerboard_background(self.preview_canvas, 200, 200)

        # 중앙: 해상도 선택
        mid_frame = tk.Frame(self.paned, bg="white")
        self.paned.add(mid_frame, weight=0) # weight를 0으로 설정하여 너비 확장을 막고 최소 크기를 유지
        tk.Label(mid_frame, text="해상도 선택", font=("Arial", 10)).pack(pady=5)

        canvas = tk.Canvas(mid_frame, width=150) # Canvas에 고정 너비를 지정
        scrollbar = ttk.Scrollbar(mid_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        for res in self.resolutions:
            var = tk.BooleanVar(value=True)
            self.resolution_vars[res] = var
            tk.Checkbutton(scrollable_frame, text=f"{res}x{res} pixels", variable=var, font=("Arial", 10)).pack(anchor="w")

        control_frame = tk.Frame(mid_frame)
        control_frame.pack(pady=5)
        tk.Button(control_frame, text="전체 선택", command=self.select_all).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="전체 해제", command=self.deselect_all).pack(side=tk.LEFT, padx=5)

        canvas.pack(side="left", fill="y") # expand=True 제거, fill="y"로 세로 채우기만 유지
        scrollbar.pack(side="right", fill="y")

        # 오른쪽: 구조 + 엔트리 미리보기
        # right_frame을 다시 분할하여 왼쪽은 트리, 오른쪽은 미리보기로 사용
        right_frame = tk.Frame(self.paned, bg="lightgray")
        self.paned.add(right_frame, weight=3)
        right_paned = ttk.PanedWindow(right_frame, orient=tk.HORIZONTAL)
        right_paned.pack(fill=tk.BOTH, expand=True)

        # 트리 스타일 개선 (모던 테마)
        style = ttk.Style()
        try:
            # Windows 11/10 에서는 'vista' 테마가 더 네이티브한 느낌을 줍니다.
            style.theme_use('vista') 
        except tk.TclError:
            # 'vista' 테마가 없는 경우 (e.g., Linux, macOS) 'clam'을 사용합니다.
            style.theme_use('clam')

        # Windows 11 탐색기 스타일과 유사하게 설정
        style.configure("Treeview", background="#ffffff", fieldbackground="#ffffff", foreground="black", rowheight=28, borderwidth=0)
        style.configure("Treeview.Heading", font=("맑은 고딕", 10, "bold"), background="#ffffff", borderwidth=0)
        style.map("Treeview", background=[('selected', '#E6F3FF')], foreground=[('selected', 'black')])
        # 헤딩 부분 클릭/활성화 시 스타일 변경 방지
        style.map("Treeview.Heading", relief=[('!active', 'flat')], background=[('!active', '#ffffff')])
        
        # 오른쪽 패널의 왼쪽 부분 (트리)
        tree_frame = tk.Frame(right_paned)
        right_paned.add(tree_frame, weight=2) # 트리뷰가 더 넓은 공간을 차지하도록 weight 조정

        tk.Label(tree_frame, text="ICO 파일 구조", font=("Arial", 10)).pack(pady=5, anchor='w', padx=5)
        self.header_info_label = tk.Label(tree_frame, text="", font=("Arial", 9), justify=tk.LEFT)
        self.header_info_label.pack(pady=2, fill=tk.X, padx=10)
        
        self.structure_tree = ttk.Treeview(tree_frame, columns=("Value"), show="tree headings", height=15, style="Treeview")
        self.structure_tree.heading("#0", text="항목")
        self.structure_tree.heading("Value", text="값")
        self.structure_tree.column("#0", stretch=tk.YES) # 항목 컬럼이 남은 공간을 모두 사용
        self.structure_tree.column("Value", width=100, anchor='w', stretch=tk.NO) # 값 컬럼 너비 축소
        self.structure_tree.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        self.structure_tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # 펼침/축소 버튼 추가
        tree_control_frame = tk.Frame(tree_frame)
        tree_control_frame.pack(pady=5)
        tk.Button(tree_control_frame, text="전체 펼침", command=self.expand_all_tree).pack(side=tk.LEFT, padx=5)
        tk.Button(tree_control_frame, text="전체 축소", command=self.collapse_all_tree).pack(side=tk.LEFT, padx=5)

        # 오른쪽 패널의 오른쪽 부분 (미리보기)
        preview_frame = tk.Frame(right_paned)
        right_paned.add(preview_frame, weight=1)
        tk.Label(preview_frame, text="선택 엔트리 미리보기", font=("Arial", 10)).pack(pady=5)
        self.entry_preview_canvas = tk.Canvas(preview_frame, width=256, height=256, bg="white")
        self.entry_preview_canvas.pack(pady=5, padx=5)
        self.create_checkerboard_background(self.entry_preview_canvas, 256, 256)

        # 하단 상태 바
        self.status_label = tk.Label(self.root, text="이미지를 선택해주세요.", font=("Arial", 10))
        self.status_label.pack(pady=10)

    # 새: checkerboard 배경 생성 (투명 표현용)
    def create_checkerboard_background(self, canvas, width, height, square_size=10):
        colors = ["#f0f0f0", "#d0d0d0"]
        for y in range(0, height, square_size):
            for x in range(0, width, square_size):
                color = colors[(x // square_size + y // square_size) % 2]
                canvas.create_rectangle(x, y, x + square_size, y + square_size, fill=color, outline="")

    def select_all(self):
        for var in self.resolution_vars.values():
            var.set(True)

    def deselect_all(self):
        for var in self.resolution_vars.values():
            var.set(False)

    def load_image(self):
        filetypes = [("이미지 파일", "*.jpg *.jpeg *.png *.bmp *.gif"), ("All files", "*.*")]
        file_path = filedialog.askopenfilename(title="256x256 이상 이미지를 선택하세요", filetypes=filetypes)
        if file_path:
            try:
                self.image = Image.open(file_path)
                width, height = self.image.size
                if width < 256 or height < 256:
                    messagebox.showerror("해상도 오류", f"이미지 해상도: {width}x{height}\n256x256 이상만 지원.")
                    self.image = None
                    return

                self.status_label.config(text=f"로드 완료: {width}x{height} ({os.path.basename(file_path)})")
                messagebox.showinfo("성공", "이미지가 로드되었습니다!")
                self.generate_btn.config(state="normal")

                # 미리보기 (checkerboard 위에 합성)
                preview_img = self.image.copy()
                preview_img.thumbnail((200, 200))
                if preview_img.mode != 'RGBA':
                    preview_img = preview_img.convert('RGBA')
                self.photo = ImageTk.PhotoImage(preview_img)
                self.preview_canvas.create_image(100, 100, image=self.photo)

            except Exception as e:
                messagebox.showerror("오류", f"이미지 로드 실패: {str(e)}")

    def generate_ico(self):
        if not self.image:
            messagebox.showwarning("경고", "먼저 이미지를 선택하세요.")
            return
        if not any(self.resolution_vars[res].get() for res in self.resolutions):
            messagebox.showwarning("경고", "적어도 하나의 해상도를 선택하세요.")
            return
        
        output_path = filedialog.asksaveasfilename(defaultextension=".ico", filetypes=[("ICO 파일", "*.ico")], title="ICO 파일 저장 위치")
        if output_path:
            selected_sizes = [res for res in self.resolutions if self.resolution_vars[res].get()]
            success, message = self.ico_gen.create_ico(self.image, selected_sizes, output_path)
            if success:
                self.last_ico_path = output_path
                self.view_structure_btn.config(state="normal")
                with open(output_path, 'rb') as f:
                    self.ico_data = f.read()
                messagebox.showinfo("성공", f"{message} ({', '.join(map(str, selected_sizes))} 선택)")
            else:
                messagebox.showerror("오류", message)

    def open_existing_ico(self):
        file_path = filedialog.askopenfilename(filetypes=[("ICO 파일", "*.ico")], title="ICO 파일 열기")
        if file_path:
            self.last_ico_path = file_path
            with open(file_path, 'rb') as f:
                self.ico_data = f.read()
            self.view_structure_btn.config(state="normal")
            self.view_ico_structure()
            self.status_label.config(text=f"ICO 로드 완료: {os.path.basename(file_path)}")

    def parse_ico(self, data):
        try:
            reserved, type_, count = struct.unpack('<HHH', data[0:6])
            header = {'Reserved': reserved, 'Type': type_, 'Count': count}
            
            entries = []
            self.entries_data = []
            offset = 6
            for i in range(count):
                width, height, colors, _, planes, bitcount, size, img_offset = struct.unpack('<BBBBHHII', data[offset:offset+16])
                w = width if width != 0 else 256
                h = height if height != 0 else 256
                entries.append({
                    'Width': w,
                    'Height': h,
                    'Colors': colors,
                    'Planes': planes,
                    'BitCount': bitcount,
                    'Size': size,
                    'Offset': img_offset
                })
                img_data = data[img_offset:img_offset + size]
                self.entries_data.append(img_data)
                offset += 16
            return {'header': header, 'entries': entries}
        except Exception as e:
            messagebox.showerror("파싱 오류", str(e))
            return None

    def view_ico_structure(self):
        if not self.last_ico_path:
            messagebox.showwarning("경고", "먼저 ICO를 생성하세요.")
            return
        
        structure = self.parse_ico(self.ico_data)
        if not structure:
            return
        
        for item in self.structure_tree.get_children():
            self.structure_tree.delete(item)
        
        # 헤더 정보를 레이블에 텍스트로 표시
        header = structure['header']
        header_text = f"타입: {header['Type']} (1: ICO)  |  이미지 개수: {header['Count']}"
        self.header_info_label.config(text=header_text)

        # 트리에는 엔트리 목록만 표시
        top_level_items = []
        for i, entry in enumerate(structure['entries']):
            entry_text = f"Entry {i+1}: {entry['Width']}x{entry['Height']}, BitCount={entry['BitCount']}"
            entry_id = self.structure_tree.insert("", "end", text=entry_text, values=(), tags=(str(i),), open=True)
            top_level_items.append(entry_id)
            for key, val in entry.items():
                self.structure_tree.insert(entry_id, "end", text=key, values=(val,))
        
        self.status_label.config(text="ICO 구조 로드 완료")
        self.collapse_all_tree() # 먼저 모두 닫고
        for item in top_level_items: # 최상위 엔트리들만 펼침
            self.structure_tree.item(item, open=True)

    def on_tree_select(self, event):
        selected = self.structure_tree.selection()
        if not selected:
            return
        item = selected[0]
        tags = self.structure_tree.item(item, "tags")
        if tags and tags[0].isdigit():
            index = int(tags[0])
            if index < len(self.entries_data):
                img_data = self.entries_data[index]
                try:
                    img = Image.open(io.BytesIO(img_data))
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    img.thumbnail((256, 256))
                    self.entry_photo = ImageTk.PhotoImage(img)
                    self.entry_preview_canvas.delete("image") # 이전 이미지 삭제
                    self.entry_preview_canvas.create_image(128, 128, image=self.entry_photo, tags="image")
                    self.status_label.config(text=f"엔트리 {index+1} 미리보기 로드")
                except Exception as e:
                    self.entry_preview_canvas.delete("image")
                    messagebox.showerror("미리보기 오류", str(e))

    def expand_tree(self, tree, item):
        tree.item(item, open=True)
        for child in tree.get_children(item):
            self.expand_tree(tree, child)

    def expand_all_tree(self):
        for item in self.structure_tree.get_children(''):
            self.expand_tree(self.structure_tree, item)

    def collapse_all_tree(self):
        for item in self.structure_tree.get_children(''):
            self.collapse_tree(self.structure_tree, item)

    def collapse_tree(self, tree, item):
        tree.item(item, open=False)
        for child in tree.get_children(item):
            self.collapse_tree(tree, child)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = ICOMakerGUI(root)
    app.run()