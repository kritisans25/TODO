from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth
from api_key import CLIENT_ID, CLIENT_SECRET

app = Flask(__name__)
app.secret_key = 'Rans_1403'

# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///new_users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# OAuth setup
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)


# DATABASE MODELS

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(125), nullable=True)
    tasks = db.relationship('Task', backref='owner', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    created = db.Column(db.DateTime, default=db.func.current_timestamp())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


# ROUTES


@app.route('/')
def home():
    if "username" in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


# ---------- Authentication ----------
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        session['username'] = username
        return redirect(url_for('dashboard'))
    return render_template('index.html', error="Invalid credentials.")


@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return render_template('index.html', error="Please enter both fields.")
    if User.query.filter_by(username=username).first():
        return render_template('index.html', error="Username already exists.")

    new_user = User(username=username)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    session['username'] = username
    return redirect(url_for('dashboard'))



@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))


# Google OAuth 
@app.route('/login/google')
def google_login():
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route('/authorize/google')
def authorize():
    token = google.authorize_access_token()

    # Correct way to fetch user info in latest Authlib
    userinfo_endpoint = google.server_metadata['userinfo_endpoint']
    resp = google.get(userinfo_endpoint)
    userinfo = resp.json()

    username = userinfo['email']

    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(username=username, password_hash=None)
        db.session.add(user)
        db.session.commit()

    session['username'] = username
    return redirect(url_for('dashboard'))





# To-Do Dashboard 
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if "username" not in session:
        return redirect(url_for('home'))
    
    user = User.query.filter_by(username=session['username']).first()

    if request.method == 'POST':
        content = request.form.get('task')
        if content:
            new_task = Task(content=content, owner=user)
            db.session.add(new_task)
            db.session.commit()
        return redirect(url_for('dashboard'))

    tasks = Task.query.filter_by(owner=user).all()
    return render_template('dashboard.html', username=user.username, tasks=tasks)



@app.route('/delete/<int:id>')
def delete(id):
    if "username" not in session:
        return redirect(url_for('home'))
    
    task = Task.query.get_or_404(id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('dashboard'))


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    if "username" not in session:
        return redirect(url_for('home'))
    
    task = Task.query.get_or_404(id)
    if request.method == 'POST':
        task.content = request.form['task']
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('edit.html', task=task)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
