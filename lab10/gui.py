import sys
import math
import random
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QDoubleSpinBox, QSpinBox, QPushButton, QFormLayout,
    QGroupBox, QSplitter, QGridLayout, QFrame, QGraphicsDropShadowEffect,
    QSizePolicy
)
from PyQt6.QtGui import (
    QPainter, QColor, QFont, QPen, QPainterPath,
    QLinearGradient, QRadialGradient
)
from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from core import MultiServerSimulator

# ── Палитра ───────────────────────────────────────────────────────────────────
BG_DEEP   = "#070711"
BG_PANEL  = "#0d0d1a"
BG_CARD   = "#111122"
BG_INPUT  = "#15152a"
BORDER    = "#252545"

NEON_BLUE  = "#4fc3f7"
NEON_PURP  = "#b39ddb"
NEON_GREEN = "#69f0ae"
NEON_PINK  = "#f48fb1"
NEON_AMBER = "#ffcc02"
NEON_CYAN  = "#18ffff"
NEON_RED   = "#ff5252"

TEXT_PRI  = "#e8eaf6"
TEXT_SEC  = "#7986cb"
TEXT_DIM  = "#3d4068"

FONT = "Segoe UI" if sys.platform == "win32" else "SF Pro Display"


# ── Тень ──────────────────────────────────────────────────────────────────────
def shadow(w, r=18, a=80, dx=0, dy=4):
    ef = QGraphicsDropShadowEffect()
    ef.setBlurRadius(r)
    ef.setColor(QColor(0, 0, 0, a))
    ef.setOffset(dx, dy)
    w.setGraphicsEffect(ef)


