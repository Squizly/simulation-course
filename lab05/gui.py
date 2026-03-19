import sys
import math
import random
import time
from PyQt6.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtGui import (QPainter, QColor, QRadialGradient, QLinearGradient, 
                         QFont, QTransform, QPolygonF)
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF
import core 

class Particle:
    def __init__(self, w, h):
        self.x = random.uniform(0, w)
        self.y = random.uniform(0, h)
        self.z = random.uniform(0.1, 2.0) 
        self.speed = random.uniform(0.2, 1.0)
        self.brightness = random.randint(100, 255)

    def update(self, h):
        self.y -= self.speed * self.z
        if self.y < 0: self.y = h

class BeautifulApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔮 Quantum Predictor & Stats Lab")
        self.resize(1000, 800)
        
        self.layout = QVBoxLayout(self)
        self.layout.addStretch()
        
        self.controls_panel = QHBoxLayout()
        
        self.label_n = QLabel("Объем выборки (N):")
        self.label_n.setStyleSheet("color: white; font-weight: bold;")
        
        self.input_n = QLineEdit()
        self.input_n.setText("10000")
        self.input_n.setFixedWidth(100)
        self.input_n.setStyleSheet("background: rgba(255,255,255,0.1); color: #00FFCC; border: 1px solid #00FFCC; padding: 5px;")
        
        self.btn_run = QPushButton("ЗАПУСТИТЬ ТЕСТ")
        self.btn_run.setStyleSheet("""
            QPushButton { background: #00FFCC; color: black; font-weight: bold; padding: 7px 15px; border-radius: 5px; }
            QPushButton:hover { background: #00CCAA; }
        """)
        self.btn_run.clicked.connect(self.start_simulation)
        
        self.controls_panel.addStretch()
        self.controls_panel.addWidget(self.label_n)
        self.controls_panel.addWidget(self.input_n)
        self.controls_panel.addWidget(self.btn_run)
        self.controls_panel.addStretch()
        
        self.layout.addLayout(self.controls_panel)

        self.timer = QTimer()
        self.timer.timeout.connect(self.game_loop)
        self.timer.start(16)
        
        self.mode = "8BALL" 
        self.particles = []
        self.show_stats = False
        
        self.stats_data = {"8BALL": None, "YESNO": None}
        self.n_vals = {"8BALL": 0, "YESNO": 0}
        
        self.ball_shake = 0
        self.ball_text = ""
        self.text_alpha = 0
        self.is_predicting = False
        self.prediction_timer = 0
        self.coin_rotation = 0
        self.coin_spin_speed = 0.5
        self.coin_text = "?"
        self.coin_color = QColor(255, 215, 0)
        self.is_flipping = False
        self.flip_duration = 0

    def start_simulation(self):
        """Метод вызывается при нажатии кнопки"""
        try:
            n = int(self.input_n.text())
            if n <= 0: return
        except:
            n = 10000
            
        self.stats_data[self.mode], self.n_vals[self.mode] = core.run_simulation(self.mode, n)
        self.show_stats = True

    def init_particles(self):
        if not self.particles:
            for _ in range(150):
                self.particles.append(Particle(self.width(), self.height()))

    def game_loop(self):
        self.init_particles()
        for p in self.particles: p.update(self.height())
            
        if self.is_predicting and self.mode == "8BALL":
            if self.prediction_timer > 0:
                self.ball_shake = random.uniform(-15, 15)
                self.prediction_timer -= 1
            else:
                self.ball_shake = 0
                self.is_predicting = False
                self.ball_text = core.get_magic_8_ball()
                self.text_alpha = 0
        
        if not self.is_predicting and self.text_alpha < 255 and self.ball_text:
            self.text_alpha = min(255, self.text_alpha + 5)

        if self.mode == "YESNO":
            if self.is_flipping:
                self.coin_spin_speed = min(30, self.coin_spin_speed + 2)
                self.flip_duration -= 1
                if self.flip_duration <= 0:
                    self.is_flipping = False
                    ans = core.get_yes_no()
                    self.coin_text = ans
                    self.coin_color = QColor(0, 255, 100) if ans == "ДА" else QColor(255, 50, 50)
            else:
                self.coin_spin_speed = max(0.5, self.coin_spin_speed - 0.5)
            self.coin_rotation += self.coin_spin_speed

        self.update()

    def mousePressEvent(self, event):
        if self.childAt(event.pos()): return 

        if self.show_stats:
            self.show_stats = False
            return

        w = self.width()
        if 20 <= event.pos().y() <= 60:
            self.mode = "8BALL" if event.pos().x() < w/2 else "YESNO"
            return

        if self.mode == "8BALL" and not self.is_predicting:
            self.is_predicting = True
            self.prediction_timer = 40
            self.ball_text = ""
        elif self.mode == "YESNO" and not self.is_flipping:
            self.is_flipping = True
            self.flip_duration = 60

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        bg_grad = QLinearGradient(0, 0, 0, self.height())
        bg_grad.setColorAt(0, QColor(10, 15, 30))
        bg_grad.setColorAt(1, QColor(40, 20, 60))
        painter.fillRect(self.rect(), bg_grad)

        for p in self.particles:
            painter.setPen(QColor(255, 255, 255, p.brightness))
            painter.drawEllipse(QPointF(p.x, p.y), p.z, p.z)

        self.draw_header(painter)

        painter.save()
        levitation = math.sin(time.time() * 2) * 15
        painter.translate(self.width() / 2, self.height() / 2 + levitation)
        if self.mode == "8BALL": self.draw_magic_ball(painter)
        else: self.draw_coin(painter)
        painter.restore()

        if self.show_stats and self.stats_data[self.mode]:
            self.draw_stats(painter)

    def draw_header(self, painter):
        w = self.width()
        painter.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        c1 = QColor(255,255,255) if self.mode == "8BALL" else QColor(100,100,150)
        c2 = QColor(255,255,255) if self.mode == "YESNO" else QColor(100,100,150)
        
        painter.setPen(c1)
        painter.drawText(QRectF(0, 20, w/2, 40), Qt.AlignmentFlag.AlignCenter, "MAGIC 8-BALL")
        painter.setPen(c2)
        painter.drawText(QRectF(w/2, 20, w/2, 40), Qt.AlignmentFlag.AlignCenter, "ДАТЧИК ДА/НЕТ")

    def draw_magic_ball(self, painter):
        radius = 130
        painter.translate(self.ball_shake, self.ball_shake)
        ball_grad = QRadialGradient(-30, -40, 150)
        ball_grad.setColorAt(0, QColor(60, 60, 80)); ball_grad.setColorAt(1, QColor(0,0,0))
        painter.setBrush(ball_grad); painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(0, 0), radius, radius)
        painter.setBrush(QColor(10, 10, 20))
        painter.drawEllipse(QPointF(0, 0), 70, 70)
        if self.ball_text:
            painter.setPen(QColor(255,255,255, self.text_alpha))
            painter.setFont(QFont("Arial", 8))
            painter.drawText(QRectF(-60, -30, 120, 60), Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, self.ball_text)

    def draw_coin(self, painter):
        radius = 100
        t = QTransform(); t.scale(math.cos(math.radians(self.coin_rotation)), 1.0)
        painter.setTransform(t, True)
        painter.setBrush(self.coin_color); painter.setPen(QColor(255,255,255))
        painter.drawEllipse(QPointF(0, 0), radius, radius)
        if abs(math.cos(math.radians(self.coin_rotation))) > 0.2:
            painter.setPen(QColor(0,0,0))
            painter.setFont(QFont("Impact", 30))
            painter.drawText(QRectF(-radius, -radius, radius*2, radius*2), Qt.AlignmentFlag.AlignCenter, self.coin_text)

    def draw_stats(self, painter):
        w, h = self.width(), self.height()
        painter.setBrush(QColor(0, 0, 0, 240))
        painter.drawRect(0, 0, w, h)
        
        painter.setPen(QColor(0, 255, 204))
        painter.setFont(QFont("Consolas", 10))
        
        stats = self.stats_data[self.mode]
        n = self.n_vals[self.mode]
        
        y = 120
        painter.drawText(50, 70, f"ОТЧЕТ ТЕСТИРОВАНИЯ [{self.mode}] | N = {n}")
        header = f"{'ОТВЕТ':<25} | {'n_k':<8} | {'p_emp':<8} | {'p_theo':<8} | {'ОШИБКА'}"
        painter.drawText(50, 100, header)
        painter.drawLine(50, 105, w-50, 105)

        for s in stats:
            if y > h - 100: break
            diff_color = QColor(0, 255, 100) if s['diff'] < (1/math.sqrt(n)) else QColor(255, 80, 80)
            painter.setPen(diff_color)
            line = f"{s['answer'][:23]:<25} | {s['count']:<8} | {s['p_empirical']:.4f} | {s['p_theory']:.4f} | {s['diff']:.5f}"
            painter.drawText(50, y, line)
            y += 22
        
        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(50, h-80, "Кликните в любом месте, чтобы закрыть отчет")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BeautifulApp()
    window.show()
    sys.exit(app.exec())