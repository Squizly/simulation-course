import random
import math
import numpy as np
import scipy.stats as stats

class StatCore:
    # --- СЕКЦИЯ ДИСКРЕТНЫХ ВЕЛИЧИН ---
    @staticmethod
    def generate_drv(probabilities, values):
        """Метод рулетки для генерации ДСВ"""
        alpha = random.random()
        for p, v in zip(probabilities, values):
            alpha -= p
            if alpha <= 0:
                return v
        return values[-1]

    @staticmethod
    def get_theoretical_stats_discrete(probabilities, values):
        E_th = sum(p * x for p, x in zip(probabilities, values))
        D_th = sum(p * (x**2) for p, x in zip(probabilities, values)) - E_th**2
        return E_th, D_th

    def run_experiment_discrete(self, probabilities, values, N, alpha_significance=0.05):
        m = len(values)
        E_th, D_th = self.get_theoretical_stats_discrete(probabilities, values)

        counts = {x: 0 for x in values}
        for _ in range(N):
            x_val = self.generate_drv(probabilities, values)
            counts[x_val] += 1

        emp_probs = [counts[x] / N for x in values]

        E_emp = sum(p * x for p, x in zip(emp_probs, values))
        D_emp = sum(p * (x**2) for p, x in zip(emp_probs, values)) - E_emp**2

        err_E_rel = abs(E_emp - E_th) / abs(E_th) if E_th != 0 else 0
        err_D_rel = abs(D_emp - D_th) / abs(D_th) if D_th != 0 else 0

        chi_emp = sum((counts[values[i]]**2) / (N * probabilities[i]) for i in range(m)) - N
        df = m - 1 
        chi_crit = stats.chi2.ppf(1 - alpha_significance, df)

        return {
            "N": N, "values": values, "counts": [counts[x] for x in values], "emp_probs": emp_probs,
            "E_th": E_th, "E_emp": E_emp, "err_E_rel": err_E_rel,
            "D_th": D_th, "D_emp": D_emp, "err_D_rel": err_D_rel,
            "chi_emp": chi_emp, "chi_crit": chi_crit,
            "is_valid": chi_emp <= chi_crit
        }

    # --- СЕКЦИЯ НЕПРЕРЫВНЫХ ВЕЛИЧИН ---
    @staticmethod
    def generate_normal(mu, sigma):
        """Генерация нормальной СВ методом Бокса-Мюллера"""
        u1 = random.random()
        u2 = random.random()
        z0 = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
        return mu + z0 * sigma

    def run_experiment_normal(self, mu, sigma, N, alpha_significance=0.05):

        sample = [self.generate_normal(mu, sigma) for _ in range(N)]
        
        E_th = mu
        D_th = sigma**2
        
        E_emp = np.mean(sample)
        D_emp = np.var(sample)
        
        err_E = abs(E_emp - E_th) / abs(E_th) if E_th != 0 else abs(E_emp)
        err_D = abs(D_emp - D_th) / D_th
        
        k = int(1 + math.log2(N))
        counts, bin_edges = np.histogram(sample, bins=k)
        
        chi_emp = 0
        for i in range(k):
            p_i = stats.norm.cdf(bin_edges[i+1], mu, sigma) - stats.norm.cdf(bin_edges[i], mu, sigma)
            expected_count = N * p_i
            if expected_count > 0:
                chi_emp += ((counts[i] - expected_count)**2) / expected_count
                
        df = k - 1
        chi_crit = stats.chi2.ppf(1 - alpha_significance, df)
        
        return {
            "N": N,
            "E_emp": E_emp, "err_E": err_E,
            "D_emp": D_emp, "err_D": err_D,
            "chi_emp": chi_emp, "chi_crit": chi_crit,
            "is_valid": chi_emp <= chi_crit,
            "sample": sample,
            "E_th": E_th,
            "D_th": D_th
        }