# ── Визуализатор СМО (без частиц, статичная перерисовка) ─────────────────────
class FlowVisualizer(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(220)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.queue_count   = 0
        self.max_k         = 10
        self.servers_state = []

        # Анимация только пульса серверов — лёгкий синус
        self._phase = 0.0
        self._anim  = QTimer(self)
        self._anim.timeout.connect(self._tick)
        self._anim.start(50)   # 20 fps — достаточно для плавного пульса

    def update_state(self, queue_count, max_k, servers_state):
        self.queue_count   = queue_count
        self.max_k         = max_k
        self.servers_state = servers_state

    def _tick(self):
        self._phase += 0.12
        self.update()

    # ── Рисование ─────────────────────────────────────────────────────────────
    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()

        # Фон
        p.fillRect(0, 0, W, H, QColor(BG_DEEP))

        # Тонкая сетка точек на фоне (статичная, не анимированная)
        self._draw_dot_grid(p, W, H)

        cy = H / 2

        # Труба потока
        self._draw_tube(p, W, H, cy)

        # Зона очереди
        self._draw_queue(p, W, H, cy)

        # Балансировщик
        bx = self._draw_balancer(p, W, H, cy)

        # Серверы
        self._draw_servers(p, W, H, bx)

    def _draw_dot_grid(self, p, W, H):
        p.save()
        p.setPen(Qt.PenStyle.NoPen)
        step = 28
        for gx in range(0, W, step):
            for gy in range(0, H, step):
                p.setBrush(QColor(40, 40, 90, 45))
                p.drawEllipse(QPointF(gx, gy), 1.2, 1.2)
        p.restore()

    def _draw_tube(self, p, W, H, cy):
        x1   = 40
        x2   = int(W * 0.74)
        rect = QRectF(x1, cy - 24, x2 - x1, 48)

        grad = QLinearGradient(x1, cy - 24, x1, cy + 24)
        grad.setColorAt(0,   QColor(25, 35, 80, 55))
        grad.setColorAt(0.5, QColor(15, 25, 60, 90))
        grad.setColorAt(1,   QColor(25, 35, 80, 55))

        path = QPainterPath()
        path.addRoundedRect(rect, 12, 12)
        p.setBrush(grad)

        fill = self.queue_count / max(1, self.max_k)
        border_col = QColor(NEON_PINK if fill >= 1.0 else NEON_BLUE)
        border_col.setAlpha(100)
        p.setPen(QPen(border_col, 1.5))
        p.drawPath(path)

    def _draw_queue(self, p, W, H, cy):
        cell  = 20
        gap   = 6
        slots = min(self.max_k, int((W * 0.55) / (cell + gap)))
        ox    = 55

        # Заголовок очереди
        fill = self.queue_count / max(1, self.max_k)
        bar_color = NEON_PINK if fill >= 1.0 else (NEON_AMBER if fill > 0.7 else NEON_BLUE)

        p.setFont(QFont(FONT, 8, QFont.Weight.Bold))
        p.setPen(QColor(bar_color))
        p.drawText(ox, int(cy - 30),
                   f"ОЧЕРЕДЬ  {self.queue_count} / {self.max_k}")

        # Полоса заполненности
        bw, bh = 100, 4
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(30, 30, 60))
        p.drawRoundedRect(ox, int(cy - 24), bw, bh, 2, 2)
        fw = int(bw * min(fill, 1.0))
        if fw > 0:
            bg = QLinearGradient(ox, 0, ox + bw, 0)
            bg.setColorAt(0, QColor(NEON_BLUE))
            bg.setColorAt(1, QColor(bar_color))
            p.setBrush(bg)
            p.drawRoundedRect(ox, int(cy - 24), fw, bh, 2, 2)

        # Слоты
        for i in range(slots):
            cx = ox + i * (cell + gap)
            filled = i < self.queue_count

            if filled:
                fg = QRadialGradient(cx + cell/2, cy, cell)
                fg.setColorAt(0, QColor(NEON_PURP).lighter(130))
                fg.setColorAt(1, QColor(NEON_PURP).darker(140))
                p.setBrush(fg)
                p.setPen(QPen(QColor(NEON_PURP), 1.5))
            else:
                p.setBrush(QColor(18, 18, 45, 90))
                p.setPen(QPen(QColor(55, 55, 110, 100), 1,
                              Qt.PenStyle.DashLine))

            p.drawEllipse(QRectF(cx, cy - cell / 2, cell, cell))

    def _draw_balancer(self, p, W, H, cy):
        """Рисует шестиугольный балансировщик, возвращает правый X"""
        cx = W * 0.78
        r  = 32

        # Контур шестиугольника
        hex_path = QPainterPath()
        for i in range(6):
            ang = math.radians(60 * i - 30)
            px  = cx + r * math.cos(ang)
            py  = cy + r * math.sin(ang)
            if i == 0:
                hex_path.moveTo(px, py)
            else:
                hex_path.lineTo(px, py)
        hex_path.closeSubpath()

        bg = QLinearGradient(cx - r, cy - r, cx + r, cy + r)
        bg.setColorAt(0, QColor("#1a2055"))
        bg.setColorAt(1, QColor("#0d1535"))
        p.setBrush(bg)
        p.setPen(QPen(QColor(NEON_CYAN), 1.8))
        p.drawPath(hex_path)

        p.setPen(QColor(NEON_CYAN))
        p.setFont(QFont(FONT, 7, QFont.Weight.Bold))
        p.drawText(QRectF(cx - r, cy - r, r * 2, r * 2),
                   Qt.AlignmentFlag.AlignCenter, "БАЛАНСИР\nЗАГРУЗКИ")

        return cx + r

    def _draw_servers(self, p, W, H, bal_right_x):
        n = len(self.servers_state)
        if n == 0:
            return

        sx    = W * 0.91
        marg  = 20
        step  = (H - marg * 2) / max(n, 1)
        r     = min(26, step * 0.36)

        for i, busy in enumerate(self.servers_state):
            sy    = marg + step * i + step / 2
            color = QColor(NEON_GREEN if not busy else NEON_PINK)

            # Соединительная линия
            conn = QLinearGradient(bal_right_x, H / 2, sx - r, sy)
            c1   = QColor(NEON_CYAN);  c1.setAlpha(60)
            c2   = QColor(color);      c2.setAlpha(50)
            conn.setColorAt(0, c1)
            conn.setColorAt(1, c2)
            p.setPen(QPen(conn, 1.2))
            p.drawLine(QPointF(bal_right_x, H / 2), QPointF(sx - r, sy))

            # Пульсирующий ореол только у занятых серверов
            if busy:
                pulse_r = r * 1.55 + 5 * math.sin(self._phase + i * 1.2)
                gc      = QColor(NEON_PINK)
                gc.setAlpha(int(28 + 22 * abs(math.sin(self._phase + i))))
                p.setBrush(gc)
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(QPointF(sx, sy), pulse_r, pulse_r)

            # Тело сервера
            sv = QRadialGradient(sx - r * 0.3, sy - r * 0.3, r * 1.4)
            sv.setColorAt(0, QColor(color).lighter(115))
            sv.setColorAt(1, QColor(color).darker(185))
            p.setBrush(sv)
            p.setPen(QPen(color, 2.2))
            p.drawEllipse(QPointF(sx, sy), r, r)

            # Внутреннее кольцо
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(QColor(255, 255, 255, 45), 1))
            p.drawEllipse(QPointF(sx, sy), r * 0.52, r * 0.52)

            # Номер сервера
            p.setPen(QColor(255, 255, 255, 210))
            p.setFont(QFont(FONT, int(max(7, r * 0.42)), QFont.Weight.Bold))
            p.drawText(QRectF(sx - r, sy - r, r * 2, r * 2),
                       Qt.AlignmentFlag.AlignCenter, f"S{i+1}")

            # Маленький цветной бейдж статуса
            bx, by = sx + r - 6, sy - r + 6
            badge  = QColor(NEON_GREEN if not busy else NEON_RED)
            p.setBrush(badge)
            p.setPen(QPen(QColor(BG_DEEP), 1.2))
            p.drawEllipse(QPointF(bx, by), 6, 6)

            # Подпись статуса
            label = "ЗАНЯТ" if busy else "ПРОСТОЙ"
            p.setPen(color)
            p.setFont(QFont(FONT, 7, QFont.Weight.Bold))
            p.drawText(int(sx + r + 7), int(sy + 4), label)


