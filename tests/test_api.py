from app import db
from app.models import User


# Helpers utilises par les tests d'authentification et d'autorisation.
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


def connecter_utilisateur(client, email="client@example.com"):
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 200
    return response.get_json()["access_token"]


def creer_entetes_authentification(token):
    return {"Authorization": f"Bearer {token}"}


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


def test_client_ne_peut_pas_gerer_les_produits(client):
    inscrire_utilisateur(client)
    token = connecter_utilisateur(client)

    response = client.post(
        "/api/produits",
        headers=creer_entetes_authentification(token),
        json={
            "nom": "Clavier",
            "prix": 49.99,
            "categorie": "Informatique",
            "quantite_stock": 5,
        },
    )

    assert response.status_code == 403


def test_administrateur_peut_creer_modifier_supprimer_produit(client, app):
    with app.app_context():
        admin = User(nom="admin", email="admin@example.com", role="admin")
        admin.set_password("password123")
        db.session.add(admin)
        db.session.commit()

    token = connecter_utilisateur(client, "admin@example.com")
    headers = creer_entetes_authentification(token)
    product_data = {
        "nom": "Clavier",
        "prix": 49.99,
        "categorie": "Informatique",
        "quantite_stock": 5,
    }

    create_response = client.post(
        "/api/produits", headers=headers, json=product_data
    )
    assert create_response.status_code == 201
    product_id = create_response.get_json()["id"]

    update_response = client.put(
        f"/api/produits/{product_id}",
        headers=headers,
        json={"nom": "Clavier mecanique"},
    )
    assert update_response.status_code == 200
    assert update_response.get_json()["nom"] == "Clavier mecanique"

    delete_response = client.delete(
        f"/api/produits/{product_id}", headers=headers
    )
    assert delete_response.status_code == 200


def test_utilisateur_authentifie_peut_creer_et_lister_commandes(client):
    inscrire_utilisateur(client)
    token = connecter_utilisateur(client)
    headers = creer_entetes_authentification(token)

    invalid_response = client.post(
        "/api/commandes", headers=headers, json={}
    )
    assert invalid_response.status_code == 400

    create_response = client.post(
        "/api/commandes",
        headers=headers,
        json={"adresse_livraison": "1 rue des Tests"},
    )
    assert create_response.status_code == 201
    assert create_response.get_json()["adresse_livraison"] == "1 rue des Tests"

    list_response = client.get("/api/commandes", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.get_json()["orders"]) == 1


# Tests des routes de consultation et des regles de visibilite des commandes.
def test_commandes_exigent_une_authentification(client):
    response = client.get("/api/commandes")

    assert response.status_code == 401


def test_utilisateur_peut_consulter_sa_commande_et_ses_lignes(client):
    inscrire_utilisateur(client)
    token = connecter_utilisateur(client)
    headers = creer_entetes_authentification(token)

    creation = client.post(
        "/api/commandes",
        headers=headers,
        json={"adresse_livraison": "1 rue des Tests"},
    )
    commande_id = creation.get_json()["id"]

    detail = client.get(f"/api/commandes/{commande_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.get_json()["adresse_livraison"] == "1 rue des Tests"

    lignes = client.get(
        f"/api/commandes/{commande_id}/lignes", headers=headers
    )
    assert lignes.status_code == 200
    assert lignes.get_json() == {"lignes": []}


def test_utilisateur_ne_peut_pas_consulter_la_commande_d_un_autre(client, app):
    inscrire_utilisateur(client)
    premier_token = connecter_utilisateur(client)
    premiere_commande = client.post(
        "/api/commandes",
        headers=creer_entetes_authentification(premier_token),
        json={"adresse_livraison": "1 rue des Tests"},
    )
    commande_id = premiere_commande.get_json()["id"]

    inscrire_utilisateur(
        client, nom="second_client", email="second@example.com"
    )
    second_token = connecter_utilisateur(client, "second@example.com")

    detail = client.get(
        f"/api/commandes/{commande_id}",
        headers=creer_entetes_authentification(second_token),
    )
    assert detail.status_code == 403
    assert detail.get_json()["error"] == "Accès refusé"


def test_administrateur_peut_voir_toutes_les_commandes_et_modifier_statut(
    client, app
):
    inscrire_utilisateur(client)
    client_token = connecter_utilisateur(client)
    creation = client.post(
        "/api/commandes",
        headers=creer_entetes_authentification(client_token),
        json={"adresse_livraison": "1 rue des Tests"},
    )
    commande_id = creation.get_json()["id"]

    with app.app_context():
        administrateur = User(
            nom="admin", email="admin@example.com", role="admin"
        )
        administrateur.set_password("password123")
        db.session.add(administrateur)
        db.session.commit()

    admin_token = connecter_utilisateur(client, "admin@example.com")
    admin_headers = creer_entetes_authentification(admin_token)

    liste = client.get("/api/commandes", headers=admin_headers)
    assert liste.status_code == 200
    assert len(liste.get_json()["orders"]) == 1

    modification = client.patch(
        f"/api/commandes/{commande_id}",
        headers=admin_headers,
        json={"statut": "expediee"},
    )
    assert modification.status_code == 200
    assert modification.get_json()["statut"] == "expediee"


def test_client_ne_peut_pas_modifier_le_statut_d_une_commande(client):
    inscrire_utilisateur(client)
    token = connecter_utilisateur(client)
    headers = creer_entetes_authentification(token)

    creation = client.post(
        "/api/commandes",
        headers=headers,
        json={"adresse_livraison": "1 rue des Tests"},
    )
    commande_id = creation.get_json()["id"]

    modification = client.patch(
        f"/api/commandes/{commande_id}",
        headers=headers,
        json={"statut": "expediee"},
    )
    assert modification.status_code == 403


def test_modifier_commande_exige_un_statut(client, app):
    inscrire_utilisateur(client)
    client_token = connecter_utilisateur(client)
    creation = client.post(
        "/api/commandes",
        headers=creer_entetes_authentification(client_token),
        json={"adresse_livraison": "1 rue des Tests"},
    )
    commande_id = creation.get_json()["id"]

    with app.app_context():
        administrateur = User(
            nom="admin", email="admin@example.com", role="admin"
        )
        administrateur.set_password("password123")
        db.session.add(administrateur)
        db.session.commit()

    token = connecter_utilisateur(client, "admin@example.com")
    response = client.patch(
        f"/api/commandes/{commande_id}",
        headers=creer_entetes_authentification(token),
        json={},
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Le statut est requis"