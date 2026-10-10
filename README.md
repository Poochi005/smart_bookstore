# Smart Bookstore Management System

## Technologies
- HTML
- CSS
- Python
- Flask
- SQLite

## Project structure

smart_bookstore/
├── app.py
├── requirements.txt
├── bookstore.db              # created automatically on first run
├── templates/
│   ├── index.html
│   ├── add_book.html
│   ├── sell.html
│   ├── sales.html
│   └── contact.html
└── static/
    └── style.css

## Run in VS Code / terminal

1. Open this folder in VS Code.
2. Create a virtual environment:

   Windows:
   python -m venv venv
   venv\Scripts\activate

   macOS/Linux:
   python3 -m venv venv
   source venv/bin/activate

3. Install Flask:

   pip install -r requirements.txt

4. Start the application:

   python app.py

5. Open the address shown in the terminal, normally:
   http://127.0.0.1:5000

## Features included
- Dashboard
- View books
- Add books
- Delete books
- Record book sales
- Automatic stock reduction after a sale
- Sales history
- SQLite database created automatically
- Sample books inserted on first run
