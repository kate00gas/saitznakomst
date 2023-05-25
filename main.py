from flask import Flask, render_template, request, redirect, url_for, flash, session  # из библиотеки импортировать класс Flask
import psycopg2
import psycopg2.extras
import re
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import random
from random import randint

# Создание экземляра класса
app = Flask(__name__)
# Создание ключа для сессий
app.secret_key = "super secret key"

# Подключение к базе данных
def get_db_connection():
   conn = psycopg2.connect(host='localhost',
                           database='Primer',
                           user='postgres',
                           password='Lada$')
   return conn

# Главная страница приложения
@app.route('/')
def index():
    return render_template('index.html')

# Страничка регистрации пользователя
@app.route('/registr', methods=['GET', 'POST'])
def registr():
    # Получение данных
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        fullname = request.form['fullname']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        phone = request.form['phone']

        # Хеширование пароля
        _hashed_password = generate_password_hash(password)

        # Открытие курсора для работы с БД
        conn = get_db_connection()
        cur = conn.cursor()

        # Check if account exists using MySQL
        cur.execute('SELECT * FROM users WHERE username = %s', (username,))
        account = cur.fetchone()
        print(account)
        # Проверка аккаунта
        if account:
            flash('Account already exists!')
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash('Invalid email address!')
        elif not re.match(r'[A-Za-z0-9]+', username):
            flash('Username must contain only characters and numbers!')
        elif not username or not password or not email:
            flash('Please fill out the form!')
        else:
            # Account doesnt exists and the form data is valid, now insert new account into users table
            # Добавление нового пользователя в базу
            cur.execute("INSERT INTO users (fullname, username, password, email, phone) VALUES (%s,%s,%s,%s,%s) RETURNING id_user",
                           (fullname, username, _hashed_password, email, phone))
            # Возвращенный id нового пользователя заносим в id_u
            id_u = cur.fetchall()[0]
            # print("ID покупателя: ", id_c[0])

            # Обновляем базу
            conn.commit()
            # Обновляем кол-во лайков пользователя
            cur.execute("INSERT INTO obnov_like (id_user) VALUES (%s)",
                        (id_u))
            conn.commit()
            # Вывод сообщения при успеной регистрации
            flash('You have successfully registered!')

        # Закрываем подключение к базе
        cur.close()
        conn.close()

    elif request.method == 'POST':
        # Form is empty... (no POST data)
        flash('Please fill out the form!')
    # Show registration form with message (if any)
    # Возвращаем страницу регистации, если никакие данные не поступают
    return render_template('registr.html')

# Страничка входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()

        # Check if account exists using MySQL
        cur.execute('SELECT * FROM users WHERE username = %s', (username,))
        # Fetch one record and return result

        account = cur.fetchone()
        # Если аккаунт есть
        if account:
            # Достаем пароль из базы
            password_rs = account[5]
            print(password_rs)
            # If account exists in users table in out database
            # Сравниваем пароль из базы и введенный
            if check_password_hash(password_rs, password):
                # Create session data, we can access this data in other routes
                # Открываем сессию - пользователь в системе
                session['loggedin'] = True
                session['id'] = account[0]
                session['username'] = account[2]
                # Получаем текущую дату и время
                d = datetime.now().date()
                t = datetime.now().time()

                # Добавляем запись о входе пользователя в аккаунт в базу
                cur.execute("INSERT INTO vhod_v_acc (date_vhod, time_vhod, id_user) VALUES (%s,%s,%s)",
                            (d, t, account[0]))
                conn.commit()

                # Redirect to home page
                # Переадресуем на домашнюю страницу
                return redirect(url_for('home'))
            else:
                # Account doesnt exist or username/password incorrect
                flash('Incorrect username/password')

        # Если аккаунт в таблице Users не найден, смотрим таблицу Администарторы
        else:
            cur.execute('SELECT * FROM adm WHERE username = %s', (username,))
            account = cur.fetchone()
            if account:
                password_rs = account[3]
                print(password_rs)
                # If account exists in users table in out database
                if password_rs == password:
                    # Create session data, we can access this data in other routes
                    session['loggedin'] = True
                    session['id'] = account[0]
                    session['username'] = account[2]

                    # Переадресуем на домашнюю страницу администратора
                    return redirect(url_for('homeadm'))
            # Account doesnt exist or username/password incorrect
            # Если все мимо
            flash('Incorrect username/password')
        cur.close()
        conn.close()
    return render_template('base.html')

