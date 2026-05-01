import numpy as np
import math
from collections import Counter

def simulate_poisson_stream(lmbda, T):
    """Моделирует один прогон. Возвращает список моментов времени поступления заявок."""
    t = 0.0
    arrivals = []
    while True:
        t += -np.log(np.random.rand()) / lmbda
        if t > T:
            break
        arrivals.append(t)
    return arrivals

def get_theoretical_probs(lmbda, T, max_k):
    """Возвращает словарь с теоретическими вероятностями Пуассона до k = max_k"""
    mu = lmbda * T
    probs = {}
    for k in range(max_k + 1):
        try:
            probs[k] = (math.pow(mu, k) * math.exp(-mu)) / math.factorial(k)
        except OverflowError:
            probs[k] = 0.0
    return probs

def calculate_empirical_stats(all_counts):
    """Считает эмпирическое среднее, дисперсию и частоты"""
    emp_mean = np.mean(all_counts)
    emp_var = np.var(all_counts, ddof=1) if len(all_counts) > 1 else 0.0
    freqs = dict(Counter(all_counts))
    return emp_mean, emp_var, freqs