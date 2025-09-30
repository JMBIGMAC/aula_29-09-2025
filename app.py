from flask import Flask, request, render_template, redirect, url_for, session, flash
import sqlite3
import hashlib
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_change_in_production'

# Database configuration
DATABASE = 'users.db'

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with users table"""
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/')
def home():
    """Home page - only accessible if logged in"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    user = conn.execute('SELECT username FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    
    return render_template('home.html', username=user['username'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if not username or not password:
            flash('Please fill in all fields')
            return render_template('login.html')
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ? AND password = ?',
            (username, hash_password(password))
        ).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Signup page"""
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Validation
        if not username or not email or not password or not confirm_password:
            flash('Please fill in all fields')
            return render_template('signup.html')
        
        if password != confirm_password:
            flash('Passwords do not match')
            return render_template('signup.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long')
            return render_template('signup.html')
        
        conn = get_db_connection()
        
        # Check if username already exists
        existing_user = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
        if existing_user:
            flash('Username already exists')
            conn.close()
            return render_template('signup.html')
        
        # Check if email already exists
        existing_email = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
        if existing_email:
            flash('Email already registered')
            conn.close()
            return render_template('signup.html')
        
        # Insert new user
        try:
            conn.execute(
                'INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                (username, email, hash_password(password))
            )
            conn.commit()
            conn.close()
            flash('Account created successfully! Please log in.')
            return redirect(url_for('login'))
        except sqlite3.Error:
            flash('Error creating account. Please try again.')
            conn.close()
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    flash('You have been logged out')
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)