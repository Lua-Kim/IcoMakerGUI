import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk  # ImageTk for preview
import struct
import os
from ico_generator import ICOGenerator

class ICOMakerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ICO Maker GUI v0.3")
        self.root.geometry("1000x600")  # Slightly wider for panels
        self.image = None
        self.ico_gen = ICOGenerator()
        self.resolution_vars = {}
        self.last_ico_path = None
        self.resolutions = [256, 128, 64, 48, 40, 32, 24, 20, 16]  # Class level
        self.setup_ui()

    def setup_ui(self):
        # Top toolbar (buttons)
        toolbar = tk.Frame(self.root)
        toolbar.pack(pady=10, fill=tk.X)
        self.select_btn = tk.Button(toolbar, text="이미지 선택 (256x256 이상)", command=self.load_image, font=("Arial", 12))
        self.select_btn.pack(side=tk.LEFT, padx=5)
        self.generate_btn = tk.Button(toolbar, text="ICO 생성", command=self.generate_ico, state="disabled", bg="lightgreen", font=("Arial", 12))
        self.generate_btn.pack(side=tk.LEFT, padx=5)
        self.view_structure_btn = tk.Button(toolbar, text="ICO 구조 보기", command=self.view_ico_structure, state="disabled", font=("Arial", 12))
        self.view_structure_btn.pack(side=tk.LEFT, padx=5)

        # Main: 3-panel layout
        self.paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, pady=10)

        # Left: Input image preview
        left_frame = tk.Frame(self.paned, bg="white", width=200)
        self.paned.add(left_frame, weight=1)
        tk.Label(left_frame, text="입력 이미지 미리보기", font=("Arial", 10)).pack(pady=5)
        self.preview_canvas = tk.Canvas(left_frame, width=200, height=200, bg="gray")
        self.preview_canvas.pack(pady=5)

        # Center: Resolution selection
        mid_frame = tk.Frame(self.paned, bg="white", width=200)
        self.paned.add(mid_frame, weight=1)
        tk.Label(mid_frame, text="해상도 선택", font=("Arial", 10)).pack(pady=5)

        # Scrollable resolution checkboxes (inside mid_frame)
        canvas = tk.Canvas(mid_frame)
        scrollbar = ttk.Scrollbar(mid_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        for res in self.resolutions:
            var = tk.BooleanVar(value=True)
            self.resolution_vars[res] = var
            tk.Checkbutton(scrollable_frame, text=f"{res}x{res} pixels", variable=var, font=("Arial", 10)).pack(anchor="w")

        # Select all/deselect buttons
        control_frame = tk.Frame(mid_frame)
        control_frame.pack(pady=5)
        tk.Button(control_frame, text="전체 선택", command=self.select_all).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="전체 해제", command=self.deselect_all).pack(side=tk.LEFT, padx=5)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Right: ICO structure view
        right_frame = tk.Frame(self.paned, bg="lightgray", width=400)
        self.paned.add(right_frame, weight=2)
        tk.Label(right_frame, text="ICO 파일 구조", font=("Arial", 10)).pack(pady=5)
        self.structure_tree = ttk.Treeview(right_frame, columns=("Value"), show="tree headings", height=20)
        self.structure_tree.heading("#0", text="항목")
        self.structure_tree.heading("Value", text="값")
        self.structure_tree.pack(fill=tk.BOTH, expand=True, pady=10)

        # Bottom status bar
        self.status_label = tk.Label(self.root, text="이미지를 선택해주세요.", font=("Arial", 10))
        self.status_label.pack(pady=10)

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

                # Add preview
                preview_img = self.image.copy()
                preview_img.thumbnail((200, 200))
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
                messagebox.showinfo("성공", f"{message} ({', '.join(map(str, selected_sizes))} 선택)")
            else:
                messagebox.showerror("오류", message)

    def parse_ico(self, file_path):
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            reserved, type_, count = struct.unpack('<HHH', data[0:6])
            header = {'Reserved': reserved, 'Type': type_, 'Count': count}
            
            entries = []
            offset = 6
            for i in range(count):
                width, height, colors, _, planes, bitcount, size, img_offset = struct.unpack('<BBBBHHII', data[offset:offset+16])
                entries.append({
                    'Width': width if width != 0 else 256,
                    'Height': height if height != 0 else 256,
                    'Colors': colors,
                    'Planes': planes,
                    'BitCount': bitcount,
                    'Size': size,
                    'Offset': img_offset
                })
                offset += 16
            return {'header': header, 'entries': entries}
        except Exception as e:
            messagebox.showerror("파싱 오류", str(e))
            return None

    def view_ico_structure(self):
        if not self.last_ico_path:
            messagebox.showwarning("경고", "먼저 ICO를 생성하세요.")
            return
        
        structure = self.parse_ico(self.last_ico_path)
        if not structure:
            return
        
        for item in self.structure_tree.get_children():
            self.structure_tree.delete(item)
        
        root = self.structure_tree.insert("", "end", text="ICO 파일 구조")
        header_id = self.structure_tree.insert(root, "end", text="ICONDIR 헤더")
        for key, val in structure['header'].items():
            self.structure_tree.insert(header_id, "end", text=key, values=(val,))
        
        entries_id = self.structure_tree.insert(root, "end", text="ICONDIRENTRY 목록")
        for i, entry in enumerate(structure['entries']):
            entry_id = self.structure_tree.insert(entries_id, "end", text=f"Entry {i+1}: {entry['Width']}x{entry['Height']}")
            for key, val in entry.items():
                self.structure_tree.insert(entry_id, "end", text=key, values=(val,))
        
        # Expand all nodes
        self.expand_tree(self.structure_tree, root)
        self.status_label.config(text="ICO 구조 로드 완료")

    def expand_tree(self, tree, item):
        tree.item(item, open=True)
        for child in tree.get_children(item):
            self.expand_tree(tree, child)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = ICOMakerGUI(root)
    app.run()