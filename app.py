from flask import Flask, render_template, redirect, url_for, request, flash
from models import db, User, Item, Transaction
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'rewear_dev_secret_key'

BASE_DIR = os.path.abspath(os.path.dirname(__name__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'rewear.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# --- FLASK-LOGIN SETUP ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Boot users to /login if they try to access hidden pages

@login_manager.user_loader
def load_user(user_id):
    # This tells Flask-Login how to find a specific user in the database
    return db.session.get(User, int(user_id))


# --- ROUTES ---
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        # Grab the coordinates sent by our HTML form
        lat = request.form.get('latitude')
        lng = request.form.get('longitude')
        
        # Check if email is already taken
        if User.query.filter_by(email=email).first():
            flash('Email already registered.')
            return redirect(url_for('register'))
            
        # Hash the password with Werkzeug!
        hashed_password = generate_password_hash(password)
        
        new_user = User(
            username=username, 
            email=email, 
            password=hashed_password,
            latitude=float(lat),
            longitude=float(lng)
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        # Verify the user exists AND the password hash matches
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.')
            
    return render_template('login.html')

@app.route('/dashboard')
@login_required 
def dashboard():
    # Fetch all items owned by the current logged-in user, newest first
    user_items = Item.query.filter_by(user_id=current_user.id).order_by(Item.date_posted.desc()).all()
    return render_template('dashboard.html', items=user_items)

@app.route('/add_item', methods=['POST'])
@login_required
def add_item():
    name = request.form.get('name')
    category = request.form.get('category')
    condition = request.form.get('condition')
    
    # Create the new item and link it to the current user
    new_item = Item(
        name=name, 
        category=category, 
        condition=condition, 
        user_id=current_user.id
    )
    db.session.add(new_item)
    db.session.commit()
    
    flash('Item added to your inventory successfully!')
    return redirect(url_for('dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# Make sure tables exist before running
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)