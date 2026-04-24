import sys
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QSlider, QFrame, 
                             QGridLayout, QLineEdit, QProgressBar, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QDoubleValidator, QColor

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from core import WeatherMarkovModel

# ═══════════════════════════════════════════════════════════════════════════════
# 🎨 ДИЗАЙН-СИСТЕМА
# ═══════════════════════════════════════════════════════════════════════════════

class Colors:
    # Основные цвета
    BG_DARK = "#0A0E1A"
    BG_CARD = "#111827"
    BG_CARD_HOVER = "#1A2332"
    BG_INPUT = "#0D1117"
    
    # Акценты
    ACCENT_PRIMARY = "#6366F1"    # Индиго
    ACCENT_SUCCESS = "#10B981"    # Изумруд
    ACCENT_WARNING = "#F59E0B"    # Янтарь
    ACCENT_DANGER = "#EF4444"     # Красный
    ACCENT_INFO = "#3B82F6"       # Синий
    
    # Текст
    TEXT_PRIMARY = "#F9FAFB"
    TEXT_SECONDARY = "#9CA3AF"
    TEXT_MUTED = "#6B7280"
    
    # Границы
    BORDER = "#1F2937"
    BORDER_HOVER = "#374151"
    
    # Графики
    CHART_BLUE = "#60A5FA"
    CHART_PINK = "#F472B6"
    CHART_PURPLE = "#A78BFA"

