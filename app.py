from flask import Flask, render_template, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

DB_PATH = 'quiz.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def setup_database():
    conn = get_db_connection()
    c = conn.cursor()

    # Create users table with email column
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL,
        option1 TEXT NOT NULL,
        option2 TEXT NOT NULL,
        option3 TEXT NOT NULL,
        option4 TEXT NOT NULL,
        answer TEXT NOT NULL
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        score INTEGER,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')

    # Insert questions if not already present
    c.execute("SELECT COUNT(*) FROM questions")
    if c.fetchone()[0] == 0:
        questions = [
            ("What is the capital of France?", "Berlin", "London", "Paris", "Madrid", "Paris"),
            ("What is 5 + 7?", "10", "12", "13", "11", "12"),
            ("Which planet is known as the Red Planet?", "Earth", "Mars", "Jupiter", "Saturn", "Mars"),
            ("Which gas do plants absorb?", "Oxygen", "Carbon Dioxide", "Nitrogen", "Hydrogen", "Carbon Dioxide"),
            ("Who wrote Hamlet?", "Dante", "Homer", "Shakespeare", "Milton", "Shakespeare"),
            ("Which is the largest ocean?", "Atlantic", "Pacific", "Indian", "Arctic", "Pacific"),
            ("What is the boiling point of water?", "90°C", "100°C", "80°C", "120°C", "100°C"),
            ("Which metal is heavier than iron?", "Aluminum", "Copper", "Silver", "Zinc", "Silver"),
            ("What is the square root of 81?", "7", "8", "9", "10", "9"),
            ("Which country is known for the Great Wall?", "India", "China", "Japan", "Korea", "China")
        ]
        c.executemany('''
        INSERT INTO questions (question, option1, option2, option3, option4, answer)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', questions)

    conn.commit()
    conn.close()

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            return redirect('/quiz')
        else:
            return render_template('login.html', error='Invalid email or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        conn = get_db_connection()
        try:
            conn.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, password))
            conn.commit()
            conn.close()
            return redirect('/')
        except sqlite3.IntegrityError:
            conn.close()
            return render_template('register.html', error='Email already registered')
    return render_template('register.html')

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if 'user_id' not in session:
        return redirect('/')
    conn = get_db_connection()
    questions = conn.execute('SELECT * FROM questions').fetchall()
    conn.close()

    if request.method == 'POST':
        score = 0
        for question in questions:
            selected = request.form.get(f'q{question["id"]}')
            if selected == question["answer"]:
                score += 1
        conn = get_db_connection()
        conn.execute('INSERT INTO results (user_id, score) VALUES (?, ?)', (session['user_id'], score))
        conn.commit()
        conn.close()
        return render_template('result.html', score=score, name=session['user_name'])

    return render_template('quiz.html', questions=questions)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)  # Automatically recreate database cleanly
    setup_database()
    app.run(debug=True)
