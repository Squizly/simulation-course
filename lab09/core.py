import math
import random

def exp_time(rate: float) -> float:
    return -math.log(1.0 - random.random()) / rate

class SMOSimulator:
    def __init__(self, lmbda: float, mu: float, total_requests: int):
        self.lmbda = lmbda
        self.mu = mu
        self.max_arrivals = total_requests

        # Состояние системы
        self.current_time = 0.0
        self.next_arrival = exp_time(self.lmbda)
        self.next_completion = float('inf')
        
        self.server_busy = False
        self.processed_requests = 0
        self.lost_requests = 0       
        self.arrivals_count = 0      
        
        self.state_times = {0: 0.0, 1: 0.0}
        self.last_event_time = 0.0
        self.service_times = []
        self.is_finished = False

    def step(self):
        if self.is_finished:
            return False

        current_state = 1 if self.server_busy else 0
        time_delta = self.current_time - self.last_event_time
        self.state_times[current_state] += time_delta
        self.last_event_time = self.current_time

        if self.arrivals_count >= self.max_arrivals and not self.server_busy:
            self.is_finished = True
            return False
        
        if self.next_arrival < self.next_completion:
            self.current_time = self.next_arrival
            self.arrivals_count += 1

            if not self.server_busy:
                self.server_busy = True
                service_time = exp_time(self.mu)
                self.service_times.append(service_time)
                self.next_completion = self.current_time + service_time
            else:
                self.lost_requests += 1

            if self.arrivals_count < self.max_arrivals:
                self.next_arrival = self.current_time + exp_time(self.lmbda)
            else:
                self.next_arrival = float('inf')
        else:
            self.current_time = self.next_completion
            self.processed_requests += 1
            self.server_busy = False
            self.next_completion = float('inf')

            if self.arrivals_count >= self.max_arrivals:
                self.is_finished = True
                return False

        return True

    def get_stats(self):
        total_time = self.current_time
        # Эмпирическая загрузка (доля времени, когда сервер занят)
        rho_emp = self.state_times[1] / total_time if total_time > 0 else 0.0

        # Вероятность отказа
        total_arrived = self.processed_requests + self.lost_requests
        p_reject = self.lost_requests / total_arrived if total_arrived > 0 else 0.0

        # Среднее время обслуживания (эмпирическое)
        avg_service_time = (sum(self.service_times) / len(self.service_times)
                            if self.service_times else 0.0)

        # Теоретическая загрузка (λ/μ)
        rho_theor = self.lmbda / self.mu

        return {
            "arrived": total_arrived,
            "processed": self.processed_requests,
            "lost": self.lost_requests,
            "p_reject": p_reject,
            "rho_emp": rho_emp,
            "rho_theor": rho_theor,
            "avg_service_time": avg_service_time,
            "total_time": total_time,
        }