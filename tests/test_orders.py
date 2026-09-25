import pytest

from app import db
from app.models import Order, Product


@pytest.fixture()
def produit(app):
    with app.app_context():
        product = Product(
            nom="Clavier",
            prix=49.99,
            description="Clavier mécanique",
            categorie="Informatique",
            quantite_stock=5,
        )
        db.session.add(product)
        db.session.commit()
        return {"id": product.id, "prix": product.prix}


def creer_commande(client, headers, product_id=None, quantity=1):
    payload = {"adresse_livraison": "1 rue des Tests"}
    if product_id is not None:
        payload["produits"] = [
            {"produit_id": product_id, "quantite": quantity}
        ]
    return client.post("/api/commandes", headers=headers, json=payload)


def test_creer_commande_avec_produits_et_mettre_a_jour_le_stock(
    client, app, client_auth, produit
):
    response = creer_commande(
        client, client_auth, produit["id"], quantity=2
    )

    assert response.status_code == 201
    order = response.get_json()
    assert order["adresse_livraison"] == "1 rue des Tests"
    assert order["statut"] == "en_attente"
    assert order["lignes"][0]["product_id"] == produit["id"]
    assert order["lignes"][0]["quantity"] == 2
    assert order["lignes"][0]["prix_unitaire"] == produit["prix"]

    with app.app_context():
        assert db.session.get(Product, produit["id"]).quantite_stock == 3


def test_refuser_une_commande_si_le_stock_est_insuffisant(
    client, app, client_auth, produit
):
    response = creer_commande(
        client, client_auth, produit["id"], quantity=6
    )

    assert response.status_code == 409

    with app.app_context():
        assert db.session.get(Product, produit["id"]).quantite_stock == 5
        assert db.session.query(Order).count() == 0


def test_liste_client_et_historique_sont_limites_a_ses_commandes(
    client, client_auth, second_client_auth
):
    own_order = creer_commande(client, client_auth)
    other_order = creer_commande(client, second_client_auth)

    assert own_order.status_code == 201
    assert other_order.status_code == 201

    response = client.get("/api/commandes", headers=client_auth)

    assert response.status_code == 200
    orders = response.get_json()["orders"]
    assert len(orders) == 1
    assert orders[0]["id"] == own_order.get_json()["id"]


def test_administrateur_voit_toutes_les_commandes(
    client, client_auth, second_client_auth, admin_auth
):
    first_order = creer_commande(client, client_auth)
    second_order = creer_commande(client, second_client_auth)

    response = client.get("/api/commandes", headers=admin_auth)

    assert response.status_code == 200
    order_ids = {order["id"] for order in response.get_json()["orders"]}
    assert order_ids == {
        first_order.get_json()["id"],
        second_order.get_json()["id"],
    }


def test_client_consulte_sa_commande_et_ses_lignes(
    client, client_auth, produit
):
    creation = creer_commande(client, client_auth, produit["id"], quantity=2)
    order_id = creation.get_json()["id"]

    detail = client.get(f"/api/commandes/{order_id}", headers=client_auth)
    lignes = client.get(
        f"/api/commandes/{order_id}/lignes", headers=client_auth
    )

    assert detail.status_code == 200
    assert lignes.status_code == 200
    assert lignes.get_json()["lignes"][0]["quantity"] == 2


def test_client_ne_peut_pas_consulter_la_commande_d_un_autre(
    client, client_auth, second_client_auth
):
    creation = creer_commande(client, client_auth)
    order_id = creation.get_json()["id"]

    detail = client.get(
        f"/api/commandes/{order_id}", headers=second_client_auth
    )
    lignes = client.get(
        f"/api/commandes/{order_id}/lignes", headers=second_client_auth
    )

    assert detail.status_code == 403
    assert lignes.status_code == 403


@pytest.mark.parametrize("statut", ["en attente", "validée", "expédiée", "annulée"])
def test_administrateur_peut_modifier_les_statuts(
    client, admin_auth, statut
):
    creation = creer_commande(client, admin_auth)
    order_id = creation.get_json()["id"]

    response = client.patch(
        f"/api/commandes/{order_id}",
        headers=admin_auth,
        json={"statut": statut},
    )

    assert response.status_code == 200
    assert response.get_json()["statut"] == statut.replace(" ", "_").replace(
        "é", "e"
    )


def test_client_ne_peut_pas_modifier_le_statut(client, client_auth, admin_auth):
    creation = creer_commande(client, client_auth)
    order_id = creation.get_json()["id"]

    response = client.patch(
        f"/api/commandes/{order_id}",
        headers=client_auth,
        json={"statut": "validée"},
    )

    assert response.status_code == 403


def test_annuler_une_commande_restitue_le_stock(
    client, app, admin_auth, produit
):
    creation = creer_commande(client, admin_auth, produit["id"], quantity=2)
    order_id = creation.get_json()["id"]

    response = client.patch(
        f"/api/commandes/{order_id}",
        headers=admin_auth,
        json={"statut": "annulée"},
    )

    assert response.status_code == 200
    assert response.get_json()["statut"] == "annulee"
    with app.app_context():
        assert db.session.get(Product, produit["id"]).quantite_stock == 5


def test_refuser_un_statut_invalide(client, admin_auth):
    creation = creer_commande(client, admin_auth)
    order_id = creation.get_json()["id"]

    response = client.patch(
        f"/api/commandes/{order_id}",
        headers=admin_auth,
        json={"statut": "livree"},
    )

    assert response.status_code == 400