# Страничка выхода из системы
@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    # Redirect to login page
    return redirect(url_for('login'))


# Домашняя страница пользователя
@app.route('/home')
def home():

    # Check if user is loggedin
    if 'loggedin' in session:
        # Текущие время и дата
        d = datetime.now().date()
        t = datetime.now().time()

        conn = get_db_connection()
        cur = conn.cursor()
        res = []
        vosrast = []

        # Получаем всю информацию о текущем пользователе
        cur.execute('SELECT * FROM users WHERE id_user = %s', [session['id']])
        acc = cur.fetchone()



        # # Проверка на активность аккаунта - удаление, если входа в систему не было 2 года
        # data_reg = acc[18]
        # new_data = data_reg.date()
        # print(new_data)
        # data = new_data + timedelta(days=730)
        # # data = datetime.strptime(str(data), "%Y-%m-%d").date()
        # if data < d:
        #     pass

        # Проверка подписок (если прериум или vip)
        if acc[16] == 2 or acc[16] == 3:
            # Отбираем запись о последней продажи подписки для пользователя
            cur.execute("""
                            SELECT * FROM prodag WHERE id_user = %s
                                ORDER BY date_prodag, time_prodag DESC
                                LIMIT 1;
                                        """,
                        ([session['id']]))

            prod = cur.fetchone()

            # Проверяем, прошел ли месяц с даты покупки подписки -> если да - меняем подписку пользователя на Стандарт
            # и меняем ему макс кол-во лайков
            if prod[1] + timedelta(days=30) < d:

                cur.execute('SELECT * FROM subscription WHERE id_subscription = 1')
                pod = cur.fetchone()

                cur.execute('UPDATE users SET id_subscription = %s, kol_like_po_podpisk = %s WHERE id_user = %s',
                            (pod[0], pod[4], acc[0]), )
                conn.commit()

        # Обновление лайков ежедневно
        # Получаем последнюю запись, когда было обновление кол-во лайков для пользователя
        cur.execute("""
                                   SELECT * FROM obnov_like WHERE id_user = %s
                                       ORDER BY id_obnov DESC
                                       LIMIT 1;
                                               """,
                    ([session['id']]))
        obnov = cur.fetchone()

        # Хоть одна запись должна быть, тк предусмотренно по коду
        if obnov == None:
            return "Ошибка"
        # Если дата обновления не равна текущему дню, вытаскиваем кол-во лайков из таб Подписки,
        # обновляем кол-во доступных лайков пользователя и добавляем запись об обновлении
        if obnov[2] != d:

            cur.execute('SELECT * FROM subscription WHERE id_subscription = %s', (acc[16],))
            pod = cur.fetchone()

            cur.execute('UPDATE users SET kol_like_po_podpisk = %s WHERE id_user = %s', (pod[4], acc[0],))
            conn.commit()

            cur.execute('INSERT INTO obnov_like (id_user) VALUES (%s)', (acc[0],))
            conn.commit()

        # Вывод данных других пользователей
        reaction = []
        if acc[11] != None:
            # Выбираем пользователей, id которых не равен нашему (чтобы пользователь не попадал в рекомендаци себе же)
            # и чтобы пользователи в подборке были другого пола
            cur.execute('SELECT id_user FROM users WHERE id_user != %s and pol != %s ', (acc[0], acc[11]))
            list = cur.fetchall()
            print("Номера пользователей")
            print(list)
            if len(list) < 4:
                res = 0
                return render_template('home.html', username=session['username'], res=res, vosrast=vosrast, acc=acc,
                                       reaction=reaction)
            # Cчитаем кол-во пользователей, которые могли бы вывестись
            cur.execute('SELECT count(id_user) FROM users WHERE pol != %s;', (acc[11]))
            N = cur.fetchone()
            aa =[]
            # Переписываем ответ из базы (id пользователей) в список
            for i in range(N[0]):
                aa.append(list[i][0])
            print(aa)

            # Рандомно выбираем 4 пользователя без повторений из заданного списка
            b = random.sample(aa, 4)
            print(b)

            # Проверяем, лайкал ли уже пользователь кого-ниубдь из этих 4 (если да, кнопка лайка будет заблокирована для пользователя)
            for i in range(len(b)):
                cur.execute('SELECT * FROM like_users WHERE id_user1 = %s and id_user2 = %s', (acc[0], b[i],))
                us = cur.fetchone()
                if us != None:
                    reaction.append(1)
                else:
                    reaction.append(0)


            # sp = []
            # while len(sp) < 3:
            #     x = randint(1, 10)
            #     if x not in sp:
            #         sp.append(x)
            # print(sp)
            #
            # for i in range(len(sp)):
            #     if sp[i] == sp[i-1]:
            #         print("ДА")
            #
            # Считаем кол-во лет каждого из 4 по дате их рождения и текущему времени  из записываем в vosrast
            # Выводим всю информацию о пользователях из записываем в res
            for i in range(len(b)):
                cur.execute('SELECT * FROM users WHERE id_user = %s', (b[i],))
                a = cur.fetchone()
                v = int((d - a[6]).days / (365.2425))
                vosrast.append(v)
                res.append(a)

        # cur.execute('SELECT * FROM like_users WHERE id_user1 = %s ', (acc[0]))
        # likes = cur.fetchone()
        # if likes != None:
        #     for i in range(len(b)):
        #         for j in range

        return render_template('home.html', username=session['username'], res=res, vosrast=vosrast, acc=acc, reaction=reaction)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

