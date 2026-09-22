from flask import Blueprint, jsonify, request  
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from sqlalchemy.exc import IntegrityError
from .decorateur import admin_required

from app import db
from app.models import Order

orders_bp = Blueprint("orders", __name__, url_prefix="/api/commandes")

# Récupérer la liste des commandes (GET /api/commandes) - Admin voit tout, client voit ses commandes
@orders_bp.route("", methods=["GET"])
@jwt_required()
def get_orders():
    claims = get_jwt()
    current_user_id = int(get_jwt_identity())

    if claims.get("role") == "admin":
        orders = Order.query.order_by(Order.date_commande.desc()).all()
    else:
        orders = Order.query.filter_by(utilisateur_id=current_user_id).order_by(Order.date_commande.desc()).all()

    return jsonify({
        "orders": [order.to_dict() for order in orders]
    }), 200 

# Récupérer une commande spécifique (GET /api/commandes/{id})
@orders_bp.route("/<int:order_id>", methods=["GET"])
@jwt_required()
def get_order(order_id):
    claims = get_jwt()
    current_user_id = int(get_jwt_identity())

    order = Order.query.get(order_id)

    if not order:
        return jsonify({"error": "Commande non trouvée"}), 404

    if claims.get("role") != "admin" and order.utilisateur_id != current_user_id:
        return jsonify({"error": "Accès refusé"}), 403

    return jsonify(order.to_dict()), 200

# Créer une nouvelle commande (POST /api/commandes)
@orders_bp.route("", methods=["POST"])
@jwt_required()
def create_order():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Aucune donnée reçue"}), 400

    current_user_id = int(get_jwt_identity())
    order = Order(utilisateur_id=current_user_id, details=data.get("details"))

    try:
        db.session.add(order)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Erreur lors de la création de la commande"}), 500

    return jsonify(order.to_dict()), 201

# Modifier le statut d'une commande (PATCH /api/commandes/{id}) - Admin uniquement
@orders_bp.route("/<int:order_id>", methods=["PATCH"])
@admin_required()
def update_order_status(order_id):
    order = Order.query.get(order_id)

    if not order:
        return jsonify({"error": "Commande non trouvée"}), 404

    data = request.get_json(silent=True)

    if not data or "statut" not in data:
        return jsonify({"error": "Le statut est requis"}), 400

    order.statut = data["statut"]

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Erreur lors de la mise à jour de la commande"}), 500

    return jsonify(order.to_dict()), 200


# Consulter les lignes d'une commande (GET /api/commandes/{id}/lignes)
@orders_bp.route("/<int:order_id>/lignes", methods=["GET"])
@jwt_required()
def get_order_items(order_id):
    claims = get_jwt()
    current_user_id = int(get_jwt_identity())

    order = Order.query.get(order_id)

    if not order:
        return jsonify({"error": "Commande non trouvée"}), 404

    if claims.get("role") != "admin" and order.utilisateur_id != current_user_id:
        return jsonify({"error": "Accès refusé"}), 403

    return jsonify({
        "lignes": [item.to_dict() for item in order.items]
    }), 200