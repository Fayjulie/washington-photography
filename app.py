from flask import Flask, request, redirect, url_for, jsonify, send_from_directory, render_template, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from werkzeug.security import check_password_hash
import os
import shutil
import json

app = Flask(__name__, template_folder='templates', static_folder='static', static_url_path='/static')

app.secret_key = 'd02d31d90bcc21e714841222d1e41add06a0f76daa48aab3'

base_dir = os.path.dirname(os.path.abspath(__file__))
images_dir = os.path.join(base_dir, 'images')
trash_dir = os.path.join(base_dir, 'trash')
users_file = os.path.join(base_dir, 'users.json')
data_file = os.path.join(base_dir, 'data.json')

if not os.path.exists(images_dir): os.makedirs(images_dir)
if not os.path.exists(trash_dir): os.makedirs(trash_dir)

if not os.path.exists(users_file):
    with open(users_file, 'w') as f:
        json.dump({}, f)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

ADMIN_USERNAME = 'faith'
ADMIN_PASSWORD_HASH = 'scrypt:32768:8:1$I657ZpQriNoY5tT9$1f0f30a986925e36bda94c9e12208a18853deb6af90f970649feb1213fe1128a73a62f49507d72d2b648f8e0b6212e127bd24cf9d88f7f2d9eef1cc609500c14'

class AdminUser(UserMixin):
    def __init__(self, username):
        self.id = username

@login_manager.user_loader
def load_user(user_id):
    if user_id == ADMIN_USERNAME:
        return AdminUser(user_id)
    return None

def load_data():
    if not os.path.exists(data_file):
        return {"pages": {}, "images": {}}
    with open(data_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/gallery')
def gallery():
    return render_template('gallery.html')

@app.route('/static/images/<filename>')
def serve_image(filename):
    return send_from_directory(images_dir, filename)

@app.route('/static/trash/<filename>')
def serve_trash(filename):
    return send_from_directory(trash_dir, filename)

@app.route('/api/data')
def get_data():
    return jsonify(load_data())

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    with open(users_file, 'r') as f: users = json.load(f)
    if email in users: return jsonify({"success": False, "message": "Email already exists."})
    users[email] = password
    with open(users_file, 'w') as f: json.dump(users, f)
    return jsonify({"success": True})

@app.route('/api/login', methods=['POST'])
def login_public():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    with open(users_file, 'r') as f: users = json.load(f)
    if email in users and users[email] == password:
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Invalid email or password."})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            login_user(AdminUser(username))
            return redirect(url_for('admin'))
        else:
            flash('Invalid username or password')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/admin')
@login_required
def admin():
    return render_template('admin.html')

@app.route('/api/save-page', methods=['POST'])
@login_required
def save_page():
    data = load_data()
    category = request.form.get('category')
    title = request.form.get('title')
    description = request.form.get('description')
    
    if category in data['pages']:
        data['pages'][category]['title'] = title
        data['pages'][category]['description'] = description
    else:
        data['pages'][category] = {'title': title, 'description': description}
        if category not in data['images']:
            data['images'][category] = []
            
    save_data(data)
    return redirect(url_for('admin'))

@app.route('/api/add-page', methods=['POST'])
@login_required
def add_page():
    data = load_data()
    page_id = request.form.get('page_id').strip().lower().replace(' ', '-')
    title = request.form.get('title')
    description = request.form.get('description')
    
    if page_id not in data['pages']:
        data['pages'][page_id] = {'title': title, 'description': description}
        data['images'][page_id] = []
        save_data(data)
        
    return redirect(url_for('admin'))

@app.route('/api/delete-page', methods=['POST'])
@login_required
def delete_page():
    category = request.form.get('category')
    data = load_data()
    
    if category in data['pages']:
        del data['pages'][category]
    if category in data['images']:
        del data['images'][category]
        
    save_data(data)
    return redirect(url_for('admin'))

@app.route('/api/images/<category>')
@login_required
def get_images(category):
    data = load_data()
    return jsonify(data['images'].get(category, []))

@app.route('/api/trash')
@login_required
def get_trash():
    trashed_files = [f for f in os.listdir(trash_dir) if os.path.isfile(os.path.join(trash_dir, f))]
    return jsonify(trashed_files)

@app.route('/upload', methods=['POST'])
@login_required
def upload():
    category = request.form.get('category')
    files = request.files.getlist('photo')
    data = load_data()
    
    if files and files[0].filename:
        if category not in data['images']:
            data['images'][category] = []
            
        for file in files:
            if file and file.filename:
                filename = file.filename
                if filename.lower().endswith('.jpeg.jpeg'): filename = filename[:-5]
                file.save(os.path.join(images_dir, filename))
                if filename not in data['images'][category]:
                    data['images'][category].append(filename)
        
        save_data(data)
        return redirect(url_for('admin'))
    return "Error"

@app.route('/delete', methods=['POST'])
@login_required
def delete_photo():
    category = request.form.get('category')
    filenames = request.form.getlist('filename')
    data = load_data()

    for filename in filenames:
        filepath = os.path.join(images_dir, filename)
        trashpath = os.path.join(trash_dir, filename)
        if os.path.exists(filepath): shutil.move(filepath, trashpath)
        if filename in data['images'].get(category, []):
            data['images'][category].remove(filename)
            
    save_data(data)
    return redirect(url_for('admin'))

@app.route('/undo', methods=['POST'])
@login_required
def undo_photo():
    category = request.form.get('category')
    filename = request.form.get('filename')
    data = load_data()
    
    trashpath = os.path.join(trash_dir, filename)
    filepath = os.path.join(images_dir, filename)
    if os.path.exists(trashpath): shutil.move(trashpath, filepath)
    
    if category in data['images'] and filename not in data['images'][category]:
        data['images'][category].append(filename)
        
    save_data(data)
    return redirect(url_for('admin'))

@app.route('/empty-trash', methods=['POST'])
@login_required
def empty_trash():
    filename = request.form.get('filename')
    if filename:
        filepath = os.path.join(trash_dir, filename)
        if os.path.exists(filepath): os.remove(filepath)
    else:
        for f in os.listdir(trash_dir):
            filepath = os.path.join(trash_dir, f)
            if os.path.isfile(filepath): os.remove(filepath)
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)