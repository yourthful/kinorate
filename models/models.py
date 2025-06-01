from extensions import db, login_manager
from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

user_films = db.Table('user_films',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('film_id', db.Integer, db.ForeignKey('film.id'))
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    comments = db.relationship('Comment', backref='author', lazy=True, cascade="all, delete-orphan")
    ratings = db.relationship('Rating', backref='rater', lazy=True, cascade="all, delete-orphan")
    comment_likes = db.relationship('CommentLike', backref='user', lazy=True, cascade="all, delete-orphan")

class Film(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    year = db.Column(db.String(10))
    genre = db.Column(db.String(50))
    description = db.Column(db.Text)
    poster_url = db.Column(db.String(200))
    
    comments = db.relationship('Comment', backref='film', lazy=True, cascade="all, delete-orphan")
    ratings = db.relationship('Rating', backref='film', lazy=True, cascade="all, delete-orphan")

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    film_id = db.Column(db.Integer, db.ForeignKey('film.id', ondelete="CASCADE"), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id', ondelete="CASCADE"), nullable=True)
    is_deleted = db.Column(db.Boolean, default=False)

    replies = db.relationship(
        'Comment',
        backref=db.backref('parent', remote_side=[id]),
        lazy='dynamic',
        cascade="all, delete-orphan"
    )

    likes_list = db.relationship(
        'CommentLike',
        backref='comment',
        lazy=True,
        cascade="all, delete-orphan",
        passive_deletes=True
    )

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    film_id = db.Column(db.Integer, db.ForeignKey('film.id', ondelete="CASCADE"), nullable=False)

class CommentLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id', ondelete="CASCADE"), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'comment_id', name='unique_user_comment_like'),
    )
