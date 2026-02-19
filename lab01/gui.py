import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation
from typing import List

from simulation import BallisticSimulator, SimulationResult


class BallisticApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Моделирование полёта тела в атмосфере")
        self.root.geometry("1600x900")

        # Симулятор
        self.simulator = BallisticSimulator()
        self.results: List[SimulationResult] = []
        self.anim = None

        # Цвета для графиков
        self.colors = [
            "#007bff", "#dc3545", "#28a745", "#fd7e14",
            "#6f42c1", "#20c997", "#6610f2", "#e83e8c"
        ]
        self.color_index = 0

        # Построение интерфейса
        self.build_ui()

    def build_ui(self):
        main = ttk.Frame(self.root, padding=20)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="y", padx=(0, 20))

        right = ttk.Frame(main)
        right.pack(side="right", fill="both", expand=True)

        # Параметры запуска
        params_frame = tb.Labelframe(left, text="Параметры запуска", padding=15, bootstyle="primary")
        params_frame.pack(fill="x", pady=10)

        self.entries = {}
        default_params = [
            ("Начальная скорость (м/с)", 100.0),
            ("Угол запуска (°)", 45.0),
            ("Масса тела (кг)", 1.0),
            ("Плотность воздуха (кг/м³)", 1.29),
            ("Коэффициент сопротивления", 0.15),
            ("Площадь сечения (м²)", 0.01)
        ]

        for label, default in default_params:
            row = ttk.Frame(params_frame)
            row.pack(fill="x", pady=5)
            ttk.Label(row, text=label).pack(side="left")
            entry = ttk.Entry(row, width=12)
            entry.insert(0, str(default))
            entry.pack(side="right")
            self.entries[label] = entry

        ttk.Label(params_frame, text="Шаг моделирования (с)").pack(pady=(10, 0))
        self.dt_entry = ttk.Entry(params_frame, width=12)
        self.dt_entry.insert(0, "0.01")
        self.dt_entry.pack()

        # Кнопки
        btn_frame = ttk.Frame(left)
        btn_frame.pack(pady=20, fill="x")
        tb.Button(btn_frame, text="Запустить моделирование", bootstyle="success",
                  command=self.run_simulation).pack(fill="x", pady=5)
        tb.Button(btn_frame, text="Очистить результаты", bootstyle="danger",
                  command=self.clear_results).pack(fill="x", pady=5)

        # Информация
        info_frame = tb.Labelframe(left, text="Информация", padding=10, bootstyle="secondary")
        info_frame.pack(fill="x", pady=10)
        self.info_label = ttk.Label(info_frame, text="Моделирование не проводилось", justify="left")
        self.info_label.pack()

        # Графики
        graph_frame = tb.Labelframe(right, text="Графики", padding=10, bootstyle="primary")
        graph_frame.pack(fill="both", expand=True)
        self.figure = Figure(figsize=(10, 6), dpi=100)
        self.ax_traj = self.figure.add_subplot(211)
        self.ax_speed = self.figure.add_subplot(212)

        self.ax_traj.set_xlabel("Дальность, м")
        self.ax_traj.set_ylabel("Высота, м")
        self.ax_traj.grid(True, alpha=0.3)

        self.ax_speed.set_xlabel("Время, с")
        self.ax_speed.set_ylabel("Скорость, м/с")
        self.ax_speed.grid(True, alpha=0.3)

        self.canvas = FigureCanvasTkAgg(self.figure, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Таблица результатов
        table_frame = tb.Labelframe(right, text="Результаты моделирования", padding=10, bootstyle="secondary")
        table_frame.pack(fill="both", pady=10)
        columns = ("Шаг (с)", "Дальность (м)", "Макс. высота (м)", "Скорость в конце (м/с)", "Время полёта (с)")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=8)

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=150)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def get_parameters(self):
        try:
            return {
                'v0': float(self.entries["Начальная скорость (м/с)"].get()),
                'angle': float(self.entries["Угол запуска (°)"].get()),
                'mass': float(self.entries["Масса тела (кг)"].get()),
                'rho': float(self.entries["Плотность воздуха (кг/м³)"].get()),
                'Cd': float(self.entries["Коэффициент сопротивления"].get()),
                'A': float(self.entries["Площадь сечения (м²)"].get()),
                'dt': float(self.dt_entry.get())
            }
        except ValueError:
            messagebox.showerror("Ошибка", "Некорректные данные")
            return None

    def run_simulation(self):
        params = self.get_parameters()
        if params is None:
            return

        result = self.simulator.simulate(
            v0=params['v0'],
            angle=params['angle'],
            mass=params['mass'],
            rho=params['rho'],
            Cd=params['Cd'],
            A=params['A'],
            dt=params['dt']
        )

        self.results.append(result)
        self.animate_new_trajectory(result)
        self.update_table()
        self.update_info()

    def animate_new_trajectory(self, result: SimulationResult):
        xs = [p[0] for p in result.trajectory]
        ys = [p[1] for p in result.trajectory]
        speeds = result.speeds
        times = [i * result.dt for i in range(len(speeds))]

        color = self.colors[self.color_index % len(self.colors)]
        self.color_index += 1

        self.ax_speed.plot(times, speeds, color=color, linewidth=2, label=f"dt={result.dt}")
        self.ax_speed.legend()

        max_frames = 800
        n = len(xs)
        if n > max_frames:
            step = n // max_frames
            xs = xs[::step]
            ys = ys[::step]

        line, = self.ax_traj.plot([], [], color=color, linewidth=2, label=f"dt={result.dt}")
        self.ax_traj.legend()
        self.ax_traj.set_xlim(0, max(xs) * 1.05)
        self.ax_traj.set_ylim(0, max(ys) * 1.05)

        def animate(i):
            line.set_data(xs[:i], ys[:i])
            return line,

        if self.anim and self.anim.event_source:
            self.anim.event_source.stop()

        self.anim = FuncAnimation(
            self.figure,
            animate,
            frames=len(xs),
            interval=1,
            blit=True,
            repeat=False
        )

        self.canvas.draw()

    def update_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for r in self.results:
            flight_time = len(r.trajectory) * r.dt
            self.tree.insert("", "end", values=(
                f"{r.dt:.6f}",
                f"{r.range:.2f}",
                f"{r.max_height:.2f}",
                f"{r.final_speed:.2f}",
                f"{flight_time:.2f}"
            ))

    def update_info(self):
        if not self.results:
            self.info_label.config(text="Моделирование не проводилось")
            return

        r = self.results[-1]
        self.info_label.config(text=(
            f"Последнее моделирование:\n"
            f"Шаг: {r.dt:.6f} с\n"
            f"Дальность: {r.range:.2f} м\n"
            f"Макс. высота: {r.max_height:.2f} м\n"
            f"Скорость в конце: {r.final_speed:.2f} м/с"
        ))

    def clear_results(self):
        self.results.clear()
        self.color_index = 0

        self.ax_traj.clear()
        self.ax_speed.clear()

        self.ax_traj.set_xlabel("Дальность, м")
        self.ax_traj.set_ylabel("Высота, м")
        self.ax_traj.grid(True, alpha=0.3)

        self.ax_speed.set_xlabel("Время, с")
        self.ax_speed.set_ylabel("Скорость, м/с")
        self.ax_speed.grid(True, alpha=0.3)

        self.canvas.draw()
        self.update_table()
        self.update_info()
