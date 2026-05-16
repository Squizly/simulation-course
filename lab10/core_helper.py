import math
import random
from collections import deque

def exp_time(rate: float) -> float:
    """Генерирует случайное время по экспоненциальному закону."""
    if rate <= 0:
        return float('inf')
    # Формула обратного преобразования для генерации случайной величины
    return -math.log(1.0 - random.random()) / rate

class Request:
    """Класс Заявки (человек, клиент, пакет данных)."""
    def __init__(self, id: int, arrival_time: float, max_patience: float):
        self.id = id
        self.arrival_time = arrival_time
        
        # Время, когда терпение лопнет и клиент уйдет из очереди
        # = время прихода + сколько он готов ждать
        self.abandon_time = arrival_time + max_patience 
        
        # Запишем сюда время, когда его реально начнут обслуживать, 
        # чтобы потом точно посчитать время ожидания
        self.start_service_time = None 

class Server:
    """Класс Обслуживающего прибора (оператор, касса, сервер)."""
    def __init__(self, id: int):
        self.id = id
        self.is_busy = False           # false - свободен, true - занят
        self.current_request = None    # кого сейчас обслуживает
        self.next_completion = float('inf') # когда закончит обслуживать текущего чела

    def get_next_event_time(self) -> float:
        """ООП фишка: сервер сам говорит, когда у него следующее событие."""
        # Если занят - вернет время окончания, если свободен - бесконечность
        return self.next_completion if self.is_busy else float('inf')

    def start_service(self, request: Request, current_time: float, mu: float):
        """Начинаем обслуживать чела."""
        self.is_busy = True
        self.current_request = request
        self.current_request.start_service_time = current_time # запомнили, когда начали
        
        # Клиент уйдет = текущее время + сгенерированное время обслуги
        self.next_completion = current_time + exp_time(mu)

    def finish_service(self):
        """Заканчиваем обслуживание чела."""
        self.is_busy = False
        req = self.current_request
        self.current_request = None
        self.next_completion = float('inf') # Снова свободен (бесконечность)
        return req # возвращаем чела, чтобы собрать с него стату

