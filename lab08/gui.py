import sys
import math
import random
import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QFrame, QGridLayout, QMessageBox)
from PyQt6.QtCore import QTimer, Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QFont

from core import simulate_poisson_stream, get_theoretical_probs, calculate_empirical_stats

# --- Глобальная настройка графиков ---
pg.setConfigOptions(antialias=True)
pg.setConfigOption('background', '#0b0f19') # Глубокий космос
pg.setConfigOption('foreground', '#64748b')

class CyberCoreWidget(QWidget):
    """Визуализация Сервера как центрального Кибер-Ядра, принимающего запросы отовсюду."""
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(300)
        
        # Внутренний таймер исключительно для плавной отрисовки 60 FPS (вращение, затухание)
        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self.physics_step)
        self.anim_timer.start(16) # ~60 FPS
        
        self.rotation_angle = 0.0
        self.events_count = 0
        
        # Эффекты
        self.lasers = []    # Входящие лучи данных
        self.shockwaves = [] # Исходящие волны от сервера
        self.core_flash = 0.0 # Яркость центра

    def trigger_event(self, exact_count):
        """Вызывается строго в момент прихода заявки (синхронизировано с графиком)"""
        self.events_count = exact_count
        self.core_flash = 1.0
        
        # Луч летит со случайного угла
        angle = random.uniform(0, 2 * math.pi)
        self.lasers.append({
            'angle': angle,
            'alpha': 255.0,
            'length': random.randint(100, 200)
        })
        
        # Ударная волна
        self.shockwaves.append({'radius': 30.0, 'alpha': 200.0})

    def physics_step(self):
        """Обновление анимаций (не зависит от математического времени)"""
        self.rotation_angle = (self.rotation_angle + 1.5) % 360
        
        if self.core_flash > 0:
            self.core_flash = max(0, self.core_flash - 0.05)
            
        for l in self.lasers:
            l['alpha'] -= 15 # Скорость затухания луча
        self.lasers = [l for l in self.lasers if l['alpha'] > 0]
        
        for s in self.shockwaves:
            s['radius'] += 3.0
            s['alpha'] -= 5.0
        self.shockwaves = [s for s in self.shockwaves if s['alpha'] > 0]
        
        self.update()

    def reset(self):
        self.events_count = 0
        self.lasers.clear()
        self.shockwaves.clear()
        self.core_flash = 0.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        
        # Смещаем начало координат в центр
        painter.translate(cx, cy)
        
        # 1. Отрисовка летящих лучей (Lasers)
        for l in self.lasers:
            painter.save()
            painter.rotate(math.degrees(l['angle']))
            
            # Луч рисуется от края к центру
            grad = QLinearGradient(0, 0, l['length'], 0)
            grad.setColorAt(0, QColor(14, 165, 233, int(l['alpha']))) # Ядро (у центра)
            grad.setColorAt(1, QColor(14, 165, 233, 0)) # Хвост луча
            
            painter.setPen(QPen(QBrush(grad), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(35, 0, 35 + l['length'], 0)
            painter.restore()

        # 2. Отрисовка ударных волн (Shockwaves)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for s in self.shockwaves:
            painter.setPen(QPen(QColor(56, 189, 248, int(s['alpha'])), 2))
            painter.drawEllipse(QPointF(0, 0), s['radius'], s['radius'])

        # 3. Внешнее вращающееся кольцо (HUD-элемент)
        painter.save()
        painter.rotate(self.rotation_angle)
        painter.setPen(QPen(QColor(30, 41, 59), 4, Qt.PenStyle.DashLine))
        painter.drawEllipse(QPointF(0, 0), 55, 55)
        painter.setPen(QPen(QColor(14, 165, 233, 150), 4, Qt.PenStyle.SolidLine))
        painter.drawArc(QRectF(-55, -55, 110, 110), 0, 16 * 90) # Четверть круга
        painter.drawArc(QRectF(-55, -55, 110, 110), 16 * 180, 16 * 90)
        painter.restore()

        # Внутреннее кольцо (вращается в обратную сторону)
        painter.save()
        painter.rotate(-self.rotation_angle * 1.5)
        painter.setPen(QPen(QColor(16, 185, 129, 100), 2, Qt.PenStyle.DotLine))
        painter.drawEllipse(QPointF(0, 0), 45, 45)
        painter.restore()

        # 4. Центральное ядро (Сервер)
        flash_c = int(255 * self.core_flash)
        painter.setBrush(QBrush(QColor(15, 23, 42)))
        painter.setPen(QPen(QColor(56 + flash_c, 189 + flash_c//2, 248), 3 + self.core_flash * 2))
        painter.drawEllipse(QPointF(0, 0), 35, 35)

        # 5. Центральный счетчик заявок
        painter.setPen(QColor('#ffffff'))
        font = painter.font()
        font.setBold(True)
        font.setPointSize(16)
        painter.setFont(font)
        painter.drawText(QRectF(-35, -20, 70, 40), Qt.AlignmentFlag.AlignCenter, str(self.events_count))

        font.setPointSize(7)
        font.setBold(False)
        painter.setFont(font)
        painter.setPen(QColor('#38bdf8'))
        painter.drawText(QRectF(-35, 10, 70, 20), Qt.AlignmentFlag.AlignCenter, "ЗАЯВОК")

        painter.translate(-cx, -cy)


class PoissonApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pro Poisson Simulator : CyberCore")
        self.resize(1350, 900)
        self.setStyleSheet("""
            background-color: #0b0f19; 
            color: #f8fafc; 
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        """)

        self.timer = QTimer()
        self.timer.timeout.connect(self.timer_tick)
        self.params = {}

        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(25)

        # --- ЛЕВАЯ ПАНЕЛЬ ---
        left_panel = QFrame()
        left_panel.setFixedWidth(360)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(20)

        # Настройки
        settings_card = self.create_card(left_layout)
        settings_card.layout().addWidget(self.styled_label("Управление потоком", "#ffffff", True, 18))
        self.in_lmbda = self.create_input(settings_card.layout(), "Интенсивность λ:", "2.0")
        self.in_T = self.create_input(settings_card.layout(), "Интервал времени T:", "10.0")
        self.in_N = self.create_input(settings_card.layout(), "Число экспериментов N:", "1000")

        self.btn_run = QPushButton("ЗАПУСК СИМУЛЯЦИИ")
        self.btn_run.setStyleSheet("""
            QPushButton { background-color: #0ea5e9; color: white; font-weight: bold; font-size: 14px;
                          border-radius: 8px; padding: 15px; margin-top: 10px; letter-spacing: 1px;}
            QPushButton:hover { background-color: #0284c7; }
            QPushButton:disabled { background-color: #1e293b; color: #475569; }
        """)
        self.btn_run.clicked.connect(self.start_simulation)
        settings_card.layout().addWidget(self.btn_run)

        # Статистика (HUD-стайл)
        self.stats_card = self.create_card(left_layout)
        self.stats_card.layout().addWidget(self.styled_label("СТАТИСТИКА", "#ffffff", True, 18))

        # Блок Мат.Ожидания
        self.stats_card.layout().addWidget(self.styled_label("Математическое ожидание:", "#94a3b8", size=11))
        self.val_m = self.create_metric_row(self.stats_card.layout(), "Эмпирика", "Теория")
        
        # Блок Дисперсии
        self.stats_card.layout().addWidget(self.styled_label("Дисперсия потока:", "#94a3b8", size=11))
        self.val_v = self.create_metric_row(self.stats_card.layout(), "Эмпирика", "Теория")

        self.status_badge = QLabel("СИСТЕМА ГОТОВА К ЗАПУСКУ")
        self.status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_badge.setStyleSheet("background: #1e293b; color: #cbd5e1; border-radius: 8px; padding: 12px; font-weight: bold; margin-top: 15px; font-size: 13px;")
        self.stats_card.layout().addWidget(self.status_badge)
        left_layout.addStretch()

        # --- ПРАВАЯ ПАНЕЛЬ ---
        right_panel = QVBoxLayout()
        right_panel.setSpacing(20)
        
        self.anim_widget = CyberCoreWidget()
        right_panel.addWidget(self.anim_widget, stretch=1)

        # Графики в один слой
        graphs_layout = QHBoxLayout()
        graphs_layout.setSpacing(20)

        # График 1: Таймлайн
        self.plot_timeline = pg.PlotWidget(title="Временная развертка (Синхронно)")
        self.format_plot(self.plot_timeline, "Время (t)", "Суммарно заявок")
        self.time_scanner = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen(color='#10b981', width=2))
        self.plot_timeline.addItem(self.time_scanner)
        graphs_layout.addWidget(self.plot_timeline)

        # График 2: Гистограмма
        self.plot_hist = pg.PlotWidget(title="Распределение Пуассона")
        self.format_plot(self.plot_hist, "Количество заявок (k)", "Вероятность P(k)")
        self.plot_hist.addLegend(offset=(-10, 10))
        graphs_layout.addWidget(self.plot_hist)

        right_panel.addLayout(graphs_layout, stretch=2)
        layout.addWidget(left_panel)
        layout.addLayout(right_panel)

    def create_card(self, parent_layout):
        card = QFrame()
        card.setStyleSheet("QFrame { background-color: #0f172a; border: 1px solid #1e293b; border-radius: 16px; }")
        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(25, 25, 25, 25)
        parent_layout.addWidget(card)
        return card

    def create_input(self, layout, label, default):
        lbl = QLabel(label)
        lbl.setStyleSheet("color: #94a3b8; font-size: 13px; margin-top: 8px;")
        inp = QLineEdit(default)
        inp.setStyleSheet("QLineEdit { background: #0b0f19; border: 1px solid #334155; border-radius: 8px; padding: 10px; color: #38bdf8; font-weight: bold; font-size: 15px;} QLineEdit:focus { border: 1px solid #0ea5e9; }")
        layout.addWidget(lbl)
        layout.addWidget(inp)
        return inp

    def styled_label(self, text, color, bold=False, size=14):
        lbl = QLabel(text)
        w = "bold" if bold else "normal"
        lbl.setStyleSheet(f"color: {color}; font-weight: {w}; font-size: {size}px; background: transparent; border: none;")
        return lbl

    def create_metric_row(self, layout, name1, name2):
        row = QHBoxLayout()
        v1 = QLabel("0.000"); v1.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 18px;")
        v2 = QLabel("0.000"); v2.setStyleSheet("color: #f59e0b; font-weight: bold; font-size: 18px;")
        
        box1 = QVBoxLayout(); box1.addWidget(self.styled_label(name1, "#475569", size=10)); box1.addWidget(v1)
        box2 = QVBoxLayout(); box2.addWidget(self.styled_label(name2, "#475569", size=10)); box2.addWidget(v2)
        
        row.addLayout(box1); row.addLayout(box2)
        layout.addLayout(row)
        return v1, v2

    def format_plot(self, plot, xlabel, ylabel):
        plot.setLabel('bottom', xlabel, color='#64748b')
        plot.setLabel('left', ylabel, color='#64748b')
        plot.showGrid(x=True, y=True, alpha=0.1)
        plot.getAxis('bottom').setPen(pg.mkPen(color='#1e293b', width=2))
        plot.getAxis('left').setPen(pg.mkPen(color='#1e293b', width=2))
        plot.getAxis('bottom').setTextPen('#94a3b8')
        plot.getAxis('left').setTextPen('#94a3b8')

    def start_simulation(self):
        try:
            self.params['lmbda'] = float(self.in_lmbda.text())
            self.params['T'] = float(self.in_T.text())
            self.params['N'] = int(self.in_N.text())
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Некорректный ввод!")
            return

        self.btn_run.setEnabled(False)
        self.status_badge.setStyleSheet("background: #0ea5e9; color: #ffffff; border-radius: 8px; padding: 12px; font-weight: bold;")
        self.status_badge.setText("АКТИВЕН СБОР ДАННЫХ...")
        
        self.plot_timeline.clear()
        self.plot_hist.clear()
        self.plot_timeline.addItem(self.time_scanner)
        self.anim_widget.reset()

        self.current_run_arrivals = simulate_poisson_stream(self.params['lmbda'], self.params['T'])
        self.arrival_index = 0
        self.current_t = 0.0
        
        # Красивый таймлайн (Градиент под кривой)
        self.timeline_curve = pg.PlotDataItem(pen=pg.mkPen(color='#38bdf8', width=3))
        self.timeline_fill = pg.FillBetweenItem(self.timeline_curve, pg.PlotCurveItem(x=[0], y=[0]), brush=pg.mkBrush(56, 189, 248, 30))
        self.plot_timeline.addItem(self.timeline_curve)
        self.plot_timeline.addItem(self.timeline_fill)
        self.plot_timeline.setXRange(0, self.params['T'])

        self.t_data, self.y_data = [0.0], [0]
        
        fps, duration = 60, 4.0
        self.dt = self.params['T'] / (fps * duration)
        self.timer.start(int(1000 / fps))

    def timer_tick(self):
        self.current_t += self.dt
        self.time_scanner.setPos(self.current_t)

        while self.arrival_index < len(self.current_run_arrivals) and self.current_run_arrivals[self.arrival_index] <= self.current_t:
            arr_time = self.current_run_arrivals[self.arrival_index]
            self.t_data.extend([arr_time, arr_time])
            self.y_data.extend([self.y_data[-1], self.y_data[-1] + 1])
            
            # ТРИГГЕР ВИЗУАЛА (Синхронизация идеальная)
            self.anim_widget.trigger_event(self.y_data[-1])
            self.arrival_index += 1

        cur_t_plot = self.t_data + [self.current_t]
        cur_y_plot = self.y_data + [self.y_data[-1]]
        self.timeline_curve.setData(cur_t_plot, cur_y_plot)
        base_curve = pg.PlotCurveItem(x=cur_t_plot, y=[0]*len(cur_t_plot))
        self.timeline_fill.setCurves(self.timeline_curve, base_curve)

        if self.current_t >= self.params['T']:
            self.timer.stop()
            self.time_scanner.setPos(self.params['T'])
            self.finish_simulation()

    def finish_simulation(self):
        self.status_badge.setText("АНАЛИЗ N ЭКСПЕРИМЕНТОВ...")
        QApplication.processEvents()

        lmbda, T, N = self.params['lmbda'], self.params['T'], self.params['N']
        all_counts = [len(self.current_run_arrivals)]
        for _ in range(N - 1):
            all_counts.append(len(simulate_poisson_stream(lmbda, T)))

        emp_mean, emp_var, freqs = calculate_empirical_stats(all_counts)
        max_k = max(all_counts) if all_counts else 0
        theo_probs = get_theoretical_probs(lmbda, T, max_k)

        self.draw_histogram(N, max_k, freqs, theo_probs)

        theo_mean = theo_var = lmbda * T
        
        self.val_m[0].setText(f"{emp_mean:.4f}"); self.val_m[1].setText(f"{theo_mean:.4f}")
        self.val_v[0].setText(f"{emp_var:.4f}"); self.val_v[1].setText(f"{theo_var:.4f}")

        # Проверка Пуассоновской гипотезы
        if abs(emp_mean - theo_mean) / theo_mean < 0.1 and abs(emp_var - theo_var) / theo_var < 0.2:
            self.status_badge.setStyleSheet("background: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid #10b981; border-radius: 8px; padding: 12px;")
            self.status_badge.setText("✔ Пуассоновский характер подтвержден")
        else:
            self.status_badge.setStyleSheet("background: rgba(245, 158, 11, 0.2); color: #f59e0b; border: 1px solid #f59e0b; border-radius: 8px; padding: 12px;")
            self.status_badge.setText("⚠ Низкая точность (Увеличьте N)")

        self.btn_run.setEnabled(True)

    def draw_histogram(self, N, max_k, freqs, theo_probs):
        x = np.arange(max_k + 2)
        y_emp = np.array([freqs.get(k, 0) / N for k in x])
        y_theo = np.array([theo_probs.get(k, 0) for k in x])

        # Эмпирика: Синие полупрозрачные столбцы
        bar_item = pg.BarGraphItem(x=x, height=y_emp, width=0.6, brush=pg.mkBrush(14, 165, 233, 180), pen=pg.mkPen('#bae6fd', width=1), name="Имитация")
        self.plot_hist.addItem(bar_item)

        # Теория: Оранжевая линия
        self.plot_hist.plot(x, y_theo, pen=pg.mkPen(color='#f59e0b', width=3), symbol='o', symbolSize=8, symbolBrush='#0b0f19', symbolPen=pg.mkPen('#f59e0b', width=2), name="Теория Пуассона")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setFont(QFont("Helvetica", 12))
    window = PoissonApp()
    window.show()
    sys.exit(app.exec())