# Домашняя страничка администратора БД
@app.route('/homeadm')
def homeadm():

    # Check if user is loggedin
    if 'loggedin' in session:


        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('SELECT * FROM adm WHERE id_adm = %s', [session['id']])
        acc = cur.fetchone()


        return render_template('homeadm.html', username=session['username'], acc=acc)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

# Страничка просмотра чужого профиля
@app.route('/profile/<int:id_u>')
def profil_polzovat(id_u):
    # Check if user is loggedin
    if 'loggedin' in session:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE id_user = %s', [session['id']])
        useracc = cur.fetchone()

        # Пользователь с подпиской Стандарт не может смотреть профили других
        if useracc[16] != 2 and useracc[16] != 3:
            return redirect(url_for('home'))

        cur.execute('SELECT * FROM users WHERE id_user = %s', (id_u,))
        account = cur.fetchone()

        cur.execute('SELECT * FROM subscription WHERE id_subscription = %s', (account[16],))
        pod = cur.fetchone()
        # print(pod)
        if len(pod) == 0:
            return "Ошибка"

        # Если дата рождения уже введена пользователем, переписываем формат даты из бд в более красивый
        if account[6] != None:
            date = datetime.strptime(str(account[6]), "%Y-%m-%d")
            birthday = date.strftime("%d.%m.%Y")
        else:
            birthday = "-"
        # if account[16] == pod[0]:
        #     return "Подписка уже приобретена!"

        # cur.execute('UPDATE users SET id_subscription = %s WHERE id_user = %s', (pod[0], account[0]), )
        # conn.commit()
        #
        # cur.execute("INSERT INTO prodag (id_subscription, id_user, id_emp) VALUES (%s,%s,%s)",
        #             (id, account[0], 1))
        # conn.commit()
        cur.close()
        conn.close()
        return render_template('profile_polzovat.html', account=account, useracc=useracc, podpiska=pod, birthday=birthday)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

