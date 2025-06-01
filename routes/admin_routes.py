from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app import db
from models.models import Film

admin_bp = Blueprint('admin', __name__)

def admin_required(func):
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Требуются права администратора.', 'danger')
            return redirect(url_for('auth.login'))
        return func(*args, **kwargs)
    return wrapper

@admin_bp.route('/admin')
@login_required
@admin_required
def admin_panel():
    films = Film.query.all()
    return render_template('admin_panel.html', films=films)

@admin_bp.route('/admin/add_film', methods=['GET', 'POST'])
@login_required
@admin_required
def add_film():
    if request.method == 'POST':
        title = request.form['title']
        year = request.form['year']
        genre = request.form['genre']
        description = request.form['description']
        poster_url = request.form['poster_url']
        film = Film(title=title, year=year, genre=genre,
                    description=description, poster_url=poster_url)
        db.session.add(film)
        db.session.commit()
        flash('Фильм добавлен.', 'success')
        return redirect(url_for('admin.admin_panel'))
    return render_template('add_film.html')

@admin_bp.route('/delete/<int:film_id>', methods=['POST'])
@login_required
def delete_film(film_id):
    if not current_user.is_admin:
        flash("Доступ запрещён.", "danger")
        return redirect(url_for('film.index'))
    
    film = Film.query.get_or_404(film_id)
    db.session.delete(film)
    db.session.commit()
    flash(f"Фильм «{film.title}» удалён.", "success")
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin:
        return redirect(url_for('film.index'))
    films = Film.query.all()
    return render_template('admin_dashboard.html', films=films)
