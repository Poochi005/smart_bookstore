# Smart Bookstore Management System

Built with HTML, CSS, Python, Flask and SQLite.

## Run
    python -m venv venv
    venv\Scripts\activate        (Windows)   |   source venv/bin/activate  (macOS/Linux)
    pip install -r requirements.txt
    python app.py
Open http://127.0.0.1:5000

## Structure
    app.py, requirements.txt, database.sql
    templates/  base.html (shared layout), index, add_book, sell, sales, contact
    static/style.css
bookstore.db is created automatically on first run with 3 sample books.

## Note on GitHub Pages
GitHub Pages only hosts static files, so a Flask app cannot run there.
Deploy on PythonAnywhere / Render / Railway instead (start command: gunicorn app:app).
