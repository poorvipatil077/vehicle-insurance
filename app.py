from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session
import sqlite3
import os
import joblib
import pandas as pd
from datetime import datetime
from reportlab.pdfgen import canvas
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', "vehicleinsurancekey")

# Use absolute path for database
basedir = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(basedir, 'database.db')

# =========================
# DATABASE SETUP
# =========================

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        email TEXT,
        password TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS claims (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        amount REAL,
        age REAL,
        accidents REAL,
        vehicle_age REAL,
        result TEXT,
        created_at TEXT
    )
    ''')

    conn.commit()
    conn.close()

init_db()

# =========================
# LOAD ML MODEL
# =========================

MODEL_PATH = os.path.join(basedir, 'model', 'fraud_model.pkl')

if os.path.exists(MODEL_PATH):
    model = joblib.load(MODEL_PATH)
else:
    model = None

# =========================
# HOME PAGE
# =========================

@app.route('/')
def home():
    return render_template('index.html')

# =========================
# REGISTER
# =========================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            'INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
            (username, email, password)
        )

        conn.commit()
        conn.close()

        flash('Registration Successful!')
        return redirect(url_for('login'))

    return render_template('register.html')

# =========================
# LOGIN
# =========================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            'SELECT * FROM users WHERE email=? AND password=?',
            (email, password)
        )

        user = cursor.fetchone()
        conn.close()

        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            flash('Login Successful!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid Email or Password')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# =========================
# DASHBOARD
# =========================

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM claims ORDER BY id DESC')
    claims = cursor.fetchall()

    conn.close()

    return render_template('dashboard.html', claims=claims, name=session['username'])

# =========================
# FRAUD PREDICTION
# =========================

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    prediction = None

    if request.method == 'POST':
        try:
            amount = float(request.form['amount'])
            age = float(request.form['age'])
            accidents = float(request.form['accidents'])
            vehicle_age = float(request.form['vehicle_age'])

            # Features must match train_model.py exactly
            input_data = pd.DataFrame(
                [[age, accidents, vehicle_age]],
                columns=['age', 'accidents', 'vehicle_age']
            )

            if model:
                result = model.predict(input_data)[0]
                prediction = "Fraud Claim Detected" if result == 1 else "Genuine Claim"
            else:
                prediction = "Model Not Found"

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute('''
            INSERT INTO claims (
                amount, age, accidents,
                vehicle_age, result, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                amount,
                age,
                accidents,
                vehicle_age,
                prediction,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            flash(f"Error during prediction: {str(e)}")

    return render_template('predict.html', prediction=prediction)

# =========================
# PDF REPORT
# =========================

@app.route('/download_report/<int:claim_id>')
def download_report(claim_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM claims WHERE id=?', (claim_id,))
    claim = cursor.fetchone()

    conn.close()

    if not claim:
        return "Claim Not Found"

    pdf_file = os.path.join(basedir, f"claim_report_{claim_id}.pdf")

    c = canvas.Canvas(pdf_file)

    c.drawString(100, 800, "Vehicle Insurance Claim Report")
    c.drawString(100, 760, f"Claim ID: {claim[0]}")
    c.drawString(100, 740, f"Amount: {claim[1]}")
    c.drawString(100, 720, f"Age: {claim[2]}")
    c.drawString(100, 700, f"Accidents: {claim[3]}")
    c.drawString(100, 680, f"Vehicle Age: {claim[4]}")
    c.drawString(100, 660, f"Result: {claim[5]}")
    c.drawString(100, 640, f"Date: {claim[6]}")

    c.save()

    return send_file(pdf_file, as_attachment=True)

# =========================
# ANALYTICS PAGE
# =========================

@app.route('/analytics')
def analytics():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT result, COUNT(*) FROM claims GROUP BY result')
    data = cursor.fetchall()

    conn.close()

    labels = [row[0] for row in data]
    values = [row[1] for row in data]

    return render_template(
        'analytics.html',
        labels=labels,
        values=values
    )

# =========================
# MAIN
# =========================

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
