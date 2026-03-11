import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import engine  # Подключаем ваш файл с логикой

# Настройка внешнего вида CustomTkinter
ctk.set_appearance_mode("Dark")  # Тёмная тема
ctk.set_default_color_theme("blue")  # Синие акценты

class LabApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Анализ датчиков случайных чисел")
        self.geometry("1300x850")
        self.minsize(1100, 700)

        # Создаем сетку: левая панель (статистика) и правая (графики)
        self.grid_columnconfigure(0, weight=0, minsize=400) # Фиксированная левая панель
        self.grid_columnconfigure(1, weight=1)              # Растягиваемая правая панель
        self.grid_rowconfigure(0, weight=1)

        # --- ЛЕВАЯ ПАНЕЛЬ (Меню и статистика) ---
        self.sidebar_frame = ctk.CTkScrollableFrame(self, corner_radius=0, fg_color="#1E1E1E")
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")

        # Заголовок
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Панель управления", font=ctk.CTkFont(size=24, weight="bold"))
        self.logo_label.pack(pady=(20, 20), padx=20)

        # Ввод размера выборки
        self.n_label = ctk.CTkLabel(self.sidebar_frame, text="Размер выборки (N):", font=ctk.CTkFont(size=14))
        self.n_label.pack(anchor="w", padx=20)
        
        self.n_entry = ctk.CTkEntry(self.sidebar_frame, placeholder_text="100000")
        self.n_entry.insert(0, "100000")
        self.n_entry.pack(fill="x", padx=20, pady=(0, 20))

        # Кнопка генерации
        self.generate_btn = ctk.CTkButton(self.sidebar_frame, text="Сгенерировать и проанализировать", 
                                          height=40, font=ctk.CTkFont(size=14, weight="bold"),
                                          command=self.run_analysis)
        self.generate_btn.pack(fill="x", padx=20, pady=(0, 20))

        # Карточки со статистикой
        self.stats_cards = {}
        
        # Теоретическая карточка
        self.create_stat_card("Теоретические значения", "theoretical", "#2B2B2B", ["mean", "variance"])
        # Карточка Custom (LCG)
        self.create_stat_card("Базовый датчик (LCG)", "custom", "#1E3D59", ["mean", "variance", "err_mean", "err_var"])
        # Карточка Встроенного (MT)
        self.create_stat_card("Встроенный датчик (MT)", "builtin", "#1E5939", ["mean", "variance", "err_mean", "err_var"])

        # --- ПРАВАЯ ПАНЕЛЬ (Графики) ---
        self.plot_frame = ctk.CTkFrame(self, fg_color="#242424", corner_radius=15)
        self.plot_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        # Настройка Matplotlib под тёмную тему
        plt.style.use('dark_background')
        self.figure = Figure(figsize=(8, 8), dpi=100)
        self.figure.patch.set_facecolor('#242424') # Цвет фона графика совпадает с рамкой

        self.canvas = FigureCanvasTkAgg(self.figure, self.plot_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

        # Инициализация пустым графиком
        self.ax1 = self.figure.add_subplot(211)
        self.ax2 = self.figure.add_subplot(212)
        self.figure.tight_layout(pad=3.0)

    def create_stat_card(self, title, key, bg_color, fields):
        """Создает красивую карточку для вывода статистики"""
        frame = ctk.CTkFrame(self.sidebar_frame, fg_color=bg_color, corner_radius=10)
        frame.pack(fill="x", padx=20, pady=10)
        
        title_label = ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=16, weight="bold"))
        title_label.pack(pady=(10, 5), padx=10, anchor="w")

        self.stats_cards[key] = {}
        
        for field in fields:
            text_name = {
                "mean": "Среднее:",
                "variance": "Дисперсия:",
                "err_mean": "Погрешность ср.:",
                "err_var": "Погрешность дисп.:"
            }[field]
            
            row = ctk.CTkFrame(frame, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=2)
            
            lbl_name = ctk.CTkLabel(row, text=text_name, font=ctk.CTkFont(size=13))
            lbl_name.pack(side="left")
            
            lbl_val = ctk.CTkLabel(row, text="—", font=ctk.CTkFont(size=13, family="Consolas", weight="bold"))
            lbl_val.pack(side="right")
            
            self.stats_cards[key][field] = lbl_val

    def run_analysis(self):
        """Запуск расчета и обновление интерфейса"""
        self.generate_btn.configure(state="disabled", text="Анализируем...")
        self.update()

        try:
            n = int(self.n_entry.get())
            if n <= 0: raise ValueError
        except ValueError:
            self.n_entry.delete(0, 'end')
            self.n_entry.insert(0, "100000")
            n = 100000

        # Получаем данные из вашего engine.py
        results = engine.get_analysis_results(n)

        # Обновляем текстовые значения в карточках
        self.update_card("theoretical", results["theoretical"])
        self.update_card("custom", results["custom"])
        self.update_card("builtin", results["builtin"])

        # Отрисовываем графики
        self.draw_plots(results)

        self.generate_btn.configure(state="normal", text="Сгенерировать и проанализировать")

    def update_card(self, key, data):
        """Обновляет цифры в нужной карточке"""
        for field, label in self.stats_cards[key].items():
            if field in data:
                # Форматируем красиво до 6 знаков (научный формат для малых погрешностей)
                val = data[field]
                if "err" in field and val < 0.0001:
                    formatted_val = f"{val:.2e}"
                else:
                    formatted_val = f"{val:.6f}"
                label.configure(text=formatted_val)

    def draw_plots(self, results):
        """Рисует гистограммы распределения"""
        data_custom = results['custom']['data']
        data_builtin = results['builtin']['data']

        self.ax1.clear()
        self.ax2.clear()

        # Гистограмма для базового генератора (LCG)
        self.ax1.hist(data_custom, bins=50, density=True, color='#4A90E2', alpha=0.8, edgecolor='black')
        self.ax1.axhline(1, color='#FF5252', linestyle='dashed', linewidth=2, label='Теоретическая плотность (U(0,1))')
        self.ax1.set_title("Плотность распределения: Базовый датчик (LCG)", fontsize=12, pad=10)
        self.ax1.set_xlim(0, 1)
        self.ax1.legend(loc="upper right")
        self.ax1.grid(color='#333333', linestyle='-', linewidth=0.5)

        # Гистограмма для встроенного генератора (MT)
        self.ax2.hist(data_builtin, bins=50, density=True, color='#50E3C2', alpha=0.8, edgecolor='black')
        self.ax2.axhline(1, color='#FF5252', linestyle='dashed', linewidth=2, label='Теоретическая плотность (U(0,1))')
        self.ax2.set_title("Плотность распределения: Встроенный датчик (Python MT)", fontsize=12, pad=10)
        self.ax2.set_xlim(0, 1)
        self.ax2.legend(loc="upper right")
        self.ax2.grid(color='#333333', linestyle='-', linewidth=0.5)

        self.figure.tight_layout(pad=3.0)
        self.canvas.draw()

if __name__ == "__main__":
    app = LabApp()
    app.mainloop()