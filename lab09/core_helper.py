import math
import random
from collections import deque

def exp_time(rate: float) -> float:
    return -math.log(1.0 - random.random()) / rate

class SMOSimulator:
    def __init__(self, lmbda: float, mu: float, total_requests: int):
        self.lmbda = lmbda
        self.mu = mu
        self.total_requests = total_requests

        # Состояние системы
        self.current_time = 0.0
        self.next_arrival = exp_time(self.lmbda)
        self.next_completion = float('inf')
        
        self.queue_count = 0
        self.processed_requests = 0
        self.server_busy = False     # false свободен, true занят
        
        self.area_queue = 0.0
        self.last_event_time = 0.0
        self.arrival_times = deque()
        
        # для графиков
        self.wait_times = []      # чел -> время ожидания
        self.state_times = {}     # колво челиков : время в этом состоянии
        self.is_finished = False

    def step(self):
        # если обслужили нужное количество людей -> выходим
        # количество обслуженных => требуемого количества
        if self.processed_requests >= self.total_requests:
            self.is_finished = True
            return False

        # сейчас в очереди = в очереди + 1 если оператор занят
        current_clients = self.queue_count + (1 if self.server_busy else 0)
        # сколько времени прошло с предыдущего события
        time_delta = self.current_time - self.last_event_time
        
        # =-=-= =-=-= =-=-= ДЛЯ ГРАФИКА =-=-= =-=-= =-=-= 
        # если такого количества людей еще не встречалось в словаре, добавляем
        if current_clients not in self.state_times:
            self.state_times[current_clients] = 0.0
        self.state_times[current_clients] += time_delta
        # =-=-= =-=-= =-=-= =-=-= =-=-= =-=-= =-=-= =-=-= 

        # Считаем площадь, длина очереди на прошедшее время
        self.area_queue += self.queue_count * time_delta
        # теперь текущее время становится прошлым для следующего шага
        self.last_event_time = self.current_time

        # придет новый чел < обслужить чела ?
        if self.next_arrival < self.next_completion:
            # текущее время = время прихода
            self.current_time = self.next_arrival
            
            # если сейчас никого не обслуживают
            if not self.server_busy:
                self.server_busy = True
                self.wait_times.append(0.0) 
                
                # время обслуживания
                service_time = exp_time(self.mu)
                # клиент уйдет = текущее время + время обслуги
                self.next_completion = self.current_time + service_time
            else:
                # Клиент встает в очередь
                self.queue_count += 1
                self.arrival_times.append(self.current_time)
                
            self.next_arrival = self.current_time + exp_time(self.lmbda)
            
        # завершится обслуживание
        else:
            # текущее время = клиент ушел
            self.current_time = self.next_completion
            self.processed_requests += 1
            
            # если очередь есть
            if self.queue_count > 0:
                # вытаскиваем первого чела из очереди, время кгд он в нее встал
                arrival = self.arrival_times.popleft()
                # время ожидания текущее время - время кгд он в нее встал
                wait_time = self.current_time - arrival
                # для этого клиента сохраняем время ожидания
                self.wait_times.append(wait_time)
                
                # генерим время на обслугу
                service_time = exp_time(self.mu)
                # уменьшаем очередь
                self.queue_count -= 1
                # время кгд уйдет новый чел = текущее время + время обслуги
                self.next_completion = self.current_time + service_time
            # очереди нет
            else:
                # оператор теперь свободен
                self.server_busy = False
                self.next_completion = float('inf')

        return True

    def get_stats(self):
        # среднее ожидание = сумма всех ожидания / колво людей
        avg_wait = sum(self.wait_times) / len(self.wait_times) if self.wait_times else 0.0
        
        # средняя очередь = площадь / текущее модальное время
        avg_q = self.area_queue / self.current_time if self.current_time > 0 else 0.0
        # теор нагрузка на оператора
        rho = self.lmbda / self.mu
        
        # превышение предела = 3 * среднее время обслуги
        wait_threshold = 3.0 / self.mu if self.mu > 0 else 1.0
        # по времени ходим, если он превысил предел ставим 1, считаем сколько их
        long_waits = sum(1 for w in self.wait_times if w > wait_threshold)
        # вероятность = число недовольных / общее число клиентов
        prob_long_wait = (long_waits / len(self.wait_times)) if self.wait_times else 0.0
        
        return {
            "avg_wait": avg_wait,
            "avg_q": avg_q,
            "rho": rho,
            "processed": self.processed_requests,
            "prob_long_wait": prob_long_wait,
            "wait_threshold": wait_threshold
        }