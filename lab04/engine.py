import random
import numpy as np

class CustomRNG:
    def __init__(self, seed=52):
        self.m = 2**31
        self.a = 1103515245
        self.c = 12345
        self.state = seed

    def next(self):
        self.state = (self.a * self.state + self.c) % self.m
        return self.state / self.m

    def generate(self, n):
        return np.array([self.next() for _ in range(n)])

def get_builtin_rng(n):
    return np.array([random.random() for _ in range(n)])

def calculate_stats(data):
    mean = np.mean(data)
    variance = np.var(data, ddof=1) 
    return mean, variance

THEORETICAL_MEAN = 0.5
THEORETICAL_VARIANCE = 1.0 / 12.0

def get_analysis_results(n=100000):
    custom_rng = CustomRNG()
    data_custom = custom_rng.generate(n)
    data_builtin = get_builtin_rng(n)

    mean_cust, var_cust = calculate_stats(data_custom)
    mean_built, var_built = calculate_stats(data_builtin)

    results = {
        'n': n,
        'theoretical': {
            'mean': THEORETICAL_MEAN,
            'variance': THEORETICAL_VARIANCE
        },
        'custom': {
            'data': data_custom,
            'mean': mean_cust,
            'variance': var_cust,
            'err_mean': abs(mean_cust - THEORETICAL_MEAN),
            'err_var': abs(var_cust - THEORETICAL_VARIANCE)
        },
        'builtin': {
            'data': data_builtin,
            'mean': mean_built,
            'variance': var_built,
            'err_mean': abs(mean_built - THEORETICAL_MEAN),
            'err_var': abs(var_built - THEORETICAL_VARIANCE)
        }
    }
    return results