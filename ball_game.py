import pygame
import random
import sys
import os
import math

# Инициализация Pygame
pygame.init()
pygame.mixer.init()

# Задаем размеры окна
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Поймай шарик")

# Определяем цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Загрузка звуков
try:
    catch_sound = pygame.mixer.Sound('catch.wav')
    miss_sound = pygame.mixer.Sound('miss.wav')
except:
    catch_sound = None
    miss_sound = None

# Шрифт для отображения текста
font = pygame.font.SysFont(None, 36)
large_font = pygame.font.SysFont(None, 72)

def load_high_score():
    """Загружает рекорд из файла."""
    if os.path.exists('high_score.txt'):
        with open('high_score.txt', 'r') as f:
            return int(f.read())
    else:
        return 0

def save_high_score(score):
    """Сохраняет рекорд в файл."""
    with open('high_score.txt', 'w') as f:
        f.write(str(score))

def draw_text_center(text, font, color, surface, y):
    """Отображает текст по центру экрана."""
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect(center=(WIDTH / 2, y))
    surface.blit(textobj, textrect)

class Ball:
    """Класс для создания и управления объектами (шариками, бустерами, бомбами)."""
    def __init__(self, color, radius, speed, ball_type='normal', shape='circle'):
        self.color = color
        self.radius = radius
        self.speed = speed
        self.x = random.randint(radius, WIDTH - radius)
        self.y = random.randint(radius, HEIGHT - radius)
        self.dx = random.choice([-1, 1]) * speed
        self.dy = random.choice([-1, 1]) * speed
        self.ball_type = ball_type
        self.shape = shape

    def move(self):
        """Двигает объект и отражает его от стен."""
        self.x += self.dx
        self.y += self.dy

        # Отражение от стен
        if self.x <= self.radius or self.x >= WIDTH - self.radius:
            self.dx = -self.dx
        if self.y <= self.radius or self.y >= HEIGHT - self.radius:
            self.dy = -self.dy

    def draw(self, screen):
        """Рисует объект на экране в зависимости от его формы."""
        if self.shape == 'circle':
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        elif self.shape == 'square':
            rect = pygame.Rect(int(self.x - self.radius), int(self.y - self.radius), self.radius * 2, self.radius * 2)
            pygame.draw.rect(screen, self.color, rect)
        elif self.shape == 'triangle':
            point1 = (int(self.x), int(self.y - self.radius))
            point2 = (int(self.x - self.radius), int(self.y + self.radius))
            point3 = (int(self.x + self.radius), int(self.y + self.radius))
            pygame.draw.polygon(screen, self.color, [point1, point2, point3])

class Particle:
    """Класс для частиц."""
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.radius = random.randint(2, 5)
        self.color = color
        self.dx = random.uniform(-2, 2)
        self.dy = random.uniform(-2, 2)
        self.life = 30

    def move(self):
        self.x += self.dx
        self.y += self.dy
        self.life -= 1

    def draw(self, screen):
        if self.life > 0:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

