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
        if self.processed_requests >= self.total_requests:
            self.is_finished = True
            return False

        current_clients = self.queue_count + (1 if self.server_busy else 0)
        time_delta = self.current_time - self.last_event_time
        
        if current_clients not in self.state_times:
            self.state_times[current_clients] = 0.0
        self.state_times[current_clients] += time_delta

        self.area_queue += self.queue_count * time_delta
        self.last_event_time = self.current_time

        if self.next_arrival < self.next_completion:
            self.current_time = self.next_arrival
            
            if not self.server_busy:
                self.server_busy = True
                self.wait_times.append(0.0) 
                
                service_time = exp_time(self.mu)
                self.next_completion = self.current_time + service_time
            else:
                self.queue_count += 1
                self.arrival_times.append(self.current_time)
                
            self.next_arrival = self.current_time + exp_time(self.lmbda)
            
        else:
            self.current_time = self.next_completion
            self.processed_requests += 1
            
            if self.queue_count > 0:
                arrival = self.arrival_times.popleft()
                wait_time = self.current_time - arrival
                self.wait_times.append(wait_time)
                
                service_time = exp_time(self.mu)
                self.queue_count -= 1
                self.next_completion = self.current_time + service_time
            else:
                self.server_busy = False
                self.next_completion = float('inf')

        return True

    def get_stats(self):
        avg_wait = sum(self.wait_times) / len(self.wait_times) if self.wait_times else 0.0
        
        avg_q = self.area_queue / self.current_time if self.current_time > 0 else 0.0
        rho = self.lmbda / self.mu
        
        wait_threshold = 3.0 / self.mu if self.mu > 0 else 1.0
        long_waits = sum(1 for w in self.wait_times if w > wait_threshold)
        prob_long_wait = (long_waits / len(self.wait_times)) if self.wait_times else 0.0
        
        return {
            "avg_wait": avg_wait,
            "avg_q": avg_q,
            "rho": rho,
            "processed": self.processed_requests,
            "prob_long_wait": prob_long_wait,
            "wait_threshold": wait_threshold
        }