from typing import Optional
from sqlmodel import Field, SQLModel


# ── DB Table ─────────────────────────────────────────────
class Book(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True, min_length=1, max_length=200)
    author: str = Field(min_length=1, max_length=100)
    year: int = Field(ge=0, le=2100)
    price: float = Field(gt=0)
    in_stock: bool = Field(default=True)


# ── Request body: create (all fields required) ────────────
class BookCreate(SQLModel):
    title: str = Field(min_length=1, max_length=200)
    author: str = Field(min_length=1, max_length=100)
    year: int = Field(ge=0, le=2100)
    price: float = Field(gt=0)
    in_stock: bool = True


# ── Request body: update (all fields optional) ────────────
class BookUpdate(SQLModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    author: Optional[str] = Field(default=None, min_length=1, max_length=100)
    year: Optional[int] = Field(default=None, ge=0, le=2100)
    price: Optional[float] = Field(default=None, gt=0)
    in_stock: Optional[bool] = None
