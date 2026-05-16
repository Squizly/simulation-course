import sys
import math
from collections import Counter
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QDoubleSpinBox, QSpinBox, QPushButton, QFormLayout, 
    QGroupBox, QSplitter, QGridLayout, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import (
    QPainter, QColor, QFont, QPen, QPainterPath, QPolygonF
)
from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from core import MultiServerSimulator

MAC_FONT = "Helvetica Neue"

def add_shadow(widget, blur_radius=15, alpha=40, offset=(0, 4)):
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur_radius)
    shadow.setColor(QColor(0, 0, 0, alpha))
    shadow.setOffset(offset[0], offset[1])
    widget.setGraphicsEffect(shadow)

# --- Кастомный виджет-карточка статистики ---
class StatCard(QFrame):
    def __init__(self, title, color_hex):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #181825;
                border: 1px solid #313244;
                border-radius: 8px;
            }}
        """)
        add_shadow(self, blur_radius=10, alpha=30)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 10, 5, 10)
        
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("color: #A6ADC8; font-size: 10px; font-weight: bold; border: none;")
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_value = QLabel("0")
        self.lbl_value.setStyleSheet(f"color: {color_hex}; font-size: 18px; font-weight: bold; border: none;")
        self.lbl_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_value)

    def set_value(self, val):
        self.lbl_value.setText(str(val))

# --- Визуализатор Мультисерверного Кластера ---
class VisualizerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(240)
        self.queue_count = 0
        self.max_k = 0
        self.servers_state = []
        
        self.anim_phase = 0.0
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.update_animation)
        self.anim_timer.start(16)

    def update_animation(self):
        self.anim_phase += 0.15
        self.update() 

    def update_state(self, queue_count, max_k, servers_state):
        self.queue_count = queue_count
        self.max_k = max_k
        self.servers_state = servers_state

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        width, height = self.width(), self.height()
        center_y = height / 2

        # Фон
        painter.fillRect(0, 0, width, height, QColor("#11111B"))

        # Отрисовка Трубы Очереди
        pipe_width = width - 300
        pipeline_rect = QRectF(20, center_y - 25, pipe_width, 50)
        pipe_path = QPainterPath()
        pipe_path.addRoundedRect(pipeline_rect, 10, 10)
        painter.setBrush(QColor(255, 255, 255, 5))
        
        pipe_border_color = QColor("#F38BA8") if self.queue_count >= self.max_k else QColor("#89B4FA")
        painter.setPen(QPen(pipe_border_color, 2, Qt.PenStyle.DashLine))
        painter.drawPath(pipe_path)

        painter.setPen(QColor("#A6ADC8"))
        painter.setFont(QFont(MAC_FONT, 10, QFont.Weight.Bold))
        painter.drawText(25, int(center_y - 35), f"БУФЕР ОЧЕРЕДИ [ {self.queue_count} / {self.max_k} ]")

        # Пакеты в очереди
        hex_size = 14
        max_vis = min(self.queue_count, int((pipe_width - 20) / (hex_size * 2 + 5)))
        start_x = pipeline_rect.right() - 25

        for i in range(max_vis):
            x = start_x - (i * (hex_size * 2 + 8))
            y = center_y
            points = QPolygonF()
            for j in range(6):
                angle_rad = math.pi / 180 * (60 * j - 30)
                points.append(QPointF(x + hex_size * math.cos(angle_rad), y + hex_size * math.sin(angle_rad)))
            painter.setBrush(QColor("#CBA6F7"))
            painter.setPen(QPen(QColor("#11111B"), 1))
            painter.drawPolygon(points)

        # Балансировщик нагрузки
        bal_rect = QRectF(pipeline_rect.right() + 10, center_y - 40, 30, 80)
        painter.setBrush(QColor("#313244"))
        painter.setPen(QPen(QColor("#CDD6F4"), 2))
        painter.drawRoundedRect(bal_rect, 5, 5)
        painter.setFont(QFont(MAC_FONT, 8, QFont.Weight.Bold))
        painter.drawText(bal_rect, Qt.AlignmentFlag.AlignCenter, "LB")

        # Отрисовка Серверов
        num_servers = len(self.servers_state)
        if num_servers == 0: return

        server_radius = min(25, (height - 40) / (num_servers * 2))
        spacing = (height - 40 - (server_radius * 2 * num_servers)) / max(1, num_servers)
        start_y = 20 + server_radius
        server_x = bal_rect.right() + 80

        for i, is_busy in enumerate(self.servers_state):
            y = start_y + i * (server_radius * 2 + spacing)
            
            painter.setPen(QPen(QColor("#45475A"), 2, Qt.PenStyle.DotLine))
            painter.drawLine(int(bal_rect.right()), int(center_y), int(server_x - server_radius), int(y))

            s_color = QColor("#F38BA8") if is_busy else QColor("#A6E3A1")
            
            if is_busy:
                pulse = int(30 + 40 * math.sin(self.anim_phase))
                painter.setBrush(QColor(s_color.red(), s_color.green(), s_color.blue(), pulse))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPointF(server_x, y), server_radius*1.5, server_radius*1.5)

            painter.setBrush(QColor("#181825"))
            painter.setPen(QPen(s_color, 3))
            painter.drawEllipse(QPointF(server_x, y), server_radius, server_radius)
            
            painter.setPen(QColor("#CDD6F4"))
            painter.setFont(QFont(MAC_FONT, max(8, int(server_radius*0.4)), QFont.Weight.Bold))
            painter.drawText(QRectF(server_x - server_radius, y - server_radius, server_radius*2, server_radius*2), 
                             Qt.AlignmentFlag.AlignCenter, f"S{i+1}")


# --- Главное окно ---
class AdvancedSMOApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ProSim: M/M/c/K Cluster Analysis")
        self.resize(1400, 850)
        self.apply_dark_theme()

        self.sim = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.sim_step)
        self.animation_speed = 40 

        self.setup_ui()

    def apply_dark_theme(self):
        dark_qss = f"""
        QMainWindow, QWidget {{ background-color: #1E1E2E; color: #CDD6F4; font-family: '{MAC_FONT}', sans-serif; }}
        QGroupBox {{ border: 1px solid #45475A; border-radius: 10px; margin-top: 15px; padding-top: 20px; font-weight: bold; font-size: 14px; background-color: #181825; }}
        QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top center; padding: 5px 10px; color: #89B4FA; }}
        QSpinBox, QDoubleSpinBox {{ background-color: #11111B; border: 1px solid #313244; padding: 6px; border-radius: 6px; color: #CDD6F4; font-weight: bold; }}
        QSpinBox:focus, QDoubleSpinBox:focus {{ border: 1px solid #89B4FA; }}
        QLabel {{ font-size: 12px; }}
        QPushButton {{ font-weight: bold; font-size: 13px; border-radius: 8px; padding: 10px; color: #11111B; border: none; }}
        QPushButton#btn_start {{ background-color: #A6E3A1; }}
        QPushButton#btn_pause {{ background-color: #F9E2AF; }}
        QPushButton#btn_ff {{ background-color: #CBA6F7; }}
        QPushButton#btn_reset {{ background-color: #F38BA8; }}
        """
        self.setStyleSheet(dark_qss)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # === ЛЕВАЯ ПАНЕЛЬ ===
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0,0,0,0)

        # Настройки
        settings_group = QGroupBox("ПАРАМЕТРЫ КЛАСТЕРА")
        add_shadow(settings_group)
        form_layout = QFormLayout(settings_group)
        
        self.in_lmbda = QDoubleSpinBox(); self.in_lmbda.setValue(10.0); self.in_lmbda.setSingleStep(1.0)
        self.in_mu = QDoubleSpinBox(); self.in_mu.setValue(3.0); self.in_mu.setSingleStep(0.5)
        self.in_c = QSpinBox(); self.in_c.setRange(1, 15); self.in_c.setValue(3)
        self.in_k = QSpinBox(); self.in_k.setRange(1, 500); self.in_k.setValue(10)
        self.in_theta = QDoubleSpinBox(); self.in_theta.setValue(0.5); self.in_theta.setSingleStep(0.1)
        self.in_n = QSpinBox(); self.in_n.setMaximum(10000); self.in_n.setValue(500)
        
        form_layout.addRow("Поступление (λ):", self.in_lmbda)
        form_layout.addRow("Обслуживание (μ):", self.in_mu)
        form_layout.addRow("Серверов (c):", self.in_c)
        form_layout.addRow("Лимит очереди (K):", self.in_k)
        form_layout.addRow("Нетерпение (θ):", self.in_theta)
        form_layout.addRow("Всего заявок (N):", self.in_n)
        
        # Кнопки
        btn_layout = QGridLayout()
        self.btn_start = QPushButton("⏵ СТАРТ"); self.btn_start.setObjectName("btn_start")
        self.btn_pause = QPushButton("⏸ ПАУЗА"); self.btn_pause.setObjectName("btn_pause")
        self.btn_ff = QPushButton("⏭ МГНОВЕННО"); self.btn_ff.setObjectName("btn_ff")
        self.btn_reset = QPushButton("⟲ СБРОС"); self.btn_reset.setObjectName("btn_reset")

        for btn in [self.btn_start, self.btn_pause, self.btn_ff, self.btn_reset]:
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            add_shadow(btn, blur_radius=10, alpha=40, offset=(0, 2))

        self.btn_start.clicked.connect(self.play_sim)
        self.btn_pause.clicked.connect(self.pause_sim)
        self.btn_ff.clicked.connect(self.fast_forward)
        self.btn_reset.clicked.connect(self.reset_sim)

        btn_layout.addWidget(self.btn_start, 0, 0); btn_layout.addWidget(self.btn_pause, 0, 1)
        btn_layout.addWidget(self.btn_ff, 1, 0); btn_layout.addWidget(self.btn_reset, 1, 1)

        # Статистика
        stats_group = QGroupBox("МЕТРИКИ КЛАСТЕРА")
        add_shadow(stats_group)
        stats_layout = QGridLayout(stats_group)
        
        self.cards = {
            "arr": StatCard("ПОСТУПИЛО", "#CDD6F4"),
            "proc": StatCard("УСПЕШНО", "#A6E3A1"),
            "rej": StatCard("ОТКАЗ (FULL)", "#F38BA8"),
            "abn": StatCard("УШЛИ (TIMEOUT)", "#FAB387"),
            "p_rej": StatCard("% ОТКАЗОВ", "#F38BA8"),
            "p_abn": StatCard("% УХОДОВ", "#FAB387"),
            "time": StatCard("ВРЕМЯ (с)", "#89B4FA"),
            "avg_q": StatCard("СР. ОЧЕРЕДЬ", "#CBA6F7"),
        }
        
        row, col = 0, 0
        for key, card in self.cards.items():
            stats_layout.addWidget(card, row, col)
            col += 1
            if col > 1:
                col = 0
                row += 1

        left_layout.addWidget(settings_group)
        left_layout.addSpacing(10)
        left_layout.addLayout(btn_layout)
        left_layout.addSpacing(10)
        left_layout.addWidget(stats_group)
        left_layout.addStretch()

        # === ПРАВАЯ ПАНЕЛЬ ===
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0,0,0,0)
        right_layout.setSpacing(15)
        
        self.visualizer = VisualizerWidget()
        add_shadow(self.visualizer)
        
        # Область графиков (Гистограмма и Полигон)
        self.fig = Figure(facecolor='#1E1E2E')
        self.fig.subplots_adjust(left=0.06, right=0.97, bottom=0.15, top=0.85, wspace=0.2)
        self.canvas = FigureCanvas(self.fig)
        
        self.ax_hist = self.fig.add_subplot(121)
        self.ax_poly = self.fig.add_subplot(122)
        
        chart_container = QFrame()
        chart_container.setStyleSheet("background-color: #181825; border-radius: 10px;")
        add_shadow(chart_container)
        QVBoxLayout(chart_container).addWidget(self.canvas)

        self.format_axes()
        
        right_layout.addWidget(self.visualizer, stretch=1)
        right_layout.addWidget(chart_container, stretch=2)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([320, 1080])
        splitter.setHandleWidth(0)
        
        main_layout.addWidget(splitter)

    def format_axes(self):
        for ax in [self.ax_hist, self.ax_poly]:
            ax.set_facecolor('#181825')
            ax.tick_params(colors='#A6ADC8', labelsize=10)
            for spine in ['top', 'right']: ax.spines[spine].set_visible(False)
            for spine in ['left', 'bottom']: ax.spines[spine].set_color('#313244')
            ax.grid(True, axis='y', linestyle='--', alpha=0.3, color='#CDD6F4')

        self.ax_hist.set_title("ГИСТОГРАММА: ВРЕМЯ В ОЧЕРЕДИ", color='#CDD6F4', fontsize=11, fontweight='bold', family=MAC_FONT)
        self.ax_hist.set_xlabel("Время ожидания (с)", color='#A6ADC8')
        self.ax_hist.set_ylabel("Частота", color='#A6ADC8')

        self.ax_poly.set_title("ПОЛИГОН: КЛИЕНТОВ В СИСТЕМЕ", color='#CDD6F4', fontsize=11, fontweight='bold', family=MAC_FONT)
        self.ax_poly.set_xlabel("Число клиентов (к)", color='#A6ADC8')
        self.ax_poly.set_ylabel("Частота", color='#A6ADC8')

    def reset_sim(self):
        self.timer.stop()
        self.sim = MultiServerSimulator(
            self.in_lmbda.value(), self.in_mu.value(), self.in_c.value(),
            self.in_k.value(), self.in_theta.value(), self.in_n.value()
        )
        self.ax_hist.clear()
        self.ax_poly.clear()
        self.format_axes()
        self.canvas.draw()
        self.visualizer.update_state(0, self.in_k.value(), [False]*self.in_c.value())
        self.update_stats_ui()

    def play_sim(self):
        if self.sim is None or self.sim.is_finished: self.reset_sim()
        self.timer.start(self.animation_speed)

    def pause_sim(self): self.timer.stop()

    def fast_forward(self):
        if self.sim is None: self.reset_sim()
        self.timer.stop()
        while not self.sim.is_finished: self.sim.step()
        self.update_ui_full()

    def sim_step(self):
        for _ in range(5): 
            if not self.sim.step():
                self.timer.stop()
                self.update_ui_full()
                return
        self.update_ui_full()

    def update_ui_full(self):
        # 1. Визуал серверов и очереди
        srv_state = [s.is_busy for s in self.sim.servers]
        self.visualizer.update_state(len(self.sim.queue), self.sim.k, srv_state)
        
        # 2. Обновление графиков (Эмпирические распределения)
        self.ax_hist.clear()
        self.ax_poly.clear()
        self.format_axes()

        # График 1: Гистограмма времени в очереди
        if self.sim.wait_times_data:
            self.ax_hist.hist(self.sim.wait_times_data, bins=15, color='#CBA6F7', edgecolor='#181825', alpha=0.8)

        # График 2: Полигон частот (число клиентов в системе)
        if self.sim.system_states_data:
            # Подсчет частот каждого состояния системы
            counts = Counter(self.sim.system_states_data)
            states = sorted(counts.keys())
            frequencies = [counts[s] for s in states]
            
            self.ax_poly.plot(states, frequencies, marker='o', color='#A6E3A1', linestyle='-', linewidth=2, markersize=5)
            self.ax_poly.fill_between(states, frequencies, color='#A6E3A1', alpha=0.15)
            # Принудительно делаем шаг по оси X целым числом
            self.ax_poly.set_xticks(range(min(states), max(states) + 1))

        self.canvas.draw()
        
        # 3. Обновление текстовой статистики
        self.update_stats_ui()

    def update_stats_ui(self):
        if not self.sim: return
        st = self.sim.get_stats()
        
        self.cards["arr"].set_value(st["arrived"])
        self.cards["proc"].set_value(st["processed"])
        self.cards["rej"].set_value(st["rejected"])
        self.cards["abn"].set_value(st["abandoned"])
        self.cards["p_rej"].set_value(f"{st['p_rej']:.1f}%")
        self.cards["p_abn"].set_value(f"{st['p_abn']:.1f}%")
        self.cards["time"].set_value(f"{st['time']:.1f}")
        self.cards["avg_q"].set_value(f"{st['avg_q']:.2f}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AdvancedSMOApp()
    window.show()
    sys.exit(app.exec())