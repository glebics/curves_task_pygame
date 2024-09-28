#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pygame
import random
import math

# Размеры экрана
SCREEN_DIM = (800, 600)


class Vec2d:
    """Класс для работы с 2-мерными векторами."""

    def __init__(self, x, y):
        """Инициализация вектора с координатами x и y."""
        self.x = x
        self.y = y

    def __add__(self, other):
        """Сложение двух векторов."""
        return Vec2d(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        """Вычитание двух векторов."""
        return Vec2d(self.x - other.x, self.y - other.y)

    def __mul__(self, k):
        """Умножение вектора на скаляр."""
        if isinstance(k, (int, float)):
            return Vec2d(self.x * k, self.y * k)
        else:
            raise NotImplementedError("Умножение на данный тип не поддерживается.")

    def __rmul__(self, k):
        """Умножение скаляра на вектор."""
        return self.__mul__(k)

    def __len__(self):
        """Возвращает длину вектора как целое число."""
        return int(math.hypot(self.x, self.y))

    def int_pair(self):
        """Возвращает координаты вектора как кортеж из двух целых чисел."""
        return (int(self.x), int(self.y))

    def copy(self):
        """Возвращает копию вектора."""
        return Vec2d(self.x, self.y)


class Polyline:
    """Класс, представляющий замкнутую ломаную."""

    def __init__(self):
        """Инициализация ломаной без опорных точек."""
        self.points = []  # Список опорных точек (Vec2d)
        self.speeds = []  # Список скоростей для каждой точки (Vec2d)

    def add_point(self, point: Vec2d):
        """Добавляет опорную точку с случайной скоростью."""
        self.points.append(point)
        speed = Vec2d(random.uniform(-2, 2), random.uniform(-2, 2))
        self.speeds.append(speed)

    def set_points(self, screen_dim):
        """Перерасчитывает координаты опорных точек на основе их скоростей."""
        for i in range(len(self.points)):
            self.points[i] += self.speeds[i]
            # Отскок от границ экрана
            if self.points[i].x > screen_dim[0] or self.points[i].x < 0:
                self.speeds[i].x = -self.speeds[i].x
            if self.points[i].y > screen_dim[1] or self.points[i].y < 0:
                self.speeds[i].y = -self.speeds[i].y

    def draw_points(self, surface, style="points", width=3, color=(255, 255, 255)):
        """Отрисовка опорных точек или ломаной на поверхности."""
        if style == "line":
            if len(self.points) > 1:
                pygame.draw.aalines(surface, color, True,
                                    [p.int_pair() for p in self.points], width)
        elif style == "points":
            for p in self.points:
                pygame.draw.circle(surface, color, p.int_pair(), width)

    def clear(self):
        """Очистка всех опорных точек и скоростей."""
        self.points = []
        self.speeds = []


class Knot(Polyline):
    """Класс, представляющий гладкую кривую (узел) на основе опорных точек."""

    def __init__(self):
        """Инициализация узла без опорных точек и гладкой кривой."""
        super().__init__()
        self.curve = []  # Список точек гладкой кривой (Vec2d)

    def add_point(self, point: Vec2d):
        """Добавляет опорную точку и перерасчитывает кривую."""
        super().add_point(point)
        self.calculate_curve()

    def set_points(self, screen_dim):
        """Перерасчитывает позиции опорных точек и обновляет кривую."""
        super().set_points(screen_dim)
        self.calculate_curve()

    def calculate_curve(self, count=35):
        """
        Расчет точек гладкой кривой на основе опорных точек.
        :param count: количество точек сглаживания между опорными точками
        """
        if len(self.points) < 3:
            self.curve = []
            return
        self.curve = []
        alpha = 1 / count
        for i in range(-2, len(self.points) - 2):
            # Формирование контрольных точек для сегмента кривой
            ptn = [
                (self.points[i] + self.points[i + 1]) * 0.5,
                self.points[i + 1],
                (self.points[i + 1] + self.points[i + 2]) * 0.5
            ]
            # Генерация точек кривой для текущего сегмента
            for j in range(count):
                point = self.get_point(ptn, j * alpha)
                self.curve.append(point)

    def get_point(self, points, alpha):
        """
        Рекурсивный расчет точки на кривой методом линейной интерполяции.
        :param points: список точек для интерполяции
        :param alpha: параметр интерполяции (0 <= alpha <= 1)
        :return: точка Vec2d на кривой
        """
        if len(points) == 1:
            return points[0]
        new_points = [points[i] * alpha + points[i + 1] * (1 - alpha) for i in range(len(points) - 1)]
        return self.get_point(new_points, alpha)

    def draw_curve(self, surface, color=(255, 255, 255)):
        """Отрисовка гладкой кривой на поверхности."""
        if len(self.curve) > 1:
            pygame.draw.aalines(surface, color, False,
                                [p.int_pair() for p in self.curve], 3)

    def clear(self):
        """Очистка опорных точек, скоростей и гладкой кривой."""
        super().clear()
        self.curve = []


class App:
    """Основной класс приложения, управляющий Pygame циклом и событиями."""

    def __init__(self):
        """Инициализация Pygame и основных параметров приложения."""
        pygame.init()
        self.screen = pygame.display.set_mode(SCREEN_DIM)
        pygame.display.set_caption("MyScreenSaver")
        self.clock = pygame.time.Clock()

        self.knot = Knot()  # Инициализация узла
        self.steps = 35  # Количество точек сглаживания
        self.running = True
        self.show_help = False
        self.pause = True  # Программа запускается в состоянии паузы

        self.hue = 0  # Начальный оттенок цвета
        self.color = pygame.Color(0)  # Начальный цвет

        # Инициализация шрифта для отображения количества точек сглаживания
        self.font = pygame.font.SysFont("Arial", 24)

    def run(self):
        """Основной цикл приложения."""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)  # Ограничение до 60 кадров в секунду

        pygame.quit()

    def handle_events(self):
        """Обработка событий Pygame."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_r:
                    self.knot.clear()  # Рестарт: очистка всех точек
                elif event.key == pygame.K_p:
                    self.pause = not self.pause  # Пауза/снятие паузы
                elif event.key in (pygame.K_KP_PLUS, pygame.K_EQUALS):
                    # Проверяем, если нажата клавиша + на NumPad или Shift + =
                    if event.key == pygame.K_EQUALS and not (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                        # Это просто '=' без Shift, не реагируем
                        pass
                    else:
                        self.steps += 1  # Увеличение количества точек сглаживания
                        self.knot.calculate_curve(count=self.steps)
                elif event.key in (pygame.K_KP_MINUS, pygame.K_MINUS):
                    if self.steps > 1:
                        self.steps -= 1  # Уменьшение количества точек сглаживания
                        self.knot.calculate_curve(count=self.steps)
                elif event.key == pygame.K_F1:
                    self.show_help = not self.show_help  # Показать/скрыть справку

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Левая кнопка мыши
                    point = Vec2d(*event.pos)
                    self.knot.add_point(point)  # Добавление опорной точки

    def update(self):
        """Обновление состояния приложения."""
        if not self.pause:
            self.knot.set_points(SCREEN_DIM)  # Обновление позиций точек
            self.knot.calculate_curve(count=self.steps)  # Перерасчет кривой

    def draw(self):
        """Отрисовка всех элементов на экране."""
        self.screen.fill((0, 0, 0))  # Очистка экрана
        self.hue = (self.hue + 1) % 360  # Изменение оттенка цвета
        self.color.hsla = (self.hue, 100, 50, 100)  # Обновление цвета

        self.knot.draw_points(self.screen, "points", 3, self.color)  # Отрисовка опорных точек
        self.knot.draw_curve(self.screen, self.color)  # Отрисовка гладкой кривой

        # Отображение количества точек сглаживания в верхнем левом углу
        steps_text = f"Точек сглаживания: {self.steps}"
        text_surface = self.font.render(steps_text, True, (255, 255, 255))
        self.screen.blit(text_surface, (10, 10))

        if self.show_help:
            self.draw_help()  # Отрисовка экрана справки

    def draw_help(self):
        """Отрисовка экрана справки."""
        font1 = pygame.font.SysFont("courier", 24)
        font2 = pygame.font.SysFont("serif", 24)
        data = [
            ("F1", "Show Help"),
            ("R", "Restart"),
            ("P", "Pause/Play"),
            ("Num+", "More points"),
            ("Num-", "Less points"),
            ("", ""),
            (str(self.steps), "Current points")
        ]

        # Отрисовка фона справки
        pygame.draw.rect(self.screen, (50, 50, 50), (50, 50, 700, 500))
        pygame.draw.rect(self.screen, (255, 50, 50), (50, 50, 700, 500), 5)

        # Отрисовка текста справки
        for i, text in enumerate(data):
            key_text, desc_text = text
            if key_text:
                key_surf = font1.render(key_text, True, (128, 128, 255))
                self.screen.blit(key_surf, (60, 60 + 30 * i))
            desc_surf = font2.render(desc_text, True, (128, 128, 255))
            self.screen.blit(desc_surf, (150, 60 + 30 * i))


if __name__ == "__main__":
    app = App()
    app.run()
