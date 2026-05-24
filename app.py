from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
import pickle
import pandas as pd
import os
from datetime import datetime
from fpdf import FPDF
import io
import random
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_default_secret_key_for_local_dev')

# Mail Config
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')

mail = Mail(app)

# Use absolute path for SQLite to avoid issues on Windows/Render
basedir = os.path.abspath(os.path.dirname(__file__))
default_db_url = 'sqlite:///' + os.path.join(basedir, 'database', 'insurance.db')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', default_db_url)

if app.config['SQLALCHEMY_DATABASE_URI'].startswith("postgres://"):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    claims = db.relationship('Claim', backref='owner', lazy=True)

class Claim(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    age = db.Column(db.Integer, nullable=False)
    policy_state = db.Column(db.Integer, nullable=False)
    policy_deductable = db.Column(db.Integer, nullable=False)
    incident_type = db.Column(db.Integer, nullable=False)
    prediction = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create database and directories
if not os.path.exists('database'):
    os.makedirs('database')

with app.app_context():
    db.create_all()
    # Create admin if not exists
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@example.com', 
                     password=generate_password_hash('admin123', method='pbkdf2:sha256'), 
                     is_admin=True)
        db.session.add(admin)
        db.session.commit()

# Load the model
MODEL_PATH = 'model/fraud_model.pkl'
if os.path.exists(MODEL_PATH):
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
else:
    model = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Login failed. Check your username and password.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists.', 'danger')
            return redirect(url_for('register'))
        
        # Generate OTP
        otp = str(random.randint(100000, 999999))
        session['registration_data'] = {
            'username': username,
            'email': email,
            'password': generate_password_hash(password, method='pbkdf2:sha256'),
            'otp': otp
        }
        
        # Send OTP
        try:
            msg = Message('Email Verification OTP', recipients=[email])
            msg.body = f'Your OTP for registration is: {otp}'
            mail.send(msg)
            flash('OTP sent to your email. Please verify.', 'info')
            return redirect(url_for('verify_otp'))
        except Exception as e:
            flash(f'Error sending email: {str(e)}', 'danger')
            # For local testing if mail fails, just allow redirect
            return redirect(url_for('verify_otp'))
            
    return render_template('register.html')

@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if 'registration_data' not in session:
        return redirect(url_for('register'))
        
    if request.method == 'POST':
        entered_otp = request.form.get('otp')
        data = session['registration_data']
        
        if entered_otp == data['otp']:
            new_user = User(username=data['username'], email=data['email'], 
                            password=data['password'])
            db.session.add(new_user)
            db.session.commit()
            session.pop('registration_data')
            flash('Registration successful. Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Invalid OTP.', 'danger')
            
    return render_template('verify_otp.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_claims = Claim.query.filter_by(user_id=current_user.id).order_by(Claim.timestamp.desc()).all()
    return render_template('dashboard.html', name=current_user.username, claims=user_claims)

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    all_claims = Claim.query.all()
    return render_template('admin.html', claims=all_claims)

@app.route('/analytics')
@login_required
def analytics():
    # Fetch real data from database for analytics
    claims = Claim.query.all()
    fraud_count = len([c for c in claims if c.prediction == 'Fraud Reported'])
    legit_count = len([c for c in claims if c.prediction == 'No Fraud Reported'])
    
    # Simple logic for other charts
    states = {}
    for c in claims:
        states[c.policy_state] = states.get(c.policy_state, 0) + 1
    
    return render_template('analytics.html', 
                           fraud_count=fraud_count, 
                           legit_count=legit_count,
                           states=states)

@app.route('/predict', methods=['POST'])
@login_required
def predict():
    if model:
        try:
            age = int(request.form['age'])
            policy_state = int(request.form['policy_state'])
            policy_deductable = int(request.form['policy_deductable'])
            incident_type = int(request.form['incident_type'])
            
            data = pd.DataFrame([[age, policy_state, policy_deductable, incident_type]], 
                                columns=['age', 'policy_state', 'policy_deductable', 'incident_type'])
            
            prediction = model.predict(data)[0]
            result = 'Fraud Reported' if prediction == 1 else 'No Fraud Reported'
            
            # Save claim to database
            new_claim = Claim(age=age, policy_state=policy_state, 
                              policy_deductable=policy_deductable, 
                              incident_type=incident_type, 
                              prediction=result, 
                              owner=current_user)
            db.session.add(new_claim)
            db.session.commit()
            
            return render_template('result.html', prediction=result, claim_id=new_claim.id)
        except Exception as e:
            return f"Error during prediction: {str(e)}", 500
    return "Model not found", 404

@app.route('/report/<int:claim_id>')
@login_required
def generate_report(claim_id):
    claim = Claim.query.get_or_404(claim_id)
    if not current_user.is_admin and claim.owner != current_user:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Insurance Claim Report", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Claim ID: {claim.id}", ln=True)
    pdf.cell(200, 10, txt=f"User: {claim.owner.username}", ln=True)
    pdf.cell(200, 10, txt=f"Date: {claim.timestamp.strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
    pdf.ln(5)
    
    pdf.cell(200, 10, txt=f"Age: {claim.age}", ln=True)
    pdf.cell(200, 10, txt=f"Policy State: {claim.policy_state}", ln=True)
    pdf.cell(200, 10, txt=f"Policy Deductable: {claim.policy_deductable}", ln=True)
    pdf.cell(200, 10, txt=f"Incident Type: {claim.incident_type}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt=f"AI Prediction: {claim.prediction}", ln=True)
    
    output = io.BytesIO()
    pdf_str = pdf.output(dest='S').encode('latin-1')
    output.write(pdf_str)
    output.seek(0)
    
    return send_file(output, mimetype='application/pdf', as_attachment=True, download_name=f'claim_{claim.id}_report.pdf')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
