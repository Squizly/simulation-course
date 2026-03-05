import numpy as np
import math
import random

EMPTY = 0  
TREE = 1   
FIRE = 2   
WATER = 3  
ASH = 4    

class ForestFire:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = np.full((height, width), EMPTY, dtype=np.uint8)
        self.generation = 0
        
        self.wind_angle = random.uniform(0, 2 * math.pi)
        
        self.generate_water()
        self.generate_textures()
        self.generate_forest()

    def generate_water(self):
        noise = np.random.rand(self.height, self.width)
        for _ in range(8):
            N = np.roll(noise, 1, axis=0)
            S = np.roll(noise, -1, axis=0)
            E = np.roll(noise, 1, axis=1)
            W = np.roll(noise, -1, axis=1)
            noise = (noise + N + S + E + W) / 5.0
        self.grid[noise < 0.46] = WATER

    def generate_textures(self):
        h, w = self.height, self.width
        noise = np.random.randint(-15, 15, (h, w, 3), dtype=np.int16)
        
        base_soil = np.full((h, w, 3),[60, 45, 35], dtype=np.int16)
        self.tex_soil = np.clip(base_soil + noise, 0, 255).astype(np.uint8)
        
        base_water = np.full((h, w, 3),[25, 100, 180], dtype=np.int16)
        self.tex_water = np.clip(base_water + noise, 0, 255).astype(np.uint8)
        
        base_tree = np.full((h, w, 3),[34, 120, 50], dtype=np.int16)
        self.tex_tree = np.clip(base_tree + noise * 1.5, 0, 255).astype(np.uint8)
        
        base_ash = np.full((h, w, 3),[80, 80, 85], dtype=np.int16)
        self.tex_ash = np.clip(base_ash + noise, 0, 255).astype(np.uint8)

    def generate_forest(self):
        mask = (self.grid == EMPTY) & (np.random.rand(self.height, self.width) < 0.6)
        self.grid[mask] = TREE

    def update(self, p_grow, p_lightning, wind_strength, p_ash_clear):
        """Обновление поколений (Математика)"""
        # Плавающая погода: ветер плавно меняет направление
        self.wind_angle += random.uniform(-0.05, 0.05)
        
        # Векторы ветра
        wind_x = math.cos(self.wind_angle) * wind_strength
        wind_y = math.sin(self.wind_angle) * wind_strength

        # Маски текущих состояний
        is_tree = (self.grid == TREE)
        is_fire = (self.grid == FIRE)
        is_empty = (self.grid == EMPTY)
        is_ash = (self.grid == ASH)

        # Сдвиги матриц
        fire_N = np.roll(is_fire, 1, axis=0)  # Сосед СВЕРХУ
        fire_S = np.roll(is_fire, -1, axis=0) # Сосед СНИЗУ
        fire_E = np.roll(is_fire, 1, axis=1)  # Сосед СЛЕВА (Запад)
        fire_W = np.roll(is_fire, -1, axis=1) # Сосед СПРАВА (Восток)

        # Расчет вероятностей на основе векторов ветра
        p_base = 0.15 
        p_E = max(p_base, wind_x) if wind_x > 0 else p_base   # Шанс пойти на Восток
        p_W = max(p_base, -wind_x) if wind_x < 0 else p_base  # Шанс пойти на Запад
        p_S = max(p_base, wind_y) if wind_y > 0 else p_base   # Шанс пойти на Юг
        p_N = max(p_base, -wind_y) if wind_y < 0 else p_base  # Шанс пойти на Север

        # Если горит сосед СВЕРХУ (fire_N), огонь ползет ВНИЗ (на Юг) -> используем p_S
        rand_N = np.random.rand(self.height, self.width) < p_S 
        # Если горит сосед СНИЗУ (fire_S), огонь ползет ВВЕРХ (на Север) -> используем p_N
        rand_S = np.random.rand(self.height, self.width) < p_N 
        # Если горит сосед СЛЕВА (fire_E), огонь ползет ВПРАВО (на Восток) -> используем p_E
        rand_E = np.random.rand(self.height, self.width) < p_E 
        # Если горит сосед СПРАВА (fire_W), огонь ползет ВЛЕВО (на Запад) -> используем p_W
        rand_W = np.random.rand(self.height, self.width) < p_W 

        # Правила автомата
        ignite = (fire_N & rand_N) | (fire_S & rand_S) | (fire_E & rand_E) | (fire_W & rand_W)
        lightning = np.random.rand(self.height, self.width) < p_lightning
        grow = np.random.rand(self.height, self.width) < p_grow
        ash_clear = np.random.rand(self.height, self.width) < p_ash_clear

        # Применяем изменения
        new_grid = self.grid.copy()
        new_grid[is_fire] = ASH
        new_grid[is_ash & ash_clear] = EMPTY
        new_grid[is_tree & (ignite | lightning)] = FIRE
        new_grid[is_empty & grow] = TREE

        self.grid = new_grid
        self.generation += 1

    def ignite_at(self, x, y, radius=4):
        for iy in range(y - radius, y + radius):
            for ix in range(x - radius, x + radius):
                if 0 <= ix < self.width and 0 <= iy < self.height:
                    if (ix - x)**2 + (iy - y)**2 <= radius**2:
                        if self.grid[iy, ix] == TREE:
                            self.grid[iy, ix] = FIRE

    def get_render_image(self):
        img = self.tex_soil.copy()
        img[self.grid == WATER] = self.tex_water[self.grid == WATER]
        img[self.grid == TREE] = self.tex_tree[self.grid == TREE]
        img[self.grid == ASH] = self.tex_ash[self.grid == ASH]
        
        fire_mask = (self.grid == FIRE)
        if fire_mask.any():
            flicker = np.random.randint(-40, 40, (self.height, self.width, 3), dtype=np.int16)
            base_fire = np.full((self.height, self.width, 3),[255, 90, 20], dtype=np.int16)
            fire_colors = np.clip(base_fire + flicker, 0, 255).astype(np.uint8)
            img[fire_mask] = fire_colors[fire_mask]
            
        return img, fire_mask