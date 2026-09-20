from flask import Flask

from .config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager

jwt = JWTManager()
db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    jwt.init_app(app)

    from .routes.auth import auth_bp
    from .routes.orders import orders_bp
    from .routes.products import products_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(products_bp, url_prefix="/api/produits")
    app.register_blueprint(orders_bp, url_prefix="/api/commandes")

    @app.get("/health")
    def health_check():
        return {"status": "ok"}

    return app