# Страничка профиля пользователя
@app.route('/profile')
def profile():

    conn = get_db_connection()
    cur = conn.cursor()

    # Check if user is loggedin
    if 'loggedin' in session:
        cur.execute('SELECT * FROM users WHERE id_user = %s', [session['id']])
        account = cur.fetchone()

        if account[6] != None:
            date = datetime.strptime(str(account[6]), "%Y-%m-%d")
            birthday = date.strftime("%d.%m.%Y")
        else:
            birthday = "-"
        # Выводим название подписки пользователя
        cur.execute("""
                        SELECT name FROM users
                            JOIN subscription USING (id_subscription) 
                            WHERE id_user = %s;
                                    """,
                    ([session['id']]))
        podpiska = cur.fetchone()
        # Show the profile page with account info
        cur.close()
        conn.close()
        return render_template('profile.html', account=account, podpiska=podpiska, birthday=birthday)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

# Страничка редактирования профиля
@app.route('/redact', methods=['GET', 'POST'])
def redact():
    # Check if user is loggedin
    if 'loggedin' in session:
        conn = get_db_connection()
        cur = conn.cursor()
        # Если получаем данные со страницы
        if request.method == 'POST':
            birthday = request.form['birthday']
            town = request.form['town']
            goal = request.form['goal']
            znak = request.form['znak']
            obr = request.form['obr']
            rost = request.form['rost']
            pol = request.form['pol']
            yvlech = request.form['yvlech']
            bio = request.form['bio']
            img = request.form['img']

            birthday = datetime.strptime(birthday, "%d.%m.%Y").date()
            cur.execute('SELECT * FROM users WHERE id_user = %s', [session['id']])
            account = cur.fetchone()

            # Если введенный рост равен аналальным значеням возвращаем сообщение
            if int(rost) < 50 or int(rost) > 300:
                return "Измените введенный рост"
            # Если все хорошо, формируем список для вставки в бд
            inf = (birthday, znak, obr, bio, rost, pol, town, goal, yvlech, img, account[0])
            try:
                # Пытаемся вставить в бд инф о пользователе
                cur.execute(
                    "UPDATE users SET birthday = %s, zodiak = %s, education = %s, boigraphy = %s, height = %s, pol = %s, town = %s, purpofdating = %s, hobbies = %s, img = %s WHERE id_user = %s",
                    inf)
                # Обновление
                conn.commit()
                # Закрытие подключения к бд
                cur.close()
                conn.close()
                return redirect(url_for('profile'))
            except:
                return "Ошибка"
        return render_template('redact.html')
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

# @app.route('/about')
# def about():
#     return render_template('base.html')
# Страничка с парами пользователя

# Страничка платных подписок
@app.route('/podpiski')
def podpiski():
    if 'loggedin' in session:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('SELECT * FROM users WHERE id_user = %s', [session['id']])
        account = cur.fetchone()

        cur.execute('SELECT * FROM subscription;')
        pod = cur.fetchall()

        return render_template('podpiski.html', account=account, pod=pod)
    return redirect(url_for('login'))

# Страничка вывода результата покупки подписки
@app.route('/buy/<int:id>')
def buy(id):
    # Check if user is loggedin
    if 'loggedin' in session:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE id_user = %s', [session['id']])
        account = cur.fetchone()

        cur.execute('SELECT * FROM subscription WHERE id_subscription = %s', (id,))
        pod = cur.fetchone()
        # print(pod)
        if len(pod) == 0:
            return "Ошибка"

        # Если купленная подписка уже есть у пользователя
        if account[16] == pod[0]:
            return "Подписка уже приобретена!"

        # Обновляем номер подписки и кол-во лайков для пользователя при покупке
        cur.execute('UPDATE users SET id_subscription = %s, kol_like_po_podpisk = %s WHERE id_user = %s', (pod[0], pod[4], account[0]), )
        conn.commit()

        # Добавляем запись о продаже
        cur.execute("INSERT INTO prodag (id_subscription, id_user, id_emp) VALUES (%s,%s,%s)",
                    (id, account[0], 1))
        conn.commit()
        cur.close()
        conn.close()
        return render_template('buy.html', account=account, pod=pod)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

