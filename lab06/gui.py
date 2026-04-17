import sys
import random
import numpy as np
import scipy.stats as stats
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QScrollArea, QFrame, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QMessageBox, QGridLayout, QStackedWidget,
                             QAbstractItemView)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QFont
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
import core

# --- ПАЛИТРА (Tokyo Night) ---
BG_MAIN = "#1a1b26"
BG_CARD = "#24283b"
BG_INPUT = "#16161e"
TEXT_MAIN = "#a9b1d6"
TEXT_BRIGHT = "#c0caf5"
ACCENT = "#7aa2f7"
SUCCESS = "#9ece6a"
DANGER = "#f7768e"
BORDER = "#292e42"
HOVER = "#3b4261"

STYLE_SHEET = f"""
QMainWindow {{
    background-color: {BG_MAIN};
}}
QWidget {{
    color: {TEXT_MAIN};
    font-family: 'Segoe UI', 'San Francisco', sans-serif;
    font-size: 13px;
}}
QFrame#Card {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 12px;
}}
QLineEdit {{
    background-color: {BG_INPUT};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 8px 12px;
    color: {TEXT_BRIGHT};
    font-weight: 500;
}}
QLineEdit:focus {{
    border: 1px solid {ACCENT};
    background-color: #1f2335;
}}
QPushButton {{
    background-color: {HOVER};
    border: none;
    border-radius: 6px;
    padding: 10px 16px;
    font-weight: bold;
    color: {TEXT_BRIGHT};
}}
QPushButton:hover {{
    background-color: #4b527e;
}}
QPushButton:pressed {{
    background-color: {ACCENT};
    color: {BG_MAIN};
}}
QPushButton#PrimaryBtn {{
    background-color: {ACCENT};
    color: {BG_MAIN};
    font-size: 14px;
}}
QPushButton#PrimaryBtn:hover {{
    background-color: #8db0f9;
}}
QPushButton#ModeBtn {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER};
    color: {TEXT_MAIN};
}}
QPushButton#ModeBtn[active="true"] {{
    background-color: {ACCENT};
    color: {BG_MAIN};
    border: 1px solid {ACCENT};
}}

/* --- Скроллбары (убираем белые рамки) --- */
QScrollArea {{ border: none; background-color: transparent; }}
QScrollBar:vertical {{
    border: none;
    background: {BG_CARD};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: #565f89;
    min-height: 20px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical:hover {{ background: {ACCENT}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ border: none; background: none; }}

/* --- Таблица --- */
QTableWidget {{
    background-color: {BG_CARD};
    color: {TEXT_BRIGHT};
    gridline-color: {BORDER};
    border: none;
    outline: none;
}}
QTableWidget::item:selected {{
    background-color: {HOVER};
    color: #ffffff;
}}
QHeaderView::section {{
    background-color: #1f2335;
    color: {TEXT_MAIN};
    padding: 8px;
    border: none;
    border-bottom: 2px solid {ACCENT};
    font-weight: bold;
}}
QTableCornerButton::section {{ background-color: #1f2335; border: none; }}
"""

class StatCard(QFrame):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        self.title_label = QLabel(title.upper())
        self.title_label.setStyleSheet(f"color: #565f89; font-size: 11px; font-weight: 800; letter-spacing: 1px;")
        
        self.value_label = QLabel("НЕТ ДАННЫХ")
        self.value_label.setStyleSheet(f"color: {TEXT_BRIGHT}; font-size: 14px; font-family: 'Consolas', monospace;")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addStretch()

    def update_text(self, text, color=None):
        self.value_label.setText(text)
        color_str = color if color else TEXT_BRIGHT
        self.value_label.setStyleSheet(f"color: {color_str}; font-size: 14px; font-family: 'Consolas', monospace; line-height: 1.5;")

