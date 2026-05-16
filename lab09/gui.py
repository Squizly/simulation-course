import sys
import math
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QDoubleSpinBox, QSpinBox, QPushButton, QFormLayout, 
    QGroupBox, QSplitter, QGridLayout, QFrame, QGraphicsDropShadowEffect,
    QTabWidget
)
from PyQt6.QtGui import (
    QPainter, QColor, QFont, QPen, QBrush, 
    QLinearGradient, QPainterPath, QPolygonF
)
from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from core_helper import SMOSimulator

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


class VisualizerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(220)
        self.queue_count = 0
        self.server_busy = False
        self.anim_phase = 0.0
        self.rotation_angle = 0.0
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.update_animation)
        self.anim_timer.start(16)

    def update_animation(self):
        self.anim_phase += 0.1
        self.rotation_angle += 1.5
        if self.rotation_angle >= 360: self.rotation_angle = 0
        self.update() 

    def update_state(self, queue_count, server_busy):
        self.queue_count = queue_count
        self.server_busy = server_busy

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width(); height = self.height(); center_y = height / 2
        painter.fillRect(0, 0, width, height, QColor("#11111B"))

        core_color = QColor("#F38BA8") if self.server_busy else QColor("#89DCEB") 
        status_text = "ЗАНЯТ" if self.server_busy else "СВОБОДЕН"

        pipeline_rect = QRectF(20, center_y - 30, width - 200, 60)
        pipe_path = QPainterPath()
        pipe_path.addRoundedRect(pipeline_rect, 15, 15)
        painter.setBrush(QColor(255, 255, 255, 5))
        painter.setPen(QPen(QColor(255, 255, 255, 20), 1))
        painter.drawPath(pipe_path)
        
        painter.setPen(QPen(core_color, 1, Qt.PenStyle.DashLine))
        painter.drawLine(30, int(center_y - 20), int(width - 190), int(center_y - 20))
        painter.drawLine(30, int(center_y + 20), int(width - 190), int(center_y + 20))

        painter.setPen(QColor("#A6ADC8"))
        painter.setFont(QFont(MAC_FONT, 11, QFont.Weight.Bold))
        painter.drawText(30, int(center_y - 40), f"ОЧЕРЕДЬ : {self.queue_count} КЛИЕНТОВ")

        hex_size = 18
        max_vis = min(self.queue_count, int((pipeline_rect.width() - 40) / (hex_size * 2 + 5)))
        start_x = pipeline_rect.right() - 30

        for i in range(max_vis):
            x = start_x - (i * (hex_size * 2 + 10)); y = center_y
            points = QPolygonF()
            for j in range(6):
                angle_rad = math.pi / 180 * (60 * j - 30)
                points.append(QPointF(x + hex_size * math.cos(angle_rad), y + hex_size * math.sin(angle_rad)))
                
            hex_grad = QLinearGradient(x - hex_size, y - hex_size, x + hex_size, y + hex_size)
            hex_grad.setColorAt(0, QColor("#CBA6F7")); hex_grad.setColorAt(1, QColor("#89B4FA"))
            painter.setBrush(QBrush(hex_grad)); painter.setPen(QPen(QColor("#11111B"), 2))
            painter.drawPolygon(points)
            painter.setPen(QColor("#11111B")); painter.setFont(QFont(MAC_FONT, 9, QFont.Weight.Bold))
            painter.drawText(QRectF(x - hex_size, y - hex_size, hex_size*2, hex_size*2), Qt.AlignmentFlag.AlignCenter, str(self.queue_count - i))

        if self.queue_count > max_vis:
            painter.setPen(QColor("#F9E2AF")); painter.setFont(QFont(MAC_FONT, 14, QFont.Weight.Bold))
            painter.drawText(int(pipeline_rect.left() + 5), int(center_y + 5), "...")

        server_cx = width - 100; server_cy = center_y
        
        pulse_alpha = int(40 + 40 * math.sin(self.anim_phase))
        painter.setBrush(QColor(core_color.red(), core_color.green(), core_color.blue(), pulse_alpha))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(server_cx, server_cy), 60, 60)
        
        painter.translate(server_cx, server_cy)
        painter.setPen(QPen(core_color, 2)); painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.rotate(self.rotation_angle)
        painter.drawArc(-50, -50, 100, 100, 0 * 16, 100 * 16); painter.drawArc(-50, -50, 100, 100, 180 * 16, 100 * 16)
        painter.rotate(-self.rotation_angle * 2)
        painter.drawArc(-40, -40, 80, 80, 90 * 16, 80 * 16); painter.drawArc(-40, -40, 80, 80, 270 * 16, 80 * 16)
        painter.resetTransform()
        
        painter.setBrush(QColor("#181825")); painter.setPen(QPen(core_color, 3))
        painter.drawEllipse(QPointF(server_cx, server_cy), 30, 30)
        
        painter.setPen(QColor("#CDD6F4")); painter.setFont(QFont(MAC_FONT, 12, QFont.Weight.Bold))
        painter.drawText(QRectF(server_cx - 60, server_cy + 65, 120, 20), Qt.AlignmentFlag.AlignCenter, "ОПЕРАТОР")
        painter.setPen(core_color); painter.setFont(QFont(MAC_FONT, 9, QFont.Weight.Bold))
        painter.drawText(QRectF(server_cx - 40, server_cy - 10, 80, 20), Qt.AlignmentFlag.AlignCenter, status_text)


class ProfessionalSMOApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Система M/M/1")
        self.resize(1350, 850)
        self.apply_dark_theme()

        self.sim = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.sim_step)
        self.animation_speed = 50 
        self.steps_per_render = 5 # Для оптимизации отрисовки графиков

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
        
        # --- ЛЕВАЯ ПАНЕЛЬ ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0,0,0,0)

        settings_group = QGroupBox("НАЧАЛЬНЫЕ ПАРАМЕТРЫ")
        form_layout = QFormLayout()
        
        self.lambda_in = QDoubleSpinBox(); self.lambda_in.setValue(5.0); self.lambda_in.setSingleStep(0.5)
        self.mu_in = QDoubleSpinBox(); self.mu_in.setValue(6.0); self.mu_in.setSingleStep(0.5)
        self.n_in = QSpinBox(); self.n_in.setMaximum(100000); self.n_in.setValue(500)
        
        form_layout.addRow("Приход клиентов (λ):", self.lambda_in)
        form_layout.addRow("Обслуживание (μ):", self.mu_in)
        form_layout.addRow("Всего клиентов (N):", self.n_in)
        settings_group.setLayout(form_layout)
        
        btn_layout = QGridLayout()
        self.btn_start = QPushButton("⏵ СТАРТ"); self.btn_start.setObjectName("btn_start")
        self.btn_pause = QPushButton("⏸ ПАУЗА"); self.btn_pause.setObjectName("btn_pause")
        self.btn_ff = QPushButton("⏭ МГНОВЕННО"); self.btn_ff.setObjectName("btn_ff")
        self.btn_reset = QPushButton("⟲ СБРОС"); self.btn_reset.setObjectName("btn_reset")
        self.btn_start.clicked.connect(self.play_sim); self.btn_pause.clicked.connect(self.pause_sim)
        self.btn_ff.clicked.connect(self.fast_forward); self.btn_reset.clicked.connect(self.reset_sim)
        btn_layout.addWidget(self.btn_start, 0, 0); btn_layout.addWidget(self.btn_pause, 0, 1)
        btn_layout.addWidget(self.btn_ff, 1, 0); btn_layout.addWidget(self.btn_reset, 1, 1)

        stats_group = QGroupBox("РЕЗУЛЬТАТЫ ФУНКЦИОНИРОВАНИЯ")
        stats_layout = QGridLayout()
        self.card_proc = StatCard("ОБСЛУЖЕНО", "#CDD6F4")
        self.card_wait = StatCard("СРЕДНЕЕ ОЖИДАНИЕ", "#F9E2AF")
        self.card_prob = StatCard("ВЕРОЯТНОСТЬ ОЖИДАНИЯ", "#F38BA8")
        self.card_qlen = StatCard("СРЕДНЯЯ ОЧЕРЕДЬ", "#CBA6F7")
        self.card_rho = StatCard("ЗАГРУЗКА (ρ)", "#A6E3A1")

        stats_layout.addWidget(self.card_proc, 0, 0, 1, 2)
        stats_layout.addWidget(self.card_wait, 1, 0)
        stats_layout.addWidget(self.card_qlen, 1, 1)
        stats_layout.addWidget(self.card_rho, 2, 0)
        stats_layout.addWidget(self.card_prob, 2, 1)
        stats_group.setLayout(stats_layout)

        left_layout.addWidget(settings_group); left_layout.addSpacing(10)
        left_layout.addLayout(btn_layout); left_layout.addSpacing(10)
        left_layout.addWidget(stats_group); left_layout.addStretch()

        # --- ПРАВАЯ ПАНЕЛЬ ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0,0,0,0)
        
        self.visualizer = VisualizerWidget()
        
        # Вкладки с графиками
        self.tabs = QTabWidget()
        
        # Вкладка 1: Клиенты в системе
        self.tab_sys = QWidget()
        self.fig_sys = Figure(facecolor='#181825'); self.fig_sys.subplots_adjust(bottom=0.15, left=0.1)
        self.canvas_sys = FigureCanvas(self.fig_sys)
        self.ax_sys = self.fig_sys.add_subplot(111)
        l1 = QVBoxLayout(self.tab_sys); l1.addWidget(self.canvas_sys); l1.setContentsMargins(0,0,0,0)
        
        # Вкладка 2: Время ожидания
        self.tab_wait = QWidget()
        self.fig_wait = Figure(facecolor='#181825'); self.fig_wait.subplots_adjust(bottom=0.15, left=0.1)
        self.canvas_wait = FigureCanvas(self.fig_wait)
        self.ax_wait = self.fig_wait.add_subplot(111)
        l2 = QVBoxLayout(self.tab_wait); l2.addWidget(self.canvas_wait); l2.setContentsMargins(0,0,0,0)

        self.tabs.addTab(self.tab_sys, "Распределение клиентов в системе")
        self.tabs.addTab(self.tab_wait, "Время ожидания в очереди")
        add_shadow(self.tabs)
        
        right_layout.addWidget(self.visualizer, stretch=1)
        right_layout.addWidget(self.tabs, stretch=3)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel); splitter.addWidget(right_panel)
        splitter.setSizes([350, 1000])
        main_layout.addWidget(splitter)
        
        self.style_axes(self.ax_sys, "Количество клиентов в системе (k)", "Вероятность (Pk)")
        self.style_axes(self.ax_wait, "Время ожидания в очереди (t)", "Частота")

    def style_axes(self, ax, xlabel, ylabel):
        ax.set_facecolor('#181825')
        ax.tick_params(colors='#A6ADC8', labelsize=10)
        for spine in ['top', 'right']: ax.spines[spine].set_visible(False)
        for spine in ['left', 'bottom']: ax.spines[spine].set_color('#313244')
        ax.set_xlabel(xlabel, color='#A6ADC8', fontweight='bold', family=MAC_FONT)
        ax.set_ylabel(ylabel, color='#A6ADC8', fontweight='bold', family=MAC_FONT)
        ax.grid(True, axis='y', linestyle='--', alpha=0.3, color='#CDD6F4')

    def reset_sim(self):
        self.timer.stop()
        self.sim = SMOSimulator(self.lambda_in.value(), self.mu_in.value(), self.n_in.value())
        self.ax_sys.clear(); self.style_axes(self.ax_sys, "Количество клиентов в системе (k)", "Вероятность (Pk)")
        self.ax_wait.clear(); self.style_axes(self.ax_wait, "Время ожидания в очереди (t)", "Частота / Плотность")
        self.canvas_sys.draw(); self.canvas_wait.draw()
        self.visualizer.update_state(0, False)
        self.update_stats_ui()

    def play_sim(self):
        if self.sim is None or self.sim.is_finished: self.reset_sim()
        self.timer.start(self.animation_speed)

    def pause_sim(self): self.timer.stop()

    def fast_forward(self):
        if self.sim is None: self.reset_sim()
        self.timer.stop()
        while not self.sim.is_finished: self.sim.step()
        self.update_ui_full(force_plot=True)

    def sim_step(self):
        for _ in range(self.steps_per_render): 
            if not self.sim.step():
                self.timer.stop()
                self.update_ui_full(force_plot=True)
                return
        self.update_ui_full(force_plot=False) # Графики рисуем не каждый кадр для производительности

    def update_ui_full(self, force_plot=True):
        self.visualizer.update_state(self.sim.queue_count, self.sim.server_busy)
        self.update_stats_ui()
        
        # Обновляем графики только если симуляция завершена или вызвана принудительно (экономит ресурсы)
        # Если хотите видеть рост гистограмм в live-режиме, можно убрать условие, но возможны подлагивания.
        
        self.plot_distributions()

    def plot_distributions(self):
        # 1. ГРАФИК: КЛИЕНТЫ В СИСТЕМЕ (ДИСКРЕТНОЕ РАСПРЕДЕЛЕНИЕ)
        self.ax_sys.clear()
        self.style_axes(self.ax_sys, "Количество клиентов в системе (k)", "Вероятность (Pk)")
        if self.sim.state_times:
            states = sorted(list(self.sim.state_times.keys()))
            times = [self.sim.state_times[s] for s in states]
            total_time = sum(times)
            if total_time > 0:
                probs = [t / total_time for t in times]
                
                # Гистограмма (Столбцы)
                self.ax_sys.bar(states, probs, color='#CBA6F7', alpha=0.6, width=0.6, align='center')
                # Полигон частот (Линия)
                self.ax_sys.plot(states, probs, color='#89B4FA', marker='o', linestyle='-', linewidth=2)
                
                self.ax_sys.set_xticks(states)
        self.canvas_sys.draw()

        # 2. ГРАФИК: ВРЕМЯ ОЖИДАНИЯ В ОЧЕРЕДИ (НЕПРЕРЫВНОЕ РАСПРЕДЕЛЕНИЕ)
        self.ax_wait.clear()
        self.style_axes(self.ax_wait, "Время ожидания в очереди (t)", "Частота / Плотность")
        if len(self.sim.wait_times) > 1:
            waits = self.sim.wait_times
            # Гистограмма
            counts, bins, _ = self.ax_wait.hist(waits, bins=20, density=True, color='#F9E2AF', alpha=0.5, edgecolor='#181825')
            # Полигон частот (по центрам интервалов)
            bin_centers = 0.5 * (bins[:-1] + bins[1:])
            self.ax_wait.plot(bin_centers, counts, color='#FAB387', marker='o', linestyle='-', linewidth=2)
        self.canvas_wait.draw()

    def update_stats_ui(self):
        if self.sim:
            stats = self.sim.get_stats()
            self.card_proc.set_value(f"{stats['processed']} / {self.sim.total_requests}")
            self.card_wait.set_value(f"{stats['avg_wait']:.3f} с")
            self.card_qlen.set_value(f"{stats['avg_q']:.2f}")
            
            # Вероятность долгого ожидания
            prob_percent = stats['prob_long_wait'] * 100
            limit_str = f"LIMIT={stats['wait_threshold']:.1f}c"
            self.card_prob.lbl_title.setText(f"ВЕРОЯТНОСТЬ ОЖИДАНИЯ ({limit_str})")
            self.card_prob.set_value(f"{prob_percent:.1f}%")

            rho_percent = stats['rho'] * 100
            self.card_rho.lbl_value.setStyleSheet(
                "color: #F38BA8; font-size: 20px; font-weight: bold; border: none;" if rho_percent >= 100 else 
                "color: #A6E3A1; font-size: 20px; font-weight: bold; border: none;"
            )
            self.card_rho.set_value(f"{rho_percent:.1f}%")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ProfessionalSMOApp()
    window.show()
    sys.exit(app.exec())