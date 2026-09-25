from app import db
from app.models import Product


def inscrire_utilisateur(client, nom="client", email="client@example.com"):
    response = client.post(
        "/api/auth/register",
        json={
            "username": nom,
            "email": email,
            "password": "password123",
        },
    )
    assert response.status_code == 201

def test_verifier_etat_api(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_inscription_et_connexion_retournent_un_jwt(client):
    inscrire_utilisateur(client)

    response = client.post(
        "/api/auth/login",
        json={"email": "client@example.com", "password": "password123"},
    )

    assert response.status_code == 200
    assert response.get_json()["user"]["email"] == "client@example.com"
    assert response.get_json()["access_token"]


def test_produits_exigent_une_authentification(client):
    response = client.get("/api/produits")

    assert response.status_code == 401


def test_client_ne_peut_pas_gerer_les_produits(client, client_auth):
    response = client.post(
        "/api/produits",
        headers=client_auth,
        json={
            "nom": "Clavier",
            "prix": 49.99,
            "categorie": "Informatique",
            "quantite_stock": 5,
        },
    )

    assert response.status_code == 403


def test_recuperation_de_produits_par_nom_ou_description(client, app, client_auth):
    with app.app_context():
        product = Product(
            nom="Clavier",
            prix=49.99,
            description="Clavier mécanique",
            categorie="Informatique",
            quantite_stock=5
        )
        db.session.add(product)
        db.session.commit()

    response = client.get("/api/produits", query_string={"nom": "Clavier"}, headers=client_auth)
    assert response.status_code == 200
    assert len(response.get_json()) == 1

    response = client.get("/api/produits", query_string={"description": "mécanique"}, headers=client_auth)
    assert response.status_code == 200
    assert len(response.get_json()) == 1


def test_administrateur_peut_creer_modifier_supprimer_produit(client, admin_auth):
    product_data = {
        "nom": "Clavier",
        "prix": 49.99,
        "categorie": "Informatique",
        "quantite_stock": 5,
    }

    create_response = client.post(
        "/api/produits", headers=admin_auth, json=product_data
    )
    assert create_response.status_code == 201
    product_id = create_response.get_json()["id"]

    update_response = client.put(
        f"/api/produits/{product_id}",
        headers=admin_auth,
        json={"nom": "Clavier mecanique"},
    )
    assert update_response.status_code == 200
    assert update_response.get_json()["nom"] == "Clavier mecanique"

    delete_response = client.delete(
        f"/api/produits/{product_id}", headers=admin_auth
    )
    assert delete_response.status_code == 200


def test_utilisateur_authentifie_peut_creer_et_lister_commandes(client, client_auth):
    invalid_response = client.post(
        "/api/commandes", headers=client_auth, json={}
    )
    assert invalid_response.status_code == 400

    create_response = client.post(
        "/api/commandes",
        headers=client_auth,
        json={"adresse_livraison": "1 rue des Tests"},
    )
    assert create_response.status_code == 201
    assert create_response.get_json()["adresse_livraison"] == "1 rue des Tests"

    list_response = client.get("/api/commandes", headers=client_auth)
    assert list_response.status_code == 200
    assert len(list_response.get_json()["orders"]) == 1


# Tests des routes de consultation et des regles de visibilite des commandes.
def test_commandes_exigent_une_authentification(client):
    response = client.get("/api/commandes")

    assert response.status_code == 401


def test_utilisateur_peut_consulter_sa_commande_et_ses_lignes(client, client_auth):
    creation = client.post(
        "/api/commandes",
        headers=client_auth,
        json={"adresse_livraison": "1 rue des Tests"},
    )
    commande_id = creation.get_json()["id"]

    detail = client.get(f"/api/commandes/{commande_id}", headers=client_auth)
    assert detail.status_code == 200
    assert detail.get_json()["adresse_livraison"] == "1 rue des Tests"

    lignes = client.get(
        f"/api/commandes/{commande_id}/lignes", headers=client_auth
    )
    assert lignes.status_code == 200
    assert lignes.get_json() == {"lignes": []}


def test_utilisateur_ne_peut_pas_consulter_la_commande_d_un_autre(
    client, client_auth, second_client_auth
):
    premiere_commande = client.post(
        "/api/commandes",
        headers=client_auth,
        json={"adresse_livraison": "1 rue des Tests"},
    )
    commande_id = premiere_commande.get_json()["id"]

    detail = client.get(
        f"/api/commandes/{commande_id}",
        headers=second_client_auth,
    )
    assert detail.status_code == 403
    assert detail.get_json()["error"] == "Accès refusé"


def test_administrateur_peut_voir_toutes_les_commandes_et_modifier_statut(
    client, client_auth, admin_auth
):
    creation = client.post(
        "/api/commandes",
        headers=client_auth,
        json={"adresse_livraison": "1 rue des Tests"},
    )
    commande_id = creation.get_json()["id"]

    liste = client.get("/api/commandes", headers=admin_auth)
    assert liste.status_code == 200
    assert len(liste.get_json()["orders"]) == 1

    modification = client.patch(
        f"/api/commandes/{commande_id}",
        headers=admin_auth,
        json={"statut": "expediee"},
    )
    assert modification.status_code == 200
    assert modification.get_json()["statut"] == "expediee"


def test_client_ne_peut_pas_modifier_le_statut_d_une_commande(client, client_auth):
    creation = client.post(
        "/api/commandes",
        headers=client_auth,
        json={"adresse_livraison": "1 rue des Tests"},
    )
    commande_id = creation.get_json()["id"]

    modification = client.patch(
        f"/api/commandes/{commande_id}",
        headers=client_auth,
        json={"statut": "expediee"},
    )
    assert modification.status_code == 403


def test_modifier_commande_exige_un_statut(client, client_auth, admin_auth):
    creation = client.post(
        "/api/commandes",
        headers=client_auth,
        json={"adresse_livraison": "1 rue des Tests"},
    )
    commande_id = creation.get_json()["id"]

    response = client.patch(
        f"/api/commandes/{commande_id}",
        headers=admin_auth,
        json={},
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Le statut est requis"