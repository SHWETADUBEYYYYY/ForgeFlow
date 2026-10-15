import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.database import Base, get_db
from backend.models import User, Product, CartItem, Order, OrderItem
from backend.auth import verify_password, create_session_token, init_session_serializer, generate_secret_key
from backend.seed_data import create_db_and_seed_data

# Setup for testing database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(name="session")
def session_fixture():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(name="client")
def client_fixture(session):
    def override_get_db():
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    init_session_serializer(generate_secret_key()) # Initialize session serializer for tests
    create_db_and_seed_data() # Seed data for each test run
    with TestClient(app) as c:
        yield c


def register_and_login(client, username, password):
    client.post("/api/auth/register", json={"username": username, "password": password})
    response = client.post("/api/auth/login", data={"username": username, "password": password})
    assert response.status_code == 200
    return response.cookies.get("session")


# --- Test Authentication Endpoints ---

def test_register_user(client):
    response = client.post("/api/auth/register", json={"username": "testuser", "password": "testpassword"})
    assert response.status_code == 200
    assert response.json() == {"message": "User registered successfully"}

    # Try registering with existing username
    response = client.post("/api/auth/register", json={"username": "testuser", "password": "anotherpassword"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Username already registered"}


def test_login_user(client):
    client.post("/api/auth/register", json={"username": "loginuser", "password": "loginpassword"})
    response = client.post("/api/auth/login", data={"username": "loginuser", "password": "loginpassword"})
    assert response.status_code == 200
    assert "session" in response.cookies

    # Test invalid credentials
    response = client.post("/api/auth/login", data={"username": "loginuser", "password": "wrongpassword"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


def test_logout_user(client):
    session_cookie = register_and_login(client, "logoutuser", "logoutpassword")
    response = client.post("/api/auth/logout", cookies={"session": session_cookie})
    assert response.status_code == 200
    assert response.json() == {"message": "Logged out successfully"}
    assert "session" not in response.cookies


def test_get_current_user_authenticated(client):
    session_cookie = register_and_login(client, "currentuser", "currentpassword")
    response = client.get("/api/auth/me", cookies={"session": session_cookie})
    assert response.status_code == 200
    assert response.json()["username"] == "currentuser"


def test_get_current_user_unauthenticated(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


# --- Test Product Endpoints ---

def test_get_products(client):
    response = client.get("/api/products/")
    assert response.status_code == 200
    products = response.json()
    assert len(products) > 0  # Assuming seed_database populates products
    assert "title" in products[0]
    assert "price" in products[0]


def test_get_product_by_id(client):
    # Assuming product with ID 1 exists from seeding
    response = client.get("/api/products/1")
    assert response.status_code == 200
    product = response.json()
    assert product["id"] == 1
    assert "title" in product

    response = client.get("/api/products/999")  # Non-existent product
    assert response.status_code == 404
    assert response.json() == {"detail": "Product not found"}


# --- Test Cart Endpoints ---

def test_add_to_cart(client):
    session_cookie = register_and_login(client, "cartuser", "cartpassword")
    response = client.post("/api/cart/add", json={"product_id": 1, "quantity": 1}, cookies={"session": session_cookie})
    assert response.status_code == 200
    assert response.json() == {"message": "Item added to cart"}

    # Add same item again, quantity should increase
    response = client.post("/api/cart/add", json={"product_id": 1, "quantity": 2}, cookies={"session": session_cookie})
    assert response.status_code == 200
    assert response.json() == {"message": "Item added to cart"}

    cart_response = client.get("/api/cart/", cookies={"session": session_cookie})
    assert cart_response.status_code == 200
    assert len(cart_response.json()["items"]) == 1
    assert cart_response.json()["items"][0]["quantity"] == 3


def test_add_to_cart_unauthenticated(client):
    response = client.post("/api/cart/add", json={"product_id": 1, "quantity": 1})
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_get_cart(client):
    session_cookie = register_and_login(client, "getcartuser", "getcartpassword")
    client.post("/api/cart/add", json={"product_id": 1, "quantity": 1}, cookies={"session": session_cookie})
    client.post("/api/cart/add", json={"product_id": 2, "quantity": 2}, cookies={"session": session_cookie})

    response = client.get("/api/cart/", cookies={"session": session_cookie})
    assert response.status_code == 200
    cart_data = response.json()
    assert len(cart_data["items"]) == 2
    assert cart_data["total_price"] > 0


def test_update_cart_item_quantity(client):
    session_cookie = register_and_login(client, "updatecartuser", "updatecartpassword")
    client.post("/api/cart/add", json={"product_id": 1, "quantity": 5}, cookies={"session": session_cookie})

    response = client.put("/api/cart/update", json={"product_id": 1, "quantity": 3}, cookies={"session": session_cookie})
    assert response.status_code == 200
    assert response.json() == {"message": "Cart item quantity updated"}

    cart_response = client.get("/api/cart/", cookies={"session": session_cookie})
    assert cart_response.status_code == 200
    assert cart_response.json()["items"][0]["quantity"] == 3

    # Update to 0 quantity should remove item
    response = client.put("/api/cart/update", json={"product_id": 1, "quantity": 0}, cookies={"session": session_cookie})
    assert response.status_code == 200
    assert response.json() == {"message": "Cart item removed"}

    cart_response = client.get("/api/cart/", cookies={"session": session_cookie})
    assert cart_response.status_code == 200
    assert len(cart_response.json()["items"]) == 0


def test_remove_from_cart(client):
    session_cookie = register_and_login(client, "removecartuser", "removecartpassword")
    client.post("/api/cart/add", json={"product_id": 1, "quantity": 1}, cookies={"session": session_cookie})

    response = client.delete("/api/cart/remove/1", cookies={"session": session_cookie})
    assert response.status_code == 200
    assert response.json() == {"message": "Item removed from cart"}

    cart_response = client.get("/api/cart/", cookies={"session": session_cookie})
    assert cart_response.status_code == 200
    assert len(cart_response.json()["items"]) == 0


# --- Test Order Endpoints ---

def test_checkout(client):
    session_cookie = register_and_login(client, "checkoutuser", "checkoutpassword")
    client.post("/api/cart/add", json={"product_id": 1, "quantity": 1}, cookies={"session": session_cookie})
    client.post("/api/cart/add", json={"product_id": 2, "quantity": 2}, cookies={"session": session_cookie})

    response = client.post("/api/orders/checkout", cookies={"session": session_cookie})
    assert response.status_code == 200
    assert response.json() == {"message": "Checkout successful, order placed"}

    # Verify cart is empty after checkout
    cart_response = client.get("/api/cart/", cookies={"session": session_cookie})
    assert cart_response.status_code == 200
    assert len(cart_response.json()["items"]) == 0

    # Verify order exists
    orders_response = client.get("/api/orders/", cookies={"session": session_cookie})
    assert orders_response.status_code == 200
    orders = orders_response.json()
    assert len(orders) == 1
    assert len(orders[0]["items"]) == 2
    assert orders[0]["total_price"] > 0


def test_checkout_empty_cart(client):
    session_cookie = register_and_login(client, "emptycartuser", "emptycartpassword")
    response = client.post("/api/orders/checkout", cookies={"session": session_cookie})
    assert response.status_code == 400
    assert response.json() == {"detail": "Cart is empty"}


def test_get_orders(client):
    session_cookie = register_and_login(client, "ordersuser", "orderspassword")
    client.post("/api/cart/add", json={"product_id": 1, "quantity": 1}, cookies={"session": session_cookie})
    client.post("/api/orders/checkout", cookies={"session": session_cookie})

    client.post("/api/cart/add", json={"product_id": 2, "quantity": 3}, cookies={"session": session_cookie})
    client.post("/api/orders/checkout", cookies={"session": session_cookie})

    response = client.get("/api/orders/", cookies={"session": session_cookie})
    assert response.status_code == 200
    orders = response.json()
    assert len(orders) == 2
    assert orders[0]["id"] != orders[1]["id"]


def test_get_order_by_id(client):
    session_cookie = register_and_login(client, "singleorderuser", "singleorderpassword")
    client.post("/api/cart/add", json={"product_id": 1, "quantity": 1}, cookies={"session": session_cookie})
    client.post("/api/orders/checkout", cookies={"session": session_cookie})

    orders_response = client.get("/api/orders/", cookies={"session": session_cookie})
    order_id = orders_response.json()[0]["id"]

    response = client.get(f"/api/orders/{order_id}", cookies={"session": session_cookie})
    assert response.status_code == 200
    order = response.json()
    assert order["id"] == order_id
    assert len(order["items"]) == 1

    # Test getting another user's order (should fail)
    session_cookie_other = register_and_login(client, "otheruser", "otherpassword")
    response = client.get(f"/api/orders/{order_id}", cookies={"session": session_cookie_other})
    assert response.status_code == 404 # Or 403, depending on implementation, 404 is fine for not found for current user


def test_get_order_by_id_not_found(client):
    session_cookie = register_and_login(client, "notfoundorderuser", "notfoundorderpassword")
    response = client.get("/api/orders/999", cookies={"session": session_cookie})
    assert response.status_code == 404
    assert response.json() == {"detail": "Order not found"}
