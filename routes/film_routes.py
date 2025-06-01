from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import current_user, login_required
from app import db
from models.models import Film, Comment, Rating, CommentLike
from sqlalchemy import or_, and_, exists

film_bp = Blueprint('film', __name__)

from flask import Blueprint, render_template, request
from flask_login import current_user
from app import db
from models.models import Film
from sqlalchemy import func

film_bp = Blueprint('film', __name__)

@film_bp.route('/')
def index():
    # Получаем параметры из запроса
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 6, type=int)
    search = request.args.get('search', '')
    genre = request.args.get('genre', '')
    year = request.args.get('year', '')
    sort = request.args.get('sort', 'newest')
    
    # Базовый запрос
    films_query = Film.query
    
    # Фильтрация
    if search:
        films_query = films_query.filter(Film.title.ilike(f'%{search}%'))
    if genre:
        films_query = films_query.filter(Film.genre.ilike(f'%{genre}%'))
    if year:
        films_query = films_query.filter(Film.year == year)
    
    # Сортировка
    if sort == 'newest':
        films_query = films_query.order_by(Film.id.desc())
    elif sort == 'oldest':
        films_query = films_query.order_by(Film.id.asc())
    elif sort == 'top_rated':
        films_query = films_query.outerjoin(Film.ratings).group_by(Film.id).order_by(func.avg(Rating.score).desc())
    elif sort == 'most_rated':
        films_query = films_query.outerjoin(Film.ratings).group_by(Film.id).order_by(func.count(Rating.id).desc())
    
    # Пагинация
    films = films_query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Получаем уникальные жанры и годы для фильтров
    genres = db.session.query(Film.genre).distinct().all()
    years = db.session.query(Film.year).distinct().order_by(Film.year.desc()).all()
    
    return render_template('index.html',
                         films=films,
                         search=search,
                         genre=genre,
                         year=year,
                         sort=sort,
                         genres=[g[0] for g in genres if g[0]],
                         years=[y[0] for y in years if y[0]])

@film_bp.route('/film/<int:film_id>', methods=['GET', 'POST'])
def film_detail(film_id):
    film = Film.query.get_or_404(film_id)

    if request.method == 'POST':
        if not current_user.is_authenticated:
            flash('Войдите, чтобы комментировать или оценивать.', 'warning')
            return redirect(url_for('auth.login'))

        content = request.form.get('comment')
        score = request.form.get('rating')

        # Обработка комментария
        if content:
            comment = Comment(content=content, author=current_user, film=film)
            db.session.add(comment)

        # Обработка рейтинга
        existing_rating = Rating.query.filter_by(user_id=current_user.id, film_id=film.id).first()
        if not existing_rating and score:
            try:
                score_int = int(score)
                rating = Rating(score=score_int, rater=current_user, film=film)
                db.session.add(rating)
            except ValueError:
                pass

        db.session.commit()
        flash('Ваш отзыв сохранен.', 'success')
        return redirect(url_for('film.film_detail', film_id=film.id))

    # --- Новый блок: определяем пользователей с неудалёнными комментариями ---
    active_comment_user_ids = db.session.query(Comment.user_id).filter_by(film_id=film.id, is_deleted=False).distinct().all()
    active_user_ids = [uid for (uid,) in active_comment_user_ids]

    # Фильтруем оценки по ним
    filtered_ratings = Rating.query.filter(Rating.film_id == film.id, Rating.user_id.in_(active_user_ids)).all()

    # Вычисляем среднюю оценку
    avg_rating = None
    if filtered_ratings:
        avg_rating = round(sum(r.score for r in filtered_ratings) / len(filtered_ratings), 1)

    # Оценка текущего пользователя
    user_rating = None
    if current_user.is_authenticated:
        rating = Rating.query.filter_by(user_id=current_user.id, film_id=film.id).first()
        if rating:
            user_rating = rating.score

    # Комментарии (все, включая удалённые)
    comments = Comment.query.filter_by(film_id=film.id).order_by(Comment.date_posted.desc()).all()

    # Оценки для отображения рядом с комментариями
    comment_ratings = {}
    for comment in comments:
        rating = Rating.query.filter_by(user_id=comment.user_id, film_id=film.id).first()
        comment_ratings[comment.id] = rating.score if rating else None

    return render_template('film_detail.html',
                           film=film,
                           comments=comments,
                           avg_rating=avg_rating,
                           user_rating=user_rating,
                           comment_ratings=comment_ratings)



@film_bp.route('/like/<int:comment_id>', methods=['POST'])
@login_required
def like(comment_id):
    comment = Comment.query.get_or_404(comment_id)

    # Проверяем, ставил ли уже лайк текущий пользователь
    existing_like = CommentLike.query.filter_by(user_id=current_user.id, comment_id=comment.id).first()
    if existing_like:
        flash('Вы уже лайкали этот комментарий.', 'warning')
    else:
        new_like = CommentLike(user_id=current_user.id, comment_id=comment.id)
        db.session.add(new_like)
        # Обновляем число лайков (если хотите хранить кеш)
        comment.likes = CommentLike.query.filter_by(comment_id=comment.id).count()
        db.session.commit()
        flash('Лайк добавлен.', 'success')

    return redirect(request.referrer or url_for('film.film_detail', film_id=comment.film_id))



@film_bp.route('/reply/<int:comment_id>', methods=['POST'])
@login_required
def reply(comment_id):
    parent = Comment.query.get_or_404(comment_id)
    content = request.form.get('reply_content')
    if content:
        reply = Comment(
            content=content,
            user_id=current_user.id,
            film_id=parent.film_id,
            parent_id=parent.id
        )
        db.session.add(reply)
        db.session.commit()
    return redirect(request.referrer or url_for('main.index'))

@film_bp.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if not current_user.is_admin:
        abort(403)
    
    comment.content = "Комментарий был удален модерацией"
    comment.is_deleted = True
    db.session.commit()
    flash('Комментарий удалён.', 'success')
    return redirect(request.referrer or url_for('main.index'))
