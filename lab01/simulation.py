import math
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class SimulationResult:
    dt: float
    trajectory: List[Tuple[float, float]]
    speeds: List[float]
    range: float
    max_height: float
    final_speed: float


class BallisticSimulator:
    def __init__(self, g: float = 9.81):
        self.g = g

    def simulate(self, v0: float, angle: float, mass: float, rho: float,
                 Cd: float, A: float, dt: float) -> SimulationResult:

        angle_rad = angle * math.pi / 180
        x, y = 0.0, 0.0

        vx = v0 * math.cos(angle_rad)
        vy = v0 * math.sin(angle_rad)

        k = 0.5 * rho * Cd * A / mass

        trajectory = [(x, y)]
        speeds = [v0]
        t = 0.0
        max_height = 0.0

        while y >= 0:

            t += dt
            v = math.sqrt(vx ** 2 + vy ** 2)

            vx = vx - k * vx * v * dt
            vy = vy - (self.g + k * vy * v) * dt

            x = x + vx * dt
            y = y + vy * dt

            trajectory.append((x, y))
            speeds.append(math.sqrt(vx * vx + vy * vy))

            if y > max_height:
                max_height = y

        return SimulationResult(
            dt=dt,
            trajectory=trajectory,
            speeds=speeds,
            range=x,
            max_height=max_height,
            final_speed=speeds[-1]
        )
