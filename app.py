from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from pathlib import Path

app = Flask(__name__)
app.secret_key = "smart-bookstore-secret-key"

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "bookstore.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
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
            "INSERT INTO books (title, author, price, stock, category) VALUES (?, ?, ?, ?, ?)",
            [
                ("The Alchemist", "Paulo Coelho", 350, 10, "Fiction"),
                ("Atomic Habits", "James Clear", 499, 15, "Self Help"),
                ("Rich Dad Poor Dad", "Robert Kiyosaki", 399, 8, "Finance"),
            ],
        )
    conn.commit()
    conn.close()


@app.route("/")
def home():
    conn = get_db()
    books = conn.execute("SELECT * FROM books ORDER BY id DESC").fetchall()
    total_books = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    total_stock = conn.execute("SELECT COALESCE(SUM(stock), 0) FROM books").fetchone()[0]
    total_sales = conn.execute("SELECT COALESCE(SUM(total), 0) FROM sales").fetchone()[0]
    conn.close()
    return render_template(
        "index.html",
        books=books,
        total_books=total_books,
        total_stock=total_stock,
        total_sales=total_sales,
    )


@app.route("/add-book", methods=["GET", "POST"])
def add_book():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        category = request.form.get("category", "General").strip()
        try:
            price = float(request.form.get("price", 0))
            stock = int(request.form.get("stock", 0))
        except ValueError:
            flash("Price and stock must be valid numbers.", "error")
            return render_template("add_book.html")

        if not title or not author or price < 0 or stock < 0:
            flash("Please enter valid book details.", "error")
            return render_template("add_book.html")

        conn = get_db()
        conn.execute(
            "INSERT INTO books (title, author, price, stock, category) VALUES (?, ?, ?, ?, ?)",
            (title, author, price, stock, category),
        )
        conn.commit()
        conn.close()
        flash("Book added successfully.", "success")
        return redirect(url_for("home"))

    return render_template("add_book.html")


@app.post("/delete-book/<int:book_id>")
def delete_book(book_id):
    conn = get_db()
    conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()
    flash("Book deleted successfully.", "success")
    return redirect(url_for("home"))


@app.route("/sell/<int:book_id>", methods=["GET", "POST"])
def sell_book(book_id):
    conn = get_db()
    book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()

    if not book:
        conn.close()
        flash("Book not found.", "error")
        return redirect(url_for("home"))

    if request.method == "POST":
        try:
            quantity = int(request.form.get("quantity", 0))
        except ValueError:
            quantity = 0

        if quantity <= 0 or quantity > book["stock"]:
            conn.close()
            flash("Enter a quantity within the available stock.", "error")
            return render_template("sell.html", book=book)

        total = quantity * book["price"]
        conn.execute("UPDATE books SET stock = stock - ? WHERE id = ?", (quantity, book_id))
        conn.execute(
            "INSERT INTO sales (book_id, quantity, total) VALUES (?, ?, ?)",
            (book_id, quantity, total),
        )
        conn.commit()
        conn.close()
        flash(f"Sale recorded. Total: ₹{total:.2f}", "success")
        return redirect(url_for("sales"))

    conn.close()
    return render_template("sell.html", book=book)


@app.route("/sales")
def sales():
    conn = get_db()
    rows = conn.execute("""
        SELECT sales.id, books.title, sales.quantity, sales.total, sales.sale_date
        FROM sales
        JOIN books ON books.id = sales.book_id
        ORDER BY sales.id DESC
    """).fetchall()
    conn.close()
    return render_template("sales.html", sales=rows)


@app.route("/contact")
def contact():
    return render_template("contact.html")


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