# ── Карточка метрики ──────────────────────────────────────────────────────────
class MetricCard(QFrame):
    def __init__(self, title, accent, icon=""):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #13132b, stop:1 #0e0e20);
                border: 1px solid #252545;
                border-top: 2px solid {accent};
                border-radius: 10px;
            }}
        """)
        shadow(self, r=10, a=70)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 9, 10, 10)
        lay.setSpacing(2)

        top = QHBoxLayout()
        if icon:
            ico = QLabel(icon)
            ico.setStyleSheet(
                f"color:{accent};font-size:13px;"
                "border:none;background:transparent;")
            top.addWidget(ico)

        lbl_t = QLabel(title)
        lbl_t.setStyleSheet(
            f"color:{TEXT_SEC};font-size:9px;font-weight:700;"
            "letter-spacing:1px;border:none;background:transparent;")
        top.addWidget(lbl_t)
        top.addStretch()

        self.lbl_v = QLabel("—")
        self.lbl_v.setStyleSheet(
            f"color:{accent};font-size:21px;font-weight:800;"
            "border:none;background:transparent;")
        self.lbl_v.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lay.addLayout(top)
        lay.addWidget(self.lbl_v)

    def set_value(self, v):
        self.lbl_v.setText(str(v))


# ── Кнопка ────────────────────────────────────────────────────────────────────
class NeonButton(QPushButton):
    def __init__(self, text, color):
        super().__init__(text)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(38)
        self.setFont(QFont(FONT, 10, QFont.Weight.Bold))
        c_light = QColor(color).lighter(118).name()
        c_dark  = QColor(color).darker(165).name()
        c_press = QColor(color).darker(135).name()
        self.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 {c_light}, stop:1 {c_dark});
                color: #06060f;
                border: 1.5px solid {color};
                border-radius: 9px;
                padding: 8px 6px;
                font-weight: 800;
                letter-spacing: 0.4px;
            }}
            QPushButton:hover  {{ background: {color}; border-color: #ffffff; }}
            QPushButton:pressed {{ background: {c_press}; }}
        """)
        shadow(self, r=8, a=35)


