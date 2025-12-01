from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, VideoCard, User
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = ''

base_dir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_dir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@example.com', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        existing_user = User.query.filter_by(username=username).first()
        existing_email = User.query.filter_by(email=email).first()

        errors = []
        if existing_user:
            errors.append('Пользователь с таким именем уже существует')
        if existing_email:
            errors.append('Пользователь с таким email уже существует')

        if errors:
            return render_template('register.html', errors=errors)

        user = User(username=username, email=email)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            errors = ['Неверное имя пользователя или пароль']
            return render_template('login.html', errors=errors)

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_card():
    if not current_user.is_admin():
        flash('У вас нет прав для доступа к этой странице', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form['name']
        manufacturer = request.form['manufacturer']
        memory = int(request.form['memory'])
        memory_type = request.form['memory_type']
        price = float(request.form['price'])
        description = request.form['description']
        image_url = request.form['image_url']

        new_card = VideoCard(
            name=name,
            manufacturer=manufacturer,
            memory=memory,
            memory_type=memory_type,
            price=price,
            description=description,
            image_url=image_url,
            created_by=current_user.id
        )

        db.session.add(new_card)
        db.session.commit()

        return redirect(url_for('all_cards'))

    return render_template('add_card.html')


@app.route('/cards')
def all_cards():
    cards = VideoCard.query.all()
    return render_template('cards.html', cards=cards)


@app.route('/search')
def search():
    manufacturer = request.args.get('manufacturer', '')
    min_price = request.args.get('min_price', 0, type=float)
    max_price = request.args.get('max_price', 100000, type=float)

    query = VideoCard.query

    if manufacturer:
        query = query.filter(VideoCard.manufacturer == manufacturer)
    if min_price:
        query = query.filter(VideoCard.price >= min_price)
    if max_price:
        query = query.filter(VideoCard.price <= max_price)

    cards = query.all()
    return render_template('cards.html', cards=cards)


@app.route('/edit/<int:card_id>', methods=['GET', 'POST'])
@login_required
def edit_card(card_id):
    if not current_user.is_admin():
        flash('У вас нет прав для редактирования видеокарт', 'error')
        return redirect(url_for('all_cards'))

    card = VideoCard.query.get_or_404(card_id)

    if request.method == 'POST':
        errors = []

        name = request.form['name']
        manufacturer = request.form['manufacturer']
        memory = request.form['memory']
        memory_type = request.form['memory_type']
        price = request.form['price']
        description = request.form['description']
        image_url = request.form['image_url']
        in_stock = 'in_stock' in request.form

        if not name or len(name) < 2:
            errors.append('Название видеокарты должно содержать минимум 2 символа')

        if not memory.isdigit() or int(memory) <= 0:
            errors.append('Объем памяти должен быть положительным числом')

        if not price.replace('.', '').isdigit() or float(price) <= 0:
            errors.append('Цена должна быть положительным числом')

        if errors:
            return render_template('edit_card.html', card=card, errors=errors)

        card.name = name
        card.manufacturer = manufacturer
        card.memory = int(memory)
        card.memory_type = memory_type
        card.price = float(price)
        card.description = description
        card.image_url = image_url
        card.in_stock = in_stock

        db.session.commit()

        return redirect(url_for('all_cards'))

    return render_template('edit_card.html', card=card)


@app.route('/delete/<int:card_id>', methods=['POST'])
@login_required
def delete_card(card_id):
    if not current_user.is_admin():
        flash('У вас нет прав для удаления видеокарт', 'error')
        return redirect(url_for('all_cards'))

    card = VideoCard.query.get_or_404(card_id)
    db.session.delete(card)
    db.session.commit()

    return redirect(url_for('all_cards'))

if __name__ == '__main__':
    app.run(debug=True)