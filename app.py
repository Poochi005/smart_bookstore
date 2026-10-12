import math
import os
import sqlite3
from contextlib import closing
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "smart-bookstore-secret-key")

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "bookstore.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with closing(get_db()) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                price REAL NOT NULL,
                stock INTEGER NOT NULL DEFAULT 0,
                category TEXT DEFAULT 'General'
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                total REAL NOT NULL,
                sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (book_id) REFERENCES books(id)
            )
        """)
        count = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
        if count == 0:
            conn.executemany(
                "INSERT INTO books (title, author, price, stock, category) "
                "VALUES (?, ?, ?, ?, ?)",
                [
                    ("The Alchemist", "Paulo Coelho", 350, 10, "Fiction"),
                    ("Atomic Habits", "James Clear", 499, 15, "Self Help"),
                    ("Rich Dad Poor Dad", "Robert Kiyosaki", 399, 8, "Finance"),
                ],
            )
        conn.commit()


# Create tables on import so `flask run` / gunicorn work too,
# not only `python app.py`.
init_db()


@app.route("/")
def home():
    with closing(get_db()) as conn:
        books = conn.execute("SELECT * FROM books ORDER BY id DESC").fetchall()
        total_books = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
        total_stock = conn.execute(
            "SELECT COALESCE(SUM(stock), 0) FROM books"
        ).fetchone()[0]
        total_sales = conn.execute(
            "SELECT COALESCE(SUM(total), 0) FROM sales"
        ).fetchone()[0]
    return render_template(
        "index.html",
        books=books,
        total_books=total_books,
        total_stock=total_stock,
        total_sales=total_sales,
    )


@app.route("/add-book", methods=["GET", "POST"])
def add_book():
    form = {"title": "", "author": "", "category": "General", "price": "", "stock": ""}

    if request.method == "POST":
        form = {
            "title": request.form.get("title", "").strip(),
            "author": request.form.get("author", "").strip(),
            "category": request.form.get("category", "").strip() or "General",
            "price": request.form.get("price", "").strip(),
            "stock": request.form.get("stock", "").strip(),
        }

        try:
            price = float(form["price"])
            stock = int(form["stock"])
        except ValueError:
            flash("Price and stock must be valid numbers.", "error")
            return render_template("add_book.html", form=form)

        if (
            not form["title"]
            or not form["author"]
            or not math.isfinite(price)
            or price < 0
            or stock < 0
        ):
            flash("Please enter valid book details.", "error")
            return render_template("add_book.html", form=form)

        with closing(get_db()) as conn:
            conn.execute(
                "INSERT INTO books (title, author, price, stock, category) "
                "VALUES (?, ?, ?, ?, ?)",
                (form["title"], form["author"], price, stock, form["category"]),
            )
            conn.commit()
        flash("Book added successfully.", "success")
        return redirect(url_for("home"))

    return render_template("add_book.html", form=form)


@app.post("/delete-book/<int:book_id>")
def delete_book(book_id):
    with closing(get_db()) as conn:
        cur = conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
        conn.commit()
    if cur.rowcount:
        flash("Book deleted successfully.", "success")
    else:
        flash("Book not found.", "error")
    return redirect(url_for("home"))


@app.route("/sell/<int:book_id>", methods=["GET", "POST"])
def sell_book(book_id):
    with closing(get_db()) as conn:
        book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()

        if not book:
            flash("Book not found.", "error")
            return redirect(url_for("home"))

        if request.method == "POST":
            try:
                quantity = int(request.form.get("quantity", 0))
            except ValueError:
                quantity = 0

            if quantity <= 0 or quantity > book["stock"]:
                flash("Enter a quantity within the available stock.", "error")
                return render_template("sell.html", book=book)

            # Atomic stock update: only succeeds if enough stock is still left.
            cur = conn.execute(
                "UPDATE books SET stock = stock - ? WHERE id = ? AND stock >= ?",
                (quantity, book_id, quantity),
            )
            if cur.rowcount == 0:
                conn.rollback()
                flash("Enter a quantity within the available stock.", "error")
                book = conn.execute(
                    "SELECT * FROM books WHERE id = ?", (book_id,)
                ).fetchone()
                return render_template("sell.html", book=book)

            total = round(quantity * book["price"], 2)
            conn.execute(
                "INSERT INTO sales (book_id, quantity, total) VALUES (?, ?, ?)",
                (book_id, quantity, total),
            )
            conn.commit()
            flash(f"Sale recorded. Total: ₹{total:.2f}", "success")
            return redirect(url_for("sales"))

    return render_template("sell.html", book=book)


@app.route("/sales")
def sales():
    with closing(get_db()) as conn:
        # LEFT JOIN so sales stay visible even if the book was deleted later.
        rows = conn.execute("""
            SELECT sales.id,
                   COALESCE(books.title, '(Deleted book)') AS title,
                   sales.quantity, sales.total, sales.sale_date
            FROM sales
            LEFT JOIN books ON books.id = sales.book_id
            ORDER BY sales.id DESC
        """).fetchall()
    return render_template("sales.html", sales=rows)


@app.route("/contact")
def contact():
    return render_template("contact.html")


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "1") == "1")
