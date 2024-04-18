import math


def simple_sqrt(x):
    return math.sqrt(x)


def newton_sqrt(x):
    guess = x / 2.0
    while abs(guess*guess - x) > 0.0001:
        guess = (guess + x / guess) / 2.0
    return guess

# Пример использования
number = float(input("Введите число: "))
result = newton_sqrt(number)
print("Квадратный корень:", result)
