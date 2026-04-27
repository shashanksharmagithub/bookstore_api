"""
Full test suite for the Bookstore API.
Uses an in-memory SQLite DB so tests never touch bookstore.db.
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from main import app
from database import get_session

# ── Test DB setup ─────────────────────────────────────────
TEST_DATABASE_URL = "sqlite://"   # in-memory


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


# ── Helper ────────────────────────────────────────────────
SAMPLE_BOOK = {
    "title": "Clean Code",
    "author": "Robert C. Martin",
    "year": 2008,
    "price": 35.99,
    "in_stock": True,
}


def create_sample_book(client):
    response = client.post("/books", json=SAMPLE_BOOK)
    assert response.status_code == 201
    return response.json()


# ── CREATE ────────────────────────────────────────────────
def test_create_book(client):
    response = client.post("/books", json=SAMPLE_BOOK)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == SAMPLE_BOOK["title"]
    assert data["author"] == SAMPLE_BOOK["author"]
    assert data["id"] is not None


def test_create_book_missing_field(client):
    bad_payload = {"title": "Incomplete Book"}   # missing required fields
    response = client.post("/books", json=bad_payload)
    assert response.status_code == 422


def test_create_book_invalid_price(client):
    bad_payload = {**SAMPLE_BOOK, "price": -5.0}
    response = client.post("/books", json=bad_payload)
    assert response.status_code == 422


def test_create_book_empty_title(client):
    bad_payload = {**SAMPLE_BOOK, "title": ""}
    response = client.post("/books", json=bad_payload)
    assert response.status_code == 422


# ── READ ALL ──────────────────────────────────────────────
def test_get_books_empty(client):
    response = client.get("/books")
    assert response.status_code == 200
    assert response.json() == []


def test_get_books_returns_list(client):
    create_sample_book(client)
    create_sample_book(client)
    response = client.get("/books")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_books_pagination(client):
    for _ in range(5):
        create_sample_book(client)
    response = client.get("/books?skip=2&limit=2")
    assert response.status_code == 200
    assert len(response.json()) == 2


# ── READ ONE ──────────────────────────────────────────────
def test_get_book_by_id(client):
    book = create_sample_book(client)
    response = client.get(f"/books/{book['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == book["id"]


def test_get_book_not_found(client):
    response = client.get("/books/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Book not found"


# ── UPDATE ────────────────────────────────────────────────
def test_update_book_price(client):
    book = create_sample_book(client)
    response = client.patch(f"/books/{book['id']}", json={"price": 19.99})
    assert response.status_code == 200
    assert response.json()["price"] == 19.99
    assert response.json()["title"] == SAMPLE_BOOK["title"]   # unchanged


def test_update_book_not_found(client):
    response = client.patch("/books/9999", json={"price": 10.0})
    assert response.status_code == 404


def test_update_book_invalid_value(client):
    book = create_sample_book(client)
    response = client.patch(f"/books/{book['id']}", json={"price": 0})
    assert response.status_code == 422


def test_update_book_in_stock(client):
    book = create_sample_book(client)
    response = client.patch(f"/books/{book['id']}", json={"in_stock": False})
    assert response.status_code == 200
    assert response.json()["in_stock"] is False


# ── DELETE ────────────────────────────────────────────────
def test_delete_book(client):
    book = create_sample_book(client)
    response = client.delete(f"/books/{book['id']}")
    assert response.status_code == 204


def test_delete_book_not_found(client):
    response = client.delete("/books/9999")
    assert response.status_code == 404


def test_delete_then_get_returns_404(client):
    book = create_sample_book(client)
    client.delete(f"/books/{book['id']}")
    response = client.get(f"/books/{book['id']}")
    assert response.status_code == 404
