from flask import Flask, request, redirect, url_for, jsonify, send_from_directory, render_template
import os
import shutil
import json

app = Flask(__name__, template_folder='templates', static_folder='static', static_url_path='/static')

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

@app.route('/admin')
def admin():
    return render_template('admin.html')

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
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    with open(users_file, 'r') as f: users = json.load(f)
    if email in users and users[email] == password:
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Invalid email or password."})

@app.route('/api/save-page', methods=['POST'])
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
def get_images(category):
    data = load_data()
    return jsonify(data['images'].get(category, []))

@app.route('/api/trash')
def get_trash():
    trashed_files = [f for f in os.listdir(trash_dir) if os.path.isfile(os.path.join(trash_dir, f))]
    return jsonify(trashed_files)

@app.route('/upload', methods=['POST'])
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