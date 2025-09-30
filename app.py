from flask import Flask, request, render_template, redirect, url_for, session, flash
import sqlite3
import hashlib
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "biblioteca123"

# Database configuration
DATABASE = 'database.db'

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with biblioteca tables"""
    conn = get_db_connection()
    
    # Create usuarios table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        )
    ''')
    
    # Create livros table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS livros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            autor TEXT NOT NULL,
            ano INTEGER,
            disponivel INTEGER DEFAULT 1
        )
    ''')
    
    # Create emprestimos table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS emprestimos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER NOT NULL,
            id_livro INTEGER NOT NULL,
            data_emprestimo TEXT NOT NULL,
            data_devolucao TEXT,
            FOREIGN KEY (id_usuario) REFERENCES usuarios(id),
            FOREIGN KEY (id_livro) REFERENCES livros(id)
        )
    ''')
    
    # Insert sample data if tables are empty
    usuarios_count = conn.execute('SELECT COUNT(*) FROM usuarios').fetchone()[0]
    if usuarios_count == 0:
        # Insert sample usuarios
        conn.execute("INSERT INTO usuarios (nome, email, senha) VALUES ('Ana Silva', 'ana@email.com', ?)", (hash_password('1234'),))
        conn.execute("INSERT INTO usuarios (nome, email, senha) VALUES ('João Souza', 'joao@email.com', ?)", (hash_password('abcd'),))
        conn.execute("INSERT INTO usuarios (nome, email, senha) VALUES ('Maria Lima', 'maria@email.com', ?)", (hash_password('senha'),))
        
        # Insert sample livros
        conn.execute("INSERT INTO livros (titulo, autor, ano, disponivel) VALUES ('Dom Casmurro', 'Machado de Assis', 1899, 1)")
        conn.execute("INSERT INTO livros (titulo, autor, ano, disponivel) VALUES ('O Pequeno Príncipe', 'Antoine de Saint-Exupéry', 1943, 1)")
        conn.execute("INSERT INTO livros (titulo, autor, ano, disponivel) VALUES ('1984', 'George Orwell', 1949, 1)")
        
        # Insert sample emprestimos
        conn.execute("INSERT INTO emprestimos (id_usuario, id_livro, data_emprestimo) VALUES (1, 1, '2025-09-29')")
        conn.execute("INSERT INTO emprestimos (id_usuario, id_livro, data_emprestimo) VALUES (2, 2, '2025-09-28')")
        conn.execute("INSERT INTO emprestimos (id_usuario, id_livro, data_emprestimo) VALUES (3, 3, '2025-09-27')")
        
        # Update livro availability based on active loans
        conn.execute("UPDATE livros SET disponivel = 0 WHERE id IN (SELECT id_livro FROM emprestimos WHERE data_devolucao IS NULL)")
    
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

# Helper function to check authentication
def require_login():
    """Check if user is logged in, redirect to login if not"""
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return None

@app.route('/')
def index():
    """Home page - only accessible if logged in"""
    auth_check = require_login()
    if auth_check:
        return auth_check
    
    conn = get_db_connection()
    usuario = conn.execute('SELECT nome FROM usuarios WHERE id = ?', (session['usuario_id'],)).fetchone()
    conn.close()
    
    return render_template('index.html', usuario=usuario['nome'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        
        if not email or not senha:
            flash('Por favor, preencha todos os campos')
            return render_template('login.html')
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM usuarios WHERE email = ? AND senha = ?',
            (email, hash_password(senha))
        ).fetchone()
        conn.close()
        
        if user:
            session['usuario_id'] = user['id']
            session['usuario_nome'] = user['nome']
            return redirect(url_for('index'))
        else:
            flash('Email ou senha inválidos')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    flash('Você foi desconectado')
    return redirect(url_for('login'))

# Usuarios management routes
@app.route('/usuarios')
def usuarios():
    """List all usuarios"""
    auth_check = require_login()
    if auth_check:
        return auth_check
    
    conn = get_db_connection()
    usuarios = conn.execute('SELECT * FROM usuarios ORDER BY nome').fetchall()
    conn.close()
    
    return render_template('usuarios.html', usuarios=usuarios)

@app.route('/usuarios/novo', methods=['GET', 'POST'])
def novo_usuario():
    """Add new usuario"""
    auth_check = require_login()
    if auth_check:
        return auth_check
    
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        
        if not nome or not email or not senha:
            flash('Por favor, preencha todos os campos')
            return render_template('novo_usuario.html')
        
        conn = get_db_connection()
        
        # Check if email already exists
        existing_email = conn.execute('SELECT id FROM usuarios WHERE email = ?', (email,)).fetchone()
        if existing_email:
            flash('Email já cadastrado')
            conn.close()
            return render_template('novo_usuario.html')
        
        try:
            conn.execute(
                'INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)',
                (nome, email, hash_password(senha))
            )
            conn.commit()
            conn.close()
            flash('Usuário criado com sucesso!')
            return redirect(url_for('usuarios'))
        except sqlite3.Error:
            flash('Erro ao criar usuário. Tente novamente.')
            conn.close()
    
    return render_template('novo_usuario.html')

@app.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id):
    """Edit usuario"""
    auth_check = require_login()
    if auth_check:
        return auth_check
    
    conn = get_db_connection()
    
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form.get('senha')
        
        if not nome or not email:
            flash('Nome e email são obrigatórios')
            return redirect(url_for('editar_usuario', id=id))
        
        # Check if email already exists for other users
        existing_email = conn.execute('SELECT id FROM usuarios WHERE email = ? AND id != ?', (email, id)).fetchone()
        if existing_email:
            flash('Email já está em uso por outro usuário')
            conn.close()
            return redirect(url_for('editar_usuario', id=id))
        
        try:
            if senha:  # Update password if provided
                conn.execute(
                    'UPDATE usuarios SET nome = ?, email = ?, senha = ? WHERE id = ?',
                    (nome, email, hash_password(senha), id)
                )
            else:  # Keep existing password
                conn.execute(
                    'UPDATE usuarios SET nome = ?, email = ? WHERE id = ?',
                    (nome, email, id)
                )
            conn.commit()
            flash('Usuário atualizado com sucesso!')
            return redirect(url_for('usuarios'))
        except sqlite3.Error:
            flash('Erro ao atualizar usuário.')
        finally:
            conn.close()
    
    usuario = conn.execute('SELECT * FROM usuarios WHERE id = ?', (id,)).fetchone()
    conn.close()
    
    if not usuario:
        flash('Usuário não encontrado')
        return redirect(url_for('usuarios'))
    
    return render_template('editar_usuario.html', usuario=usuario)

@app.route('/usuarios/excluir/<int:id>')
def excluir_usuario(id):
    """Delete usuario"""
    auth_check = require_login()
    if auth_check:
        return auth_check
    
    conn = get_db_connection()
    
    # Check if user has active loans
    active_loans = conn.execute('SELECT COUNT(*) FROM emprestimos WHERE id_usuario = ? AND data_devolucao IS NULL', (id,)).fetchone()[0]
    
    if active_loans > 0:
        flash('Não é possível excluir usuário com empréstimos ativos')
        conn.close()
        return redirect(url_for('usuarios'))
    
    try:
        conn.execute('DELETE FROM usuarios WHERE id = ?', (id,))
        conn.commit()
        flash('Usuário excluído com sucesso!')
    except sqlite3.Error:
        flash('Erro ao excluir usuário.')
    finally:
        conn.close()
    
    return redirect(url_for('usuarios'))

# Livros management routes
@app.route('/livros')
def livros():
    """List all livros"""
    auth_check = require_login()
    if auth_check:
        return auth_check
    
    conn = get_db_connection()
    livros = conn.execute('SELECT * FROM livros ORDER BY titulo').fetchall()
    conn.close()
    
    return render_template('livros.html', livros=livros)

@app.route('/livros/novo', methods=['GET', 'POST'])
def novo_livro():
    """Add new livro"""
    auth_check = require_login()
    if auth_check:
        return auth_check
    
    if request.method == 'POST':
        titulo = request.form['titulo']
        autor = request.form['autor']
        ano = request.form.get('ano', type=int)
        
        if not titulo or not autor:
            flash('Título e autor são obrigatórios')
            return render_template('novo_livro.html')
        
        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO livros (titulo, autor, ano, disponivel) VALUES (?, ?, ?, 1)',
                (titulo, autor, ano)
            )
            conn.commit()
            flash('Livro adicionado com sucesso!')
            return redirect(url_for('livros'))
        except sqlite3.Error:
            flash('Erro ao adicionar livro.')
        finally:
            conn.close()
    
    return render_template('novo_livro.html')

@app.route('/livros/editar/<int:id>', methods=['GET', 'POST'])
def editar_livro(id):
    """Edit livro"""
    auth_check = require_login()
    if auth_check:
        return auth_check
    
    conn = get_db_connection()
    
    if request.method == 'POST':
        titulo = request.form['titulo']
        autor = request.form['autor']
        ano = request.form.get('ano', type=int)
        
        if not titulo or not autor:
            flash('Título e autor são obrigatórios')
            return redirect(url_for('editar_livro', id=id))
        
        try:
            conn.execute(
                'UPDATE livros SET titulo = ?, autor = ?, ano = ? WHERE id = ?',
                (titulo, autor, ano, id)
            )
            conn.commit()
            flash('Livro atualizado com sucesso!')
            return redirect(url_for('livros'))
        except sqlite3.Error:
            flash('Erro ao atualizar livro.')
        finally:
            conn.close()
    
    livro = conn.execute('SELECT * FROM livros WHERE id = ?', (id,)).fetchone()
    conn.close()
    
    if not livro:
        flash('Livro não encontrado')
        return redirect(url_for('livros'))
    
    return render_template('editar_livro.html', livro=livro)

@app.route('/livros/excluir/<int:id>')
def excluir_livro(id):
    """Delete livro"""
    auth_check = require_login()
    if auth_check:
        return auth_check
    
    conn = get_db_connection()
    
    # Check if book has active loans
    active_loans = conn.execute('SELECT COUNT(*) FROM emprestimos WHERE id_livro = ? AND data_devolucao IS NULL', (id,)).fetchone()[0]
    
    if active_loans > 0:
        flash('Não é possível excluir livro com empréstimos ativos')
        conn.close()
        return redirect(url_for('livros'))
    
    try:
        conn.execute('DELETE FROM livros WHERE id = ?', (id,))
        conn.commit()
        flash('Livro excluído com sucesso!')
    except sqlite3.Error:
        flash('Erro ao excluir livro.')
    finally:
        conn.close()
    
    return redirect(url_for('livros'))

# Emprestimos management routes
@app.route('/emprestimos')
def emprestimos():
    """List all emprestimos"""
    auth_check = require_login()
    if auth_check:
        return auth_check
    
    conn = get_db_connection()
    emprestimos = conn.execute('''
        SELECT e.*, u.nome as usuario_nome, l.titulo as livro_titulo
        FROM emprestimos e
        JOIN usuarios u ON e.id_usuario = u.id
        JOIN livros l ON e.id_livro = l.id
        ORDER BY e.data_emprestimo DESC
    ''').fetchall()
    conn.close()
    
    return render_template('emprestimos.html', emprestimos=emprestimos)

@app.route('/emprestimos/novo', methods=['GET', 'POST'])
def novo_emprestimo():
    """Create new emprestimo"""
    auth_check = require_login()
    if auth_check:
        return auth_check
    
    conn = get_db_connection()
    
    if request.method == 'POST':
        id_usuario = request.form.get('id_usuario', type=int)
        id_livro = request.form.get('id_livro', type=int)
        data_emprestimo = request.form['data_emprestimo']
        
        if not id_usuario or not id_livro or not data_emprestimo:
            flash('Todos os campos são obrigatórios')
            usuarios = conn.execute('SELECT * FROM usuarios ORDER BY nome').fetchall()
            livros_disponiveis = conn.execute('SELECT * FROM livros WHERE disponivel = 1 ORDER BY titulo').fetchall()
            conn.close()
            return render_template('novo_emprestimo.html', usuarios=usuarios, livros=livros_disponiveis)
        
        # Check if book is available
        livro = conn.execute('SELECT disponivel FROM livros WHERE id = ?', (id_livro,)).fetchone()
        if not livro or not livro['disponivel']:
            flash('Livro não está disponível para empréstimo')
            usuarios = conn.execute('SELECT * FROM usuarios ORDER BY nome').fetchall()
            livros_disponiveis = conn.execute('SELECT * FROM livros WHERE disponivel = 1 ORDER BY titulo').fetchall()
            conn.close()
            return render_template('novo_emprestimo.html', usuarios=usuarios, livros=livros_disponiveis)
        
        try:
            # Create loan
            conn.execute(
                'INSERT INTO emprestimos (id_usuario, id_livro, data_emprestimo) VALUES (?, ?, ?)',
                (id_usuario, id_livro, data_emprestimo)
            )
            # Mark book as unavailable
            conn.execute('UPDATE livros SET disponivel = 0 WHERE id = ?', (id_livro,))
            conn.commit()
            flash('Empréstimo registrado com sucesso!')
            return redirect(url_for('emprestimos'))
        except sqlite3.Error:
            flash('Erro ao registrar empréstimo.')
        finally:
            conn.close()
    
    usuarios = conn.execute('SELECT * FROM usuarios ORDER BY nome').fetchall()
    livros_disponiveis = conn.execute('SELECT * FROM livros WHERE disponivel = 1 ORDER BY titulo').fetchall()
    conn.close()
    
    return render_template('novo_emprestimo.html', usuarios=usuarios, livros=livros_disponiveis)

@app.route('/emprestimos/devolver/<int:id>')
def devolver_livro(id):
    """Return a book"""
    auth_check = require_login()
    if auth_check:
        return auth_check
    
    conn = get_db_connection()
    
    # Get loan info
    emprestimo = conn.execute('SELECT * FROM emprestimos WHERE id = ?', (id,)).fetchone()
    
    if not emprestimo:
        flash('Empréstimo não encontrado')
        conn.close()
        return redirect(url_for('emprestimos'))
    
    if emprestimo['data_devolucao']:
        flash('Este livro já foi devolvido')
        conn.close()
        return redirect(url_for('emprestimos'))
    
    try:
        data_devolucao = datetime.now().strftime('%Y-%m-%d')
        
        # Update loan with return date
        conn.execute('UPDATE emprestimos SET data_devolucao = ? WHERE id = ?', (data_devolucao, id))
        # Mark book as available
        conn.execute('UPDATE livros SET disponivel = 1 WHERE id = ?', (emprestimo['id_livro'],))
        conn.commit()
        flash('Livro devolvido com sucesso!')
    except sqlite3.Error:
        flash('Erro ao processar devolução.')
    finally:
        conn.close()
    
    return redirect(url_for('emprestimos'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5001)