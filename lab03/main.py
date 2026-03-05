import pygame
import numpy as np
import math
from simulation import ForestFire, EMPTY, TREE, FIRE, WATER, ASH

# --- Настройки окна ---
SIM_WIDTH = 900
SIM_HEIGHT = 700
UI_WIDTH = 380
WINDOW_WIDTH = SIM_WIDTH + UI_WIDTH
WINDOW_HEIGHT = SIM_HEIGHT

CELL_SIZE = 5
GRID_W = SIM_WIDTH // CELL_SIZE
GRID_H = SIM_HEIGHT // CELL_SIZE
FPS = 60

BG_COLOR = (18, 18, 24)
PANEL_COLOR = (28, 28, 38)
TEXT_COLOR = (230, 230, 240)
ACCENT_COLOR = (0, 212, 255)
FIRE_ACCENT = (255, 100, 50)
BUTTON_COLOR = (50, 50, 65)
BUTTON_HOVER = (80, 80, 100)

class Slider:
    def __init__(self, x, y, w, h, min_val, max_val, start_val, text, format_str="{:.3f}"):
        self.rect = pygame.Rect(x, y, w, h)
        self.min_val = min_val
        self.max_val = max_val
        self.val = start_val
        self.text = text
        self.format_str = format_str
        self.dragging = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos) or \
               math.hypot(event.pos[0] - self.get_handle_x(), event.pos[1] - self.rect.centery) < 15:
                self.dragging = True
                self.update_val(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.update_val(event.pos[0])

    def update_val(self, mouse_x):
        rel_x = max(0, min(mouse_x - self.rect.x, self.rect.width))
        self.val = self.min_val + (rel_x / self.rect.width) * (self.max_val - self.min_val)

    def get_handle_x(self):
        return self.rect.x + int((self.val - self.min_val) / (self.max_val - self.min_val) * self.rect.width)

    def draw(self, screen, font):
        label = font.render(self.text, True, TEXT_COLOR)
        val_text = font.render(self.format_str.format(self.val), True, ACCENT_COLOR)
        screen.blit(label, (self.rect.x, self.rect.y - 25))
        screen.blit(val_text, (self.rect.right - val_text.get_width(), self.rect.y - 25))
        
        pygame.draw.rect(screen, (15, 15, 20), self.rect.move(0, 2), border_radius=self.rect.height//2)
        pygame.draw.rect(screen, (60, 60, 75), self.rect, border_radius=self.rect.height//2)
        
        fill_w = self.get_handle_x() - self.rect.x
        if fill_w > 0:
            fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_w, self.rect.height)
            pygame.draw.rect(screen, ACCENT_COLOR, fill_rect, border_radius=self.rect.height//2)
            
        handle_x = self.get_handle_x()
        pygame.draw.circle(screen, (255, 255, 255), (handle_x, self.rect.centery), self.rect.height + 3)
        pygame.draw.circle(screen, ACCENT_COLOR, (handle_x, self.rect.centery), self.rect.height - 1)

class Button:
    def __init__(self, x, y, w, h, text, color=BUTTON_COLOR):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.base_color = color
        self.color = color
        self.is_hovered = False

    def draw(self, screen, font):
        pygame.draw.rect(screen, (15, 15, 20), self.rect.move(0, 4), border_radius=8)
        pygame.draw.rect(screen, self.color, self.rect, border_radius=8)
        text_surf = font.render(self.text, True, (255, 255, 255))
        screen.blit(text_surf, text_surf.get_rect(center=self.rect.center))

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
            self.color = BUTTON_HOVER if self.is_hovered else self.base_color
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                return True
        return False

def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF)
    pygame.display.set_caption("Лесные пожары: Advanced Edition")
    clock = pygame.time.Clock()
    
    font_main = pygame.font.SysFont("Segoe UI, Helvetica", 14, bold=True)
    font_title = pygame.font.SysFont("Segoe UI, Helvetica", 22, bold=True)
    font_stats = pygame.font.SysFont("Consolas, Courier", 14)

    sim = ForestFire(GRID_W, GRID_H)
    running = True
    paused = False

    ui_x = SIM_WIDTH + 25
    
    sliders =[
        Slider(ui_x, 80, 330, 8, 0.0, 0.1, 0.015, "Рост деревьев (p)"),
        Slider(ui_x, 145, 330, 8, 0.0, 0.001, 0.0001, "Удар молнии (f)", "{:.5f}"),
        Slider(ui_x, 210, 330, 8, 0.0, 1.0, 0.8, "Сила ветра", "{:.2f}"),
        Slider(ui_x, 395, 330, 8, 0.0, 0.5, 0.03, "Остывание пепла", "{:.3f}")
    ]
    
    btn_pause = Button(ui_x, 445, 155, 45, "ПАУЗА / ПУСК")
    btn_reset = Button(ui_x + 175, 445, 155, 45, "НОВЫЙ МИР", color=(180, 60, 60))

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            for slider in sliders:
                slider.handle_event(event)
            
            if btn_pause.handle_event(event):
                paused = not paused
            if btn_reset.handle_event(event):
                sim = ForestFire(GRID_W, GRID_H)

            if pygame.mouse.get_pressed()[0]:
                mx, my = pygame.mouse.get_pos()
                if mx < SIM_WIDTH:
                    sim.ignite_at(mx // CELL_SIZE, my // CELL_SIZE)

        if not paused:
            sim.update(sliders[0].val, sliders[1].val, sliders[2].val, sliders[3].val)

        screen.fill(BG_COLOR)
        
        img, fire_mask = sim.get_render_image()
        surf = pygame.surfarray.make_surface(np.transpose(img, (1, 0, 2)))
        surf = pygame.transform.scale(surf, (SIM_WIDTH, SIM_HEIGHT))
        screen.blit(surf, (0, 0))

        if fire_mask.any():
            glow_img = np.zeros_like(img)
            glow_img[fire_mask] = img[fire_mask]
            glow_surf = pygame.surfarray.make_surface(np.transpose(glow_img, (1, 0, 2)))
            glow_surf = pygame.transform.scale(glow_surf, (SIM_WIDTH, SIM_HEIGHT))
            
            mini_size = (SIM_WIDTH // 6, SIM_HEIGHT // 6)
            glow_blur = pygame.transform.smoothscale(glow_surf, mini_size)
            glow_blur = pygame.transform.smoothscale(glow_blur, (SIM_WIDTH, SIM_HEIGHT))
            screen.blit(glow_blur, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        pygame.draw.rect(screen, PANEL_COLOR, (SIM_WIDTH, 0, UI_WIDTH, SIM_HEIGHT))
        pygame.draw.line(screen, (45, 45, 60), (SIM_WIDTH, 0), (SIM_WIDTH, SIM_HEIGHT), 2)

        title = font_title.render("Симуляция пожара", True, (255, 255, 255))
        screen.blit(title, (ui_x, 20))
        pygame.draw.line(screen, FIRE_ACCENT, (ui_x, 50), (ui_x + 80, 50), 3)

        for slider in sliders:
            slider.draw(screen, font_main)
            
        compass_center = (ui_x + 165, 300)
        compass_radius = 45
        
        pygame.draw.circle(screen, (20, 20, 28), compass_center, compass_radius)
        pygame.draw.circle(screen, (60, 60, 80), compass_center, compass_radius, 2)
        pygame.draw.circle(screen, (40, 40, 55), compass_center, compass_radius//2, 1)
        pygame.draw.line(screen, (60, 60, 80), (compass_center[0]-compass_radius, compass_center[1]), (compass_center[0]+compass_radius, compass_center[1]))
        pygame.draw.line(screen, (60, 60, 80), (compass_center[0], compass_center[1]-compass_radius), (compass_center[0], compass_center[1]+compass_radius))
        
        screen.blit(font_stats.render("С", True, (150, 150, 150)), (compass_center[0]-4, compass_center[1]-compass_radius-15))
        screen.blit(font_stats.render("Ю", True, (150, 150, 150)), (compass_center[0]-4, compass_center[1]+compass_radius+2))
        screen.blit(font_stats.render("З", True, (150, 150, 150)), (compass_center[0]-compass_radius-15, compass_center[1]-6))
        screen.blit(font_stats.render("В", True, (150, 150, 150)), (compass_center[0]+compass_radius+5, compass_center[1]-6))

        wind_strength = sliders[2].val
        if wind_strength > 0:
            arrow_len = compass_radius * wind_strength
            end_x = compass_center[0] + math.cos(sim.wind_angle) * arrow_len
            end_y = compass_center[1] + math.sin(sim.wind_angle) * arrow_len
            pygame.draw.line(screen, ACCENT_COLOR, compass_center, (end_x, end_y), 3)
            pygame.draw.circle(screen, (255, 255, 255), (int(end_x), int(end_y)), 4)
            pygame.draw.circle(screen, ACCENT_COLOR, (int(end_x), int(end_y)), 2)
        else:
            pygame.draw.circle(screen, ACCENT_COLOR, compass_center, 4) # Штиль

        radar_text = font_main.render("Направление ветра", True, TEXT_COLOR)
        screen.blit(radar_text, (ui_x, 245))

        btn_pause.draw(screen, font_main)
        btn_reset.draw(screen, font_main)

        trees = np.count_nonzero(sim.grid == TREE)
        fires = np.count_nonzero(sim.grid == FIRE)
        
        stats_bg = pygame.Rect(ui_x, 520, 330, 130)
        pygame.draw.rect(screen, (20, 20, 28), stats_bg, border_radius=10)
        pygame.draw.rect(screen, (40, 40, 50), stats_bg, border_radius=10, width=1)
        
        stats =[
            f"FPS:          {int(clock.get_fps())}",
            f"ПОКОЛЕНИЕ:    {sim.generation}",
            f"ЖИВЫЕ ДЕРЕВЬЯ:{trees}",
            f"ОЧАГИ ПОЖАРА: {fires}",
            f"СТАТУС:       {'ПАУЗА' if paused else 'СИМУЛЯЦИЯ'}"
        ]
        
        for i, text in enumerate(stats):
            color = FIRE_ACCENT if "ПАУЗА" in text else TEXT_COLOR
            stat_surf = font_stats.render(text, True, color)
            screen.blit(stat_surf, (ui_x + 15, 535 + i * 22))

        hint = font_main.render("ЛКМ по лесу - поджечь область", True, (100, 100, 120))
        screen.blit(hint, (ui_x + 40, WINDOW_HEIGHT - 30))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()