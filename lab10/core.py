import math
import random
from collections import deque

def exp_time(rate: float) -> float:
    if rate <= 0:
        return float('inf')
    return -math.log(1.0 - random.random()) / rate

class Request:
    def __init__(self, id: int, arrival_time: float, max_patience: float):
        self.id = id
        self.arrival_time = arrival_time
        self.abandon_time = arrival_time + max_patience 
        self.start_service_time = None

class Server:
    def __init__(self, id: int):
        self.id = id
        self.is_busy = False
        self.current_request = None
        self.next_completion = float('inf')

    def get_next_event_time(self) -> float:
        return self.next_completion if self.is_busy else float('inf')

    def start_service(self, request: Request, current_time: float, mu: float):
        self.is_busy = True
        self.current_request = request
        self.current_request.start_service_time = current_time
        self.next_completion = current_time + exp_time(mu)

    def finish_service(self):
        self.is_busy = False
        req = self.current_request
        self.current_request = None
        self.next_completion = float('inf')
        return req

class MultiServerSimulator:
    def __init__(self, lmbda: float, mu: float, c: int, k: int, theta: float, total_requests: int):
        self.lmbda = lmbda          # Интенсивность входящего потока
        self.mu = mu                # Интенсивность обслуживания
        self.c = c                  # Количество каналов обслуживания
        self.k = k                  # Предельный размер очереди
        self.theta = theta          # Интенсивность ухода
        self.total_requests = total_requests

        self.current_time = 0.0
        self.servers = [Server(i) for i in range(c)]
        self.queue = deque()
        
        self.next_arrival = exp_time(self.lmbda)
        
        self.arrived_count = 0
        self.processed_count = 0
        self.rejected_count = 0     
        self.abandoned_count = 0    
        
        self.sum_wait_time = 0.0
        self.area_queue = 0.0
        self.last_event_time = 0.0
        
        self.wait_times_data = []
        self.state_durations = {}
        
        self.is_finished = False

    def get_free_server(self):
        for s in self.servers:
            if not s.is_busy:
                return s
        return None

    def step(self):
        if self.arrived_count >= self.total_requests and len(self.queue) == 0 and all(not s.is_busy for s in self.servers):
            self.is_finished = True
            return False

        t_arrival = self.next_arrival if self.arrived_count < self.total_requests else float('inf')
        t_completion = min((s.get_next_event_time() for s in self.servers), default=float('inf'))
        t_abandon = min((req.abandon_time for req in self.queue), default=float('inf'))

        next_time = min(t_arrival, t_completion, t_abandon)
        dt = next_time - self.last_event_time

        current_in_system = len(self.queue) + sum(1 for s in self.servers if s.is_busy)
        if dt > 0:
            self.state_durations[current_in_system] = self.state_durations.get(current_in_system, 0.0) + dt
            self.area_queue += len(self.queue) * dt

        self.last_event_time = next_time
        self.current_time = next_time

        if next_time == t_arrival:
            self._handle_arrival()
        elif next_time == t_completion:
            self._handle_completion()
        elif next_time == t_abandon:
            self._handle_abandon()

        return True

    def _handle_arrival(self):
        self.arrived_count += 1
        self.next_arrival = self.current_time + exp_time(self.lmbda)

        free_server = self.get_free_server()
        if free_server:
            req = Request(self.arrived_count, self.current_time, float('inf'))
            free_server.start_service(req, self.current_time, self.mu)
            self.wait_times_data.append(0.0)
        else:
            if len(self.queue) < self.k:
                patience = exp_time(self.theta) 
                req = Request(self.arrived_count, self.current_time, patience)
                self.queue.append(req)
            else:
                self.rejected_count += 1

    def _handle_completion(self):
        for s in self.servers:
            if abs(s.next_completion - self.current_time) < 1e-9:
                req = s.finish_service()
                self.processed_count += 1
                
                if self.queue:
                    next_req = self.queue.popleft()
                    wait_time = self.current_time - next_req.arrival_time
                    self.sum_wait_time += wait_time
                    self.wait_times_data.append(wait_time)
                    
                    s.start_service(next_req, self.current_time, self.mu)

    def _handle_abandon(self):
        for req in list(self.queue):
            if abs(req.abandon_time - self.current_time) < 1e-9:
                self.queue.remove(req)
                self.abandoned_count += 1
                
                # Заяка не дождалась обслуживания
                wait_time = self.current_time - req.arrival_time
                self.sum_wait_time += wait_time
                self.wait_times_data.append(wait_time)
                break

    def get_stats(self):
        p_rej = (self.rejected_count / self.arrived_count * 100) if self.arrived_count > 0 else 0.0
        p_abn = (self.abandoned_count / self.arrived_count * 100) if self.arrived_count > 0 else 0.0
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