class GameState:
    """Класс для управления состояниями игры."""
    def __init__(self):
        self.state = 'start'
        self.score = 0
        self.lives = 5
        self.level = 1
        self.balls = []
        self.max_level = 10
        self.time_limit = 30  # Ограничение по времени на уровень
        self.start_ticks = pygame.time.get_ticks()  # Время начала уровня
        self.high_score = load_high_score()
        self.difficulty = 'Normal'
        self.paused = False
        self.combo = 0  # Счетчик комбо
        self.combo_time = 2000  # Время для поддержания комбо в миллисекундах
        self.last_hit_time = 0  # Время последнего успешного попадания
        self.particles = []
        self.new_high_score = False  # Флаг для нового рекорда
        self.freeze = False
        self.freeze_duration = 0
        self.freeze_start_time = 0

    def start_screen(self):
        """Отображает стартовый экран."""
        while self.state == 'start':
            screen.fill(WHITE)
            draw_text_center("Поймай шарик", large_font, BLACK, screen, HEIGHT / 2 - 100)
            draw_text_center("Нажмите S, чтобы начать игру", font, BLACK, screen, HEIGHT / 2 - 20)
            draw_text_center("Нажмите O, чтобы открыть настройки", font, BLACK, screen, HEIGHT / 2 + 20)
            draw_text_center(f"Рекорд: {self.high_score}", font, BLACK, screen, HEIGHT / 2 + 60)
            pygame.display.flip()
            self.handle_start_events()

    def handle_start_events(self):
        """Обрабатывает события на стартовом экране."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:
                    self.state = 'playing'
                    self.start_game()
                elif event.key == pygame.K_o:
                    self.state = 'options'
                    self.options_menu()

    def options_menu(self):
        """Отображает меню настроек."""
        while self.state == 'options':
            screen.fill(WHITE)
            draw_text_center("Настройки", large_font, BLACK, screen, HEIGHT / 2 - 100)
            draw_text_center(f"Сложность: {self.difficulty}", font, BLACK, screen, HEIGHT / 2 - 20)
            draw_text_center("Нажмите D, чтобы изменить сложность", font, BLACK, screen, HEIGHT / 2 + 20)
            draw_text_center("Нажмите B, чтобы вернуться назад", font, BLACK, screen, HEIGHT / 2 + 60)
            pygame.display.flip()
            self.handle_options_events()

    def handle_options_events(self):
        """Обрабатывает события в меню настроек."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_high_score(self.high_score)
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_b:
                    self.state = 'start'
                elif event.key == pygame.K_d:
                    self.change_difficulty()

    def change_difficulty(self):
        """Изменяет уровень сложности."""
        difficulties = ['Easy', 'Normal', 'Hard']
        index = difficulties.index(self.difficulty)
        index = (index + 1) % len(difficulties)
        self.difficulty = difficulties[index]
        # Настраиваем параметры игры в зависимости от сложности
        if self.difficulty == 'Easy':
            self.lives = 7
            self.time_limit = 40
        elif self.difficulty == 'Normal':
            self.lives = 5
            self.time_limit = 30
        elif self.difficulty == 'Hard':
            self.lives = 3
            self.time_limit = 20

    def pause_screen(self):
        """Отображает экран паузы."""
        while self.paused:
            screen.fill(WHITE)
            draw_text_center("Пауза", large_font, BLACK, screen, HEIGHT / 2 - 50)
            draw_text_center("Нажмите P, чтобы продолжить", font, BLACK, screen, HEIGHT / 2 + 10)
            draw_text_center("Нажмите Q, чтобы выйти в меню", font, BLACK, screen, HEIGHT / 2 + 50)
            pygame.display.flip()
            self.handle_pause_events()

    def handle_pause_events(self):
        """Обрабатывает события на экране паузы."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_high_score(self.high_score)
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    self.paused = False
                    self.start_ticks = pygame.time.get_ticks() - self.paused_time
                elif event.key == pygame.K_q:
                    self.state = 'start'
                    self.paused = False

    def game_over_screen(self):
        """Отображает экран окончания игры."""
        while self.state == 'game_over':
            screen.fill(WHITE)
            draw_text_center("Игра окончена", large_font, BLACK, screen, HEIGHT / 2 - 120)
            draw_text_center(f"Ваш счет: {self.score}", font, BLACK, screen, HEIGHT / 2 - 40)
            draw_text_center(f"Рекорд: {self.high_score}", font, BLACK, screen, HEIGHT / 2)
            draw_text_center("Нажмите R, чтобы начать заново", font, BLACK, screen, HEIGHT / 2 + 80)
            draw_text_center("Нажмите Q, чтобы выйти в меню", font, BLACK, screen, HEIGHT / 2 + 120)
            pygame.display.flip()
            self.handle_game_over_events()

    def handle_game_over_events(self):
        """Обрабатывает события на экране окончания игры."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_high_score(self.high_score)
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.reset_game()
                    self.state = 'playing'
                    self.start_game()
                elif event.key == pygame.K_q:
                    self.state = 'start'

    def new_high_score_screen(self):
        """Отображает экран поздравления с новым рекордом."""
        screen.fill(WHITE)
        draw_text_center("Поздравляем!", large_font, BLACK, screen, HEIGHT / 2 - 60)
        draw_text_center("Вы установили новый рекорд!", font, BLACK, screen, HEIGHT / 2)
        pygame.display.flip()
        pygame.time.delay(3000)  # Пауза на 3 секунды

    def start_game(self):
        """Начинает игру."""
        self.balls.clear()
        self.create_balls()
        self.start_ticks = pygame.time.get_ticks()
        self.new_high_score = False
        self.freeze = False
        self.game_loop()

    def reset_game(self):
        """Сбрасывает параметры игры."""
        self.score = 0
        self.lives = 5 if self.difficulty == 'Normal' else self.lives
        self.level = 1
        self.balls.clear()
        self.create_balls()
        self.start_ticks = pygame.time.get_ticks()
        self.combo = 0  # Сброс комбо
        self.particles.clear()
        self.freeze = False

    def create_balls(self):
        """Создает объекты для текущего уровня."""
        num_balls = self.level * 2  # Увеличиваем количество объектов
        for i in range(num_balls):
            # Определяем, какие типы объектов будут появляться в зависимости от уровня
            if self.level >= 2:
                ball_type = random.choices(
                    ['normal', 'fast', 'bomb', 'extra_life', 'more_time', 'freeze'],
                    weights=[40, 20, 15, 10, 10, 5],
                    k=1
                )[0]
            else:
                ball_type = 'normal'

            if ball_type == 'normal':
                color = random.choice([(255, 0, 0), (0, 255, 0), (0, 0, 255)])
                radius = random.randint(25, 40)
                speed = random.randint(3 + self.level, 5 + self.level)
                shape = 'circle'
            elif ball_type == 'fast':
                color = (255, 255, 0)  # Желтый цвет для быстрых шариков
                radius = random.randint(20, 35)
                speed = random.randint(6 + self.level, 8 + self.level)
                shape = 'circle'
            elif ball_type == 'bomb':
                color = (0, 0, 0)  # Черный цвет для бомб
                radius = 25
                speed = random.randint(3 + self.level, 5 + self.level)
                shape = 'triangle'  # Бомбы отображаются как треугольники
            elif ball_type == 'extra_life':
                color = (0, 255, 255)  # Голубой цвет для дополнительных жизней
                radius = 25
                speed = random.randint(3, 5)
                shape = 'square'  # Бустеры отображаются как квадраты
            elif ball_type == 'more_time':
                color = (255, 165, 0)  # Оранжевый цвет для увеличения времени
                radius = 25
                speed = random.randint(3, 5)
                shape = 'square'  # Бустеры отображаются как квадраты
            elif ball_type == 'freeze':
                color = (160, 32, 240)  # Фиолетовый цвет для заморозки
                radius = 25
                speed = random.randint(3, 5)
                shape = 'square'  # Бустеры отображаются как квадраты
            self.balls.append(Ball(color, radius, speed, ball_type, shape))

    def game_loop(self):
        """Основной игровой цикл."""
        while self.state == 'playing':
            screen.fill(WHITE)
            seconds = (pygame.time.get_ticks() - self.start_ticks) / 1000  # Сколько секунд прошло

            self.handle_game_events()
            self.update_game(seconds)
            self.draw_game(seconds)

            pygame.display.flip()
            pygame.time.Clock().tick(60)

    def handle_game_events(self):
        """Обрабатывает события во время игры."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_high_score(self.high_score)
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    self.paused = True
                    self.paused_time = pygame.time.get_ticks() - self.start_ticks
                    self.pause_screen()
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.check_ball_click(event.pos)

    def check_ball_click(self, position):
        """Проверяет, попал ли игрок по объекту."""
        mouse_x, mouse_y = position
        hit = False
        for ball in self.balls[:]:
            if ball.ball_type == 'bomb':
                continue  # Игнорируем клики по бомбам
            distance = math.hypot(mouse_x - ball.x, mouse_y - ball.y)
            collision = False
            if ball.shape == 'circle':
                if distance <= ball.radius:
                    collision = True
            elif ball.shape == 'square':
                rect = pygame.Rect(ball.x - ball.radius, ball.y - ball.radius, ball.radius * 2, ball.radius * 2)
                if rect.collidepoint(mouse_x, mouse_y):
                    collision = True

            if collision:
                hit = True
                self.last_hit_time = pygame.time.get_ticks()
                if ball.ball_type == 'normal':
                    self.score += 1 * (self.combo + 1)
                    self.combo += 1
                    if catch_sound:
                        catch_sound.play()
                elif ball.ball_type == 'fast':
                    self.score += 2 * (self.combo + 1)
                    self.combo += 1
                    if catch_sound:
                        catch_sound.play()
                elif ball.ball_type == 'extra_life':
                    self.lives += 1
                    if catch_sound:
                        catch_sound.play()
                elif ball.ball_type == 'more_time':
                    self.time_limit += 5
                    if catch_sound:
                        catch_sound.play()
                elif ball.ball_type == 'freeze':
                    self.freeze = True
                    self.freeze_duration = 5000  # Заморозка на 5 секунд
                    self.freeze_start_time = pygame.time.get_ticks()
                    if catch_sound:
                        catch_sound.play()
                self.balls.remove(ball)
                # Создаем частицы
                for _ in range(10):
                    self.particles.append(Particle(ball.x, ball.y, ball.color))
                break
        if not hit and not self.paused:
            self.lives -= 1
            self.combo = 0  # Сброс комбо при промахе
            if miss_sound:
                miss_sound.play()
            if self.lives <= 0:
                self.check_high_score()
                self.state = 'game_over'
                if self.new_high_score:
                    self.new_high_score_screen()
                self.game_over_screen()

    def check_high_score(self):
        """Проверяет и обновляет рекорд."""
        if self.score > self.high_score:
            self.high_score = self.score
            self.new_high_score = True
            save_high_score(self.high_score)

    def update_game(self, seconds):
        """Обновляет состояние игры."""
        current_time = pygame.time.get_ticks()
        if self.combo > 0 and current_time - self.last_hit_time > self.combo_time:
            self.combo = 0  # Сброс комбо при превышении времени

        if self.freeze:
            if current_time - self.freeze_start_time >= self.freeze_duration:
                self.freeze = False
        else:
            for ball in self.balls:
                ball.move()

        # Обновляем частицы
        for particle in self.particles[:]:
            particle.move()
            if particle.life <= 0:
                self.particles.remove(particle)

        # Проверяем, если все объекты, кроме бомб, пойманы
        non_bomb_balls = [ball for ball in self.balls if ball.ball_type != 'bomb']
        if not non_bomb_balls:
            self.level += 1
            if self.level > self.max_level:
                self.check_high_score()
                if self.new_high_score:
                    self.new_high_score_screen()
                self.state = 'game_over'
                self.game_over_screen()
            else:
                self.create_balls()
                self.start_ticks = pygame.time.get_ticks()  # Сбрасываем таймер

        # Проверяем время
        if seconds > self.time_limit:
            self.lives -= 1
            if self.lives <= 0:
                self.check_high_score()
                self.state = 'game_over'
                if self.new_high_score:
                    self.new_high_score_screen()
                self.game_over_screen()
            else:
                self.balls.clear()
                self.create_balls()
                self.start_ticks = pygame.time.get_ticks()

    def draw_game(self, seconds):
        """Рисует элементы игры на экране."""
        for ball in self.balls:
            ball.draw(screen)

        # Рисуем частицы
        for particle in self.particles:
            particle.draw(screen)

        # Отображаем информацию
        score_text = font.render(f"Счет: {self.score}", True, BLACK)
        lives_text = font.render(f"Жизни: {self.lives}", True, BLACK)
        level_text = font.render(f"Уровень: {self.level}", True, BLACK)
        time_text = font.render(f"Время: {int(self.time_limit - seconds)}", True, BLACK)
        difficulty_text = font.render(f"Сложность: {self.difficulty}", True, BLACK)
        combo_text = font.render(f"Комбо: x{self.combo + 1}", True, BLACK)
        pause_text = font.render("Нажмите P, чтобы поставить на паузу", True, BLACK)

        screen.blit(score_text, (10, 10))
        screen.blit(lives_text, (10, 50))
        screen.blit(level_text, (WIDTH - 200, 10))
        screen.blit(time_text, (WIDTH - 200, 50))
        screen.blit(difficulty_text, (WIDTH / 2 - 100, 10))
        screen.blit(combo_text, (WIDTH / 2 - 100, 50))
        screen.blit(pause_text, (10, HEIGHT - 40))

        # Если заморожено, отображаем сообщение
        if self.freeze:
            freeze_text = large_font.render("Заморозка!", True, (0, 0, 255))
            screen.blit(freeze_text, (WIDTH / 2 - 100, HEIGHT / 2 - 50))

def main():
    """Запускает игру."""
    game = GameState()
    game.start_screen()

if __name__ == "__main__":
    main()
