from functools import wraps

from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt


def admin_required():
    def decorator(fn):

        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):

            claims = get_jwt()

            if claims.get("role") != "admin":
                return jsonify({
                    "error": "Accès réservé aux administrateurs"
                }), 403

            return fn(*args, **kwargs)

        return wrapper

    return decorator