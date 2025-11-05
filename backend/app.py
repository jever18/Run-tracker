# backend/app.py

from flask import Flask, request, jsonify, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
from datetime import datetime
import math

# =======================================================
# 0. KONFIGURASI DASAR DAN INISIALISASI
# =======================================================

app = Flask(__name__, 
            static_folder='dist/assets', # Lokasi file statis (CSS, JS) yang diakses via /assets
            static_url_path='/assets')   # URL untuk mengakses folder statis

app.config['SECRET_KEY'] = 'kunci_rahasia_yang_kuat'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///run_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.session_protection = "strong"

# =======================================================
# 1. UTILITY: PACE DAN HAVERSINE
# =======================================================

R = 6371

def haversine(lat1, lon1, lat2, lon2):
    """Menghitung jarak antara dua titik koordinat di permukaan bumi (dalam km)."""
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def calculate_pace(distance_km, duration_min):
    """Menghitung pace (menit/km) dari jarak dan durasi total."""
    if distance_km is None or duration_min is None or distance_km <= 0 or duration_min <= 0:
        return 'N/A'
    pace_decimal = duration_min / distance_km
    minutes = int(pace_decimal)
    seconds = round((pace_decimal - minutes) * 60)
    return f"{minutes:02d}:{seconds:02d} / km"

def calculate_total_distance_from_path(path_coordinates_json):
    """Menghitung total jarak lari dari serangkaian koordinat GPS."""
    try:
        path = json.loads(path_coordinates_json)
    except json.JSONDecodeError:
        raise ValueError("Gagal parsing JSON koordinat.")

    if len(path) < 2:
        return 0.0

    total_distance = 0.0
    for i in range(1, len(path)):
        lat1, lon1 = path[i-1]
        lat2, lon2 = path[i]
        total_distance += haversine(lat1, lon1, lat2, lon2)

    return round(total_distance, 3)

# =======================================================
# 2. MODEL DATABASE (Run dan User)
# =======================================================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    runs = db.relationship('Run', backref='runner', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Run(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    distance_km = db.Column(db.Float, nullable=False)
    duration_min = db.Column(db.Integer, nullable=False)
    path_coordinates = db.Column(db.Text, nullable=True) # Data GPS mentah

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'date': self.date,
            'distance_km': round(self.distance_km, 2),
            'duration_min': self.duration_min,
            'pace': calculate_pace(self.distance_km, self.duration_min),
            'path_coordinates': self.path_coordinates
        }

# =======================================================
# 3. SETUP & USER LOADER
# =======================================================

@login_manager.user_loader
def load_user(user_id):
    """Mengambil objek User dari ID sesi."""
    return User.query.get(int(user_id))

def create_db_and_sample_data():
    """Memastikan database dan tabel dibuat, lalu mengisi data sampel."""
    db.create_all()
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'run_tracker.db')

    if not os.path.exists(os.path.join(os.path.dirname(__file__), 'instance')) or not User.query.first():
        print("Database 'run_tracker.db' sedang diinisialisasi.")
        
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(username='admin')
            admin_user.set_password('123456')
            db.session.add(admin_user)
            db.session.commit()
            print("Pengguna default (username: admin, password: 123456) dibuat.")
        
        admin_id = admin_user.id

        if not Run.query.filter_by(user_id=admin_id).first():
            runs_data = [
                {'date': '2025-10-25', 'distance_km': 5.2, 'duration_min': 32, 'path_coordinates': '[[106.8227, -6.1745], [106.8250, -6.1770], [106.8300, -6.1795]]'},
                {'date': '2025-10-27', 'distance_km': 10.0, 'duration_min': 65, 'path_coordinates': '[[106.8227, -6.1745], [106.8400, -6.1700]]'},
                {'date': '2025-10-29', 'distance_km': 7.0, 'duration_min': 39, 'path_coordinates': '[[106.8227, -6.1745], [106.8100, -6.1800]]'},
            ]
            for data in runs_data:
                run = Run(
                    user_id=admin_id, 
                    date=data['date'],
                    distance_km=data['distance_km'],
                    duration_min=data['duration_min'],
                    path_coordinates=data['path_coordinates']
                )
                db.session.add(run)
            db.session.commit()
            print("Data sampel lari (milik 'admin') telah ditambahkan.")
    else:
         print("Database sudah ada, melewati inisialisasi data sampel.")

# =======================================================
# 4. ENDPOINT API (Runs)
# =======================================================

