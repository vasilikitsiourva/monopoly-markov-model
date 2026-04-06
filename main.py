import pygame
import numpy as np
from scipy.linalg import eig
import matplotlib.pyplot as plt
import matplotlib.cm as cm


BOARD_SIZE = 40
WIDTH, HEIGHT = 1000, 700
WHITE, BLACK, GRAY = (255, 255, 255), (0, 0, 0), (200, 200, 200)
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Winning Monopoly!!")
font = pygame.font.SysFont("Arial", 26)
menu_font = pygame.font.SysFont("Arial", 36, bold=True) 

def build_transition_matrix():
    P = np.zeros((BOARD_SIZE, BOARD_SIZE))
    dice_probs = {2: 1/36, 3: 2/36, 4: 3/36, 5: 4/36,
                  6: 5/36, 7: 6/36, 8: 5/36, 9: 4/36,
                  10: 3/36, 11: 2/36, 12: 1/36}
    for from_sq in range(BOARD_SIZE):
        for roll, prob in dice_probs.items():
            P[from_sq][(from_sq + roll) % BOARD_SIZE] += prob
    return P

def apply_special_squares(P):
    chance_squares = [7, 22, 36]
    community_squares = [2, 17, 33]
    chance_moves = [0, 10, 24, 11, 12, 5, -3]
    chance_prob = 1 / 16
    comm_prob = 1 / 16

    for square in chance_squares:
        for from_sq in range(BOARD_SIZE):
            prob = P[from_sq][square]
            if prob == 0: continue
            P[from_sq][square] = 0
            for move in chance_moves:
                if move == -3: dest = (square - 3) % BOARD_SIZE
                elif move == 12: dest = 12 if square in [7,36] else 28
                elif move == 5: dest = 5 if square in [7,22] else 35
                else: dest = move
                P[from_sq][dest] += prob * chance_prob
            remaining = 1 - len(chance_moves) * chance_prob
            P[from_sq][square] += prob * remaining

    for square in community_squares:
        for from_sq in range(BOARD_SIZE):
            prob = P[from_sq][square]
            if prob == 0: continue
            P[from_sq][square] = 0
            P[from_sq][0] += prob * comm_prob
            P[from_sq][10] += prob * comm_prob
            P[from_sq][square] += prob * (1 - 2*comm_prob)

    for from_sq in range(BOARD_SIZE):
        prob = P[from_sq][30]
        if prob > 0:
            P[from_sq][30] = 0
            P[from_sq][10] += prob

    return P

def compute_steady_state(P):
    eigvals, eigvecs = eig(P.T)
    idx = np.argmax(np.isclose(eigvals, 1.0))
    stationary = np.real(eigvecs[:, idx])
    stationary /= np.sum(stationary)
    return stationary

def n_rolls_distribution(P, start_square, n):
    p = np.zeros(BOARD_SIZE)
    p[start_square] = 1.0
    for _ in range(n):
        p = p @ P
    return p

def draw_text_shadow(text, x, y, color=BLACK, shadow_color=GRAY, font_obj=None):
    if font_obj is None:
        font_obj = font
    # Shadow
    shadow = font_obj.render(text, True, shadow_color)
    screen.blit(shadow, (x+2, y+2))
    
    label = font_obj.render(text, True, color)
    screen.blit(label, (x, y))


def draw_text(text, x, y, color=BLACK):
    label = font.render(text, True, color)
    screen.blit(label, (x, y))

def draw_button(x, y, w, h, text, color=GRAY, text_color=BLACK):
    rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(screen, color, rect, border_radius=8)
    label = font.render(text, True, text_color)
    label_rect = label.get_rect(center=rect.center)
    screen.blit(label, label_rect)
    return rect

def histogram(screen, distribution):
    bar_width = WIDTH / BOARD_SIZE
    max_height = max(distribution)
    cmap = cm.get_cmap("coolwarm")  

    for i, prob in enumerate(distribution):
        intensity = prob / max_height
        color = cmap(intensity)
        rgb = tuple(int(c*255) for c in color[:3])
        bar_height = (prob / max_height) * (HEIGHT - 150)
        x = i * bar_width
        y = HEIGHT - bar_height - 50
        pygame.draw.rect(screen, rgb, (x, y, bar_width-2, bar_height))


def main():
    P = apply_special_squares(build_transition_matrix())
    steady_state = compute_steady_state(P)
    distribution = steady_state.copy()
    mode = "menu"
    n_rolls = 10
    start_square = 0
    clock = pygame.time.Clock()
    running = True

    while running:
        screen.fill(WHITE)

        
        if mode == "menu":
            # Heading
            heading_text = "Choose an option:"
            text_surface = menu_font.render(heading_text, True, BLACK)
            text_rect = text_surface.get_rect(center=(WIDTH//2, 150))
            draw_text_shadow(heading_text, text_rect.x, text_rect.y, color=BLACK, shadow_color=(150,150,150), font_obj=menu_font)

            # Buttons with nice muted colors
            steady_btn = draw_button(300, 250, 400, 70, "Steady State", color=(59, 89, 152), text_color=WHITE)
            nrolls_btn = draw_button(300, 350, 400, 70, "Simulate n Rolls", color=(128, 0, 32), text_color=WHITE)

        
        elif mode == "steady":
            draw_text("Steady-State Distribution", 330, 10)
            histogram(screen, distribution)
            back_btn = draw_button(20, 20, 100, 40, "Back", color=(200,50,50), text_color=WHITE)

       
        elif mode == "nrolls":
            draw_text("n-Rolls Simulation", 370, 10)
            histogram(screen, distribution)
            back_btn = draw_button(20, 20, 100, 40, "Back", GRAY, text_color=WHITE)

           
            draw_text(f"Rolls: {n_rolls}", 170, 110)
            draw_text(f"Start Square: {start_square}", 170, 160)
            rolls_minus = draw_button(40, 110, 30, 30, "-", GRAY, text_color=WHITE)
            rolls_plus  = draw_button(120, 110, 30, 30, "+", GRAY, text_color=WHITE)
            square_minus = draw_button(40, 160, 30, 30, "-", GRAY, text_color=WHITE)
            square_plus  = draw_button(120, 160, 30, 30, "+", GRAY, text_color=WHITE)

        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if mode == "menu":
                    if steady_btn.collidepoint(mx,my):
                        mode = "steady"
                        distribution = steady_state.copy()
                    elif nrolls_btn.collidepoint(mx,my):
                        mode = "nrolls"
                        distribution = n_rolls_distribution(P, start_square, n_rolls)
                elif mode == "steady":
                    if back_btn.collidepoint(mx,my):
                        mode = "menu"
                elif mode == "nrolls":
                    if back_btn.collidepoint(mx,my):
                        mode = "menu"
                    elif rolls_minus.collidepoint(mx,my):
                        n_rolls = max(1, n_rolls-1)
                    elif rolls_plus.collidepoint(mx,my):
                        n_rolls += 1
                    elif square_minus.collidepoint(mx,my):
                        start_square = (start_square-1) % BOARD_SIZE
                    elif square_plus.collidepoint(mx,my):
                        start_square = (start_square+1) % BOARD_SIZE
                    
                    distribution = n_rolls_distribution(P, start_square, n_rolls)

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    main()

