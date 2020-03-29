from flask import Flask, render_template, request, redirect, jsonify, json, session
from schedule_access import *
tm = Flask(__name__, template_folder="../templates", static_folder="../../time_manager")

tm.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # В КОНЦЕ ПРОЕКТА УБРАТЬ СТРОКУ
tm.config['TEMPLATES_AUTO_RELOAD'] = False

User.guest_reset()
now = None


# Запросы
@tm.route('/login', methods=['POST'])
def login():
    global now
    now = User(*request.get_json())
    return jsonify({
        "login": now.log,
        "theme": now.theme[0],
        "color": now.theme[1],
        "avatar": now.avatar
    })


@tm.route('/get_page', methods=['POST'])
def get_page():
    """Отсылка HTML шаблонов"""
    page = request.get_json()
    return render_template(f'{page}.html')


@tm.route('/change_theme', methods=['POST'])
def change_theme():
    """Изменение темы"""
    now.change_theme(request.get_json().split())
    return jsonify(success=True)


@tm.route('/logout', methods=['POST'])
def logout():
    """Выход пользователя"""
    global now
    if now.log == 'Guest':
        now = User('Guest')
        now.del_user()
        del now
        now = User('Guest', 'best_team@gmail.com', 'День рождения Сталина')
    del now
    return jsonify(success=True)


@tm.route('/delete', methods=['POST'])
def delete():
    """Удаление учётной записи"""
    global now
    now.del_user()
    del now
    return jsonify(success=True)


# Страницы
@tm.route('/')
def page_home():
    return render_template("base.html")


@tm.route('/list')
def page_list():
    return 'list'


@tm.route('/day')
def page_day():
    return 'day'


@tm.route('/month')
def page_month():
    return 'month'


@tm.route('/about')
def page_about():
    return render_template("about.html")