@app.route('/api/runs', methods=['POST'])
@login_required
def add_run():
    data = request.get_json()

    try:
        new_run = Run(
            user_id=current_user.id,
            date=data['date'],
            distance_km=float(data['distance_km']),
            duration_min=int(data['duration_min']),
            path_coordinates=None
        )
        db.session.add(new_run)
        db.session.commit()
        return jsonify(new_run.to_dict()), 201
    except KeyError:
        return jsonify({"error": "Data lari tidak lengkap."}), 400
    except ValueError:
        return jsonify({"error": "Format data jarak atau durasi tidak valid."}), 400


@app.route('/api/runs/gps', methods=['POST'])
@login_required
def add_gps_run():
    data = request.get_json()

    if 'path_coordinates' not in data or 'duration_min' not in data:
        return jsonify({"error": "Data GPS lari tidak lengkap (koordinat atau durasi hilang)."}), 400

    path_coordinates_json = data['path_coordinates']
    raw_duration_min = data['duration_min']

    try:
        duration_min = float(raw_duration_min)
        if duration_min <= 0:
            return jsonify({"error": "Durasi lari harus lebih dari 0 menit."}), 400
    except ValueError:
        return jsonify({"error": "Format durasi tidak valid (bukan angka)."}), 400

    try:
        distance_km = calculate_total_distance_from_path(path_coordinates_json)
    except ValueError as e:
         return jsonify({"error": f"Gagal membaca data koordinat: {str(e)}"}), 400

    if distance_km < 0.01:
        return jsonify({"error": "Jarak yang terdeteksi 0 km. Data GPS terlalu sedikit atau tidak bergerak."}), 400
                                                 
    try:
        duration_to_save = round(duration_min)

        new_run = Run(
            user_id=current_user.id,
            date=data.get('date', datetime.now().strftime('%Y-%m-%d')),
            distance_km=distance_km,
            duration_min=duration_to_save,
            path_coordinates=path_coordinates_json
        )
        db.session.add(new_run)
        db.session.commit()
        return jsonify(new_run.to_dict()), 201
    except Exception as e:
        return jsonify({"error": f"Gagal menyimpan data lari GPS: {str(e)}"}), 500


@app.route('/api/runs', methods=['GET'])
@login_required
def get_runs():
    # Ambil hanya data lari milik user yang sedang login, diurutkan dari terbaru
    runs = Run.query.filter_by(user_id=current_user.id).order_by(Run.id.desc()).all()
    return jsonify([run.to_dict() for run in runs])

@app.route('/api/runs/<int:run_id>', methods=['PUT', 'DELETE'])
@login_required
def manage_run(run_id):
    run = Run.query.get_or_404(run_id)

    if run.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    if request.method == 'DELETE':
        db.session.delete(run)
        db.session.commit()
        return '', 204 # No Content

    elif request.method == 'PUT':
        data = request.get_json()

        run.date = data.get('date', run.date)
        run.distance_km = float(data.get('distance_km', run.distance_km))
        run.duration_min = int(data.get('duration_min', run.duration_min))

        db.session.commit()
        return jsonify(run.to_dict())

# =======================================================
# 5. ENDPOINT OTENTIKASI (Auth)
# =======================================================

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"message": "Username dan password diperlukan"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"message": "Username sudah terdaftar"}), 400

    new_user = User(username=username)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "Registrasi berhasil", "user": {"id": new_user.id, "username": new_user.username}}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        login_user(user)
        return jsonify({"message": "Login berhasil", "user": {"id": user.id, "username": user.username}}), 200

    return jsonify({"message": "Username atau password salah"}), 401

@app.route('/api/auth/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logout berhasil"}), 200

@app.route('/api/auth/status', methods=['GET'])
def auth_status():
    if current_user.is_authenticated:
        return jsonify({
            "is_authenticated": True,
            "user": {"id": current_user.id, "username": current_user.username}
        }), 200
    return jsonify({"is_authenticated": False}), 200

# =======================================================
# 6. ROUTE UNTUK MELAYANI FRONTEND VUE (Deployment KRITIS)
# =======================================================

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_vue_app(path):
    dist_dir = os.path.join(app.root_path, 'dist')
    
    if path != "" and os.path.exists(os.path.join(dist_dir, path)):
        return send_from_directory(dist_dir, path)
    else:
        return send_from_directory(dist_dir, 'index.html')

# =======================================================
# 7. MAIN EXECUTION
# =======================================================

if __name__ == '__main__':
    if not os.path.exists('instance'):
        os.makedirs('instance')

    with app.app_context():
        create_db_and_sample_data()

    app.run(debug=True)
