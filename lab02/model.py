import numpy as np
from numba import jit

@jit(nopython=True)
def simulate(rho, c, lam, Ta, Tn, T0, L, h, total_time, tau):
    Nx = int(round(L / h))
    if Nx < 2: Nx = 2

    h = L / Nx
    
    steps_n = int(round(total_time / tau))
    if steps_n < 1: steps_n = 1

    T = np.full(Nx + 1, float(T0))
    T[0] = float(Ta)
    T[Nx] = float(Tn)

    A_i = lam / h**2
    C_i = A_i
    B_i = (2 * lam / h**2) + (rho * c / tau)

    alpha = np.zeros(Nx + 1)
    beta = np.zeros(Nx + 1)

    for n in range(steps_n):
        alpha[0] = 0.0
        beta[0] = float(Ta)

        for i in range(1, Nx):
            F_i = -(rho * c / tau) * T[i]

            denom = B_i - C_i * alpha[i - 1]

            alpha[i] = A_i / denom
            beta[i] = (C_i * beta[i - 1] - F_i) / denom

        T_next = np.empty(Nx + 1)
        T_next[Nx] = float(Tn)
        T_next[0] = float(Ta)

        for i in range(Nx - 1, 0, -1):
            T_next[i] = alpha[i] * T_next[i + 1] + beta[i]
        
        T = T_next

    return T, T[Nx // 2]


# ТОЖЕ САМОЕ ДЛЯ GUI
@jit(nopython=True)
def calculate_next_step(T, alpha, beta, A_i, B_i, C_i, Nx, rho, c, tau, Ta, Tn):
    alpha[0] = 0.0
    beta[0] = float(Ta)

    for i in range(1, Nx):
        F_i = -(rho * c / tau) * T[i]
        denom = B_i - C_i * alpha[i - 1]
        alpha[i] = A_i / denom
        beta[i] = (C_i * beta[i - 1] - F_i) / denom

    T_next = np.empty(Nx + 1)
    T_next[Nx] = float(Tn)
    T_next[0] = float(Ta)

    for i in range(Nx - 1, 0, -1):
        T_next[i] = alpha[i] * T_next[i + 1] + beta[i]

    return T_next