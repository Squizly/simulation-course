import numpy as np
from numba import jit

@jit(nopython=True)
def simulate(rho, c, lam, Tl, Tr, T0, L, h, total_time, dt):
    Nx = int(round(L / h)) 
    if Nx < 2: Nx = 2
    dx = L / Nx
    Nt = int(round(total_time / dt))
    if Nt < 1: Nt = 1

    T = np.full(Nx + 1, float(T0))
    T[0] = float(Tl)
    T[-1] = float(Tr)

    # Коэффициенты для системы уравнений
    A = lam / dx**2
    C = A
    B = 2 * lam / dx**2 + rho * c / dt

    alpha = np.zeros(Nx + 1)
    beta = np.zeros(Nx + 1)

    for _ in range(Nt):
        alpha[0] = 0.0
        beta[0] = float(Tl)

        for i in range(1, Nx):
            Fi = -(rho * c / dt) * T[i]
            denom = B - C * alpha[i - 1]
            alpha[i] = A / denom
            beta[i] = (C * beta[i - 1] - Fi) / denom

        T_new = np.empty(Nx + 1)
        T_new[0] = float(Tl)
        T_new[-1] = float(Tr)

        for i in range(Nx - 1, 0, -1):
            T_new[i] = alpha[i] * T_new[i + 1] + beta[i]
        T = T_new

    return T, T[Nx // 2]

@jit(nopython=True)
def calculate_next_step(T, alpha, beta, A, B, C, Nx, rho, c, dt, Tl, Tr):
    # Один шаг для анимации
    alpha[0] = 0.0
    beta[0] = float(Tl)

    for i in range(1, Nx):
        Fi = -(rho * c / dt) * T[i]
        denom = B - C * alpha[i - 1]
        alpha[i] = A / denom
        beta[i] = (C * beta[i - 1] - Fi) / denom

    T_new = np.empty(Nx + 1)
    T_new[0] = float(Tl)
    T_new[-1] = float(Tr)

    for i in range(Nx - 1, 0, -1):
        T_new[i] = alpha[i] * T_new[i + 1] + beta[i]

    return T_new