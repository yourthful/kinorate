from flask import Blueprint, render_template
from flask_login import login_required, current_user

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile')
@login_required
def profile():
    user_ratings = {r.film_id: r.score for r in current_user.ratings}
    comments = current_user.comments
    return render_template('profile.html', comments=comments, user_ratings=user_ratings)
