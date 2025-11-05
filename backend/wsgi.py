# File: backend/wsgi.py (VERSI FINAL & BENAR)

from app import app as application 
from app import create_db_and_sample_data # Kita butuh fungsi ini untuk inisialisasi DB

with application.app_context():
    create_db_and_sample_data()
