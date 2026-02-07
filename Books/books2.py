from typing import Optional
from fastapi import FastAPI, Body, HTTPException, Path, Query
from pydantic import BaseModel, Field
from starlette import status

import books

app = FastAPI()


class Book:
    id: int
    title: str
    author: str
    description: str
    rating: int
    published_date: int

    def __init__(
        self,
        id: int,
        title: str,
        author: str,
        description: str,
        rating: int,
        published_date: int,
    ):
        self.id = id
        self.title = title
        self.author = author
        self.description = description
        self.rating = rating
        self.published_date = published_date


class BookRequest(BaseModel):
    id: Optional[int] = Field(
        description="The ID is not needed on create", default=None
    )
    title: str = Field(min_length=3, max_length=100)
    author: str = Field(min_length=3, max_length=100)
    description: str = Field(min_length=3, max_length=100)
    rating: int = Field(gt=-1, lt=6, description="امتیاز باید بین 0 و 5 باشد")
    published_date: int = Field(gt=1999, lt=2031)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Title Two",
                    "author": "Author Two",
                    "description": "Description Two",
                    "rating": 4,
                    "published_date": 2029,
                }
            ]
        }
    }


BOOKS = [
    Book(
        id=1,
        title="Title One",
        author="Author One",
        description="Description One",
        rating=5,
        published_date=2030,
    ),
    Book(
        id=2,
        title="Title Two",
        author="Author Two",
        description="Description Two",
        rating=4,
        published_date=2030,
    ),
    Book(
        id=3,
        title="Title Three",
        author="Author Three",
        description="Description Three",
        rating=3,
        published_date=2029,
    ),
    Book(
        id=4,
        title="Title Four",
        author="Author Four",
        description="Description Four",
        rating=2,
        published_date=2028,
    ),
    Book(
        id=5,
        title="Title Five",
        author="Author Five",
        description="Description Five",
        rating=1,
        published_date=2027,
    ),
    Book(
        id=6,
        title="Title Six",
        author="Author Six",
        description="Description Six",
        rating=3,
        published_date=2026,
    ),
]


@app.get("/books", status_code=status.HTTP_200_OK)
async def read_all_books():
    return BOOKS


@app.get("/books/{book_id}", status_code=status.HTTP_200_OK)
async def read_book(book_id: int = Path(gt=0)):
    for book in BOOKS:
        if book.id == book_id:
            return book
    raise HTTPException(status_code=404, detail="Book not found")


@app.get("/books/", status_code=status.HTTP_200_OK)
async def read_book_by_rating(book_rating: int = Query(gt=0, lt=6)):
    books_to_return = []
    for book in BOOKS:
        if book.rating == book_rating:
            books_to_return.append(book)
    return books_to_return


@app.get("/books/publish/", status_code=status.HTTP_200_OK)
async def read_books_by_publish_date(published_date: int = Query(gt=1999, lt=2031)):
    books_to_return = []
    for book in BOOKS:
        if book.published_date == published_date:
            books_to_return.append(book)
    return books_to_return


@app.post("/create-book", status_code=status.HTTP_201_CREATED)
async def create_book(book_request: BookRequest = Body(...)):
    new_book = Book(**book_request.model_dump())
    BOOKS.append(find_book_id(new_book))
    return new_book


def find_book_id(book: Book):
    book.id = 1 if len(BOOKS) == 0 else BOOKS[-1].id + 1
    return book


@app.put("/books/update-book", status_code=status.HTTP_204_NO_CONTENT)
async def update_book(updated_book: BookRequest = Body(...)):
    for i in range(len(BOOKS)):
        if BOOKS[i].id == updated_book.id:
            BOOKS[i] = updated_book
            return updated_book
    raise HTTPException(status_code=404, detail="Book not found")


@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: int = Path(gt=0)):
    for i in range(len(BOOKS)):
        if BOOKS[i].id == book_id:
            BOOKS.pop(i)
            return {"message": "Book deleted successfully"}
    raise HTTPException(status_code=404, detail="Book not found")
