from flask import Flask, render_template, request, redirect, jsonify, json, session, abort
from schedule_access import *
from mail import send_mail
from security.crypting import get_link
from werkzeug.security import gen_salt
import os


tm = Flask(__name__, template_folder="../templates", static_folder="../../time_manager")
tm.config.from_object('config.Config')
users = {}


def user_req(url, img=None):
    def wrap(func):
        def wrapper():
            if session.get('login'):
                if users[session['login']].token == session['token']:
                    if img: data = request.files.get(img)
                    else: data = request.get_json()
                    if data:
                        temp = func(users[session['login']], data)
                    else: temp = func(users[session['login']])
                    if temp: return temp
                    else: return jsonify(True)
                else: abort(505)
            else: abort(505)
        tm.add_url_rule(url, func.__name__, wrapper, methods=['POST'])
    return wrap


@tm.errorhandler(505)
def handler_assignment(error):
    return '<h1 style="text-align: center">Неверная подпись запроса</h1>'

# Запасной перехватчик
# @tm.errorhandler(502)
# def handler_assignment(error):
#     return '<h1 style="text-align: center">Неверная подпись запроса</h1>'


# Верифицрованные запросы
@user_req('/send_activation')
def req_send_activation(now):
    """Отправка сообщения для активации"""
    if now.activated: return jsonify('active')
    else:
        data = {
            'title': 'Подтверждение почты',
            'login': now.log,
            'link': get_link(now.email),
            'color': now.color
        }
        send_mail(tm, now.email, data)
        return jsonify('nonactive')


@user_req('/change_theme')
def req_change_theme(now, data):
    """Изменение темы"""
    now.change_theme(*data.split())
    return jsonify(True)


@user_req('/change_log')
def req_change_log(now, data):
    """Изменение имени пользователя"""
    now.change_log(data)
    return jsonify(True)


@user_req('/change_email')
def req_change_email(now, data):
    """Изменение имени пользователя"""
    now.change_email(data)
    return jsonify(True)


@user_req('/change_pass')
def req_change_pass(now, data):
    """Изменение имени пользователя"""
    now.change_pass(data)
    return jsonify(True)


@user_req('/change_avatar', 'img')
def req_change_avatar(now, file):
    """Изменение аватарки"""
    temp_path = f'images/avatars/{now.log}.jpg'
    with open(temp_path, 'wb') as open_file:
        open_file.write(file.read())
    return jsonify(True)


@user_req('/delete_avatar')
def req_delete_avatar(now):
    """Удаление аватарки"""
    temp_path = f'images/avatars/{now.log}.jpg'
    if os.path.isfile(temp_path):
        os.unlink(temp_path)
    return jsonify(True)


@user_req('/logout')
def req_logout(now):
    """Выход пользователя"""
    users.pop(now.log)
    session.pop('login')
    session.pop('token')
    session.pop('remember')
    User.authorisation = False
    return jsonify(True)


@user_req('/delete_user')
def req_delete_user(now):
    """Удаление учётной записи"""
    temp_path = f'images/avatars/{now.log}.jpg'
    if os.path.isfile(temp_path): os.remove(temp_path)
    now.del_user()
    users.pop(now.log)
    session.pop('login')
    session.pop('token')
    session.pop('remember')
    User.authorisation = False
    return jsonify(True)


# Запросы
@tm.route('/activate/<link>', methods=['GET'])
def req_activate(link):
    temp = User.activate(link)
    if temp:
        log = temp[0]
        users[log] = User(log)
        session['login'] = log
        session['token'] = users[log].token
        session['remember'] = True
    return redirect('/')


@tm.route('/login', methods=['POST'])
def req_login():
    log, pswsalt, remember = request.get_json()
    if User.check_psw(log, pswsalt):
        u = User(log)
        users[u.log] = u
        session['login'] = u.log
        session['token'] = u.token
        session['remember'] = remember
        return jsonify({
            "login": u.log,
            "email": u.email,
            "theme": u.theme,
            "color": u.color,
            "avatar": os.path.isfile(f'images/avatars/{u.log}.jpg'),
            "activated": u.activated
        })
    else: redirect('/')


@tm.route('/register', methods=['POST'])
def req_register():
    temp = request.get_json()
    remember = temp.pop('remember')
    User.registration(**temp)
    users[temp['log']] = User(temp['log'])
    session['login'] = temp['log']
    session['token'] = users[temp['log']].token
    session['remember'] = remember
    return jsonify(True)


@tm.route('/get_key', methods=['POST'])
def req_get_key():
    """Отправка ключа"""
    return jsonify(open('modules/security/public_key.pem').read())


@tm.route('/check_user', methods=['POST'])
def req_check_user():
    """Проверка существования пользователя"""
    return jsonify(User.check_user(request.get_json()))


@tm.route('/check_password', methods=['POST'])
def req_fast_check_password():
    """Быстрая проверка пароля"""
    return jsonify(User.fast_check_psw(**request.get_json()))


@tm.route('/get_page', methods=['POST'])
def req_get_page():
    """Отсылка HTML шаблонов"""
    page = request.get_json()
    return render_template(f'{page}.html')


# Главная страница
@tm.route('/')
def page_home():
    session.permanent = True
    if session.get('remember') and session.get('login') and session.get('token') and users.get(session.get('login')):
        if session['token'] == users.get(session.get('login')).token:
            log = session['login']
            session['token'] = users[log].token = gen_salt(50)
            if os.path.isfile(f'images/avatars/{log}.jpg'): avatar = f'style="background-image: url(time_manager/images/avatars/{log}.jpg)"'
            else: avatar = ''
            data = {
                'profile_html': render_template('profile.html', login=log, avatar=avatar),
                'login': log,
                'email': users[log].email,
                'theme': users[log].theme,
                'color': users[log].color,
                'salt': users[log].salt,
                'activated': users[log].activated,
                'avatar': avatar
            }

            return render_template("base_log.html", **data)
    if session.get('login'): session.pop('login')
    if session.get('token'): session.pop('token')
    if session.get('remember'): session.pop('remember')
    return render_template("base.html")
