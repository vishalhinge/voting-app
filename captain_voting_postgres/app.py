
from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

def get_db_connection():
    return psycopg2.connect(os.environ['DATABASE_URL'])

def init_db():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY,
                voted BOOLEAN DEFAULT FALSE
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS votes (
                candidate TEXT
            )
        ''')
        conn.commit()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        session['email'] = email
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("INSERT INTO users (email) VALUES (%s) ON CONFLICT DO NOTHING", (email,))
            conn.commit()
            c.execute("SELECT voted FROM users WHERE email = %s", (email,))
            voted = c.fetchone()[0]
            if voted:
                return redirect(url_for('results'))
            return redirect(url_for('vote'))
    return render_template('index.html')

@app.route('/vote', methods=['GET', 'POST'])
def vote():
    candidates = ["Alice", "Bob", "Charlie"]
    email = session.get('email')
    if not email:
        return redirect(url_for('index'))

    if request.method == 'POST':
        selected = request.form.get('candidate')
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("INSERT INTO votes (candidate) VALUES (%s)", (selected,))
            c.execute("UPDATE users SET voted = TRUE WHERE email = %s", (email,))
            conn.commit()
        return redirect(url_for('results'))

    return render_template('vote.html', candidates=candidates)

@app.route('/results')
def results():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT candidate, COUNT(*) FROM votes GROUP BY candidate")
        results = c.fetchall()
    return render_template('results.html', results=results)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
