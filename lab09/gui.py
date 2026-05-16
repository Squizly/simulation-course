import sys
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QDoubleSpinBox, QSpinBox, QPushButton, QFormLayout,
    QGroupBox, QSplitter, QGridLayout, QFrame, QGraphicsDropShadowEffect,
    QTabWidget
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, QTimer
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from core import SMOSimulator   # файл core.py должен быть рядом

MAC_FONT = "Helvetica Neue"

def add_shadow(widget, blur_radius=15, alpha=40, offset=(0, 4)):
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur_radius)
    shadow.setColor(QColor(0, 0, 0, alpha))
    shadow.setOffset(offset[0], offset[1])
    widget.setGraphicsEffect(shadow)

class StatCard(QFrame):
    def __init__(self, title, color_hex):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{ background-color: #181825; border: 1px solid #313244; border-radius: 10px; }}
        """)
        add_shadow(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 15, 10, 15)
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("color: #A6ADC8; font-size: 11px; font-weight: bold; border: none;")
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_value = QLabel("0.00")
        self.lbl_value.setStyleSheet(f"color: {color_hex}; font-size: 20px; font-weight: bold; border: none;")
        self.lbl_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_value)

    def set_value(self, val):
        self.lbl_value.setText(str(val))

class StatusPanel(QFrame):
    """Простая панель состояния сервера (без очереди)"""
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #181825; border: 1px solid #313244; border-radius: 10px;")
        add_shadow(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        self.server_label = QLabel("⚪ ОПЕРАТОР СВОБОДЕН")
        self.server_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.server_label.setStyleSheet("color: #89DCEB; font-size: 16px; font-weight: bold; border: none;")
        layout.addWidget(self.server_label)

    def update_state(self, server_busy):
        if server_busy:
            self.server_label.setText("🔴 ОПЕРАТОР ЗАНЯТ")
            self.server_label.setStyleSheet("color: #F38BA8; font-size: 16px; font-weight: bold; border: none;")
        else:
            self.server_label.setText("🟢 ОПЕРАТОР СВОБОДЕН")
            self.server_label.setStyleSheet("color: #A6E3A1; font-size: 16px; font-weight: bold; border: none;")

class ProfessionalSMOApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Система M/M/1/0 (с отказами)")
        self.resize(1200, 800)
        self.apply_dark_theme()

        self.sim = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.sim_step)
        self.animation_speed = 50
        self.steps_per_render = 5

        self.setup_ui()

    def apply_dark_theme(self):
        dark_qss = f"""
        QMainWindow, QWidget {{ background-color: #1E1E2E; color: #CDD6F4; font-family: '{MAC_FONT}', sans-serif; }}
        QGroupBox {{ border: 1px solid #45475A; border-radius: 10px; margin-top: 15px; padding-top: 20px; font-weight: bold; background-color: #181825; }}
        QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top center; padding: 5px 10px; color: #89B4FA; }}
        QSpinBox, QDoubleSpinBox {{ background-color: #11111B; border: 1px solid #313244; padding: 8px; border-radius: 6px; font-weight: bold; }}
        QSpinBox:focus, QDoubleSpinBox:focus {{ border: 1px solid #89B4FA; }}
        QPushButton {{ font-weight: bold; font-size: 14px; border-radius: 8px; padding: 12px; color: #11111B; border: none; }}
        QPushButton#btn_start {{ background-color: #A6E3A1; }} QPushButton#btn_start:hover {{ background-color: #8BD686; }}
        QPushButton#btn_pause {{ background-color: #F9E2AF; }} QPushButton#btn_pause:hover {{ background-color: #EBD39E; }}
        QPushButton#btn_ff {{ background-color: #CBA6F7; }} QPushButton#btn_ff:hover {{ background-color: #B991E6; }}
        QPushButton#btn_reset {{ background-color: #F38BA8; }} QPushButton#btn_reset:hover {{ background-color: #E57A98; }}
        QTabWidget::pane {{ border: 1px solid #313244; border-radius: 10px; background: #181825; }}
        QTabBar::tab {{ background: #1E1E2E; color: #A6ADC8; padding: 10px 20px; border-top-left-radius: 8px; border-top-right-radius: 8px; font-weight: bold; border: 1px solid #313244; border-bottom: none; }}
        QTabBar::tab:selected {{ background: #181825; color: #89B4FA; border-top: 2px solid #89B4FA; }}
        """
        self.setStyleSheet(dark_qss)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # ---------- ЛЕВАЯ ПАНЕЛЬ ----------
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Параметры
        settings_group = QGroupBox("НАЧАЛЬНЫЕ ПАРАМЕТРЫ")
        form_layout = QFormLayout()
        self.lambda_in = QDoubleSpinBox(); self.lambda_in.setValue(5.0); self.lambda_in.setSingleStep(0.5)
        self.mu_in = QDoubleSpinBox(); self.mu_in.setValue(6.0); self.mu_in.setSingleStep(0.5)
        self.n_in = QSpinBox(); self.n_in.setMaximum(100000); self.n_in.setValue(500)
        form_layout.addRow("Приход клиентов (λ):", self.lambda_in)
        form_layout.addRow("Обслуживание (μ):", self.mu_in)
        form_layout.addRow("Всего клиентов (N):", self.n_in)
        settings_group.setLayout(form_layout)

        # Кнопки
        btn_layout = QGridLayout()
        self.btn_start = QPushButton("⏵ СТАРТ"); self.btn_start.setObjectName("btn_start")
        self.btn_pause = QPushButton("⏸ ПАУЗА"); self.btn_pause.setObjectName("btn_pause")
        self.btn_ff = QPushButton("⏭ МГНОВЕННО"); self.btn_ff.setObjectName("btn_ff")
        self.btn_reset = QPushButton("⟲ СБРОС"); self.btn_reset.setObjectName("btn_reset")
        self.btn_start.clicked.connect(self.play_sim)
        self.btn_pause.clicked.connect(self.pause_sim)
        self.btn_ff.clicked.connect(self.fast_forward)
        self.btn_reset.clicked.connect(self.reset_sim)
        btn_layout.addWidget(self.btn_start, 0, 0); btn_layout.addWidget(self.btn_pause, 0, 1)
        btn_layout.addWidget(self.btn_ff, 1, 0); btn_layout.addWidget(self.btn_reset, 1, 1)

        # Статистика
        stats_group = QGroupBox("РЕЗУЛЬТАТЫ ФУНКЦИОНИРОВАНИЯ")
        stats_layout = QGridLayout()
        self.card_arrived = StatCard("ПОСТУПИЛО", "#CDD6F4")
        self.card_processed = StatCard("ОБСЛУЖЕНО", "#A6E3A1")
        self.card_lost = StatCard("ОТКАЗАНО", "#F38BA8")
        self.card_p_reject = StatCard("ВЕРОЯТНОСТЬ ОТКАЗА", "#F9E2AF")
        self.card_rho = StatCard("ЗАГРУЗКА (ρ)", "#CBA6F7")
        self.card_avg_svc = StatCard("СРЕДНЕЕ ВРЕМЯ ОБСЛ.", "#89B4FA")

        stats_layout.addWidget(self.card_arrived, 0, 0, 1, 2)
        stats_layout.addWidget(self.card_processed, 1, 0)
        stats_layout.addWidget(self.card_lost, 1, 1)
        stats_layout.addWidget(self.card_p_reject, 2, 0)
        stats_layout.addWidget(self.card_rho, 2, 1)
        stats_layout.addWidget(self.card_avg_svc, 3, 0, 1, 2)
        stats_group.setLayout(stats_layout)

        left_layout.addWidget(settings_group)
        left_layout.addSpacing(10)
        left_layout.addLayout(btn_layout)
        left_layout.addSpacing(10)
        left_layout.addWidget(stats_group)
        left_layout.addStretch()

        # ---------- ПРАВАЯ ПАНЕЛЬ ----------
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.status_panel = StatusPanel()

        # Вкладка с графиком состояний (0 и 1)
        self.tabs = QTabWidget()
        self.tab_states = QWidget()
        self.fig_states = Figure(facecolor='#181825')
        self.fig_states.subplots_adjust(bottom=0.15, left=0.1)
        self.canvas_states = FigureCanvas(self.fig_states)
        self.ax_states = self.fig_states.add_subplot(111)
        l1 = QVBoxLayout(self.tab_states); l1.addWidget(self.canvas_states); l1.setContentsMargins(0,0,0,0)
        self.tabs.addTab(self.tab_states, "Распределение состояний системы")
        add_shadow(self.tabs)

        right_layout.addWidget(self.status_panel, stretch=1)
        right_layout.addWidget(self.tabs, stretch=3)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([350, 850])
        main_layout.addWidget(splitter)

        self.style_axes(self.ax_states, "Состояние", "Вероятность")

    def style_axes(self, ax, xlabel, ylabel):
        ax.set_facecolor('#181825')
        ax.tick_params(colors='#A6ADC8', labelsize=10)
        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)
        for spine in ['left', 'bottom']:
            ax.spines[spine].set_color('#313244')
        ax.set_xlabel(xlabel, color='#A6ADC8', fontweight='bold', family=MAC_FONT)
        ax.set_ylabel(ylabel, color='#A6ADC8', fontweight='bold', family=MAC_FONT)
        ax.grid(True, axis='y', linestyle='--', alpha=0.3, color='#CDD6F4')

    def reset_sim(self):
        self.timer.stop()
        self.sim = SMOSimulator(self.lambda_in.value(), self.mu_in.value(), self.n_in.value())
        self.ax_states.clear()
        self.style_axes(self.ax_states, "Состояние", "Вероятность")
        self.canvas_states.draw()
        self.status_panel.update_state(False)
        self.update_stats_ui()

    def play_sim(self):
        if self.sim is None or self.sim.is_finished:
            self.reset_sim()
        self.timer.start(self.animation_speed)

    def pause_sim(self):
        self.timer.stop()

    def fast_forward(self):
        if self.sim is None:
            self.reset_sim()
        self.timer.stop()
        while not self.sim.is_finished:
            self.sim.step()
        self.update_ui_full(force_plot=True)

    def sim_step(self):
        for _ in range(self.steps_per_render):
            if not self.sim.step():
                self.timer.stop()
                self.update_ui_full(force_plot=True)
                return
        self.update_ui_full(force_plot=False)

    def update_ui_full(self, force_plot=True):
        self.status_panel.update_state(self.sim.server_busy)
        self.update_stats_ui()
        self.plot_distributions()

    def plot_distributions(self):
        self.ax_states.clear()
        self.style_axes(self.ax_states, "Состояние", "Вероятность")
        if self.sim and self.sim.current_time > 0:
            total_time = self.sim.current_time
            states = sorted(self.sim.state_times.keys())
            probs = [self.sim.state_times[s] / total_time for s in states]
            # Рисуем только два столбца (0 и 1) с подписями
            labels = ['Свободен (0)', 'Занят (1)']
            colors = ['#A6E3A1', '#F38BA8']
            self.ax_states.bar(states, probs, color=colors, alpha=0.7, width=0.5, align='center')
            self.ax_states.set_xticks(states)
            self.ax_states.set_xticklabels(labels)
            self.ax_states.set_ylim(0, 1.05)
        self.canvas_states.draw()

    def update_stats_ui(self):
        if self.sim:
            stats = self.sim.get_stats()
            self.card_arrived.set_value(str(stats['arrived']))
            self.card_processed.set_value(str(stats['processed']))
            self.card_lost.set_value(str(stats['lost']))

            p = stats['p_reject'] * 100
            self.card_p_reject.set_value(f"{p:.1f} %")

            rho = stats['rho_emp'] * 100
            # Цвет загрузки: красный, если > 100% (теоретически невозможно, но для проверки)
            if stats['rho_theor'] >= 1.0:
                self.card_rho.lbl_value.setStyleSheet("color: #F38BA8; font-size: 20px; font-weight: bold; border: none;")
            else:
                self.card_rho.lbl_value.setStyleSheet("color: #CBA6F7; font-size: 20px; font-weight: bold; border: none;")
            self.card_rho.set_value(f"{rho:.1f} %")

            avg_svc = stats['avg_service_time']
            self.card_avg_svc.set_value(f"{avg_svc:.3f}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ProfessionalSMOApp()
    window.show()
    sys.exit(app.exec())