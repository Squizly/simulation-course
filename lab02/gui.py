# gui.py — Premium macOS интерфейс для моделирования теплопроводности
import tkinter as tk
from tkinter import ttk
import numpy as np
import time
import threading
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from model import simulate, calculate_next_step


# ─────────────────────────────────────────────────────────────
#  ЦВЕТОВАЯ ПАЛИТРА — macOS Sonoma inspired
# ─────────────────────────────────────────────────────────────
class Colors:
    BG_MAIN = "#f5f5f7"
    BG_CARD = "#ffffff"
    BG_INPUT = "#fafafa"
    BG_HEADER = "#f8f8f9"
    BG_STATUS = "#f8f8f9"
    
    TEXT_PRIMARY = "#1d1d1f"
    TEXT_SECONDARY = "#86868b"
    TEXT_INVERTED = "#ffffff"
    
    ACCENT = "#0071e3"
    ACCENT_HOVER = "#0077ed"
    ACCENT_PRESSED = "#005ecb"
    
    TEMP_ACCENT = "#ff9500"
    TEMP_ACCENT_HOVER = "#ff9f0a"
    
    BORDER = "#d2d2d7"
    BORDER_SOFT = "#e5e5ea"
    
    GRID_LINE = "#e5e5ea"
    PLOT_LINE = "#0071e3"
    
    SUCCESS = "#34c759"
    WARNING = "#ff9500"
    ERROR = "#ff3b30"
    
    SHADOW = "#000000"


# ─────────────────────────────────────────────────────────────
#  ШРИФТЫ — системные macOS (только для Tkinter!)
# ─────────────────────────────────────────────────────────────
class Fonts:
    TITLE = ("Helvetica Neue", 22, "bold")
    SUBTITLE = ("Helvetica Neue", 13)
    
    LABEL = ("Helvetica Neue", 12)
    LABEL_SMALL = ("Helvetica Neue", 11)
    
    VALUE = ("Menlo", 12)
    STATUS_LABEL = ("Helvetica Neue", 10)
    STATUS_VALUE = ("Menlo", 16, "bold")
    
    BUTTON = ("Helvetica Neue", 12, "bold")
    
    TABLE_HEADER = ("Helvetica Neue", 11, "bold")
    TABLE_CELL = ("Menlo", 10)


class HeatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Теплопроводность • Premium")
        self.root.geometry("1400x880")
        self.root.minsize(1200, 750)
        self.root.configure(bg=Colors.BG_MAIN)
        
        self.running = False
        self.animation_job = None

        self.setup_styles()
        self.create_layout()

    # ─────────────────────────────────────────────────────────
    #  СТИЛИ TKINTER
    # ─────────────────────────────────────────────────────────
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TFrame", background=Colors.BG_MAIN)
        style.configure("Card.TFrame", background=Colors.BG_CARD)
        
        style.configure("Header.TLabel",
                       font=Fonts.TITLE,
                       background=Colors.BG_MAIN,
                       foreground=Colors.TEXT_PRIMARY)
        style.configure("SubHeader.TLabel",
                       font=Fonts.SUBTITLE,
                       background=Colors.BG_MAIN,
                       foreground=Colors.TEXT_SECONDARY)

        style.configure("Card.TLabelframe",
                       background=Colors.BG_CARD,
                       borderwidth=0,
                       relief="flat")
        style.configure("Card.TLabelframe.Label",
                       font=Fonts.LABEL,
                       background=Colors.BG_CARD,
                       foreground=Colors.TEXT_PRIMARY)

        style.configure("TLabel",
                       background=Colors.BG_CARD,
                       font=Fonts.LABEL_SMALL,
                       foreground=Colors.TEXT_PRIMARY)
        style.configure("Info.TLabel",
                       background=Colors.BG_CARD,
                       font=Fonts.LABEL_SMALL,
                       foreground=Colors.TEXT_SECONDARY)
        style.configure("Status.TLabel",
                       background=Colors.BG_MAIN,
                       font=Fonts.LABEL_SMALL,
                       foreground=Colors.TEXT_SECONDARY)

        style.configure("TEntry",
                       fieldbackground=Colors.BG_INPUT,
                       foreground=Colors.TEXT_PRIMARY,
                       font=Fonts.VALUE,
                       borderwidth=1,
                       relief="flat",
                       justify="right")
        style.map("TEntry",
                 fieldbackground=[("readonly", Colors.BG_HEADER),
                                ("disabled", Colors.BG_HEADER)])

        style.configure("Accent.TButton",
                       font=Fonts.BUTTON,
                       foreground=Colors.TEXT_INVERTED,
                       background=Colors.ACCENT,
                       borderwidth=0,
                       relief="flat",
                       padding=8)
        style.map("Accent.TButton",
                 background=[("active", Colors.ACCENT_HOVER),
                           ("pressed", Colors.ACCENT_PRESSED)],
                 foreground=[("disabled", Colors.TEXT_SECONDARY)])

        style.configure("Secondary.TButton",
                       font=Fonts.BUTTON,
                       foreground=Colors.TEXT_PRIMARY,
                       background=Colors.BG_HEADER,
                       borderwidth=1,
                       relief="flat",
                       padding=8,
                       bordercolor=Colors.BORDER)
        style.map("Secondary.TButton",
                 background=[("active", Colors.BORDER_SOFT),
                           ("pressed", Colors.BORDER)],
                 foreground=[("disabled", Colors.TEXT_SECONDARY)])

        style.configure("Danger.TButton",
                       font=Fonts.BUTTON,
                       foreground="#ffffff",
                       background="#ff3b30",
                       borderwidth=0,
                       relief="flat",
                       padding=8)
        style.map("Danger.TButton",
                 background=[("active", "#ff453a"),
                           ("pressed", "#e0342a")])

        style.configure("Treeview",
                       background=Colors.BG_CARD,
                       fieldbackground=Colors.BG_CARD,
                       foreground=Colors.TEXT_PRIMARY,
                       font=Fonts.TABLE_CELL,
                       rowheight=32,
                       borderwidth=0,
                       relief="flat")
        style.configure("Treeview.Heading",
                       font=Fonts.TABLE_HEADER,
                       background=Colors.BG_HEADER,
                       foreground=Colors.TEXT_PRIMARY,
                       borderwidth=0,
                       relief="flat")
        style.map("Treeview",
                 background=[("selected", Colors.ACCENT)],
                 foreground=[("selected", Colors.TEXT_INVERTED)])

        style.configure("TNotebook",
                       background=Colors.BG_MAIN,
                       borderwidth=0)
        style.configure("TNotebook.Tab",
                       font=Fonts.LABEL,
                       background=Colors.BG_HEADER,
                       foreground=Colors.TEXT_SECONDARY,
                       padding=12)
        style.map("TNotebook.Tab",
                 background=[("selected", Colors.BG_CARD)],
                 foreground=[("selected", Colors.ACCENT)])

    # ─────────────────────────────────────────────────────────
    #  ОСНОВНАЯ РАЗМЕТКА
    # ─────────────────────────────────────────────────────────
    def create_layout(self):
        header = ttk.Frame(self.root, style="TFrame")
        header.pack(fill=tk.X, padx=30, pady=(15, 5))
        
        ttk.Label(header,
                 text="Теплопроводность",
                 style="Header.TLabel").pack(anchor="w")
        ttk.Label(header,
                 text="Одномерное уравнение • Численное моделирование",
                 style="SubHeader.TLabel").pack(anchor="w", pady=(2, 0))

        main = ttk.Frame(self.root, style="TFrame")
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))

        self.create_controls(main)

        right = ttk.Frame(main, style="TFrame")
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(0, 0))

        self.create_visualization(right)
        self.create_tables(right)

    # ─────────────────────────────────────────────────────────
    #  ЛЕВАЯ ПАНЕЛЬ — Параметры + статус-карточка
    # ─────────────────────────────────────────────────────────
    def create_controls(self, parent):
        panel = ttk.Frame(parent, style="Card.TFrame")
        panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20), ipady=10)
        
        shadow = tk.Frame(panel, bg=Colors.SHADOW)
        shadow.pack(fill=tk.BOTH, expand=True, padx=0, pady=1)
        
        inner = ttk.Frame(shadow, style="Card.TFrame")
        inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        content = ttk.Frame(inner, style="Card.TFrame")
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=18)

        self.entries = {}

        self.create_block(content, "Материал", [
            "Плотность", "Теплоёмкость", "Теплопроводность", "Длина"
        ], defaults=["7800", "460", "46", "0.4"])

        self.create_block(content, "Температура", [
            "Начальная", "Слева", "Справа"
        ], defaults=["20", "0", "200"])

        self.create_block(content, "Расчёт", [
            "Шаг пространства", "Шаг времени", "Время моделирования"
        ], defaults=["0.01", "0.1", "10"])

        ttk.Frame(content, height=1, style="TFrame").pack(fill=tk.X, pady=12)
        ttk.Separator(content, orient="horizontal").pack(fill=tk.X)
        ttk.Frame(content, height=8, style="TFrame").pack()

        btn_frame = ttk.Frame(content, style="Card.TFrame")
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text="▶ Запустить",
                   style="Accent.TButton",
                   command=self.start_animation).pack(fill=tk.X, pady=(0, 6))

        ttk.Button(btn_frame, text="⏹ Остановить",
                   style="Secondary.TButton",
                   command=self.stop_animation).pack(fill=tk.X, pady=4)

        self.btn_calc = ttk.Button(btn_frame,
                                   text="📊 Рассчитать",
                                   style="Secondary.TButton",
                                   command=self.start_table_thread)
        self.btn_calc.pack(fill=tk.X, pady=(6, 0))

        # ── СТАТУС-КАРТОЧКА — ПРЕМИУМ-СТИЛЬ ─────────────────
        status_card = ttk.Frame(content, style="Card.TFrame")
        status_card.pack(fill=tk.X, pady=(8, 0))
        
        shadow = tk.Frame(status_card, bg=Colors.SHADOW)
        shadow.pack(fill=tk.BOTH, expand=True, padx=0, pady=1)
        
        inner_status = ttk.Frame(shadow, style="Card.TFrame")
        inner_status.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        status_inner = ttk.Frame(inner_status, style="Card.TFrame")
        status_inner.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)
        
        status_frame = ttk.Frame(status_inner, style="Card.TFrame")
        status_frame.pack(fill=tk.X)
        
        # Время
        time_col = ttk.Frame(status_frame, style="Card.TFrame")
        time_col.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        
        ttk.Label(time_col, text="⏱ Время", 
                 font=Fonts.STATUS_LABEL,
                 foreground=Colors.TEXT_SECONDARY,
                 background=Colors.BG_CARD,
                 anchor="w").pack(anchor="w")
        
        self.time_value = ttk.Label(time_col, text="0.00 с",
                                   font=Fonts.STATUS_VALUE,
                                   foreground=Colors.ACCENT,
                                   background=Colors.BG_CARD,
                                   anchor="w")
        self.time_value.pack(anchor="w", pady=(2, 0))
        
        # Температура в центре
        temp_col = ttk.Frame(status_frame, style="Card.TFrame")
        temp_col.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(8, 0))
        
        ttk.Label(temp_col, text="🌡 В центре", 
                 font=Fonts.STATUS_LABEL,
                 foreground=Colors.TEXT_SECONDARY,
                 background=Colors.BG_CARD,
                 anchor="e").pack(anchor="e")
        
        self.temp_value = ttk.Label(temp_col, text="— °C",
                                   font=Fonts.STATUS_VALUE,
                                   foreground=Colors.TEMP_ACCENT,
                                   background=Colors.BG_CARD,
                                   anchor="e")
        self.temp_value.pack(anchor="e", pady=(2, 0))
        
        # Разделитель
        ttk.Separator(status_frame, orient="vertical").pack(
            side=tk.LEFT, fill=tk.Y, padx=4, pady=6)

    def create_block(self, parent, title, labels, defaults):
        block = ttk.LabelFrame(parent, text=title, style="Card.TLabelframe")
        block.pack(fill=tk.X, pady=(0, 10))
        
        for label, default in zip(labels, defaults):
            row = ttk.Frame(block, style="Card.TFrame")
            row.pack(fill=tk.X, pady=4)
            
            ttk.Label(row, text=label, font=Fonts.LABEL_SMALL,
                     foreground=Colors.TEXT_SECONDARY,
                     background=Colors.BG_CARD).pack(side=tk.LEFT)
            
            entry = ttk.Entry(row, font=Fonts.VALUE, justify="right", width=10)
            entry.insert(0, default)
            entry.pack(side=tk.RIGHT, padx=(12, 0))
            
            self.entries[label] = entry

    # ─────────────────────────────────────────────────────────
    #  ПРАВАЯ ПАНЕЛЬ — Графики
    # ─────────────────────────────────────────────────────────
    def create_visualization(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame")
        card.pack(fill=tk.BOTH, expand=False, pady=(0, 10))
        
        shadow = tk.Frame(card, bg=Colors.SHADOW)
        shadow.pack(fill=tk.BOTH, expand=True, padx=0, pady=1)
        
        inner = ttk.Frame(shadow, style="Card.TFrame")
        inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        content = ttk.Frame(inner, style="Card.TFrame")
        content.pack(fill=tk.BOTH, expand=True, padx=18, pady=12)

        # Высота фигуры оптимизирована под место для таблиц
        self.fig = Figure(figsize=(10, 4.2), facecolor=Colors.BG_CARD, dpi=100)
        
        self.ax1 = self.fig.add_subplot(211)
        self.ax2 = self.fig.add_subplot(212)
        
        # Отступы — графики не наезжают
        self.fig.subplots_adjust(
            left=0.12, right=0.96, top=0.94, bottom=0.10, hspace=0.35
        )
        
        for ax in (self.ax1, self.ax2):
            ax.set_facecolor(Colors.BG_CARD)
            ax.grid(True, color=Colors.GRID_LINE, linewidth=0.5, alpha=0.8)
            ax.tick_params(colors=Colors.TEXT_SECONDARY, labelsize=8, pad=3)
            for spine in ax.spines.values():
                spine.set_color(Colors.BORDER_SOFT)
                spine.set_linewidth(0.5)

        self.canvas = FigureCanvasTkAgg(self.fig, master=content)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas._tkcanvas.config(bg=Colors.BG_CARD, highlightthickness=0)

    # ─────────────────────────────────────────────────────────
    #  ТАБЛИЦЫ — РОВНО 4 СТРОКИ ДАННЫХ + ЗАГОЛОВОК
    # ─────────────────────────────────────────────────────────
    def create_tables(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame")
        card.pack(fill=tk.BOTH, expand=True)
        
        shadow = tk.Frame(card, bg=Colors.SHADOW)
        shadow.pack(fill=tk.BOTH, expand=True, padx=0, pady=1)
        
        inner = ttk.Frame(shadow, style="Card.TFrame")
        inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        content = ttk.Frame(inner, style="Card.TFrame")
        content.pack(fill=tk.BOTH, expand=True, padx=18, pady=12)

        self.tabs = ttk.Notebook(content)
        self.tabs.pack(fill=tk.BOTH, expand=True)

        temp_frame = ttk.Frame(self.tabs, style="Card.TFrame")
        self.tabs.add(temp_frame, text="  Температура  ")
        self.temp_table = self.create_styled_table(temp_frame)

        time_frame = ttk.Frame(self.tabs, style="Card.TFrame")
        self.tabs.add(time_frame, text="  Время расчёта  ")
        self.time_table = self.create_styled_table(time_frame)

    def create_styled_table(self, parent):
        columns = ["dt\\h", "0.1", "0.01", "0.001", "0.0001"]
        
        # РОВНО 5 строк: 1 заголовок + 4 строки данных (без лишнего места)
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=5)
        
        for i, col in enumerate(columns):
            tree.heading(col, text=col, anchor="center")
            width = 90 if i == 0 else 100
            tree.column(col, width=width, anchor="center", minwidth=70)
        
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(4, 0))
        
        return tree

    # ─────────────────────────────────────────────────────────
    #  ЛОГИКА МОДЕЛИРОВАНИЯ
    # ─────────────────────────────────────────────────────────
    def read_params(self):
        p = {label: float(entry.get()) for label, entry in self.entries.items()}
        self.rho = p["Плотность"]
        self.c = p["Теплоёмкость"]
        self.lam = p["Теплопроводность"]
        self.L = p["Длина"]
        self.T0 = p["Начальная"]
        self.Tl = p["Слева"]
        self.Tr = p["Справа"]
        self.h = p["Шаг пространства"]
        self.dt = p["Шаг времени"]
        self.t_end = p["Время моделирования"]

    def start_animation(self):
        if self.running:
            return
        self.running = True
        self.read_params()

        self.Nx = int(round(self.L / self.h))
        if self.Nx < 2:
            self.Nx = 2

        self.x = np.linspace(0, self.L, self.Nx + 1)
        self.T = np.full(self.Nx + 1, self.T0)
        self.T[0], self.T[-1] = self.Tl, self.Tr

        dx = self.L / self.Nx
        self.A = self.lam / dx**2
        self.C = self.A
        self.B = 2 * self.lam / dx**2 + self.rho * self.c / self.dt

        self.alpha = np.zeros(self.Nx + 1)
        self.beta = np.zeros(self.Nx + 1)
        self.current_time = 0

        self.update_animation()

    def update_animation(self):
        if not self.running:
            return

        self.T = calculate_next_step(
            self.T, self.alpha, self.beta,
            self.A, self.B, self.C,
            self.Nx, self.rho, self.c,
            self.dt, self.Tl, self.Tr
        )
        self.current_time += self.dt

        # ── График 1: Профиль температуры ─────────────────
        self.ax1.clear()
        self.ax1.set_facecolor(Colors.BG_CARD)
        self.ax1.plot(self.x, self.T, color=Colors.PLOT_LINE, lw=2.5, marker='')
        self.ax1.set_xlabel("Длина, м", fontsize=9, color=Colors.TEXT_SECONDARY, labelpad=5)
        self.ax1.set_ylabel("°C", fontsize=9, color=Colors.TEXT_SECONDARY, labelpad=5, rotation=0)
        self.ax1.yaxis.set_label_coords(-0.08, 0.5)
        self.ax1.set_title("Профиль температуры", fontsize=11, color=Colors.TEXT_PRIMARY, pad=10, fontweight="bold")
        self.ax1.grid(True, color=Colors.GRID_LINE, alpha=0.7, linewidth=0.5)
        self.ax1.tick_params(colors=Colors.TEXT_SECONDARY, labelsize=8, pad=3)
        for spine in self.ax1.spines.values():
            spine.set_color(Colors.BORDER_SOFT)

        # ── График 2: Тепловая карта ──────────────────────
        self.ax2.clear()
        self.ax2.set_facecolor(Colors.BG_CARD)
        self.ax2.imshow([self.T], aspect='auto', cmap='magma',
                       extent=[0, self.L, 0, 0.1], interpolation='bilinear')
        self.ax2.set_yticks([])
        self.ax2.set_xlabel("Длина, м", fontsize=9, color=Colors.TEXT_SECONDARY, labelpad=5)
        self.ax2.set_title("Визуализация тепла", fontsize=11, color=Colors.TEXT_PRIMARY, pad=10, fontweight="bold")
        self.ax2.tick_params(colors=Colors.TEXT_SECONDARY, labelsize=8, pad=3)
        for spine in self.ax2.spines.values():
            spine.set_color(Colors.BORDER_SOFT)

        self.canvas.draw_idle()

        # Обновление статус-карточки
        center = self.T[self.Nx // 2]
        self.time_value.config(text=f"{self.current_time:.2f} с")
        self.temp_value.config(text=f"{center:.2f} °C")

        self.animation_job = self.root.after(40, self.update_animation)

    def stop_animation(self):
        self.running = False
        if self.animation_job:
            self.root.after_cancel(self.animation_job)
            self.animation_job = None

    def start_table_thread(self):
        if self.running:
            return
        self.btn_calc.config(state="disabled")
        threading.Thread(target=self.calculate_table, daemon=True).start()

    def calculate_table(self):
        self.root.after(0, lambda: [
            self.temp_table.delete(*self.temp_table.get_children()),
            self.time_table.delete(*self.time_table.get_children())
        ])

        self.read_params()
        dts = [0.1, 0.01, 0.001, 0.0001]
        hs = [0.1, 0.01, 0.001, 0.0001]

        for dt_val in dts:
            temp_row = [f"{dt_val:g}"]
            time_row = [f"{dt_val:g}"]

            for h_val in hs:
                start = time.perf_counter()
                try:
                    _, center = simulate(
                        self.rho, self.c, self.lam,
                        self.Tl, self.Tr, self.T0,
                        self.L, h_val, 2.0, dt_val
                    )
                    elapsed = time.perf_counter() - start
                    temp_row.append(f"{center:.2f}")
                    time_row.append(f"{elapsed:.4f}")
                except Exception:
                    temp_row.append("—")
                    time_row.append("—")

            self.root.after(0, lambda r1=temp_row, r2=time_row: self.insert_rows(r1, r2))

        self.root.after(0, lambda: self.btn_calc.config(state="normal"))

    def insert_rows(self, r1, r2):
        self.temp_table.insert("", tk.END, values=r1)
        self.time_table.insert("", tk.END, values=r2)
        
        for i, item in enumerate(self.temp_table.get_children()):
            bg = Colors.BG_CARD if i % 2 == 0 else Colors.BG_HEADER
            self.temp_table.item(item, tags=(f"row{i}",))
            self.temp_table.tag_configure(f"row{i}", background=bg)
        for i, item in enumerate(self.time_table.get_children()):
            bg = Colors.BG_CARD if i % 2 == 0 else Colors.BG_HEADER
            self.time_table.item(item, tags=(f"row{i}",))
            self.time_table.tag_configure(f"row{i}", background=bg)


# ─────────────────────────────────────────────────────────────
#  ЗАПУСК (если запускаете напрямую)
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    try:
        root.tk.call('tk', 'scaling', 1.5)  # HiDPI для Retina
    except:
        pass
    app = HeatApp(root)
    
    # Плавное появление
    def fade_in(step=0):
        if step <= 10:
            root.attributes("-alpha", step / 10)
            root.after(30, lambda: fade_in(step + 1))
    root.after(100, fade_in)
    
    root.mainloop()