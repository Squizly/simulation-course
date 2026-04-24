import numpy as np
import random

class WeatherMarkovModel:
    def __init__(self):
        self.num_states = 3
        # Дефолтная матрица
        self.Q = np.zeros((3, 3))
        self.update_matrix(0.3, 0.1, 0.4, 0.4, 0.1, 0.4)
        self.reset()

    def update_matrix(self, q01, q02, q10, q12, q20, q21):
        self.Q = np.array([
            [-(q01 + q02), q01, q02],
            [q10, -(q10 + q12), q12],
            [q20, q21, -(q20 + q21)]
        ], dtype=float)
        
        self.theoretical_pi = self._calculate_theoretical_distribution()

    def _calculate_theoretical_distribution(self):
        """
        Вычисление теоретического стационарного распределения: pi * Q = 0, sum(pi) = 1.
        Используется метод наименьших квадратов (lstsq) для устойчивости к "плохим" матрицам.
        """
        A = np.vstack((self.Q.T, np.ones(self.num_states)))
        b = np.append(np.zeros(self.num_states), 1)
        
        # Решаем переопределенную систему
        pi, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
        
        # Защита от отрицательных значений (погрешности вычислений)
        pi = np.clip(pi, 0, 1)
        if np.sum(pi) > 0:
            pi = pi / np.sum(pi)
        return pi

    def reset(self):
        self.current_state = 0
        self.total_time = 0.0
        self.durations = np.zeros(self.num_states)

    def generate_next_transition(self):
        i = self.current_state
        q_ii = self.Q[i, i]
        
        if q_ii == 0:
            # Если интенсивность выхода = 0, это поглощающее состояние (остаемся в нем бесконечно)
            return float('inf'), i
            
        alpha = random.random()
        tau = np.log(alpha) / q_ii 
        
        probs = []
        states = []
        for j in range(self.num_states):
            if j != i:
                probs.append(-self.Q[i, j] / q_ii)
                states.append(j)
                
        next_state = random.choices(states, weights=probs, k=1)[0]
        return tau, next_state

    def apply_time_tick(self, dt):
        self.durations[self.current_state] += dt
        self.total_time += dt

    def set_state(self, new_state):
        self.current_state = new_state

    def get_empirical_distribution(self):
        if self.total_time == 0:
            return np.zeros(self.num_states)
        return self.durations / self.total_time