# Страничка вывода результата лайка пользователя
@app.route('/like/<int:id>')
def like(id):
    # Check if user is loggedin
    if 'loggedin' in session:
        conn = get_db_connection()
        cur = conn.cursor()

        # Получаем данные о пользователе в системе
        cur.execute('SELECT * FROM users WHERE id_user = %s', [session['id']])
        acc1 = cur.fetchone()
        print(acc1)
        # Получаем данные о пользователе, которого лайкнули
        cur.execute('SELECT * FROM users WHERE id_user = %s', (id,))
        acc2 = cur.fetchone()

        # Ищем, лайкал ли уже этого пользователя
        cur.execute('SELECT * FROM like_users WHERE id_user1 = %s and id_user2 = %s ', (acc1[0], acc2[0],))
        us = cur.fetchone()
        if us != None:
            return "Вы уже лайкали этого пользователя!"
        pars = 0

        print(acc2)
        # Добаляем запись о лайке
        cur.execute("INSERT INTO like_users (id_user1, id_user2) VALUES (%s,%s)",
                    (acc1[0], acc2[0]))
        conn.commit()
        # Снимаем кол-во доступных лайков у пользователя и обновляем базу
        kol_like = int(acc1[20]) - 1
        print(kol_like)
        cur.execute('UPDATE users SET kol_like_po_podpisk = %s WHERE id_user = %s',
                    (kol_like, acc1[0],))
        conn.commit()
        # Добавляем кол-во лайков профиля пользователя, которого лайкнули (не влияет на вычисления, просто для рейтинга) и обновляем базу
        kol = int(acc2[15])
        print(kol)
        kol += 1
        print(kol)
        cur.execute('UPDATE users SET kol_like = %s WHERE id_user = %s',
                    (kol, acc2[0],))
        conn.commit()

        # кого лайкнул
        # Ищем в лайках, вдруг второй пользователь уже лайкал текущего
        cur.execute('SELECT * FROM like_users WHERE id_user1 = %s and id_user2 = %s', (acc2[0], acc1[0],))
        us2 = cur.fetchone()
        print(us2)
        pars = 0
        # Если да - создаем пару
        if us2 != None:
            cur.execute('SELECT * FROM pars WHERE id_user1 = %s and id_user2 = %s', (acc2[0], acc1[0],))
            n1 = cur.fetchone()

            cur.execute('SELECT * FROM pars WHERE id_user1 = %s and id_user2 = %s', (acc1[0], acc2[0],))
            n2 = cur.fetchone()
            # Если пары нет - создаем ее
            if n1 == None and n2 == None:
                cur.execute("INSERT INTO pars (id_user1, id_user2) VALUES (%s, %s)",
                            (acc1[0], acc2[0]))
                conn.commit()
                pars = 1

        cur.close()
        conn.close()
        return render_template('like.html', acc1=acc1, acc2=acc2, pars=pars)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

