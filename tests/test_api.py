from app import db
from app.models import User


def register_user(client, username="client", email="client@example.com"):
    response = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "password123",
        },
    )
    assert response.status_code == 201


def login_user(client, email="client@example.com"):
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 200
    return response.get_json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_register_and_login_returns_jwt(client):
    register_user(client)

    response = client.post(
        "/api/auth/login",
        json={"email": "client@example.com", "password": "password123"},
    )

    assert response.status_code == 200
    assert response.get_json()["user"]["email"] == "client@example.com"
    assert response.get_json()["access_token"]


def test_products_require_authentication(client):
    response = client.get("/api/produits")

    assert response.status_code == 401


def test_client_cannot_manage_products(client):
    register_user(client)
    token = login_user(client)

    response = client.post(
        "/api/produits",
        headers=auth_headers(token),
        json={
            "nom": "Clavier",
            "prix": 49.99,
            "categorie": "Informatique",
            "quantite_stock": 5,
        },
    )

    assert response.status_code == 403


def test_admin_can_create_update_and_delete_product(client, app):
    with app.app_context():
        admin = User(nom="admin", email="admin@example.com", role="admin")
        admin.set_password("password123")
        db.session.add(admin)
        db.session.commit()

    token = login_user(client, "admin@example.com")
    headers = auth_headers(token)
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


def test_authenticated_user_can_create_and_list_orders(client):
    register_user(client)
    token = login_user(client)
    headers = auth_headers(token)

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