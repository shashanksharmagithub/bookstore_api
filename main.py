from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import Session, select
from database import create_db_and_tables, get_session
from models import Book, BookCreate, BookUpdate

app = FastAPI(title="Bookstore API", version="1.0.0")


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


# ── CREATE ──────────────────────────────────────────────
@app.post("/books", response_model=Book, status_code=201)
def create_book(book: BookCreate, session: Session = Depends(get_session)):
    db_book = Book.model_validate(book)
    session.add(db_book)
    session.commit()
    session.refresh(db_book)
    return db_book


# ── READ ALL ─────────────────────────────────────────────
@app.get("/books", response_model=list[Book])
def get_books(
    skip: int = 0,
    limit: int = 10,
    session: Session = Depends(get_session),
):
    books = session.exec(select(Book).offset(skip).limit(limit)).all()
    return books


# ── READ ONE ─────────────────────────────────────────────
@app.get("/books/{book_id}", response_model=Book)
def get_book(book_id: int, session: Session = Depends(get_session)):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


# ── UPDATE ───────────────────────────────────────────────
@app.patch("/books/{book_id}", response_model=Book)
def update_book(
    book_id: int,
    book_data: BookUpdate,
    session: Session = Depends(get_session),
):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    update_fields = book_data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(book, field, value)

    session.add(book)
    session.commit()
    session.refresh(book)
    return book


# ── DELETE ───────────────────────────────────────────────
@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int, session: Session = Depends(get_session)):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    session.delete(book)
    session.commit()
