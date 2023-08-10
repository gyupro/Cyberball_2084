import pygame
import sys
import random
from pygame.locals import QUIT, KEYDOWN, K_UP, K_DOWN, K_r

pygame.init()

# Constants
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
PADDLE_SPEED = 5
BALL_SPEED = [5, 5]
PADDLE_HEIGHT = 100
PADDLE_WIDTH = 15
BALL_SIZE = 20
SPEED_INCREMENT = 0.5

# Colors
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0)

# Initialize scores
left_score = 0
right_score = 0
# Create the ball and paddles
ball = pygame.Rect(SCREEN_WIDTH // 2 - BALL_SIZE // 2, SCREEN_HEIGHT // 2 - BALL_SIZE // 2, BALL_SIZE, BALL_SIZE)
left_paddle = pygame.Rect(0, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT)
right_paddle = pygame.Rect(SCREEN_WIDTH - PADDLE_WIDTH, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT)
# Set up the screen, clock, and font renderer
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Cyberball 2084')
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)

def reset_game():
    global ball, BALL_SPEED
    ball.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    BALL_SPEED = [random.choice([-5, 5]), random.choice([-5, 5])]

def move_left_paddle():
    # Slightly better AI: Doesn't always perfectly align with the ball
    if left_paddle.centery < ball.centery and left_paddle.bottom < SCREEN_HEIGHT - 10:
        left_paddle.move_ip(0, PADDLE_SPEED)
    elif left_paddle.centery > ball.centery and left_paddle.top > 10:
        left_paddle.move_ip(0, -PADDLE_SPEED)

while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == KEYDOWN and event.key == K_r:
            left_score = 0
            right_score = 0
            reset_game()

    keys = pygame.key.get_pressed()

    move_left_paddle()

    # Move the right paddle with arrow keys
    if keys[K_UP] and right_paddle.top > 0:
        right_paddle.move_ip(0, -PADDLE_SPEED)
    if keys[K_DOWN] and right_paddle.bottom < SCREEN_HEIGHT:
        right_paddle.move_ip(0, PADDLE_SPEED)

    # Move the ball and handle collisions
    ball.move_ip(BALL_SPEED[0], BALL_SPEED[1])
    if ball.top <= 0 or ball.bottom >= SCREEN_HEIGHT:
        BALL_SPEED[1] = -BALL_SPEED[1]

    if ball.colliderect(left_paddle) or ball.colliderect(right_paddle):
        BALL_SPEED[0] = -(BALL_SPEED[0] + SPEED_INCREMENT)  # increase speed every collision
        BALL_SPEED[1] = BALL_SPEED[1] + (1 if BALL_SPEED[1] > 0 else -1) * SPEED_INCREMENT  # increase vertical speed

    if ball.left <= 0:
        right_score += 1
        reset_game()
    elif ball.right >= SCREEN_WIDTH:
        left_score += 1
        reset_game()

    # Render
    screen.fill(WHITE)
    pygame.draw.rect(screen, BLUE, left_paddle)
    pygame.draw.rect(screen, RED, right_paddle)
    pygame.draw.ellipse(screen, BLUE, ball)
    pygame.draw.aaline(screen, BLUE, (SCREEN_WIDTH // 2, 0), (SCREEN_WIDTH // 2, SCREEN_HEIGHT))

    # Display scores
    score_display = font.render(f"{left_score} - {right_score}", True, (0, 0, 0))
    screen.blit(score_display, (SCREEN_WIDTH // 2 - score_display.get_width() // 2, 10))

    pygame.display.flip()
    clock.tick(60)
