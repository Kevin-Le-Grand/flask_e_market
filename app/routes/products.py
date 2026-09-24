from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from .decorateur import admin_required
from flask_jwt_extended import jwt_required


from app import db
from app.models import Product

products_bp = Blueprint("products", __name__, url_prefix="/api/produits")



@products_bp.route("", methods=["GET"])
@jwt_required()
# Récupérer la liste des produits (GET /api/produits)
def get_products():
    products = Product.query.all()
    return jsonify([product.to_dict() for product in products]), 200

@products_bp.route("/<int:product_id>", methods=["GET"])
@jwt_required()
def get_id_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Produit non trouvé"}), 404
    return product.to_dict(), 200

# Créer un nouveau produit (POST /api/produits) - Admin uniquement
@products_bp.route("", methods=["POST"])
@admin_required()
def create_product():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Aucune donnée reçue"}), 400

    nom = data.get("nom")
    price = data.get("prix")
    description = data.get("description")
    categorie = data.get("categorie")
    quantite_stock = data.get("quantite_stock")

    if not nom or not price:
        return jsonify({"error": "nom and price are required"}), 400

    product = Product(nom=nom, 
                      prix=price, 
                      description=description,
                      categorie = categorie,
                      quantite_stock = quantite_stock)

    try:
        db.session.add(product)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Un produit avec ces informations existe déjà"}), 409

    return jsonify(product.to_dict()), 201


# Modifier un produit existant (PUT /api/produits/{id}) - Admin uniquement
@products_bp.route("/<int:product_id>", methods=["PUT"])
@admin_required()
def update_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Produit non trouvé"}), 404

    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Aucune donnée reçue"}), 400

    nom = data.get("nom")
    prix = data.get("prix")
    description = data.get("description")
    categorie = data.get("categorie")
    quantite_stock = data.get("quantite_stock")
    
    if nom:
        product.nom = nom
    if prix:
        product.prix = prix
    if description:
        product.description = description
    if categorie:
        product.categorie = categorie
    if quantite_stock :
        product.quantite_stock = quantite_stock

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Erreur lors de la mise à jour du produit"}), 500

    return jsonify(product.to_dict()), 200


# Supprimer un produit (DELETE /api/produits/{id}) - Admin uniquement
@products_bp.route("/<int:product_id>", methods=["DELETE"])
@admin_required()
def delete_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Produit non trouvé"}), 404

    try:
        db.session.delete(product)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Erreur lors de la suppression du produit"}), 500

    return jsonify({"message": "Produit supprimé avec succès"}), 200