# Страничка пар пользователя
@app.route('/pars')
def par():
    if 'loggedin' in session:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('SELECT * FROM users WHERE id_user = %s', [session['id']])
        acc = cur.fetchone()

        # Ищем все пары текущего пользователя (тк id текущего может быть и в левой колонке и в правой, поэтому эти спики нужно склеить)
        cur.execute('SELECT id_user2 FROM pars WHERE id_user1 = %s GROUP BY id_user2', (acc[0],))
        v1 = cur.fetchall()

        cur.execute('SELECT id_user1 FROM pars WHERE id_user2 = %s GROUP BY id_user1', (acc[0],))
        v2 = cur.fetchall()
        print("Список 1")
        print(v1)
        print("Список 2")
        print(v2)

        INF = []
        INF1 = []
        INF2 = []
        # Если пользователи есть в 2 списках
        if v1 != None and v2 != None:
            if len(v1) != 0 and len(v2) != 0:
                # Переписываем результаты запросов в новые списки
                for i in range(len(v1)):
                    INF1.append(v1[i][0])
                for i in range(len(v2)):
                    INF2.append(v2[i][0])
                # Анализируем пписок 2: если элемента из списка 2 нет в 1 - добавляем эллемент в 1 список
                for i in INF2:
                    if i not in INF1:
                        INF1.append(i)

                print("Прошел")
                print(INF1)
                # Находим информацию о всех пользователей из пары и добавляем все данные в новый список INF (он выводится на страницу)
                for i in range(len(INF1)):
                    cur.execute('SELECT * FROM users WHERE id_user = %s', (INF1[i],))
                    acc = cur.fetchone()
                    INF.append(acc)
                N = len(INF)
                return render_template('pars.html', INF=INF, N=N)
        # Если не пуст только 1 список
        if v1 != None:
            if len(v1) != 0:
                # Формируем только INF1, ищем информацию о пользователях и добавлем в INF
                for i in range(len(v1)):
                    INF1.append(v1[i][0])
                print("Прошел")
                print(INF1)
                for i in range(len(INF1)):
                    cur.execute('SELECT * FROM users WHERE id_user = %s', (INF1[i],))
                    acc = cur.fetchone()
                    INF.append(acc)
                N = len(INF)
                return render_template('pars.html', INF=INF, N=N)
        # Аналогично, если не пуст только 2 список
        if v2 != None:
            if len(v2) != 0:

                for i in range(len(v2)):
                    INF2.append(v2[i][0])
                print("Прошел")
                print(INF2)
                for i in range(len(INF2)):
                    cur.execute('SELECT * FROM users WHERE id_user = %s', (INF2[i],))
                    acc = cur.fetchone()
                    INF.append(acc)
                N = len(INF)
                return render_template('pars.html', INF=INF, N=N)
        # Если пар вообще нет
        N = 0
        return render_template('pars.html', N=N)
    return redirect(url_for('login'))

# Страничка для удаления пары (только выполнение операции + триггер)
@app.route('/ydal_para/<int:id>')
def ydpar(id):
    if 'loggedin' in session:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE id_user = %s', [session['id']])
        acc1 = cur.fetchone()

        cur.execute('SELECT * FROM users WHERE id_user = %s', (id,))
        acc2 = cur.fetchone()
        # print(pod)

        if len(acc2) == 0:
            return "Ошибка"

        cur.execute('delete from pars where (id_user1 = %s and id_user2 = %s) or (id_user1 = %s and id_user2 = %s)',
                    (acc1[0], acc2[0], acc2[0], acc1[0],))
        conn.commit()

        return redirect(url_for('par'))
    return redirect(url_for('login'))

# Страничка для удаления подписки (только для админестратора БД + триггер)
@app.route('/ydal_pod', methods=['GET', 'POST'])
def ydsub():
    if 'loggedin' in session:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('SELECT * FROM subscription;')
        sub = cur.fetchall()

        if request.method == 'POST':
            id = request.form['sub']
            if int(id) == 1:
                return "Удаление подписки запрещено"
            try:
                cur.execute(
                    "delete from subscription where id_subscription = %s;",
                    id)
                conn.commit()
                cur.close()
                conn.close()
                return redirect(url_for('homeadm'))
            except:
                return "Ошибка"

        return render_template('yd_pod.html', sub=sub)
    return redirect(url_for('login'))

# Страничка для удаления подписки (только для админестратора БД + триггер)
@app.route('/ydal_user', methods=['GET', 'POST'])
def yduser():
    if 'loggedin' in session:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('SELECT id_user, fullname, username, email, phone FROM users ORDER BY id_user;')
        users = cur.fetchall()

        if request.method == 'POST':
            id = request.form['user']

            try:
                cur.execute(
                    "DELETE FROM users WHERE id_user = %s;",
                    (id,))
                conn.commit()
                cur.close()
                conn.close()
                return redirect(url_for('homeadm'))
            except:
                return "Ошибка"

        return render_template('yd_user.html', users=users)
    return redirect(url_for('login'))



if __name__ == "__main__":
    app.run(debug=True)