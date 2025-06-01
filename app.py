from flask import Flask
from config import Config
from extensions import db, login_manager, bcrypt
from flask_migrate import Migrate


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    migrate = Migrate(app, db)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    from routes.auth_routes import auth_bp
    from routes.film_routes import film_bp
    from routes.user_routes import user_bp
    from routes.admin_routes import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(film_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        db.create_all()

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
