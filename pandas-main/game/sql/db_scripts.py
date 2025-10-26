# Це приклад функції, яку ти можеш змінити під свою БД
def get_question_after(last_question, quiz):
    # Псевдо-логіка: повертаємо наступне питання як кортеж (id, текст)
    questions = {
        1: [(1, "Що таке Python?"), (2, "Що таке Flask?")],
        2: [(1, "Що таке змінна?"), (2, "Що таке цикл?")],
        3: [(1, "Що таке список?"), (2, "Що таке словник?")]
    }

    quiz_questions = questions.get(quiz, [])
    for q in quiz_questions:
        if q[0] > last_question:
            return q
    return None