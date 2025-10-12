import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import sys
import ctypes
import struct
import os
import io
from ico_generator import ICOGenerator

class Win32TitleBar:
    """Windows 전용: 제목 표시줄 다크 모드 및 깜빡임 방지 처리"""
    def __init__(self, root):
        if sys.platform != 'win32':
            self.supported = False
            return
        
        self.supported = True
        self.root = root
        self.root.update_idletasks()
        hwnd = self.root.winfo_id()

        # 창 메시지 콜백 함수 정의
        self.WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_int, ctypes.c_uint, ctypes.c_int, ctypes.c_int)
        
        # 원래의 Window Procedure를 저장할 변수
        self.original_wndproc = ctypes.windll.user32.GetWindowLongPtrW(hwnd, -4) # GWL_WNDPROC = -4

        # 새로운 Window Procedure 생성
        self.new_wndproc = self.WNDPROC(self._wnd_proc_hook)

        # Window Procedure를 새로운 것으로 교체
        ctypes.windll.user32.SetWindowLongPtrW(hwnd, -4, self.new_wndproc)

    def _wnd_proc_hook(self, hwnd, msg, wparam, lparam):
        WM_NCACTIVATE = 0x0086
        if msg == WM_NCACTIVATE and wparam == 0: # 창이 비활성화될 때
            # 제목 표시줄을 다시 그리지 않도록 1을 반환
            return 1
        # 다른 모든 메시지는 원래의 프로시저로 전달
        return ctypes.windll.user32.CallWindowProcW(self.original_wndproc, hwnd, msg, wparam, lparam)

    def set_theme(self, theme_name):
        if not self.supported: return
        is_dark = 1 if theme_name == 'dark' else 0
        hwnd = self.root.winfo_id()
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(ctypes.c_int(is_dark)), ctypes.sizeof(ctypes.c_int(is_dark)))

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

        self.themes = {
            "light": {
                "bg": "#FCFCFC",
                "fg": "black",
                "toolbar_bg": "#FCFCFC",
                "button_bg": "#0000D4",
                "button_fg": "black",
                "disabled_fg": "#a3a3a3",
                "generate_btn_bg": "lightgreen",
                "canvas_bg": "white",
                "tree_bg": "#ffffff",
                "tree_fg": "black",
                "tree_field_bg": "#ffffff",
                "tree_selected_bg": "#E6F3FF",
                "tree_selected_fg": "black",
                "tree_heading_bg": "#ffffff",
                "checker_1": "#f0f0f0",
                "checker_2": "#e0e0e0",
            },
            "dark": {
                "bg": "#2b2b2b",
                "fg": "#f3f3f3",
                "toolbar_bg": "#3c3c3c",
                "button_bg": "#0000D4",
                "button_fg": "#f3f3f3",
                "disabled_fg": "#888888",
                "generate_btn_bg": "#727272",
                "canvas_bg": "#404040",
                "tree_bg": "#404040",
                "tree_fg": "#858585",
                "tree_field_bg": "#404040",
                "tree_selected_bg": "#0078d7",
                "tree_selected_fg": "#f3f3f3",
                "tree_heading_bg": "#404040",
                "tree_heading_fg": "#f3f3f3",
                "checker_1": "#404040",
                "checker_2": "#505050",
            }
        }
        self.current_theme = "dark" if self.is_dark_mode() else "light"

        self.setup_ui()
        self.title_bar_handler = Win32TitleBar(self.root)
        self.apply_theme()

    def setup_ui(self):
        # 상단 툴바
        self.toolbar = tk.Frame(self.root)
        self.toolbar.pack(pady=10, fill=tk.X)
        self.select_btn = tk.Button(self.toolbar, text="이미지 선택 (256x256 이상)", command=self.load_image, font=("Arial", 12))
        self.select_btn.pack(side=tk.LEFT, padx=5)
        self.generate_btn = tk.Button(self.toolbar, text="ICO 생성", command=self.generate_ico, state="disabled", font=("Arial", 12))
        self.generate_btn.pack(side=tk.LEFT, padx=5)
        self.open_ico_btn = tk.Button(self.toolbar, text="ICO 열기", command=self.open_existing_ico, font=("Arial", 12))
        self.open_ico_btn.pack(side=tk.LEFT, padx=5)
        self.view_structure_btn = tk.Button(self.toolbar, text="ICO 구조 보기", command=self.view_ico_structure, state="disabled", font=("Arial", 12))
        self.view_structure_btn.pack(side=tk.LEFT, padx=5)

        # 본문: 3패널
        self.paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, pady=10)

        # 왼쪽: 입력 미리보기 (checkerboard 배경 추가)
        self.left_frame = tk.Frame(self.paned, width=200)
        self.paned.add(self.left_frame, weight=1)
        self.left_label = tk.Label(self.left_frame, text="입력 이미지 미리보기", font=("Arial", 10))
        self.left_label.pack(pady=5)
        self.preview_canvas = tk.Canvas(self.left_frame, width=200, height=200)
        self.preview_canvas.pack(pady=5)

        # 중앙: 해상도 선택
        self.mid_frame = tk.Frame(self.paned)
        self.paned.add(self.mid_frame, weight=0) # weight를 0으로 설정하여 너비 확장을 막고 최소 크기를 유지
        self.mid_label = tk.Label(self.mid_frame, text="해상도 선택", font=("Arial", 10))
        self.mid_label.pack(pady=5)

        self.res_canvas = tk.Canvas(self.mid_frame, width=150, highlightthickness=0) # Canvas에 고정 너비를 지정
        self.res_scrollbar = ttk.Scrollbar(self.mid_frame, orient="vertical", command=self.res_canvas.yview)
        self.res_scrollable_frame = tk.Frame(self.res_canvas)

        self.res_scrollable_frame.bind("<Configure>", lambda e: self.res_canvas.configure(scrollregion=self.res_canvas.bbox("all")))
        self.res_canvas.create_window((0, 0), window=self.res_scrollable_frame, anchor="nw")
        self.res_canvas.configure(yscrollcommand=self.res_scrollbar.set)

        for res in self.resolutions:
            var = tk.BooleanVar(value=True)
            self.resolution_vars[res] = var
            cb = tk.Checkbutton(self.res_scrollable_frame, text=f"{res}x{res} pixels", variable=var, font=("Arial", 10))
            cb.pack(anchor="w")

        self.res_control_frame = tk.Frame(self.mid_frame)
        self.res_control_frame.pack(pady=5)
        self.select_all_btn = tk.Button(self.res_control_frame, text="전체 선택", command=self.select_all)
        self.select_all_btn.pack(side=tk.LEFT, padx=5)
        self.deselect_all_btn = tk.Button(self.res_control_frame, text="전체 해제", command=self.deselect_all)
        self.deselect_all_btn.pack(side=tk.LEFT, padx=5)

        self.res_canvas.pack(side="left", fill="y") # expand=True 제거, fill="y"로 세로 채우기만 유지
        self.res_scrollbar.pack(side="right", fill="y")

        # 오른쪽: 구조 + 엔트리 미리보기
        # right_frame을 다시 분할하여 왼쪽은 트리, 오른쪽은 미리보기로 사용
        self.right_frame = tk.Frame(self.paned)
        self.paned.add(self.right_frame, weight=3)
        self.right_paned = ttk.PanedWindow(self.right_frame, orient=tk.HORIZONTAL, style='custom.TPanedwindow')
        self.right_paned.pack(fill=tk.BOTH, expand=True)
        
        # 오른쪽 패널의 왼쪽 부분 (트리)
        self.tree_frame = tk.Frame(self.right_paned)
        self.right_paned.add(self.tree_frame, weight=2) # 트리뷰가 더 넓은 공간을 차지하도록 weight 조정

        self.tree_title_label = tk.Label(self.tree_frame, text="ICO 파일 구조", font=("Arial", 10))
        self.tree_title_label.pack(pady=5, anchor='w', padx=5)
        self.header_info_label = tk.Label(self.tree_frame, text="", font=("Arial", 9), justify=tk.LEFT)
        self.header_info_label.pack(pady=2, fill=tk.X, padx=10)
        
        self.structure_tree = ttk.Treeview(self.tree_frame, columns=("Value"), show="tree headings", height=15, style="Treeview")
        self.structure_tree.heading("#0", text="항목")
        self.structure_tree.heading("Value", text="값")
        self.structure_tree.column("#0", stretch=tk.YES)
        self.structure_tree.column("Value", width=100, anchor='w', stretch=tk.NO)
        self.structure_tree.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        self.structure_tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        
        # 오른쪽 패널의 오른쪽 부분 (미리보기)
        self.preview_frame = tk.Frame(self.right_paned)
        self.right_paned.add(self.preview_frame, weight=1)
        self.preview_label = tk.Label(self.preview_frame, text="선택 엔트리 미리보기", font=("Arial", 10))
        self.preview_label.pack(pady=5)
        self.entry_preview_canvas = tk.Canvas(self.preview_frame, width=256, height=256, highlightthickness=0)
        self.entry_preview_canvas.pack(pady=5, padx=5)

    def is_dark_mode(self):
        if sys.platform == 'win32':
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize')
                value, _ = winreg.QueryValueEx(key, 'AppsUseLightTheme')
                return value == 0
            except (FileNotFoundError, ImportError):
                return False
        return False

    def apply_theme(self):
        theme = self.themes[self.current_theme]
        
        # 기본 위젯 색상 설정
        self.root.config(bg=theme["bg"])
    
        # 툴바
        self.toolbar.config(bg=theme["toolbar_bg"])
        for btn in [self.select_btn, self.generate_btn, self.open_ico_btn, self.view_structure_btn]:
            btn.config(bg=theme["button_bg"], fg=theme["button_fg"], disabledforeground=theme["disabled_fg"])
        self.generate_btn.config(bg=theme["generate_btn_bg"])

        # 패널
        self.left_frame.config(bg=theme["canvas_bg"])
        self.mid_frame.config(bg=theme["canvas_bg"])
        self.right_frame.config(bg=theme["bg"])

        # 왼쪽 패널
        self.left_label.config(bg=theme["canvas_bg"], fg=theme["fg"])
        self.preview_canvas.config(bg=theme["canvas_bg"])
        self.create_checkerboard_background(self.preview_canvas, 200, 200)

        # 중앙 패널
        self.mid_label.config(bg=theme["canvas_bg"], fg=theme["fg"])
        self.res_canvas.config(bg=theme["canvas_bg"])
        self.res_scrollable_frame.config(bg=theme["canvas_bg"])
        for cb in self.res_scrollable_frame.winfo_children():
            if isinstance(cb, tk.Checkbutton):
                cb.config(bg=theme["canvas_bg"], fg=theme["fg"], selectcolor=theme["bg"])
        self.res_control_frame.config(bg=theme["canvas_bg"])
        for btn in [self.select_all_btn, self.deselect_all_btn]:
            btn.config(bg=theme["button_bg"], fg=theme["button_fg"])

        # 오른쪽 패널
        self.tree_frame.config(bg=theme["bg"])
        self.tree_title_label.config(bg=theme["bg"], fg=theme["fg"])
        self.header_info_label.config(bg=theme["bg"], fg=theme["fg"])
        self.preview_frame.config(bg=theme["bg"])
        self.preview_label.config(bg=theme["bg"], fg=theme["fg"])
        self.entry_preview_canvas.config(bg=theme["canvas_bg"])
        self.create_checkerboard_background(self.entry_preview_canvas, 256, 256)

        # TTK 스타일
        style = ttk.Style()
        try:
            # 'clam' 테마가 색상 커스터마이징에 더 용이하므로 우선 사용합니다.
            style.theme_use('clam') 
        except tk.TclError:
            style.theme_use('vista') # 'clam'이 없는 경우 'vista'를 사용합니다.

        style.configure("Treeview", background=theme["tree_bg"], fieldbackground=theme["tree_field_bg"], foreground=theme["tree_fg"], rowheight=28, borderwidth=0)
        style.configure("Treeview.Heading", font=("맑은 고딕", 10, "bold"), background=theme["tree_heading_bg"], foreground=theme.get("tree_heading_fg", theme["fg"]), borderwidth=0)
        style.map("Treeview", background=[('selected', theme["tree_selected_bg"])], foreground=[('selected', theme["tree_selected_fg"])])
        style.map("Treeview.Heading", relief=[('!active', 'flat')], background=[('!active', theme["tree_heading_bg"]), ('active', theme["tree_heading_bg"])])
        style.configure('custom.TPanedwindow', background=theme["bg"])
        
        # Treeview의 빈 공간 배경색이 적용되지 않는 문제를 해결하기 위한 트릭
        style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

        self.title_bar_handler.set_theme(self.current_theme)

    # 새: checkerboard 배경 생성 (투명 표현용)
    def create_checkerboard_background(self, canvas, width, height, square_size=10):
        canvas.delete("checker")
        theme = self.themes[self.current_theme]
        colors = [theme["checker_1"], theme["checker_2"]]
        for y in range(0, height, square_size):
            for x in range(0, width, square_size):
                color = colors[(x // square_size + y // square_size) % 2]
                canvas.create_rectangle(x, y, x + square_size, y + square_size, fill=color, outline="", tags="checker")
        canvas.lower("checker")

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

                messagebox.showinfo("성공", "이미지가 로드되었습니다!")
                self.generate_btn.config(state="normal")

                # 미리보기 (checkerboard 위에 합성)
                preview_img = self.image.copy()
                preview_img.thumbnail((200, 200))
                if preview_img.mode != 'RGBA':
                    preview_img = preview_img.convert('RGBA')
                self.photo = ImageTk.PhotoImage(preview_img)
                self.preview_canvas.create_image(100, 100, image=self.photo, tags="image") # 이전 이미지 삭제는 create_image가 덮어쓰므로 불필요

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
            success, message, ico_data = self.ico_gen.create_ico(self.image, selected_sizes, output_path)
            if success:
                self.last_ico_path = output_path
                self.view_structure_btn.config(state="normal")
                self.ico_data = ico_data
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

        for i, entry in enumerate(structure['entries']):
            entry_text = f"Entry {i+1}: {entry['Width']}x{entry['Height']}, BitCount={entry['BitCount']}"
            # open=False로 설정하여 기본적으로 닫힌 상태로 표시
            entry_id = self.structure_tree.insert("", "end", text=entry_text, values=(), tags=(str(i),), open=False)
            for key, val in entry.items():
                self.structure_tree.insert(entry_id, "end", text=key, values=(val,))

    def on_tree_select(self, event):
        selected = self.structure_tree.selection()
        if not selected:
            return
        item = selected[0]

        # 선택된 항목의 텍스트와 값을 가져옴
        item_text = self.structure_tree.item(item, "text")
        item_values = self.structure_tree.item(item, "values")
        item_value = item_values[0] if item_values else ""

        # 태그를 확인하여 상위 엔트리인지, 하위 속성인지 구분
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
                except Exception as e:
                    self.entry_preview_canvas.delete("image")
                    messagebox.showerror("미리보기 오류", str(e))
        else:
            # 하위 속성 항목을 선택한 경우 (현재는 특별한 동작 없음)
            pass

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = ICOMakerGUI(root)
    app.run()