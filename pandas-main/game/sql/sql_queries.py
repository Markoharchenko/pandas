import sqlite3
conn = sqlite3.connect("Artistc.db")
cursor = conn.cursor()


# Питання 1. Інформація про скільки художників представлена в базі даних? 
cursor.execute('SELECT * FROM artists')
data = cursor.fetchall()
print('Кількість художників у базі:', len(data))

# Запитання 2. Скільки жінок (Female) у базі?
cursor.execute('SELECT * FROM artists WHERE gender == "Female"')
data = cursor.fetchall()
print('Кількість жінок:', len(data))

# Запитання 3. Скільки людей у базі даних народилися до 1900 року?
cursor.execute('SELECT * FROM artists WHERE "Birth Year" < 1900')
data = cursor.fetchall()
print('Народилися до 1900 року:', len(data))

# Запитання 4*. Як звати найстаршого художника?


# Варіант рішення 1: використовуємо стандартні засоби Python
cursor.execute('SELECT * FROM artists WHERE "Birth Year" < 1900')
data = cursor.fetchall()
oldest = {'name': '', 'birthday': 1900}
for person in data:
    if person[4] < oldest['birthday']:
        oldest['name'] = person[1]
        oldest['birthday'] = person[4]
print('Найстарший:', oldest)


# Варіант рішення 2: лише SQL
cursor.execute('SELECT name FROM artists WHERE "Birth Year" < 1900 order by "Birth Year"')
data = cursor.fetchall()
print('Найстарший:', data[0][0])


conn.commit()