class DataRow(QFrame):
    def __init__(self, x_val="", p_val="", remove_cb=None):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(10)
        
        self.x_in = QLineEdit(str(x_val)); self.x_in.setFixedWidth(80)
        self.x_in.setPlaceholderText("X")
        self.p_in = QLineEdit(str(p_val))
        self.p_in.setPlaceholderText("P (вероятность)")
        
        self.del_btn = QPushButton("✕")
        self.del_btn.setFixedSize(36, 36)
        self.del_btn.setStyleSheet(f"background: {BG_INPUT}; color: {DANGER}; border: 1px solid {BORDER};")
        if remove_cb: self.del_btn.clicked.connect(lambda: remove_cb(self))
        
        lbl_x = QLabel("X:"); lbl_x.setFixedWidth(15)
        lbl_p = QLabel("P:"); lbl_p.setFixedWidth(15)
        
        layout.addWidget(lbl_x); layout.addWidget(self.x_in)
        layout.addWidget(lbl_p); layout.addWidget(self.p_in); layout.addWidget(self.del_btn)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.core = core.StatCore()
        self.setWindowTitle("Stochastic Lab | Окно моделирования")
        self.resize(1400, 900)
        self.setStyleSheet(STYLE_SHEET)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # --- ЛЕВАЯ ПАНЕЛЬ ---
        left_panel = QFrame(); left_panel.setObjectName("Card"); left_panel.setFixedWidth(420)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(20, 20, 20, 20)
        left_layout.setSpacing(15)

        # Заголовок настроек
        settings_lbl = QLabel("НАСТРОЙКИ МОДЕЛИ")
        settings_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        left_layout.addWidget(settings_lbl)

        # Переключатель
        mode_box = QHBoxLayout()
        mode_box.setSpacing(10)
        self.btn_disc = QPushButton("ДИСКРЕТНАЯ"); self.btn_disc.setObjectName("ModeBtn")
        self.btn_norm = QPushButton("НОРМАЛЬНАЯ"); self.btn_norm.setObjectName("ModeBtn")
        self.btn_disc.clicked.connect(lambda: self.switch_mode(0))
        self.btn_norm.clicked.connect(lambda: self.switch_mode(1))
        mode_box.addWidget(self.btn_disc); mode_box.addWidget(self.btn_norm)
        left_layout.addLayout(mode_box)

        self.stack = QStackedWidget()
        
        # Дискретный ввод
        self.disc_widget = QWidget()
        dv = QVBoxLayout(self.disc_widget)
        dv.setContentsMargins(0, 10, 0, 0)
        
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True)
        self.rows_cont = QWidget()
        self.rows_cont.setStyleSheet("background-color: transparent;") # Убирает белизну внутри
        self.rows_layout = QVBoxLayout(self.rows_cont)
        self.rows_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.rows_layout.setContentsMargins(0, 0, 10, 0)
        
        self.scroll.setWidget(self.rows_cont); dv.addWidget(self.scroll)
        
        # Кнопки управления строками
        disc_btns = QGridLayout()
        self.add_btn = QPushButton("+ Добавить"); self.add_btn.clicked.connect(self.auto_add_row)
        self.rand_btn = QPushButton("Случайно"); self.rand_btn.clicked.connect(self.randomize_probs)
        self.auto_btn = QPushButton("Автозаполнение (остаток)"); self.auto_btn.clicked.connect(self.autofill_probs)
        disc_btns.addWidget(self.add_btn, 0, 0)
        disc_btns.addWidget(self.rand_btn, 0, 1)
        disc_btns.addWidget(self.auto_btn, 1, 0, 1, 2)
        dv.addLayout(disc_btns)
        self.stack.addWidget(self.disc_widget)

        # Нормальный ввод
        self.norm_widget = QWidget()
        nv = QVBoxLayout(self.norm_widget)
        nv.setContentsMargins(0, 10, 0, 0)
        nv.addWidget(QLabel("Мат. ожидание (μ):"))
        self.mu_in = QLineEdit("0")
        nv.addWidget(self.mu_in)
        nv.addWidget(QLabel("Станд. отклонение (σ):"))
        self.sigma_in = QLineEdit("1.0")
        nv.addWidget(self.sigma_in)
        nv.addStretch()
        self.stack.addWidget(self.norm_widget)

        left_layout.addWidget(self.stack)
        
        # Общие параметры
        left_layout.addWidget(QLabel("Объем выборки (N):"))
        self.n_input = QLineEdit("1000")
        self.n_input.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {ACCENT};")
        left_layout.addWidget(self.n_input)

        self.run_btn = QPushButton("ЗАПУСТИТЬ МОДЕЛИРОВАНИЕ")
        self.run_btn.setObjectName("PrimaryBtn"); self.run_btn.setFixedHeight(55)
        self.run_btn.clicked.connect(self.run_single)
        left_layout.addWidget(self.run_btn)

        main_layout.addWidget(left_panel)

        # --- ПРАВАЯ ПАНЕЛЬ ---
        right_panel = QVBoxLayout()
        right_panel.setSpacing(20)
        top_row = QHBoxLayout()
        top_row.setSpacing(20)
        
        # Карточка графика
        plot_card = QFrame(); plot_card.setObjectName("Card")
        pv = QVBoxLayout(plot_card)
        pv.setContentsMargins(10, 10, 10, 10)
        
        # Настройка Matplotlib в темной теме
        self.fig = Figure(tight_layout=True)
        self.fig.patch.set_facecolor(BG_CARD) # Цвет фона окна графика
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.canvas.setStyleSheet("background-color: transparent;")
        pv.addWidget(self.canvas); top_row.addWidget(plot_card, stretch=3)

        # Вертикальный блок карточек
        stats_vbox = QVBoxLayout()
        stats_vbox.setSpacing(15)
        self.card_e = StatCard("Мат. ожидание")
        self.card_d = StatCard("Дисперсия")
        self.card_chi = StatCard("Критерий χ² (Хи-квадрат)")
        stats_vbox.addWidget(self.card_e); stats_vbox.addWidget(self.card_d); stats_vbox.addWidget(self.card_chi)
        top_row.addLayout(stats_vbox, stretch=1)
        
        right_panel.addLayout(top_row, stretch=3)

        # Карточка таблицы
        table_card = QFrame(); table_card.setObjectName("Card")
        tv = QVBoxLayout(table_card)
        tv.setContentsMargins(15, 15, 15, 15)
        tv.setSpacing(15)
        
        header_layout = QHBoxLayout()
        tbl_title = QLabel("СЕРИЯ ЭКСПЕРИМЕНТОВ")
        tbl_title.setStyleSheet("font-size: 14px; font-weight: bold; color: white;")
        self.series_btn = QPushButton("Сгенерировать (10, 100, 1000, 10000)")
        self.series_btn.setObjectName("PrimaryBtn")
        self.series_btn.setFixedWidth(300)
        self.series_btn.clicked.connect(self.run_table_series)
        header_layout.addWidget(tbl_title)
        header_layout.addStretch()
        header_layout.addWidget(self.series_btn)
        tv.addLayout(header_layout)

        self.table = QTableWidget(0, 8)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setHorizontalHeaderLabels(["Объем (N)", "Мат.ож (эмп)", "Погреш. E(%)", "Дисперсия (эмп)", "Погреш. D(%)", "χ² (эмп)", "χ² (крит)", "Результат"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False) # Убираем нумерацию строк слева
        
        tv.addWidget(self.table); right_panel.addWidget(table_card, stretch=2)

        main_layout.addLayout(right_panel)

        # Инициализация
        self.data_rows = []
        for x, p in [(1, 0.2), (2, 0.5), (3, 0.3)]: self.add_row_raw(x, p)
        self.switch_mode(0)
        self.setup_plot() # Отрисовка пустого красивого графика на старте
        self.canvas.draw()

    # --- ЛОГИКА ДИСКРЕТНОГО ВВОДА ---
    def auto_add_row(self):
        current_xs = []
        for r in self.data_rows:
            try: current_xs.append(float(r.x_in.text().replace(',', '.')))
            except: continue
        next_x = int(max(current_xs) + 1) if current_xs else 1
        self.add_row_raw(next_x, "")

    def add_row_raw(self, x, p):
        row = DataRow(x, p, self.remove_row)
        self.data_rows.append(row); self.rows_layout.addWidget(row)

    def remove_row(self, r):
        if len(self.data_rows) > 1: self.data_rows.remove(r); r.deleteLater()

    def randomize_probs(self):
        n = len(self.data_rows)
        vals = [random.random() for _ in range(n)]
        s = sum(vals)
        for i, r in enumerate(self.data_rows):
            r.p_in.setText(f"{vals[i]/s:.3f}")

    def autofill_probs(self):
        filled_sum = 0.0
        empty_rows = []
        for r in self.data_rows:
            txt = r.p_in.text().strip().replace(',', '.')
            if txt:
                try: filled_sum += float(txt)
                except: pass
            else: empty_rows.append(r)
        if not empty_rows: return
        rem = max(0, 1.0 - filled_sum)
        val = rem / len(empty_rows)
        for r in empty_rows: r.p_in.setText(f"{val:.3f}")

    # --- ОБЩАЯ ЛОГИКА ---
    def switch_mode(self, idx):
        self.stack.setCurrentIndex(idx)
        self.btn_disc.setProperty("active", idx == 0)
        self.btn_norm.setProperty("active", idx == 1)
        self.btn_disc.style().unpolish(self.btn_disc); self.btn_disc.style().polish(self.btn_disc)
        self.btn_norm.style().unpolish(self.btn_norm); self.btn_norm.style().polish(self.btn_norm)

    def setup_plot(self):
        self.ax.clear()
        self.ax.set_facecolor(BG_CARD)
        self.ax.tick_params(colors=TEXT_MAIN)
        for spine in self.ax.spines.values():
            spine.set_edgecolor(BORDER)
            spine.set_linewidth(1.5)
        self.ax.grid(True, axis='y', linestyle='--', alpha=0.15, color=TEXT_BRIGHT)

    def get_discrete_data(self):
        x = [float(r.x_in.text().replace(',', '.')) for r in self.data_rows]
        p = [float(r.p_in.text().replace(',', '.')) for r in self.data_rows]
        if abs(sum(p) - 1.0) > 1e-3: raise ValueError("Сумма вероятностей должна быть равна 1.0!")
        return p, x

    def run_single(self):
        try:
            N = int(self.n_input.text())
            self.setup_plot()
            if self.stack.currentIndex() == 0:
                p, x = self.get_discrete_data()
                res = self.core.run_experiment_discrete(p, x, N)
                # Дискретный график
                bars = self.ax.bar(x, res["emp_probs"], color=ACCENT, alpha=0.85, width=0.6, edgecolor=BG_CARD)
                self.ax.set_xticks(x)
                
                self.ax.bar_label(bars, fmt='%.3f', padding=3, color=TEXT_BRIGHT, fontsize=11, fontweight='bold')
                
                err_e, err_d = res['err_E_rel'], res['err_D_rel']
            else:
                mu, sigma = float(self.mu_in.text().replace(',', '.')), float(self.sigma_in.text().replace(',', '.'))
                res = self.core.run_experiment_normal(mu, sigma, N)
                # Непрерывный график
                self.ax.hist(res["sample"], bins='auto', density=True, color=ACCENT, alpha=0.6, edgecolor=BG_CARD, linewidth=0.5)
                xr = np.linspace(min(res["sample"]), max(res["sample"]), 200)
                self.ax.plot(xr, stats.norm.pdf(xr, mu, sigma), color=SUCCESS, lw=2.5)
                err_e, err_d = res['err_E'], res['err_D']
            
            self.canvas.draw()
            
            # Обновление карточек с выравниванием по моноширинному шрифту
            self.card_e.update_text(f"Теоретическое: {res['E_th']:>8.3f}\nЭмпирическое:  {res['E_emp']:>8.3f}\nПогрешность:   {err_e*100:>8.2f}%")
            self.card_d.update_text(f"Теоретическое: {res['D_th']:>8.3f}\nЭмпирическое:  {res['D_emp']:>8.3f}\nПогрешность:   {err_d*100:>8.2f}%")
            
            clr = SUCCESS if res["is_valid"] else DANGER
            text_valid = "ПРИНЯТА" if res["is_valid"] else "ОТВЕРГНУТА"
            self.card_chi.update_text(f"Эмпирическое:  {res['chi_emp']:>8.2f}\nКритическое:   {res['chi_crit']:>8.2f}\n{text_valid}", clr)
            
        except Exception as e: 
            QMessageBox.critical(self, "Ошибка ввода", str(e))

    def run_table_series(self):
        self.table.setRowCount(0)
        try:
            for i, n in enumerate([10, 100, 1000, 10000]):
                if self.stack.currentIndex() == 0:
                    p, x = self.get_discrete_data()
                    res = self.core.run_experiment_discrete(p, x, n)
                    ee, ed = res['err_E_rel'], res['err_D_rel']
                else:
                    mu, sigma = float(self.mu_in.text().replace(',', '.')), float(self.sigma_in.text().replace(',', '.'))
                    res = self.core.run_experiment_normal(mu, sigma, n)
                    ee, ed = res['err_E'], res['err_D']
                
                self.table.insertRow(i)
                d = [str(n), f"{res['E_emp']:.3f}", f"{ee*100:.1f}%", f"{res['D_emp']:.3f}", 
                     f"{ed*100:.1f}%", f"{res['chi_emp']:.2f}", f"{res['chi_crit']:.2f}", "ПРИНЯТА" if res["is_valid"] else "ОТВЕРГНУТА"]
                
                for j, v in enumerate(d):
                    it = QTableWidgetItem(v)
                    it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    # Выделение цветом результата
                    if j == 7: 
                        it.setForeground(QColor(SUCCESS if res["is_valid"] else DANGER))
                        font = QFont(); font.setBold(True); it.setFont(font)
                    self.table.setItem(i, j, it)
                    
        except Exception as e: 
            QMessageBox.critical(self, "Ошибка генерации серии", str(e))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Глобальный стиль приложения для системных всплывающих окон и тултипов
    app.setStyle("Fusion") 
    w = MainWindow()
    w.show()
    sys.exit(app.exec())