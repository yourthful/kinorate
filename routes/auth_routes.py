from flask import Blueprint, render_template, redirect, url_for, flash, request
from app import db, bcrypt
from models.models import User
from flask_login import login_user, logout_user, login_required, current_user

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('film.index'))
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password=hashed_pw)

        if User.query.filter_by(email=email).first():
            flash('Email уже занят', 'danger')
            return redirect(url_for('auth.register'))
        if User.query.filter_by(username=username).first():
            flash('Имя пользователя уже занято', 'danger')
            return redirect(url_for('auth.register'))

        db.session.add(user)
        db.session.commit()
        flash('Аккаунт создан! Теперь войдите.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('film.index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Вы вошли в систему.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('film.index'))
        else:
            flash('Неверный логин или пароль.', 'danger')
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('film.index'))