WEATHER_STYLES = {
    0: {
        "name": "ЯСНО", 
        "emoji": "☀️", 
        "color": "#FBBF24",
        "text_shadow": "#F59E0B",
        "bg": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0369A1, stop:0.5 #0284C7, stop:1 #38BDF8)",
        "glow": "#38BDF8"
    },
    1: {
        "name": "ОБЛАЧНО", 
        "emoji": "⛅", 
        "color": "#E5E7EB",
        "text_shadow": "#9CA3AF",
        "bg": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #374151, stop:0.5 #4B5563, stop:1 #6B7280)",
        "glow": "#9CA3AF"
    },
    2: {
        "name": "ПАСМУРНО", 
        "emoji": "☁️", 
        "color": "#9CA3AF",
        "text_shadow": "#6B7280",
        "bg": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1F2937, stop:0.5 #374151, stop:1 #4B5563)",
        "glow": "#6B7280"
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# 🧩 КАСТОМНЫЕ ВИДЖЕТЫ
# ═══════════════════════════════════════════════════════════════════════════════

class GlowingCard(QFrame):
    """Карточка с эффектом свечения"""
    def __init__(self, glow_color=Colors.ACCENT_PRIMARY, parent=None):
        super().__init__(parent)
        self.glow_color = glow_color
        self.setup_shadow()
        
    def setup_shadow(self):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)

class StyledButton(QPushButton):
    """Стилизованная кнопка с анимацией"""
    def __init__(self, text, color, parent=None):
        super().__init__(text, parent)
        self.base_color = color
        self.setFixedHeight(48)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_style()
        
    def update_style(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 {self._lighten(self.base_color, 20)}, 
                    stop:1 {self.base_color});
                border: none;
                border-radius: 12px;
                color: white;
                font-weight: 600;
                font-size: 14px;
                padding: 0 24px;
                letter-spacing: 0.5px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 {self._lighten(self.base_color, 35)}, 
                    stop:1 {self._lighten(self.base_color, 15)});
            }}
            QPushButton:pressed {{
                background: {self._darken(self.base_color, 10)};
            }}
        """)
        
    def _lighten(self, hex_color, amount):
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        new_rgb = tuple(min(255, c + amount) for c in rgb)
        return f"#{new_rgb[0]:02x}{new_rgb[1]:02x}{new_rgb[2]:02x}"
    
    def _darken(self, hex_color, amount):
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        new_rgb = tuple(max(0, c - amount) for c in rgb)
        return f"#{new_rgb[0]:02x}{new_rgb[1]:02x}{new_rgb[2]:02x}"
    
    def set_color(self, color):
        self.base_color = color
        self.update_style()

# ═══════════════════════════════════════════════════════════════════════════════
# 🎯 ГЛАВНОЕ ПРИЛОЖЕНИЕ
# ═══════════════════════════════════════════════════════════════════════════════

class WeatherSimApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.model = WeatherMarkovModel()
        self.is_running = False
        self.history_emojis = []
        
        self.time_in_current_state = 0.0
        self.target_tau = 0.0
        self.next_state = 0
        self.speed_multiplier = 1.0 
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.setInterval(33) 
        
        self.init_ui()
        self.reset_simulation()

    def init_ui(self):
        self.setWindowTitle("⛈ Марковская модель погоды — Непрерывное время")
        self.resize(1150, 750)
        self.setMinimumSize(900, 600)
        
        # Глобальные стили
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {Colors.BG_DARK};
            }}
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
            }}
            QSlider::groove:horizontal {{
                background: {Colors.BORDER};
                height: 6px;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.ACCENT_PRIMARY}, stop:1 #4F46E5);
                width: 18px;
                height: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }}
            QSlider::handle:horizontal:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #818CF8, stop:1 {Colors.ACCENT_PRIMARY});
            }}
            QSlider::sub-page:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Colors.ACCENT_PRIMARY}, stop:1 #818CF8);
                border-radius: 3px;
            }}
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(24)

        # ЛЕВАЯ КОЛОНКА
        left_panel = QVBoxLayout()
        left_panel.setSpacing(20)
        left_panel.addWidget(self.create_matrix_panel())
        left_panel.addWidget(self.create_controls_panel())
        main_layout.addLayout(left_panel, stretch=1)

        # ПРАВАЯ КОЛОНКА
        right_panel = QVBoxLayout()
        right_panel.setSpacing(20)
        right_panel.addWidget(self.create_weather_card(), stretch=2)
        right_panel.addWidget(self.create_chart_panel(), stretch=3)
        main_layout.addLayout(right_panel, stretch=2)

    def create_matrix_panel(self):
        frame = GlowingCard()
        frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.BG_CARD_HOVER}, stop:1 {Colors.BG_CARD});
                border: 1px solid {Colors.BORDER};
                border-radius: 20px;
            }}
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Заголовок с иконкой
        header_layout = QHBoxLayout()
        icon_label = QLabel("📊")
        icon_label.setFont(QFont("Arial", 20))
        title = QLabel("Матрица интенсивностей Q")
        title.setFont(QFont("SF Pro Display", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Сетка матрицы
        grid_container = QFrame()
        grid_container.setStyleSheet(f"""
            background: {Colors.BG_INPUT};
            border-radius: 12px;
            padding: 8px;
        """)
        grid = QGridLayout(grid_container)
        grid.setSpacing(8)
        self.matrix_inputs = {}
        validator = QDoubleValidator(0.0, 10.0, 3)

        labels = ["☀️ Ясно", "⛅ Облачно", "☁️ Пасмурно"]
        short_labels = ["☀️", "⛅", "☁️"]
        
        # Заголовки столбцов
        for i, lbl in enumerate(short_labels):
            header = QLabel(lbl)
            header.setFont(QFont("Arial", 16))
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(header, 0, i+1)
        
        # Заголовки строк и ячейки
        defaults = {
            (0,1): "0.3", (0,2): "0.1", 
            (1,0): "0.4", (1,2): "0.4", 
            (2,0): "0.1", (2,1): "0.4"
        }

        for i in range(3):
            row_label = QLabel(labels[i])
            row_label.setFont(QFont("SF Pro Display", 11, QFont.Weight.Medium))
            row_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
            row_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            grid.addWidget(row_label, i+1, 0)
            
            for j in range(3):
                if i == j:
                    lbl = QLabel("AUTO")
                    lbl.setStyleSheet(f"""
                        color: {Colors.ACCENT_DANGER}; 
                        font-weight: bold;
                        font-size: 10px;
                        letter-spacing: 1px;
                    """)
                    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    lbl.setFixedSize(64, 36)
                    grid.addWidget(lbl, i+1, j+1)
                else:
                    inp = QLineEdit(defaults[(i, j)])
                    inp.setValidator(validator)
                    inp.setFixedSize(64, 36)
                    inp.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    inp.setStyleSheet(f"""
                        QLineEdit {{
                            background: {Colors.BG_CARD};
                            border: 2px solid {Colors.BORDER};
                            border-radius: 8px;
                            padding: 4px;
                            color: {Colors.TEXT_PRIMARY};
                            font-weight: 600;
                            font-size: 13px;
                        }}
                        QLineEdit:focus {{
                            border: 2px solid {Colors.ACCENT_PRIMARY};
                            background: {Colors.BG_CARD_HOVER};
                        }}
                        QLineEdit:hover {{
                            border: 2px solid {Colors.BORDER_HOVER};
                        }}
                    """)
                    inp.textChanged.connect(self.on_matrix_changed)
                    self.matrix_inputs[(i, j)] = inp
                    grid.addWidget(inp, i+1, j+1)

        layout.addWidget(grid_container)
        return frame

    def create_controls_panel(self):
        frame = GlowingCard()
        frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.BG_CARD_HOVER}, stop:1 {Colors.BG_CARD});
                border: 1px solid {Colors.BORDER};
                border-radius: 20px;
            }}
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Заголовок
        header_layout = QHBoxLayout()
        icon_label = QLabel("🎮")
        icon_label.setFont(QFont("Arial", 20))
        title = QLabel("Управление")
        title.setFont(QFont("SF Pro Display", 16, QFont.Weight.Bold))
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        self.btn_start = StyledButton("▶  Старт", Colors.ACCENT_SUCCESS)
        self.btn_start.clicked.connect(self.toggle_simulation)
        
        self.btn_reset = StyledButton("↺  Сброс", Colors.ACCENT_DANGER)
        self.btn_reset.clicked.connect(self.reset_simulation)

        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_reset)
        layout.addLayout(btn_layout)

        # Ползунок скорости
        speed_container = QFrame()
        speed_container.setStyleSheet(f"""
            background: {Colors.BG_INPUT};
            border-radius: 12px;
            padding: 4px;
        """)
        speed_layout = QVBoxLayout(speed_container)
        speed_layout.setContentsMargins(16, 12, 16, 12)
        
        speed_header = QHBoxLayout()
        lbl_speed = QLabel("⚡ Скорость симуляции")
        lbl_speed.setFont(QFont("SF Pro Display", 12, QFont.Weight.Medium))
        self.lbl_speed_value = QLabel("×1.0")
        self.lbl_speed_value.setStyleSheet(f"color: {Colors.ACCENT_PRIMARY}; font-weight: bold;")
        speed_header.addWidget(lbl_speed)
        speed_header.addWidget(self.lbl_speed_value)
        speed_layout.addLayout(speed_header)
        
        self.slider_speed = QSlider(Qt.Orientation.Horizontal)
        self.slider_speed.setRange(1, 50)
        self.slider_speed.setValue(10)
        self.slider_speed.valueChanged.connect(self.on_speed_changed)
        speed_layout.addWidget(self.slider_speed)
        
        layout.addWidget(speed_container)

        # ═══════════════════════════════════════════════════════════════
        # 📜 ИСТОРИЯ ПЕРЕХОДОВ (ИСПРАВЛЕННАЯ)
        # ═══════════════════════════════════════════════════════════════
        history_container = QFrame()
        history_container.setStyleSheet(f"""
            background: {Colors.BG_INPUT};
            border-radius: 12px;
        """)
        history_layout = QVBoxLayout(history_container)
        history_layout.setContentsMargins(16, 12, 16, 12)
        
        history_header = QLabel("📜 История переходов")
        history_header.setFont(QFont("SF Pro Display", 12, QFont.Weight.Medium))
        history_layout.addWidget(history_header)
        
        # Контейнер фиксированного размера для эмодзи
        self.history_frame = QFrame()
        self.history_frame.setFixedHeight(56)
        self.history_frame.setStyleSheet(f"""
            background: {Colors.BG_CARD};
            border-radius: 10px;
            border: 1px solid {Colors.BORDER};
        """)
        
        self.history_items_layout = QHBoxLayout(self.history_frame)
        self.history_items_layout.setContentsMargins(12, 8, 12, 8)
        self.history_items_layout.setSpacing(4)
        
        # Создаём 5 фиксированных слотов для эмодзи
        self.history_slots = []
        for i in range(5):
            slot = QLabel("")
            slot.setFixedSize(36, 36)
            slot.setAlignment(Qt.AlignmentFlag.AlignCenter)
            slot.setFont(QFont("Arial", 20))
            slot.setStyleSheet("background: transparent;")
            self.history_slots.append(slot)
            self.history_items_layout.addWidget(slot)
            
            # Добавляем стрелку между слотами (кроме последнего)
            if i < 4:
                arrow = QLabel("→")
                arrow.setFixedWidth(20)
                arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
                arrow.setStyleSheet(f"color: {Colors.TEXT_MUTED}; background: transparent; font-size: 14px;")
                self.history_items_layout.addWidget(arrow)
        
        history_layout.addWidget(self.history_frame)
        layout.addWidget(history_container)
        
        layout.addStretch()
        return frame

    def create_weather_card(self):
        self.weather_frame = GlowingCard()
        self.weather_frame.setStyleSheet(f"""
            QFrame {{
                border-radius: 24px;
                background: {WEATHER_STYLES[0]['bg']};
                border: 2px solid rgba(255, 255, 255, 0.1);
            }}
        """)
        layout = QVBoxLayout(self.weather_frame)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(8)
        
        # Эмодзи шрифт
        emoji_font = "Apple Color Emoji" if sys.platform == "darwin" else (
            "Segoe UI Emoji" if sys.platform == "win32" else "Noto Color Emoji"
        )

        # Верхняя строка со статусом
        status_layout = QHBoxLayout()
        self.status_badge = QLabel("● АКТИВНО")
        self.status_badge.setStyleSheet(f"""
            background: rgba(16, 185, 129, 0.2);
            color: {Colors.ACCENT_SUCCESS};
            padding: 6px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 1px;
        """)
        status_layout.addWidget(self.status_badge)
        status_layout.addStretch()
        layout.addLayout(status_layout)

        layout.addStretch()

        # Эмодзи погоды
        self.lbl_emoji = QLabel(WEATHER_STYLES[0]['emoji'])
        self.lbl_emoji.setFont(QFont(emoji_font, 80))
        self.lbl_emoji.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_emoji.setStyleSheet("background: transparent;")
        layout.addWidget(self.lbl_emoji)
        
        # Название погоды
        self.lbl_weather_name = QLabel(WEATHER_STYLES[0]['name'])
        self.lbl_weather_name.setFont(QFont("SF Pro Display", 32, QFont.Weight.Bold))
        self.lbl_weather_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_weather_name.setStyleSheet(f"""
            background: transparent; 
            color: {WEATHER_STYLES[0]['color']};
            letter-spacing: 4px;
        """)
        layout.addWidget(self.lbl_weather_name)
        
        layout.addStretch()

        # Прогресс-бар
        progress_container = QFrame()
        progress_container.setStyleSheet("background: transparent;")
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(8)
        
        self.lbl_progress_text = QLabel("До смены погоды")
        self.lbl_progress_text.setStyleSheet("""
            background: transparent;
            color: rgba(255, 255, 255, 0.7);
            font-size: 12px;
        """)
        progress_layout.addWidget(self.lbl_progress_text)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet("""
            QProgressBar { 
                background-color: rgba(255, 255, 255, 0.15); 
                border-radius: 4px;
                border: none;
            }
            QProgressBar::chunk { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(255, 255, 255, 0.9), 
                    stop:1 rgba(255, 255, 255, 0.6));
                border-radius: 4px; 
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        layout.addWidget(progress_container)

        # Статистика
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            background: rgba(0, 0, 0, 0.2);
            border-radius: 16px;
        """)
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setContentsMargins(20, 16, 20, 16)
        
        # Прошло дней
        days_container = QVBoxLayout()
        self.lbl_days_title = QLabel("ПРОШЛО ДНЕЙ")
        self.lbl_days_title.setStyleSheet("""
            background: transparent;
            color: rgba(255, 255, 255, 0.6);
            font-size: 10px;
            font-weight: bold;
            letter-spacing: 1px;
        """)
        self.lbl_days = QLabel("0.00")
        self.lbl_days.setFont(QFont("SF Pro Display", 24, QFont.Weight.Bold))
        self.lbl_days.setStyleSheet("background: transparent; color: white;")
        days_container.addWidget(self.lbl_days_title)
        days_container.addWidget(self.lbl_days)
        
        # Разделитель
        separator = QFrame()
        separator.setFixedWidth(1)
        separator.setStyleSheet("background: rgba(255, 255, 255, 0.2);")
        
        # Смена через
        tau_container = QVBoxLayout()
        tau_container.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_tau_title = QLabel("СМЕНА ЧЕРЕЗ")
        self.lbl_tau_title.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_tau_title.setStyleSheet("""
            background: transparent;
            color: rgba(255, 255, 255, 0.6);
            font-size: 10px;
            font-weight: bold;
            letter-spacing: 1px;
        """)
        self.lbl_tau = QLabel("0.00")
        self.lbl_tau.setFont(QFont("SF Pro Display", 24, QFont.Weight.Bold))
        self.lbl_tau.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_tau.setStyleSheet("background: transparent; color: white;")
        tau_container.addWidget(self.lbl_tau_title)
        tau_container.addWidget(self.lbl_tau)
        
        stats_layout.addLayout(days_container)
        stats_layout.addStretch()
        stats_layout.addWidget(separator)
        stats_layout.addStretch()
        stats_layout.addLayout(tau_container)
        
        layout.addWidget(stats_frame)
        
        return self.weather_frame

    def create_chart_panel(self):
        frame = GlowingCard()
        frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.BG_CARD_HOVER}, stop:1 {Colors.BG_CARD});
                border: 1px solid {Colors.BORDER};
                border-radius: 20px;
            }}
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Заголовок
        header_layout = QHBoxLayout()
        icon_label = QLabel("📈")
        icon_label.setFont(QFont("Arial", 20))
        title = QLabel("Распределение состояний")
        title.setFont(QFont("SF Pro Display", 16, QFont.Weight.Bold))
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Легенда
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(16)
        
        theo_dot = QLabel("●")
        theo_dot.setStyleSheet(f"color: {Colors.CHART_BLUE};")
        theo_label = QLabel("Теоретическое")
        theo_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 12px;")
        
        emp_dot = QLabel("●")
        emp_dot.setStyleSheet(f"color: {Colors.CHART_PINK};")
        emp_label = QLabel("Эмпирическое")
        emp_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 12px;")
        
        legend_layout.addWidget(theo_dot)
        legend_layout.addWidget(theo_label)
        legend_layout.addWidget(emp_dot)
        legend_layout.addWidget(emp_label)
        
        header_layout.addLayout(legend_layout)
        layout.addLayout(header_layout)

        # График
        self.figure = Figure(facecolor=Colors.BG_CARD, edgecolor='none')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self.canvas)
        
        self.ax = self.figure.add_subplot(111)
        self.setup_chart_style()

        self.x_pos = np.arange(3)
        self.bar_width = 0.35
        
        self.bars_theo = self.ax.bar(
            self.x_pos - self.bar_width/2, 
            self.model.theoretical_pi, 
            self.bar_width, 
            label='Теоретическое (π)', 
            color=Colors.CHART_BLUE,
            edgecolor='white',
            linewidth=0.5,
            alpha=0.9,
            zorder=3
        )
        self.bars_emp = self.ax.bar(
            self.x_pos + self.bar_width/2, 
            [0, 0, 0], 
            self.bar_width, 
            label='Эмпирическое', 
            color=Colors.CHART_PINK,
            edgecolor='white',
            linewidth=0.5,
            alpha=0.9,
            zorder=3
        )
        
        # Метки под столбиками
        labels = ["☀️ Солнечно", "☁️ Облачно", "☁️ Пасмурно"]
        self.ax.set_xticks(self.x_pos)
        self.ax.set_xticklabels(labels, fontsize=11, fontweight='medium')
        self.ax.set_ylim(0, 1.0)
        
        # Горизонтальные линии сетки
        self.ax.yaxis.grid(True, linestyle='--', alpha=0.3, color=Colors.BORDER)
        self.ax.set_axisbelow(True)
        
        self.figure.tight_layout(pad=1.5, rect=[0, 0.12, 1, 1])

        return frame

    def setup_chart_style(self):
        """Настройка стиля графика matplotlib"""
        self.ax.set_facecolor(Colors.BG_INPUT)
        self.ax.tick_params(colors=Colors.TEXT_SECONDARY, labelsize=10)
        self.ax.tick_params(axis='x', colors=Colors.TEXT_PRIMARY)
        
        # Скрываем рамку
        for spine in ['top', 'right']:
            self.ax.spines[spine].set_visible(False)
        for spine in ['bottom', 'left']:
            self.ax.spines[spine].set_color(Colors.BORDER)
            self.ax.spines[spine].set_linewidth(0.5)
        
        # Метки оси Y
        self.ax.set_ylabel('Вероятность', color=Colors.TEXT_SECONDARY, fontsize=11)
        self.ax.yaxis.label.set_color(Colors.TEXT_SECONDARY)

    def on_speed_changed(self):
        self.speed_multiplier = self.slider_speed.value() / 10.0
        self.lbl_speed_value.setText(f"×{self.speed_multiplier:.1f}")

    def on_matrix_changed(self):
        """Парсит поля ввода и обновляет Q-матрицу в модели"""
        try:
            q01 = float(self.matrix_inputs[(0, 1)].text().replace(',', '.') or 0)
            q02 = float(self.matrix_inputs[(0, 2)].text().replace(',', '.') or 0)
            q10 = float(self.matrix_inputs[(1, 0)].text().replace(',', '.') or 0)
            q12 = float(self.matrix_inputs[(1, 2)].text().replace(',', '.') or 0)
            q20 = float(self.matrix_inputs[(2, 0)].text().replace(',', '.') or 0)
            q21 = float(self.matrix_inputs[(2, 1)].text().replace(',', '.') or 0)
            
            self.model.update_matrix(q01, q02, q10, q12, q20, q21)
            
            for bar, h in zip(self.bars_theo, self.model.theoretical_pi):
                bar.set_height(h)
            self.canvas.draw_idle()
            
        except ValueError:
            pass

    def reset_simulation(self):
        self.is_running = False
        self.timer.stop()
        self.btn_start.setText("▶  Старт")
        self.btn_start.set_color(Colors.ACCENT_SUCCESS)
        self.status_badge.setText("● ГОТОВО")
        self.status_badge.setStyleSheet(f"""
            background: rgba(107, 114, 128, 0.2);
            color: {Colors.TEXT_MUTED};
            padding: 6px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 1px;
        """)
        
        self.model.reset()
        self.on_matrix_changed()
        self.update_weather_display(0)
        
        # Сброс истории - только первый элемент
        self.history_emojis = [WEATHER_STYLES[0]['emoji']]
        self.update_history_ui()
        
        self.target_tau, self.next_state = self.model.generate_next_transition()
        self.time_in_current_state = 0.0
        
        self.update_labels()
        self.update_chart()

    def toggle_simulation(self):
        if self.is_running:
            self.timer.stop()
            self.btn_start.setText("▶  Продолжить")
            self.btn_start.set_color(Colors.ACCENT_SUCCESS)
            self.status_badge.setText("● ПАУЗА")
            self.status_badge.setStyleSheet(f"""
                background: rgba(245, 158, 11, 0.2);
                color: {Colors.ACCENT_WARNING};
                padding: 6px 12px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 1px;
            """)
        else:
            self.timer.start()
            self.btn_start.setText("⏸  Пауза")
            self.btn_start.set_color(Colors.ACCENT_WARNING)
            self.status_badge.setText("● АКТИВНО")
            self.status_badge.setStyleSheet(f"""
                background: rgba(16, 185, 129, 0.2);
                color: {Colors.ACCENT_SUCCESS};
                padding: 6px 12px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 1px;
            """)
        self.is_running = not self.is_running

    def tick(self):
        dt = (33 / 1000.0) * self.speed_multiplier
        self.model.apply_time_tick(dt)
        self.time_in_current_state += dt
        
        if self.time_in_current_state >= self.target_tau:
            overflow = self.time_in_current_state - self.target_tau 
            
            # Добавляем новый элемент в историю
            self.history_emojis.append(WEATHER_STYLES[self.next_state]['emoji'])
            
            # Ограничиваем до 5 элементов (удаляем слева)
            if len(self.history_emojis) > 5:
                self.history_emojis.pop(0)
            
            self.update_history_ui()

            self.model.set_state(self.next_state)
            self.update_weather_display(self.next_state)
            
            self.target_tau, self.next_state = self.model.generate_next_transition()
            self.time_in_current_state = overflow 

        self.update_labels()
        self.update_chart()

    def update_history_ui(self):
        """Обновляет фиксированные слоты истории"""
        # Очищаем все слоты
        for slot in self.history_slots:
            slot.setText("")
            slot.setStyleSheet("background: transparent;")
        
        # Заполняем слоты справа налево (новые справа)
        # Или можно слева направо - как удобнее
        for i, emoji in enumerate(self.history_emojis):
            if i < len(self.history_slots):
                self.history_slots[i].setText(emoji)
                
                # Подсвечиваем последний (самый новый) элемент
                if i == len(self.history_emojis) - 1:
                    self.history_slots[i].setStyleSheet(f"""
                        background: rgba(99, 102, 241, 0.2);
                        border-radius: 8px;
                    """)
                else:
                    self.history_slots[i].setStyleSheet("background: transparent;")

    def update_weather_display(self, state):
        style = WEATHER_STYLES[state]
        self.weather_frame.setStyleSheet(f"""
            QFrame {{
                border-radius: 24px;
                background: {style['bg']};
                border: 2px solid rgba(255, 255, 255, 0.1);
            }}
        """)
        self.lbl_emoji.setText(style['emoji'])
        self.lbl_weather_name.setText(style['name'])
        self.lbl_weather_name.setStyleSheet(f"""
            background: transparent; 
            color: {style['color']};
            letter-spacing: 4px;
        """)

    def update_labels(self):
        self.lbl_days.setText(f"{self.model.total_time:.2f}")
        time_left = max(0, self.target_tau - self.time_in_current_state)
        self.lbl_tau.setText(f"{time_left:.2f}")
        
        if self.target_tau > 0 and self.target_tau != float('inf'):
            progress = int((self.time_in_current_state / self.target_tau) * 100)
            self.progress_bar.setValue(min(100, max(0, progress)))
        else:
            self.progress_bar.setValue(0)

    def update_chart(self):
        emp_probs = self.model.get_empirical_distribution()
        for bar, h in zip(self.bars_emp, emp_probs):
            bar.set_height(h)
        self.canvas.draw_idle()


# ═══════════════════════════════════════════════════════════════════════════════
# 🚀 ЗАПУСК
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Применяем шрифт для всего приложения
    font = QFont("SF Pro Display", 10)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)
    
    window = WeatherSimApp()
    window.show()
    sys.exit(app.exec())