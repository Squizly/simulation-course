import sys
import math
import random
import time
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import (QPainter, QColor, QRadialGradient, QLinearGradient, 
                         QFont, QTransform, QPainterPath, QPolygonF)
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF
import core  # Подключаем твою математику

class Particle:
    """Система частиц для космического фона"""
    def __init__(self, w, h):
        self.x = random.uniform(0, w)
        self.y = random.uniform(0, h)
        self.z = random.uniform(0.1, 2.0) # Для эффекта параллакса
        self.speed = random.uniform(0.2, 1.0)
        self.brightness = random.randint(100, 255)

    def update(self, h):
        self.y -= self.speed * self.z
        if self.y < 0:
            self.y = h

class BeautifulApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔮 Quantum Predictor Pro")
        self.resize(800, 600)
        self.setMinimumSize(600, 500)
        
        # Настройка игрового цикла (60 FPS)
        self.timer = QTimer()
        self.timer.timeout.connect(self.game_loop)
        self.timer.start(16)
        self.start_time = time.time()

        # Состояния
        self.mode = "8BALL" # "8BALL" или "YESNO"
        self.particles = []
        
        # Анимации шара 8
        self.ball_shake = 0
        self.ball_text = ""
        self.text_alpha = 0
        self.is_predicting = False
        self.prediction_timer = 0
        
        # Анимации монетки (Да/Нет)
        self.coin_rotation = 0
        self.coin_spin_speed = 0.5
        self.coin_text = "?"
        self.coin_color = QColor(255, 215, 0) # Золотой
        self.is_flipping = False
        self.flip_duration = 0

    def init_particles(self):
        if not self.particles:
            for _ in range(150):
                self.particles.append(Particle(self.width(), self.height()))

    def game_loop(self):
        """Главный цикл обновления"""
        self.init_particles()
        for p in self.particles:
            p.update(self.height())
            
        # Логика анимации Шара
        if self.is_predicting and self.mode == "8BALL":
            if self.prediction_timer > 0:
                self.ball_shake = random.uniform(-15, 15)
                self.prediction_timer -= 1
            else:
                self.ball_shake = 0
                self.is_predicting = False
                self.ball_text = core.get_magic_8_ball() # ВЫЗОВ CORE.PY
                self.text_alpha = 0
        
        if not self.is_predicting and self.text_alpha < 255 and self.ball_text:
            self.text_alpha = min(255, self.text_alpha + 5)

        # Логика анимации монетки (3D вращение)
        if self.mode == "YESNO":
            if self.is_flipping:
                self.coin_spin_speed = min(30, self.coin_spin_speed + 2)
                self.flip_duration -= 1
                self.coin_text = ""
                if self.flip_duration <= 0:
                    self.is_flipping = False
                    # ВЫЗОВ CORE.PY
                    ans = core.get_yes_no()
                    self.coin_text = ans
                    self.coin_color = QColor(0, 255, 100) if ans == "ДА" else QColor(255, 50, 50)
            else:
                self.coin_spin_speed = max(0.5, self.coin_spin_speed - 0.5)
            
            self.coin_rotation += self.coin_spin_speed
            if self.coin_rotation >= 360:
                self.coin_rotation -= 360

        self.update() # Запускает paintEvent

    def mousePressEvent(self, event):
        """Обработка кликов"""
        w = self.width()
        
        # Клик по переключателю режимов
        if 20 <= event.pos().y() <= 60:
            if event.pos().x() < w/2:
                self.mode = "8BALL"
            else:
                self.mode = "YESNO"
            return

        # Клик по центру (генерация)
        if self.mode == "8BALL" and not self.is_predicting:
            self.is_predicting = True
            self.prediction_timer = 40 # Длительность тряски
            self.text_alpha = 0
            self.ball_text = ""
        elif self.mode == "YESNO" and not self.is_flipping:
            self.is_flipping = True
            self.flip_duration = 60 # Длительность подброса
            self.coin_color = QColor(255, 215, 0) # Сброс цвета

    def paintEvent(self, event):
        """Сверхкрасивый рендеринг"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. Отрисовка космического фона (Градиент)
        bg_grad = QLinearGradient(0, 0, 0, self.height())
        bg_grad.setColorAt(0.0, QColor(10, 15, 30))
        bg_grad.setColorAt(1.0, QColor(40, 20, 60))
        painter.fillRect(self.rect(), bg_grad)

        # 2. Отрисовка звезд (Частицы)
        for p in self.particles:
            painter.setPen(QColor(255, 255, 255, p.brightness))
            painter.setBrush(QColor(255, 255, 255, p.brightness))
            painter.drawEllipse(QPointF(p.x, p.y), p.z, p.z)

        # 3. Отрисовка UI переключателя
        self.draw_ui(painter)

        # 4. Отрисовка основного объекта с эффектом левитации (синусоида)
        levitation = math.sin(time.time() * 2) * 15
        
        painter.translate(self.width() / 2, self.height() / 2 + levitation)

        if self.mode == "8BALL":
            self.draw_magic_ball(painter)
        else:
            self.draw_coin(painter)

    def draw_ui(self, painter):
        """Отрисовка переключателя сверху"""
        w = self.width()
        painter.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        
        # Кнопка 8-Ball
        c_ball = QColor(255, 255, 255) if self.mode == "8BALL" else QColor(100, 100, 150)
        painter.setPen(c_ball)
        painter.drawText(QRectF(0, 20, w/2, 40), Qt.AlignmentFlag.AlignCenter, "MAGIC 8-BALL")
        
        # Кнопка Да/Нет
        c_yesno = QColor(255, 255, 255) if self.mode == "YESNO" else QColor(100, 100, 150)
        painter.setPen(c_yesno)
        painter.drawText(QRectF(w/2, 20, w/2, 40), Qt.AlignmentFlag.AlignCenter, "ДАТЧИК ДА/НЕТ")

        # Линия
        painter.setPen(QColor(255, 255, 255, 50))
        painter.drawLine(int(w/2), 20, int(w/2), 60)

    def draw_magic_ball(self, painter):
        """Создание реалистичного 3D-шара"""
        radius = 150
        
        # Тряска
        painter.translate(self.ball_shake, self.ball_shake)

        # Свечение (Аура) за шаром
        aura = QRadialGradient(0, 0, radius * 1.5)
        aura.setColorAt(0, QColor(80, 0, 150, 100))
        aura.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(aura)
        painter.drawEllipse(QPointF(0, 0), radius * 1.5, radius * 1.5)

        # Сам шар (3D иллюзия светом)
        ball_grad = QRadialGradient(-radius*0.3, -radius*0.4, radius*1.2)
        ball_grad.setColorAt(0.0, QColor(100, 100, 120))  # Блик
        ball_grad.setColorAt(0.3, QColor(20, 20, 25))     # Основной цвет
        ball_grad.setColorAt(1.0, QColor(0, 0, 0))        # Тень
        
        painter.setBrush(ball_grad)
        painter.drawEllipse(QPointF(0, 0), radius, radius)

        # Окошко предсказания
        window_radius = 70
        window_grad = QRadialGradient(0, 0, window_radius)
        window_grad.setColorAt(0.0, QColor(10, 10, 20))
        window_grad.setColorAt(1.0, QColor(5, 5, 10))
        painter.setBrush(window_grad)
        painter.setPen(QColor(50, 50, 70))
        painter.drawEllipse(QPointF(0, 0), window_radius, window_radius)

        # Треугольник и текст внутри окошка
        if self.ball_text:
            # Треугольник
            poly = QPolygonF([QPointF(0, -50), QPointF(45, 40), QPointF(-45, 40)])
            tri_grad = QLinearGradient(0, -50, 0, 40)
            tri_grad.setColorAt(0, QColor(0, 100, 255, int(self.text_alpha * 0.7)))
            tri_grad.setColorAt(1, QColor(50, 0, 150, int(self.text_alpha * 0.7)))
            painter.setBrush(tri_grad)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPolygon(poly)

            # Текст предсказания
            painter.setPen(QColor(255, 255, 255, self.text_alpha))
            font = QFont("Arial", 10, QFont.Weight.Bold)
            painter.setFont(font)
            
            # Разбиваем текст на строки, если он длинный
            words = self.ball_text.split()
            lines, current_line = [], ""
            for word in words:
                if len(current_line + word) > 12:
                    lines.append(current_line)
                    current_line = word + " "
                else:
                    current_line += word + " "
            lines.append(current_line)

            y_offset = -10 + (len(lines) * -5)
            for line in lines:
                painter.drawText(QRectF(-window_radius, y_offset, window_radius*2, 20), 
                                 Qt.AlignmentFlag.AlignCenter, line.strip())
                y_offset += 15

    def draw_coin(self, painter):
        """Отрисовка 3D-монетки с перспективой"""
        radius = 120
        
        # Свечение монетки
        aura = QRadialGradient(0, 0, radius * 1.5)
        r, g, b = self.coin_color.red(), self.coin_color.green(), self.coin_color.blue()
        aura.setColorAt(0, QColor(r, g, b, 80))
        aura.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(aura)
        painter.drawEllipse(QPointF(0, 0), radius * 1.5, radius * 1.5)

        # Применяем 3D-трансформацию (Вращение по оси Y)
        transform = QTransform()
        # Имитация 3D перспективы: сужение по X при вращении
        scale_x = math.cos(math.radians(self.coin_rotation))
        transform.scale(scale_x, 1.0)
        painter.setTransform(transform, True)

        # Отрисовка самой монеты
        coin_grad = QLinearGradient(-radius, -radius, radius, radius)
        coin_grad.setColorAt(0, self.coin_color.lighter(150))
        coin_grad.setColorAt(1, self.coin_color.darker(200))
        
        painter.setBrush(coin_grad)
        painter.setPen(QColor(255, 255, 255, 150))
        painter.drawEllipse(QPointF(0, 0), radius, radius)

        # Внутренний контур
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QColor(0, 0, 0, 100))
        painter.drawEllipse(QPointF(0, 0), radius - 10, radius - 10)

        # Текст (Да/Нет)
        # Если монета повернута ребром, текст не рисуем, чтобы не было "зеркально"
        if abs(scale_x) > 0.1: 
            painter.setPen(QColor(0, 0, 0, 200))
            painter.setFont(QFont("Impact", 40))
            painter.drawText(QRectF(-radius, -radius, radius*2, radius*2), 
                             Qt.AlignmentFlag.AlignCenter, self.coin_text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Делаем приложение тёмным по умолчанию (на всякий случай)
    app.setStyle("Fusion")
    
    window = BeautifulApp()
    window.show()
    sys.exit(app.exec())