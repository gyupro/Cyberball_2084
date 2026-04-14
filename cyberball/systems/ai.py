"""AI paddle movement."""
import random

from ..config import PADDLE_SPEED, SCREEN_HEIGHT, AI_SPEED_MULTIPLIER


def move_ai_paddle(paddle, ball, difficulty):
    """Move the AI paddle toward the ball, with difficulty-tuned prediction."""
    target_y = ball.rect.centery

    if difficulty in ("hard", "extreme"):
        if ball.speed_x < -0.1:  # ball moving toward AI (left)
            time_to_reach = abs(ball.rect.centerx - paddle.rect.centerx) / max(abs(ball.speed_x), 0.1)
            predicted = ball.rect.centery + (ball.speed_y + ball.spin * 0.1) * time_to_reach
            # Bounce-fold prediction off top/bottom walls
            period = 2 * SCREEN_HEIGHT
            py = predicted % period
            if py > SCREEN_HEIGHT:
                py = period - py
            target_y = py
        if difficulty == "extreme" and random.random() < 0.1:
            target_y += random.uniform(-20, 20)
    elif difficulty == "easy":
        target_y += random.uniform(-30, 30)

    mult = AI_SPEED_MULTIPLIER.get(difficulty, 0.9)
    move_speed = PADDLE_SPEED * mult
    diff = target_y - paddle.rect.centery

    if abs(diff) > 10:
        step = int(min(move_speed, abs(diff)))
        paddle.move(step if diff > 0 else -step)
