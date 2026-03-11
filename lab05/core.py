import random

MAGIC_ANSWERS = [
    "Бесспорно",
    "Предрешено",
    "Никаких сомнений",
    "Определённо да",
    "Можешь быть уверен в этом",
    "Мне кажется — да",
    "Вероятнее всего",
    "Хорошие перспективы",
    "Да",
    "Знаки говорят — да",
    "Пока не ясно, попробуй снова",
    "Спроси позже",
    "Лучше не рассказывать тебе",
    "Сейчас нельзя предсказать",
    "Сконцентрируйся и спроси опять",
    "Даже не думай",
    "Мой ответ — нет",
    "По моим данным — нет",
    "Перспективы не очень хорошие",
    "Весьма сомнительно"
]

def get_yes_no(p=0.5):
    return "ДА" if random.random() < p else "НЕТ"

def get_magic_8_ball():

    m = len(MAGIC_ANSWERS)
    p_i = 1.0 / m  

    alpha = random.random()

    cumulative_p = 0.0

    for k in range(m):
        cumulative_p += p_i

        if alpha < cumulative_p:
            return MAGIC_ANSWERS[k]
        
    return MAGIC_ANSWERS[-1]