# ── Группа параметров ─────────────────────────────────────────────────────────
class ParamGroup(QGroupBox):
    def __init__(self, title):
        super().__init__(title)
        self.setStyleSheet(f"""
            QGroupBox {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #0e0e20, stop:1 #0b0b18);
                border: 1px solid {BORDER};
                border-radius: 12px;
                margin-top: 18px;
                padding-top: 14px;
                font-weight: 700;
                font-size: 11px;
                color: {TEXT_SEC};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 3px 10px;
                background: #131330;
                border: 1px solid {BORDER};
                border-radius: 6px;
                color: {NEON_BLUE};
                left: 12px;
            }}
        """)
        shadow(self, r=12, a=55)


# ── Главное окно ──────────────────────────────────────────────────────────────
class AdvancedSMOApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Мультисерверный Анализатор СМО")
        self.resize(1480, 900)
        self._apply_theme()

        self.sim        = None
        self.timer      = QTimer()
        self.timer.timeout.connect(self._sim_step)
        self.anim_speed = 30

        self._build_ui()

    # ── Глобальная тема ───────────────────────────────────────────────────────
    def _apply_theme(self):
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {BG_DEEP};
                color: {TEXT_PRI};
                font-family: '{FONT}', 'Segoe UI', sans-serif;
            }}
            QSplitter::handle {{ background: {BORDER}; width: 1px; }}
            QSpinBox, QDoubleSpinBox {{
                background: {BG_INPUT};
                border: 1px solid {BORDER};
                border-radius: 7px;
                padding: 5px 8px;
                color: {TEXT_PRI};
                font-weight: 600;
                font-size: 11px;
            }}
            QSpinBox:focus, QDoubleSpinBox:focus {{
                border: 1.5px solid {NEON_BLUE};
                background: {BG_CARD};
            }}
            QSpinBox::up-button, QDoubleSpinBox::up-button,
            QSpinBox::down-button, QDoubleSpinBox::down-button {{
                background: {BORDER}; border: none;
                border-radius: 3px; width: 14px;
            }}
            QLabel {{
                font-size: 10px;
                color: {TEXT_SEC};
                background: transparent;
            }}
        """)

    # ── Построение UI ─────────────────────────────────────────────────────────
    def _build_ui(self):
        root     = QWidget()
        self.setCentralWidget(root)
        root_lay = QHBoxLayout(root)
        root_lay.setContentsMargins(10, 10, 10, 10)
        root_lay.setSpacing(10)

        # ─── Левая колонка ────────────────────────────────────────────────────
        left = QWidget()
        left.setFixedWidth(305)
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(10)

        # Параметры
        pg   = ParamGroup("ПАРАМЕТРЫ МОДЕЛИ")
        form = QFormLayout(pg)
        form.setContentsMargins(14, 18, 14, 14)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        def dbl(lo, hi, val, step, dec=2):
            w = QDoubleSpinBox()
            w.setRange(lo, hi); w.setValue(val)
            w.setSingleStep(step); w.setDecimals(dec)
            return w

        def intb(lo, hi, val):
            w = QSpinBox(); w.setRange(lo, hi); w.setValue(val); return w

        self.in_lmbda = dbl(0.1, 200, 10.0, 1.0)
        self.in_mu    = dbl(0.1, 200,  3.0, 0.5)
        self.in_c     = intb(1, 20,   3)
        self.in_k     = intb(1, 500, 10)
        self.in_theta = dbl(0.0, 20,  0.5, 0.1)
        self.in_n     = intb(100, 50000, 2000)

        def lbl(text, color):
            l = QLabel(text)
            l.setStyleSheet(
                f"color:{color};font-size:10px;"
                "font-weight:600;background:transparent;")
            return l

        form.addRow(lbl("Интенс. потока  λ", NEON_CYAN),  self.in_lmbda)
        form.addRow(lbl("Интенс. обслуж. μ", NEON_GREEN), self.in_mu)
        form.addRow(lbl("Число серверов  c", NEON_BLUE),  self.in_c)
        form.addRow(lbl("Ограничение  K",    NEON_PURP),  self.in_k)
        form.addRow(lbl("Нетерпение  θ",     NEON_AMBER), self.in_theta)
        form.addRow(lbl("Объём выборки  N",  TEXT_PRI),   self.in_n)

        # Кнопки управления
        cg      = ParamGroup("УПРАВЛЕНИЕ")
        cg_grid = QGridLayout(cg)
        cg_grid.setContentsMargins(10, 18, 10, 10)
        cg_grid.setSpacing(8)

        self.btn_start = NeonButton("▶  СТАРТ",     NEON_GREEN)
        self.btn_pause = NeonButton("⏸  ПАУЗА",     NEON_AMBER)
        self.btn_ff    = NeonButton("⚡  МГНОВЕННО", NEON_PURP)
        self.btn_reset = NeonButton("↺  СБРОС",      NEON_PINK)

        self.btn_start.clicked.connect(self._play)
        self.btn_pause.clicked.connect(self._pause)
        self.btn_ff.clicked.connect(self._fast_forward)
        self.btn_reset.clicked.connect(self._reset)

        cg_grid.addWidget(self.btn_start, 0, 0)
        cg_grid.addWidget(self.btn_pause, 0, 1)
        cg_grid.addWidget(self.btn_ff,    1, 0)
        cg_grid.addWidget(self.btn_reset, 1, 1)

        # Карточки метрик
        mg      = ParamGroup("МЕТРИКИ В РЕАЛЬНОМ ВРЕМЕНИ")
        mg_grid = QGridLayout(mg)
        mg_grid.setContentsMargins(8, 18, 8, 10)
        mg_grid.setSpacing(6)

        self.cards = {
            "arr":   MetricCard("ПОСТУПИЛО",       NEON_BLUE,  "→"),
            "proc":  MetricCard("ОБСЛУЖЕНО",        NEON_GREEN, "✓"),
            "rej":   MetricCard("ОТКАЗЫ",           NEON_PINK,  "✗"),
            "abn":   MetricCard("УХОДЫ",            NEON_AMBER, "⚠"),
            "p_rej": MetricCard("ВЕРОЯТН. ОТКАЗА",  NEON_PINK,  "%"),
            "p_abn": MetricCard("ВЕРОЯТН. УХОДА",   NEON_AMBER, "%"),
            "avg_q": MetricCard("СР. ОЧЕРЕДЬ",      NEON_PURP,  "Q"),
            "time":  MetricCard("ВР. СИСТЕМЫ (с)",  NEON_CYAN,  "⏱"),
        }

        pos = [(0,0),(0,1),(1,0),(1,1),(2,0),(2,1),(3,0),(3,1)]
        for (r_, c_), card in zip(pos, self.cards.values()):
            mg_grid.addWidget(card, r_, c_)

        left_lay.addWidget(pg)
        left_lay.addWidget(cg)
        left_lay.addWidget(mg)
        left_lay.addStretch()

        # ─── Правая колонка ───────────────────────────────────────────────────
        right     = QWidget()
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(10)

        # Визуализатор
        self.visualizer = FlowVisualizer()
        vis_frame = QFrame()
        vis_frame.setStyleSheet(f"""
            QFrame {{
                background: {BG_DEEP};
                border: 1px solid {BORDER};
                border-radius: 14px;
            }}
        """)
        shadow(vis_frame, r=18, a=85)
        vfl = QVBoxLayout(vis_frame)
        vfl.setContentsMargins(0, 0, 0, 0)
        vfl.addWidget(self.visualizer)

        # Графики
        charts_frame = QFrame()
        charts_frame.setStyleSheet(f"""
            QFrame {{
                background: {BG_PANEL};
                border: 1px solid {BORDER};
                border-radius: 14px;
            }}
        """)
        shadow(charts_frame, r=16, a=75)

        self.fig = Figure(facecolor=BG_PANEL)
        self.fig.subplots_adjust(
            left=0.07, right=0.97,
            bottom=0.14, top=0.88,
            wspace=0.28)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setStyleSheet("background:transparent;")

        self.ax_hist = self.fig.add_subplot(121)
        self.ax_poly = self.fig.add_subplot(122)
        self._style_axes()

        cfl = QVBoxLayout(charts_frame)
        cfl.setContentsMargins(6, 6, 6, 6)
        cfl.addWidget(self.canvas)

        right_lay.addWidget(vis_frame,    stretch=2)
        right_lay.addWidget(charts_frame, stretch=3)

        # Сплиттер
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([305, 1175])
        splitter.setHandleWidth(1)

        root_lay.addWidget(splitter)

    # ── Оформление осей ───────────────────────────────────────────────────────
    def _style_axes(self):
        TICK_C  = "#4a4a7a"
        SPINE_C = "#252550"
        GRID_C  = "#1a1a32"

        for ax in [self.ax_hist, self.ax_poly]:
            ax.set_facecolor("#0b0b1a")
            ax.tick_params(colors=TICK_C, labelsize=8)
            for sp in ["top", "right"]:
                ax.spines[sp].set_visible(False)
            for sp in ["left", "bottom"]:
                ax.spines[sp].set_color(SPINE_C)
                ax.spines[sp].set_linewidth(1)
            ax.grid(True, linestyle=":", alpha=0.3,
                    color=GRID_C, linewidth=0.8)

        self.ax_hist.set_title(
            "РАСПРЕДЕЛЕНИЕ ВРЕМЕНИ ОЖИДАНИЯ",
            color=TEXT_PRI, fontsize=9, fontweight="bold", pad=10)
        self.ax_hist.set_xlabel(
            "Время ожидания $t_w$ (сек)",
            color=TICK_C, fontsize=8)
        self.ax_hist.set_ylabel(
            "Плотность вероятности $f(t_w)$",
            color=TICK_C, fontsize=8)

        self.ax_poly.set_title(
            "ВЕРОЯТНОСТИ СОСТОЯНИЙ СИСТЕМЫ",
            color=TEXT_PRI, fontsize=9, fontweight="bold", pad=10)
        self.ax_poly.set_xlabel(
            "Число заявок в СМО $k$",
            color=TICK_C, fontsize=8)
        self.ax_poly.set_ylabel(
            "Вероятность $p_k$",
            color=TICK_C, fontsize=8)

    # ── Управление симуляцией ─────────────────────────────────────────────────
    def _reset(self):
        self.timer.stop()
        self.sim = MultiServerSimulator(
            self.in_lmbda.value(), self.in_mu.value(),
            self.in_c.value(),     self.in_k.value(),
            self.in_theta.value(), self.in_n.value()
        )
        self.ax_hist.clear()
        self.ax_poly.clear()
        self._style_axes()
        self.canvas.draw()
        self.visualizer.update_state(
            0, self.in_k.value(), [False] * self.in_c.value())
        self._update_cards()

    def _play(self):
        if self.sim is None or self.sim.is_finished:
            self._reset()
        self.timer.start(self.anim_speed)

    def _pause(self):
        self.timer.stop()

    def _fast_forward(self):
        if self.sim is None:
            self._reset()
        self.timer.stop()
        while not self.sim.is_finished:
            self.sim.step()
        self._refresh_ui()

    def _sim_step(self):
        if self.sim is None:
            return
        for _ in range(8):
            if not self.sim.step():
                self.timer.stop()
                self._refresh_ui()
                return
        self._refresh_ui()

    # ── Обновление UI ─────────────────────────────────────────────────────────
    def _refresh_ui(self):
        if self.sim is None:
            return

        srv = [s.is_busy for s in self.sim.servers]
        self.visualizer.update_state(
            len(self.sim.queue), self.sim.k, srv)

        self.ax_hist.clear()
        self.ax_poly.clear()
        self._style_axes()

        # ── Гистограмма ───────────────────────────────────────────────────────
        data = self.sim.wait_times_data
        if data:
            n_bins = min(30, max(8, len(data) // 40))
            n_vals, bins, patches = self.ax_hist.hist(
                data, bins=n_bins, density=True,
                edgecolor="#0b0b1a", linewidth=0.5, alpha=0)

            max_n = max(n_vals) if n_vals.max() > 0 else 1
            for patch, height in zip(patches, n_vals):
                t = height / max_n
                r_ = int(79  + t * (180 - 79))
                g_ = int(195 + t * (100 - 195))
                b_ = int(247 + t * (200 - 247))
                patch.set_facecolor(QColor(r_, g_, b_).name())
                patch.set_alpha(0.82)

            avg = sum(data) / len(data)
            self.ax_hist.axvline(
                avg, color=NEON_PINK,
                linestyle="--", linewidth=1.8, alpha=0.9,
                label=f"Среднее: {avg:.2f} с")

            # KDE
            if len(data) > 5:
                mn, mx = min(data), max(data)
                xs = [mn + (mx - mn) * i / 200 for i in range(201)]
                var = sum((x - avg)**2 for x in data) / len(data)
                bw  = max(1.06 * var**0.5 * len(data)**(-0.2), 1e-6)
                k   = 1.0 / (len(data) * bw * (2 * math.pi)**0.5)
                ys  = [k * sum(
                    math.exp(-0.5 * ((xi - d) / bw)**2)
                    for d in data) for xi in xs]
                self.ax_hist.plot(
                    xs, ys, color=NEON_CYAN,
                    linewidth=1.8, alpha=0.9, label="KDE")
                self.ax_hist.fill_between(
                    xs, ys, color=NEON_CYAN, alpha=0.06)

            self.ax_hist.legend(
                facecolor="#0d0d20", edgecolor=BORDER,
                labelcolor=TEXT_PRI, fontsize=8)

        # ── Полигон состояний ─────────────────────────────────────────────────
        sd = self.sim.state_durations
        T  = self.sim.current_time
        if sd and T > 0:
            states = sorted(sd.keys())
            probs  = [sd[s] / T for s in states]

            self.ax_poly.fill_between(
                states, probs, color=NEON_GREEN, alpha=0.08)
            self.ax_poly.plot(
                states, probs,
                color=NEON_GREEN, linewidth=2.2,
                marker="o", markersize=6,
                markerfacecolor=BG_DEEP,
                markeredgecolor=NEON_GREEN,
                markeredgewidth=2,
                label="$p_k$")

            for s, prob in zip(states, probs):
                self.ax_poly.plot(
                    [s, s], [0, prob],
                    color=NEON_GREEN, linewidth=0.6, alpha=0.28)

            max_p = max(probs)
            max_s = states[probs.index(max_p)]
            y_lim = self.ax_poly.get_ylim()[1]
            max_p = max(probs)
            max_s = states[probs.index(max_p)]
            y_lim = self.ax_poly.get_ylim()[1]

            # 1. Делаем отступ мощным (подберите коэффициент от 0.80 до 1.2, либо задайте константу)
            offset = (y_lim - max_p) * 0.95 

            self.ax_poly.annotate(
                f"p={max_p:.3f}",
                xy=(max_s, max_p),
                xytext=(max_s, max_p - offset),
                color=NEON_AMBER, fontsize=7, 
                ha="center", 
                va="top",         # <-- КРИТИЧНО: привязывает стрелку к верху текста, отодвигая буквы вниз
                arrowprops=dict(
                    arrowstyle="->",
                    color=NEON_AMBER, lw=1.1,
                    shrinkA=2,    # небольшой отступ от самого маркера
                    shrinkB=5     # небольшой отступ от текста, чтобы стрелка не липла к буквам
                )
            )

            self.ax_poly.set_xticks(
                range(int(min(states)), int(max(states)) + 1))
            self.ax_poly.legend(
                facecolor="#0d0d20", edgecolor=BORDER,
                labelcolor=TEXT_PRI, fontsize=8)

        self.canvas.draw()
        self._update_cards()

    def _update_cards(self):
        if not self.sim:
            return
        st = self.sim.get_stats()
        self.cards["arr"].set_value(st["arrived"])
        self.cards["proc"].set_value(st["processed"])
        self.cards["rej"].set_value(st["rejected"])
        self.cards["abn"].set_value(st["abandoned"])
        self.cards["p_rej"].set_value(f"{st['p_rej']:.1f}%")
        self.cards["p_abn"].set_value(f"{st['p_abn']:.1f}%")
        self.cards["avg_q"].set_value(f"{st['avg_q']:.2f}")
        self.cards["time"].set_value(f"{st['time']:.1f}")


# ── Точка входа ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = AdvancedSMOApp()
    w.show()
    sys.exit(app.exec())