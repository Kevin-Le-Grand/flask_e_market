from flask import Blueprint, jsonify, request  
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from .decorateur import admin_required

from app import db
from app.models import Order, OrderItem, Product

orders_bp = Blueprint("orders", __name__, url_prefix="/api/commandes")

STATUTS_COMMANDE = {
    "en_attente": "en_attente",
    "en attente": "en_attente",
    "validee": "validee",
    "validée": "validee",
    "expediee": "expediee",
    "expédiée": "expediee",
    "annulee": "annulee",
    "annulée": "annulee",
}

# Créer une nouvelle commande (POST /api/commandes)
@orders_bp.route("", methods=["POST"])
@jwt_required()
def create_order():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Aucune donnée reçue"}), 400

    current_user_id = int(get_jwt_identity())
    adresse_livraison = data.get("adresse_livraison")

    if not adresse_livraison:
        return jsonify({"error": "adresse_livraison est requise"}), 400

    lignes = data.get("produits", data.get("lignes", []))
    if not isinstance(lignes, list):
        return jsonify({"error": "produits doit être une liste"}), 400

    produits_commandes = []
    quantites_par_produit = {}
    for ligne in lignes:
        if not isinstance(ligne, dict):
            return jsonify({"error": "Chaque produit doit être un objet"}), 400

        product_id = ligne.get("produit_id", ligne.get("product_id"))
        quantite = ligne.get("quantite", ligne.get("quantity"))
        if product_id is None or quantite is None:
            return jsonify({"error": "produit_id et quantite sont requis"}), 400

        if isinstance(quantite, bool) or not isinstance(quantite, int) or quantite <= 0:
            return jsonify({"error": "La quantite doit être un entier positif"}), 400

        quantites_par_produit[product_id] = (
            quantites_par_produit.get(product_id, 0) + quantite
        )

    for product_id, quantite in quantites_par_produit.items():
        product = db.session.get(Product, product_id)
        if not product:
            return jsonify({"error": f"Produit {product_id} non trouvé"}), 404
        if product.quantite_stock < quantite:
            return jsonify({"error": f"Stock insuffisant pour le produit {product_id}"}), 409
        produits_commandes.append((product, quantite))

    order = Order(
        utilisateur_id=current_user_id,
        adresse_livraison=adresse_livraison,
    )

    for product, quantite in produits_commandes:
        product.quantite_stock -= quantite
        order.items.append(
            OrderItem(
                product=product,
                quantity=quantite,
                prix_unitaire=product.prix,
            )
        )

    try:
        db.session.add(order)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Erreur lors de la création de la commande"}), 500

    return jsonify(order.to_dict()), 201

# Récupérer la liste des commandes (GET /api/commandes) - Admin voit tout, client voit ses commandes
@orders_bp.route("", methods=["GET"])
@jwt_required()
def get_orders():
    claims = get_jwt()
    current_user_id = int(get_jwt_identity())

    if claims.get("role") == "admin":
        orders = db.session.scalars(
            select(Order).order_by(Order.date_commande.desc())
        ).all()
    else:
        orders = db.session.scalars(
            select(Order)
            .where(Order.utilisateur_id == current_user_id)
            .order_by(Order.date_commande.desc())
        ).all()

    return jsonify({
        "orders": [order.to_dict() for order in orders]
    }), 200 

# Récupérer une commande spécifique (GET /api/commandes/{id})
@orders_bp.route("/<int:order_id>", methods=["GET"])
@jwt_required()
def get_order(order_id):
    claims = get_jwt()
    current_user_id = int(get_jwt_identity())

    order = db.session.get(Order, order_id)

    if not order:
        return jsonify({"error": "Commande non trouvée"}), 404

    if claims.get("role") != "admin" and order.utilisateur_id != current_user_id:
        return jsonify({"error": "Accès refusé"}), 403

    return jsonify(order.to_dict()), 200



# Modifier le statut d'une commande (PATCH /api/commandes/{id}) - Admin uniquement
@orders_bp.route("/<int:order_id>", methods=["PATCH"])
@admin_required()
def update_order_status(order_id):
    order = db.session.get(Order, order_id)

    if not order:
        return jsonify({"error": "Commande non trouvée"}), 404

    data = request.get_json(silent=True)

    if not data or "statut" not in data:
        return jsonify({"error": "Le statut est requis"}), 400

    statut = data["statut"]
    if statut not in STATUTS_COMMANDE:
        return jsonify({
            "error": "Statut invalide",
            "statuts_acceptes": [
                "en attente", "validée", "expédiée", "annulée"
            ],
        }), 400

    statut = STATUTS_COMMANDE[statut]
    if order.statut == "annulee" and statut != "annulee":
        return jsonify({
            "error": "Une commande annulée ne peut plus être modifiée"
        }), 400

    if order.statut != "annulee" and statut == "annulee":
        for item in order.items:
            item.product.quantite_stock += item.quantity

    order.statut = statut

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

    order = db.session.get(Order, order_id)

    if not order:
        return jsonify({"error": "Commande non trouvée"}), 404

    if claims.get("role") != "admin" and order.utilisateur_id != current_user_id:
        return jsonify({"error": "Accès refusé"}), 403

    return jsonify({
        "lignes": [item.to_dict() for item in order.items]
    }), 200