class MultiServerSimulator:
    """Главный класс: Среда моделирования (Дискретно-событийный подход)."""
    def __init__(self, lmbda: float, mu: float, c: int, k: int, theta: float, total_requests: int):
        self.lmbda = lmbda          # Интенсивность поступления (λ)
        self.mu = mu                # Интенсивность обслуживания (μ)
        self.c = c                  # Количество каналов/операторов (c)
        self.k = k                  # Максимальная длина очереди (K)
        self.theta = theta          # Интенсивность ухода из очереди (θ) - нетерпение
        self.total_requests = total_requests

        # Состояние системы
        self.current_time = 0.0
        # Создаем список наших операторов (касс)
        self.servers = [Server(i) for i in range(c)]
        self.queue = deque()
        
        # Планировщик событий: генерим приход самого первого чела
        self.next_arrival = exp_time(self.lmbda)
        
        # Статистика общая
        self.arrived_count = 0      # сколько всего пришло
        self.processed_count = 0    # сколько успешно обслужили
        self.rejected_count = 0     # сколько получили отказ (очередь заполнена)
        self.abandoned_count = 0    # сколько ушли сами (не дождались в очереди)
        
        self.sum_wait_time = 0.0
        self.area_queue = 0.0       # площадь под графиком очереди (для средней очереди)
        self.last_event_time = 0.0
        
        # =-=-= =-=-= =-=-= ДЛЯ ГРАФИКОВ (Лаба 9) =-=-= =-=-= =-=-=
        self.wait_times_data = []      # складируем сюда время ожидания каждого для Гистограммы
        self.system_states_data = []   # складируем кол-во людей в системе для Полигона
        # =-=-= =-=-= =-=-= =-=-= =-=-= =-=-= =-=-= =-=-= =-=-= =-=-=
        
        self.is_finished = False

    def get_free_server(self):
        """Ищет первого свободного оператора."""
        for s in self.servers:
            if not s.is_busy:
                return s
        return None # если все заняты

    def step(self):
        """Шаг модельного времени (обрабатываем строго ОДНО ближайшее событие)."""
        
        # Условие выхода: все нужные люди пришли, очередь пустая и все операторы свободны
        if self.arrived_count >= self.total_requests and len(self.queue) == 0 and all(not s.is_busy for s in self.servers):
            self.is_finished = True
            return False

        # --- ШАГ 1: Ищем, какое событие произойдет раньше всего ---
        
        # 1. Когда придет следующий чел (если лимит исчерпан - ставим бесконечность)
        t_arrival = self.next_arrival if self.arrived_count < self.total_requests else float('inf')
        
        # 2. Когда освободится ближайший оператор (ищем минимальное время окончания среди всех)
        t_completion = min((s.get_next_event_time() for s in self.servers), default=float('inf'))
        
        # 3. Когда у кого-то в очереди лопнет терпение (ищем ближайший таймаут)
        t_abandon = min((req.abandon_time for req in self.queue), default=float('inf'))

        # Берем самое минимальное время из трех событий - это и есть наше "следующее событие"
        next_time = min(t_arrival, t_completion, t_abandon)

        # Считаем площадь для средней длины очереди (текущая длина * прошедшее время)
        self.area_queue += len(self.queue) * (next_time - self.last_event_time)
        
        # Перематываем время в момент наступления события
        self.last_event_time = next_time
        self.current_time = next_time

        # Считаем сколько сейчас всего людей в системе (в очереди + на операторах)
        current_in_system = len(self.queue) + sum(1 for s in self.servers if s.is_busy)
        # Закидываем в массив для графика Полигона частот
        self.system_states_data.append(current_in_system)

        # --- ШАГ 2: Выполняем то событие, которое наступило ---
        
        if next_time == t_arrival:
            self._handle_arrival()       # Пришел новый клиент
        elif next_time == t_completion:
            self._handle_completion()    # Оператор закончил работу
        elif next_time == t_abandon:
            self._handle_abandon()       # Клиент не дождался и ушел из очереди

        return True

    def _handle_arrival(self):
        """Событие: Появление нового клиента."""
        self.arrived_count += 1
        # Сразу планируем приход следующего (текущее время + случайный интервал)
        self.next_arrival = self.current_time + exp_time(self.lmbda)

        # Проверяем, есть ли свободный оператор
        free_server = self.get_free_server()
        if free_server:
            # Свободен -> идет сразу на обслуживание (терпение ставим бесконечное, т.к. очередь ему не грозит)
            req = Request(self.arrived_count, self.current_time, float('inf'))
            free_server.start_service(req, self.current_time, self.mu)
        else:
            # Все заняты -> пытаемся встать в очередь
            if len(self.queue) < self.k: # Проверяем, есть ли место в очереди
                # Генерим терпение (сколько он готов простоять)
                patience = exp_time(self.theta) 
                req = Request(self.arrived_count, self.current_time, patience)
                self.queue.append(req) # Встает в очередь
            else:
                # Мест в очереди нет -> клиент получает отказ и уходит навсегда
                self.rejected_count += 1 

    def _handle_completion(self):
        """Событие: Окончание обслуживания."""
        # Ищем того самого оператора (или операторов), который закончил работу именно сейчас
        for s in self.servers:
            if s.next_completion == self.current_time:
                req = s.finish_service() # Освобождаем его и забираем обслуженного чела
                self.processed_count += 1
                
                # Точный расчет времени ожидания в очереди: когда начал обслуживаться минус когда пришел
                wait_time = req.start_service_time - req.arrival_time
                self.sum_wait_time += wait_time
                self.wait_times_data.append(wait_time) # Сохраняем для гистограммы

                # Раз оператор освободился, нужно сразу взять следующего из очереди (если она есть)
                if self.queue:
                    next_req = self.queue.popleft() # Достаем первого
                    s.start_service(next_req, self.current_time, self.mu)

    def _handle_abandon(self):
        """Событие: Уход нетерпеливого клиента из очереди."""
        # Проходим по копии очереди (чтобы безопасно удалять элементы)
        for req in list(self.queue):
            # + 1e-9 - это защита от погрешностей типа float (чтобы 10.000000001 считалось как 10.0)
            if req.abandon_time <= self.current_time + 1e-9:
                self.queue.remove(req) # Убираем чела из очереди
                self.abandoned_count += 1
                
                # Он прождал ровно столько, сколько у него было терпения (от прихода до текущего момента)
                wait_time = self.current_time - req.arrival_time
                self.sum_wait_time += wait_time
                self.wait_times_data.append(wait_time) # Сохраняем для гистограммы
                break # Прерываем, так как за 1 шаг удаляем одного

    def get_stats(self):
        """Считает всю итоговую статистику для графического интерфейса."""
        # Процент отказов = (отказы / всего пришло) * 100
        p_rej = (self.rejected_count / self.arrived_count * 100) if self.arrived_count > 0 else 0.0
        # Процент уходов = (уходы / всего пришло) * 100
        p_abn = (self.abandoned_count / self.arrived_count * 100) if self.arrived_count > 0 else 0.0
        
        # Средняя длина очереди = интегральная площадь / время работы
        avg_q = self.area_queue / self.current_time if self.current_time > 0 else 0.0
        
        return {
            "arrived": self.arrived_count,
            "processed": self.processed_count,
            "rejected": self.rejected_count,
            "abandoned": self.abandoned_count,
            "p_rej": p_rej,
            "p_abn": p_abn,
            "avg_q": avg_q,
            "time": self.current_time
        }