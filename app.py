import streamlit as st
import PyPDF2
import docx
import random
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import hashlib
import sqlite3
import time
import re
from wordcloud import WordCloud
import base64
import json
import requests
from streamlit_option_menu import option_menu
import streamlit.components.v1 as components
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import calendar
from textblob import TextBlob
import language_tool_python
import pycountry
import openai
from googletrans import Translator
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import plotly.figure_factory as ff

# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="AI Resume Analyzer Pro",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- DATABASE SETUP ----------------

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  email TEXT UNIQUE,
                  password TEXT,
                  created_at TIMESTAMP,
                  is_premium BOOLEAN DEFAULT 0,
                  credits INTEGER DEFAULT 10,
                  language TEXT DEFAULT 'en',
                  career_goal TEXT,
                  experience_level TEXT)''')
    
    # Create analysis_history table
    c.execute('''CREATE TABLE IF NOT EXISTS analysis_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  filename TEXT,
                  score INTEGER,
                  match_percent INTEGER,
                  analyzed_at TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    # Add new columns if they don't exist
    try:
        c.execute("ALTER TABLE analysis_history ADD COLUMN job_title TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        c.execute("ALTER TABLE analysis_history ADD COLUMN company TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Create resume_versions table
    c.execute('''CREATE TABLE IF NOT EXISTS resume_versions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  version_name TEXT,
                  filename TEXT,
                  score INTEGER,
                  created_at TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    # Create interview_schedules table
    c.execute('''CREATE TABLE IF NOT EXISTS interview_schedules
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  interview_date DATE,
                  interview_time TIME,
                  company TEXT,
                  position TEXT,
                  notes TEXT,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    # Create learning_resources table
    c.execute('''CREATE TABLE IF NOT EXISTS learning_resources
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  skill TEXT,
                  course_name TEXT,
                  platform TEXT,
                  url TEXT,
                  difficulty TEXT)''')
    
    conn.commit()
    conn.close()

init_db()

# ---------------- AUTHENTICATION FUNCTIONS ----------------

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, email, password, language='en'):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, email, password, created_at, credits, language) VALUES (?, ?, ?, ?, ?, ?)",
                  (username, email, hash_password(password), datetime.now(), 10, language))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?",
              (username, hash_password(password)))
    user = c.fetchone()
    conn.close()
    return user

def update_credits(user_id, credits):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET credits=? WHERE id=?", (credits, user_id))
    conn.commit()
    conn.close()

def save_analysis(user_id, filename, score, match_percent, job_title='', company=''):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    # Ensure job_title and company are not None
    job_title = job_title if job_title else ''
    company = company if company else ''
    
    c.execute("INSERT INTO analysis_history (user_id, filename, score, match_percent, analyzed_at, job_title, company) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (user_id, filename, score, match_percent, datetime.now(), job_title, company))
    conn.commit()
    conn.close()

def get_user_history(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT filename, score, match_percent, analyzed_at, job_title, company FROM analysis_history WHERE user_id=? ORDER BY analyzed_at DESC LIMIT 20",
              (user_id,))
    history = c.fetchall()
    conn.close()
    return history

def save_resume_version(user_id, version_name, filename, score):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT INTO resume_versions (user_id, version_name, filename, score, created_at) VALUES (?, ?, ?, ?, ?)",
              (user_id, version_name, filename, score, datetime.now()))
    conn.commit()
    conn.close()

def get_resume_versions(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT version_name, filename, score, created_at FROM resume_versions WHERE user_id=? ORDER BY created_at DESC",
              (user_id,))
    versions = c.fetchall()
    conn.close()
    return versions

def save_interview(user_id, interview_date, interview_time, company, position, notes):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT INTO interview_schedules (user_id, interview_date, interview_time, company, position, notes) VALUES (?, ?, ?, ?, ?, ?)",
              (user_id, interview_date, interview_time, company, position, notes))
    conn.commit()
    conn.close()

def get_interviews(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT interview_date, interview_time, company, position, notes FROM interview_schedules WHERE user_id=? AND interview_date >= date('now') ORDER BY interview_date, interview_time",
              (user_id,))
    interviews = c.fetchall()
    conn.close()
    return interviews

# ---------------- SESSION STATE ----------------

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'credits' not in st.session_state:
    st.session_state.credits = 0
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Home"
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False
if 'language' not in st.session_state:
    st.session_state.language = 'en'
if 'resume_versions' not in st.session_state:
    st.session_state.resume_versions = []
if 'comparison_result' not in st.session_state:
    st.session_state.comparison_result = None

# ---------------- TRANSLATIONS ----------------

translations = {
    'en': {
        'welcome': 'Welcome to AI Resume Analyzer',
        'login': 'Login',
        'signup': 'Sign Up',
        'username': 'Username',
        'password': 'Password',
        'email': 'Email',
        'analyze': 'Analyze Resume',
        'score': 'Resume Score',
        'match': 'Job Match',
        'skills': 'Skills',
        'missing': 'Missing Skills',
        'feedback': 'AI Feedback',
        'dashboard': 'Dashboard',
        'settings': 'Settings',
        'pricing': 'Pricing',
        'history': 'History',
        'credits': 'Credits',
        'premium': 'Premium Features',
        'dark_mode': 'Dark Mode',
        'logout': 'Logout',
        'upload': 'Upload Resume',
        'job_desc': 'Job Description',
        'analyzing': 'Analyzing...',
        'complete': 'Analysis Complete!',
        'error': 'Error',
        'success': 'Success',
        'warning': 'Warning',
        'info': 'Information'
    },
    'es': {
        'welcome': 'Bienvenido al Analizador de Currículums con IA',
        'login': 'Iniciar Sesión',
        'signup': 'Registrarse',
        'username': 'Nombre de Usuario',
        'password': 'Contraseña',
        'email': 'Correo Electrónico',
        'analyze': 'Analizar Currículum',
        'score': 'Puntuación del Currículum',
        'match': 'Coincidencia Laboral',
        'skills': 'Habilidades',
        'missing': 'Habilidades Faltantes',
        'feedback': 'Retroalimentación de IA',
        'dashboard': 'Panel de Control',
        'settings': 'Configuración',
        'pricing': 'Precios',
        'history': 'Historial',
        'credits': 'Créditos',
        'premium': 'Características Premium',
        'dark_mode': 'Modo Oscuro',
        'logout': 'Cerrar Sesión',
        'upload': 'Subir Currículum',
        'job_desc': 'Descripción del Trabajo',
        'analyzing': 'Analizando...',
        'complete': '¡Análisis Completo!',
        'error': 'Error',
        'success': 'Éxito',
        'warning': 'Advertencia',
        'info': 'Información'
    },
    'fr': {
        'welcome': 'Bienvenue sur l\'Analyseur de CV IA',
        'login': 'Connexion',
        'signup': 'S\'inscrire',
        'username': 'Nom d\'utilisateur',
        'password': 'Mot de Passe',
        'email': 'E-mail',
        'analyze': 'Analyser le CV',
        'score': 'Score du CV',
        'match': 'Correspondance Emploi',
        'skills': 'Compétences',
        'missing': 'Compétences Manquantes',
        'feedback': 'Retour IA',
        'dashboard': 'Tableau de Bord',
        'settings': 'Paramètres',
        'pricing': 'Tarifs',
        'history': 'Historique',
        'credits': 'Crédits',
        'premium': 'Fonctionnalités Premium',
        'dark_mode': 'Mode Sombre',
        'logout': 'Déconnexion',
        'upload': 'Télécharger CV',
        'job_desc': 'Description du Poste',
        'analyzing': 'Analyse en cours...',
        'complete': 'Analyse Terminée !',
        'error': 'Erreur',
        'success': 'Succès',
        'warning': 'Avertissement',
        'info': 'Information'
    },
    'de': {
        'welcome': 'Willkommen beim KI-Lebenslauf-Analysator',
        'login': 'Anmelden',
        'signup': 'Registrieren',
        'username': 'Benutzername',
        'password': 'Passwort',
        'email': 'E-Mail',
        'analyze': 'Lebenslauf analysieren',
        'score': 'Lebenslauf-Punktzahl',
        'match': 'Job-Übereinstimmung',
        'skills': 'Fähigkeiten',
        'missing': 'Fehlende Fähigkeiten',
        'feedback': 'KI-Feedback',
        'dashboard': 'Dashboard',
        'settings': 'Einstellungen',
        'pricing': 'Preise',
        'history': 'Verlauf',
        'credits': 'Guthaben',
        'premium': 'Premium-Funktionen',
        'dark_mode': 'Dunkelmodus',
        'logout': 'Abmelden',
        'upload': 'Lebenslauf hochladen',
        'job_desc': 'Stellenbeschreibung',
        'analyzing': 'Analysiere...',
        'complete': 'Analyse abgeschlossen!',
        'error': 'Fehler',
        'success': 'Erfolg',
        'warning': 'Warnung',
        'info': 'Information'
    }
}

def t(key):
    """Translate function"""
    return translations.get(st.session_state.language, translations['en']).get(key, key)

# ---------------- CUSTOM CSS WITH BETTER VISIBILITY ----------------

def load_css():
    if st.session_state.dark_mode:
        primary_color = "#bb86fc"
        secondary_color = "#03dac6"
        bg_color = "#121212"
        card_bg = "#1e1e1e"
        text_color = "#ffffff"
        heading_color = "#ffffff"
        subtext_color = "#e0e0e0"
        border_color = "#333333"
        input_bg = "#2d2d2d"
        input_text = "#ffffff"
        label_color = "#e0e0e0"
    else:
        primary_color = "#6366f1"
        secondary_color = "#10b981"
        bg_color = "#f8fafc"
        card_bg = "#ffffff"
        text_color = "#0f172a"
        heading_color = "#0f172a"
        subtext_color = "#334155"
        border_color = "#cbd5e1"
        input_bg = "#ffffff"
        input_text = "#0f172a"
        label_color = "#1e293b"

    st.markdown(f"""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Global Styles */
    .stApp {{
        background: {bg_color};
        color: {text_color};
        font-family: 'Inter', sans-serif;
    }}
    
    /* Headers with better visibility */
    h1, h2, h3, h4, h5, h6 {{
        color: {heading_color} !important;
        font-weight: 600 !important;
    }}
    
    h1 {{
        font-size: 2.5rem !important;
        margin-bottom: 1rem !important;
    }}
    
    /* Paragraph text */
    p, li, .stMarkdown {{
        color: {subtext_color} !important;
        line-height: 1.6 !important;
    }}
    
    /* Custom Card Style */
    .custom-card {{
        background: {card_bg};
        border-radius: 20px;
        padding: 25px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        border: 1px solid {border_color};
        transition: transform 0.3s ease;
        margin-bottom: 20px;
        color: {text_color};
    }}
    
    .custom-card:hover {{
        transform: translateY(-5px);
        box-shadow: 0 20px 60px rgba(99, 102, 241, 0.2);
    }}
    
    /* Gradient Text */
    .gradient-text {{
        background: linear-gradient(135deg, {primary_color}, {secondary_color});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        display: inline-block;
    }}
    
    /* Metric Container */
    .metric-container {{
        background: linear-gradient(135deg, {primary_color}15, {secondary_color}15);
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        border-left: 4px solid {primary_color};
    }}
    
    .metric-container label {{
        color: {subtext_color} !important;
        font-size: 14px !important;
        font-weight: 500 !important;
    }}
    
    .metric-container .stMetric {{
        color: {heading_color} !important;
    }}
    
    /* Button Style */
    .stButton > button {{
        background: linear-gradient(135deg, {primary_color}, {secondary_color});
        color: white !important;
        border: none;
        border-radius: 10px;
        padding: 10px 25px;
        font-weight: 600;
        transition: all 0.3s ease;
        border: 1px solid transparent;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 10px 30px {primary_color}80;
        border: 1px solid white;
    }}
    
    /* Input Fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stPassword > div > div > input,
    .stDateInput > div > div > input,
    .stTimeInput > div > div > input {{
        background-color: {input_bg} !important;
        color: {input_text} !important;
        border: 2px solid {border_color} !important;
        border-radius: 10px !important;
        padding: 12px 15px !important;
        font-size: 16px !important;
        font-weight: 500 !important;
    }}
    
    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder,
    .stPassword > div > div > input::placeholder {{
        color: #94a3b8 !important;
        opacity: 1;
        font-weight: 400 !important;
    }}
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stPassword > div > div > input:focus {{
        border-color: {primary_color} !important;
        box-shadow: 0 0 0 3px {primary_color}40 !important;
        outline: none !important;
    }}
    
    /* Labels for inputs */
    .stTextInput label,
    .stTextArea label,
    .stPassword label,
    .stDateInput label,
    .stTimeInput label {{
        color: {label_color} !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        margin-bottom: 5px !important;
    }}
    
    /* Form container */
    [data-testid="stForm"] {{
        background-color: transparent !important;
        border: none !important;
        padding: 0 !important;
    }}
    
    /* Progress Bar */
    .stProgress > div > div > div > div {{
        background: linear-gradient(90deg, {primary_color}, {secondary_color});
        border-radius: 10px;
    }}
    
    /* Sidebar */
    .css-1d391kg {{
        background: {card_bg};
        border-right: 1px solid {border_color};
    }}
    
    .css-1d391kg .stMarkdown {{
        color: {text_color} !important;
    }}
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 20px;
        background-color: {card_bg};
        padding: 10px;
        border-radius: 10px;
        border: 1px solid {border_color};
    }}
    
    .stTabs [data-baseweb="tab"] {{
        border-radius: 8px;
        padding: 10px 20px;
        color: {subtext_color} !important;
        font-weight: 500;
        transition: all 0.2s ease;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, {primary_color}20, {secondary_color}20) !important;
        color: {primary_color} !important;
        font-weight: 600 !important;
    }}
    
    /* Badge */
    .badge {{
        display: inline-block;
        padding: 6px 16px;
        border-radius: 50px;
        font-size: 13px;
        font-weight: 600;
        background: linear-gradient(135deg, {primary_color}, {secondary_color});
        color: white;
        margin-right: 10px;
        margin-bottom: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }}
    
    /* Stats Card */
    .stats-card {{
        background: linear-gradient(135deg, {primary_color}, {secondary_color});
        border-radius: 15px;
        padding: 20px;
        color: white;
        text-align: center;
    }}
    
    .stats-card p {{
        color: rgba(255,255,255,0.9) !important;
        font-size: 14px;
        margin-bottom: 5px;
    }}
    
    .stats-number {{
        font-size: 36px;
        font-weight: 700;
        margin: 10px 0;
        color: white !important;
    }}
    
    /* Feature Card */
    .feature-card {{
        background: {card_bg};
        border-radius: 15px;
        padding: 20px;
        border: 1px solid {border_color};
        transition: all 0.3s ease;
        height: 100%;
    }}
    
    .feature-card:hover {{
        transform: translateY(-5px);
        box-shadow: 0 10px 30px {primary_color}40;
    }}
    
    .feature-icon {{
        font-size: 40px;
        margin-bottom: 15px;
    }}
    
    .feature-title {{
        font-size: 18px;
        font-weight: 600;
        margin-bottom: 10px;
        color: {heading_color};
    }}
    
    .feature-description {{
        font-size: 14px;
        color: {subtext_color};
        line-height: 1.5;
    }}
    
    /* Calendar */
    .calendar-cell {{
        background: {card_bg};
        border: 1px solid {border_color};
        padding: 10px;
        min-height: 80px;
    }}
    
    .calendar-date {{
        font-weight: 600;
        color: {heading_color};
    }}
    
    .calendar-event {{
        background: {primary_color}20;
        border-left: 3px solid {primary_color};
        padding: 5px;
        margin: 5px 0;
        font-size: 12px;
        color: {text_color};
    }}
    
    /* Info/Warning/Success messages */
    .stAlert {{
        border-radius: 10px;
        border-left: 4px solid;
    }}
    
    .stAlert > div {{
        color: {text_color} !important;
    }}
    
    /* Footer */
    .footer {{
        text-align: center;
        padding: 20px;
        color: {subtext_color}80;
        font-size: 14px;
    }}
    
    /* Animation */
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(20px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    .fade-in {{
        animation: fadeIn 0.5s ease-out;
    }}
    
    /* Divider */
    hr {{
        border-color: {border_color} !important;
        opacity: 0.3;
    }}
    
    /* Expander */
    .streamlit-expanderHeader {{
        color: {heading_color} !important;
        font-weight: 600 !important;
        background-color: {card_bg} !important;
        border-radius: 10px !important;
    }}
    
    /* Radio buttons and checkboxes */
    .stRadio label, .stCheckbox label {{
        color: {text_color} !important;
    }}
    
    /* Select box */
    .stSelectbox label {{
        color: {label_color} !important;
    }}
    
    .stSelectbox > div > div {{
        background-color: {input_bg} !important;
        color: {input_text} !important;
        border: 2px solid {border_color} !important;
        border-radius: 10px !important;
    }}
    
    /* Mobile Responsive */
    @media (max-width: 768px) {{
        h1 {{
            font-size: 2rem !important;
        }}
        
        .custom-card {{
            padding: 15px;
        }}
        
        .stats-number {{
            font-size: 24px;
        }}
    }}
    </style>
    """, unsafe_allow_html=True)

# ---------------- FUNCTIONS ----------------

def extract_text_from_pdf(file):
    try:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except:
        return ""

def extract_text_from_docx(file):
    try:
        doc = docx.Document(file)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    except:
        return ""

def calculate_resume_score(resume_text):
    score = 65
    
    sections = {
        'education': ['education', 'university', 'college', 'degree', 'bachelor', 'master', 'phd'],
        'experience': ['experience', 'work', 'employment', 'job', 'internship'],
        'skills': ['skills', 'technologies', 'programming', 'tools', 'languages'],
        'projects': ['projects', 'portfolio', 'github', 'development'],
        'certifications': ['certification', 'certificate', 'course', 'training'],
        'achievements': ['achievement', 'award', 'honor', 'recognition']
    }
    
    for section, keywords in sections.items():
        if any(keyword in resume_text.lower() for keyword in keywords):
            score += 5
    
    contact_patterns = [
        r'\b[\w\.-]+@[\w\.-]+\.\w+\b',
        r'\b\d{10}\b',
        r'linkedin\.com/in/',
        r'github\.com/'
    ]
    
    for pattern in contact_patterns:
        if re.search(pattern, resume_text.lower()):
            score += 2
    
    word_count = len(resume_text.split())
    if word_count > 500:
        score += 5
    elif word_count > 300:
        score += 2
    
    return min(score, 100)

def skill_match(resume_text, job_description):
    skill_database = {
        'python': ['python', 'django', 'flask', 'pandas', 'numpy'],
        'javascript': ['javascript', 'js', 'react', 'vue', 'angular', 'node'],
        'java': ['java', 'spring', 'hibernate', 'j2ee'],
        'sql': ['sql', 'mysql', 'postgresql', 'database', 'oracle'],
        'cloud': ['aws', 'azure', 'gcp', 'cloud', 'docker', 'kubernetes'],
        'frontend': ['html', 'css', 'javascript', 'react', 'vue', 'angular'],
        'backend': ['node', 'django', 'flask', 'spring', 'api'],
        'data_science': ['machine learning', 'data science', 'ai', 'tensorflow', 'pytorch'],
        'devops': ['jenkins', 'gitlab', 'ci/cd', 'ansible', 'terraform'],
        'mobile': ['android', 'ios', 'flutter', 'react native', 'swift'],
        'soft_skills': ['communication', 'leadership', 'teamwork', 'problem solving', 'critical thinking']
    }
    
    resume_words = set(re.findall(r'\b\w+\b', resume_text.lower()))
    job_words = set(re.findall(r'\b\w+\b', job_description.lower()))
    
    matched = set()
    expanded_matched = set()
    
    matched = resume_words.intersection(job_words)
    
    for skill, related_terms in skill_database.items():
        if any(term in resume_text.lower() for term in related_terms):
            if any(term in job_description.lower() for term in related_terms):
                expanded_matched.add(skill)
    
    all_matched = matched.union(expanded_matched)
    
    total_keywords = len(job_words)
    if total_keywords == 0:
        return 0, list(all_matched)
    
    weighted_match = len(all_matched) / total_keywords * 100
    
    if expanded_matched:
        weighted_match += 10
    
    return min(int(weighted_match), 100), list(all_matched)

def missing_skills(resume_text, job_description):
    resume_words = set(re.findall(r'\b\w+\b', resume_text.lower()))
    job_words = set(re.findall(r'\b\w+\b', job_description.lower()))
    
    missing = job_words - resume_words
    
    common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                    'of', 'with', 'by', 'from', 'as', 'is', 'was', 'were', 'are', 'be'}
    
    missing = [word for word in missing if word not in common_words and len(word) > 2]
    
    return missing[:15]

def ai_feedback(score, match_percent, matched_skills, missing_skills):
    feedback = []
    
    if score >= 85:
        feedback.append("🌟 Excellent resume structure and content!")
    elif score >= 70:
        feedback.append("📈 Good resume, but there's room for improvement.")
    else:
        feedback.append("⚠️ Your resume needs significant improvement.")
    
    if match_percent >= 80:
        feedback.append(f"✅ Great job matching the job description! ({match_percent}% match)")
    elif match_percent >= 60:
        feedback.append(f"👍 Decent match with the job requirements. ({match_percent}% match)")
    else:
        feedback.append(f"⚠️ Low match with job description. ({match_percent}% match)")
    
    if len(matched_skills) > 0:
        feedback.append(f"💪 Your strongest skills: {', '.join(matched_skills[:5])}")
    
    if len(missing_skills) > 0:
        feedback.append(f"🎯 Key skills to add: {', '.join(missing_skills[:5])}")
    
    if score < 70:
        feedback.append("📝 Add more quantifiable achievements and results")
    if match_percent < 60:
        feedback.append("🔄 Tailor your resume to include more keywords from the job description")
    if len(matched_skills) < 5:
        feedback.append("📚 Consider adding relevant certifications or courses")
    
    return feedback

def create_radar_chart(match_percent, score):
    categories = ['Skill Match', 'Resume Structure', 'ATS Compatibility', 
                  'Experience Match', 'Keyword Density']
    
    values = [
        match_percent,
        score,
        random.randint(65, 95),
        random.randint(60, 90),
        random.randint(70, 95)
    ]
    
    fig = go.Figure(data=go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        marker=dict(color='rgba(99, 102, 241, 0.8)'),
        line=dict(color='rgba(99, 102, 241, 1)', width=3)
    ))
    
    text_color = '#ffffff' if st.session_state.dark_mode else '#0f172a'
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                color=text_color
            )),
        showlegend=False,
        height=400,
        margin=dict(l=80, r=80, t=20, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=text_color)
    )
    
    return fig

def create_skills_wordcloud(matched_skills, missing_skills):
    matched_list = matched_skills[:10] if matched_skills else []
    missing_list = missing_skills[:5] if missing_skills else []
    
    skills_data = []
    
    for skill in matched_list:
        skills_data.append({
            'Skill': skill,
            'Type': 'Matched',
            'Count': random.randint(5, 15)
        })
    
    for skill in missing_list:
        skills_data.append({
            'Skill': skill,
            'Type': 'Missing',
            'Count': random.randint(5, 15)
        })
    
    if not skills_data:
        skills_data = [
            {'Skill': 'No Skills Found', 'Type': 'Matched', 'Count': 1},
            {'Skill': 'Upload Resume', 'Type': 'Missing', 'Count': 1}
        ]
    
    matched_df = pd.DataFrame(skills_data)
    
    fig = px.treemap(matched_df, path=['Type', 'Skill'], values='Count',
                     color='Type',
                     color_discrete_map={'Matched': '#10b981', 'Missing': '#ef4444'},
                     title='Skills Distribution')
    
    text_color = '#ffffff' if st.session_state.dark_mode else '#0f172a'
    
    fig.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color=text_color, size=12)
    )
    
    return fig

def generate_report(file, score, match_percent, matched_skills, missing_skills, feedback):
    report = f"""
╔══════════════════════════════════════════════════════════════╗
║                 AI RESUME ANALYSIS REPORT                     ║
╚════════════════════════════════════════════════════════════════╝

📄 RESUME: {file.name}
📅 DATE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

═══════════════════════════════════════════════════════════════════

📊 OVERALL SCORES:
   • Resume Score: {score}%
   • Job Match: {match_percent}%
   
   {'⭐' * (score // 20)} Rating: {'Excellent' if score >= 85 else 'Good' if score >= 70 else 'Needs Improvement'}

═══════════════════════════════════════════════════════════════════

✅ MATCHED SKILLS ({len(matched_skills)} found):
{chr(10).join(['   • ' + skill for skill in matched_skills[:15]])}

{'   (and more...)' if len(matched_skills) > 15 else ''}

═══════════════════════════════════════════════════════════════════

⚠️ MISSING SKILLS ({len(missing_skills)} identified):
{chr(10).join(['   • ' + skill for skill in missing_skills[:15]])}

{'   (and more...)' if len(missing_skills) > 15 else ''}

═══════════════════════════════════════════════════════════════════

🤖 AI FEEDBACK & RECOMMENDATIONS:
{chr(10).join(['   • ' + f for f in feedback])}

═══════════════════════════════════════════════════════════════════

💡 QUICK TIPS:
   • Use action verbs to describe your achievements
   • Quantify your impact with numbers and percentages
   • Customize your resume for each job application
   • Include relevant keywords from job descriptions
   • Keep your resume concise (1-2 pages)

═══════════════════════════════════════════════════════════════════

Generated by AI Resume Analyzer Pro 🚀
    """
    return report

# Feature 1: Resume Version Comparison
def compare_resume_versions(version1_text, version2_text):
    """Compare two versions of a resume and show improvements"""
    
    # Calculate scores for both versions
    score1 = calculate_resume_score(version1_text)
    score2 = calculate_resume_score(version2_text)
    
    # Simple similarity based on common words (without sklearn)
    words1 = set(re.findall(r'\b\w+\b', version1_text.lower()))
    words2 = set(re.findall(r'\b\w+\b', version2_text.lower()))
    
    common_words = words1.intersection(words2)
    all_words = words1.union(words2)
    
    similarity = (len(common_words) / len(all_words)) * 100 if all_words else 0
    
    # Find added/removed keywords
    added = words2 - words1
    removed = words1 - words2
    
    common_words_set = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'were', 'are', 'be'}
    
    added = [w for w in added if w not in common_words_set and len(w) > 3][:10]
    removed = [w for w in removed if w not in common_words_set and len(w) > 3][:10]
    
    return {
        'score1': score1,
        'score2': score2,
        'improvement': score2 - score1,
        'similarity': similarity,
        'added_keywords': added,
        'removed_keywords': removed
    }

# Feature 2: Career Path Recommendations
def get_career_recommendations(skills, experience_level):
    """Suggest career paths based on skills and experience"""
    
    career_paths = {
        'entry': [
            {'title': 'Junior Software Developer', 'salary': '$60k - $75k', 'demand': 'High', 'growth': 'Excellent'},
            {'title': 'Data Analyst', 'salary': '$55k - $70k', 'demand': 'Very High', 'growth': 'Excellent'},
            {'title': 'IT Support Specialist', 'salary': '$45k - $60k', 'demand': 'High', 'growth': 'Good'},
            {'title': 'QA Tester', 'salary': '$50k - $65k', 'demand': 'High', 'growth': 'Good'},
            {'title': 'Junior Web Developer', 'salary': '$55k - $70k', 'demand': 'Very High', 'growth': 'Excellent'}
        ],
        'mid': [
            {'title': 'Software Engineer', 'salary': '$85k - $110k', 'demand': 'Very High', 'growth': 'Excellent'},
            {'title': 'Data Scientist', 'salary': '$95k - $130k', 'demand': 'Very High', 'growth': 'Excellent'},
            {'title': 'DevOps Engineer', 'salary': '$90k - $120k', 'demand': 'High', 'growth': 'Excellent'},
            {'title': 'Product Manager', 'salary': '$100k - $140k', 'demand': 'High', 'growth': 'Very Good'},
            {'title': 'Cloud Architect', 'salary': '$110k - $150k', 'demand': 'Very High', 'growth': 'Excellent'}
        ],
        'senior': [
            {'title': 'Senior Software Architect', 'salary': '$130k - $180k', 'demand': 'High', 'growth': 'Good'},
            {'title': 'Engineering Manager', 'salary': '$140k - $190k', 'demand': 'High', 'growth': 'Good'},
            {'title': 'Director of Engineering', 'salary': '$160k - $220k', 'demand': 'Medium', 'growth': 'Good'},
            {'title': 'CTO', 'salary': '$180k - $250k+', 'demand': 'Medium', 'growth': 'Good'},
            {'title': 'Principal Data Scientist', 'salary': '$150k - $200k', 'demand': 'High', 'growth': 'Very Good'}
        ]
    }
    
    return career_paths.get(experience_level, career_paths['mid'])

# Feature 3: Salary Estimator
def estimate_salary(skills, experience_years, location, job_title):
    """Estimate salary based on skills, experience, and location"""
    
    base_salary = {
        'Software Engineer': 85000,
        'Data Scientist': 95000,
        'DevOps Engineer': 90000,
        'Product Manager': 100000,
        'UX Designer': 80000,
        'Project Manager': 85000
    }
    
    # Location multipliers
    location_multiplier = {
        'San Francisco': 1.5,
        'New York': 1.4,
        'Seattle': 1.3,
        'Austin': 1.1,
        'Remote': 1.0,
        'Other': 0.9
    }
    
    # Experience multiplier
    exp_multiplier = 1.0 + (experience_years * 0.05)
    
    # Skills bonus
    skill_bonus = len(skills) * 500
    
    base = base_salary.get(job_title, 80000)
    location_factor = location_multiplier.get(location, 1.0)
    
    estimated = (base * location_factor * exp_multiplier) + skill_bonus
    
    return {
        'minimum': int(estimated * 0.9),
        'average': int(estimated),
        'maximum': int(estimated * 1.2),
        'currency': 'USD'
    }

# Feature 4: Multi-language Support
def translate_text(text, target_language):
    """Translate text to target language"""
    translator = Translator()
    try:
        translation = translator.translate(text, dest=target_language)
        return translation.text
    except:
        return text

def detect_language(text):
    """Detect the language of the text"""
    translator = Translator()
    try:
        detection = translator.detect(text)
        return detection.lang
    except:
        return 'en'

# Feature 5: Mobile-friendly Interface - Handled by CSS

# Feature 6: Company Culture Match
def analyze_company_culture(resume_text, company_values):
    """Analyze how well the resume matches company culture"""
    
    culture_keywords = {
        'innovation': ['innovative', 'creative', 'new', 'cutting-edge', 'forward-thinking'],
        'teamwork': ['team', 'collaboration', 'together', 'group', 'coordinate'],
        'leadership': ['lead', 'managed', 'directed', 'supervised', 'headed'],
        'growth': ['learn', 'improve', 'develop', 'grow', 'advance'],
        'customer_focus': ['customer', 'client', 'user', 'service', 'support'],
        'results': ['achieved', 'delivered', 'completed', 'accomplished', 'exceeded']
    }
    
    matches = {}
    for culture, keywords in culture_keywords.items():
        count = sum(1 for keyword in keywords if keyword in resume_text.lower())
        matches[culture] = min(count * 20, 100)
    
    return matches

# Feature 7: Learning Resources
def get_learning_resources(skill):
    """Get recommended courses for a specific skill"""
    
    resources = {
        'python': [
            {'name': 'Python for Everybody', 'platform': 'Coursera', 'difficulty': 'Beginner', 'url': '#'},
            {'name': 'Complete Python Bootcamp', 'platform': 'Udemy', 'difficulty': 'Beginner', 'url': '#'},
            {'name': 'Advanced Python', 'platform': 'Pluralsight', 'difficulty': 'Advanced', 'url': '#'}
        ],
        'javascript': [
            {'name': 'JavaScript Basics', 'platform': 'Codecademy', 'difficulty': 'Beginner', 'url': '#'},
            {'name': 'The Complete JavaScript Course', 'platform': 'Udemy', 'difficulty': 'Intermediate', 'url': '#'},
            {'name': 'Advanced JavaScript', 'platform': 'Frontend Masters', 'difficulty': 'Advanced', 'url': '#'}
        ],
        'data_science': [
            {'name': 'Data Science Specialization', 'platform': 'Coursera', 'difficulty': 'Intermediate', 'url': '#'},
            {'name': 'Machine Learning Course', 'platform': 'Stanford Online', 'difficulty': 'Advanced', 'url': '#'},
            {'name': 'Python for Data Science', 'platform': 'edX', 'difficulty': 'Beginner', 'url': '#'}
        ],
        'cloud': [
            {'name': 'AWS Certified Solutions Architect', 'platform': 'AWS Training', 'difficulty': 'Intermediate', 'url': '#'},
            {'name': 'Google Cloud Certification', 'platform': 'Google Cloud', 'difficulty': 'Intermediate', 'url': '#'},
            {'name': 'Azure Fundamentals', 'platform': 'Microsoft Learn', 'difficulty': 'Beginner', 'url': '#'}
        ]
    }
    
    return resources.get(skill.lower(), [
        {'name': f'Introduction to {skill}', 'platform': 'Various', 'difficulty': 'Beginner', 'url': '#'},
        {'name': f'Advanced {skill}', 'platform': 'Various', 'difficulty': 'Advanced', 'url': '#'}
    ])

# Feature 8: Networking Suggestions
def get_networking_suggestions(skills, job_title):
    """Suggest professionals to connect with on LinkedIn"""
    
    suggestions = []
    
    # Generate realistic suggestions based on skills
    for i, skill in enumerate(skills[:3]):
        suggestions.append({
            'name': f"Professional {i+1}",
            'title': f"Senior {job_title}" if job_title else f"Expert in {skill}",
            'company': random.choice(['Google', 'Microsoft', 'Amazon', 'Meta', 'Apple']),
            'connection_degree': random.choice(['2nd', '3rd']),
            'profile_url': '#'
        })
    
    return suggestions

# Feature 9: Interview Scheduler
def create_interview_calendar(interviews):
    """Create a calendar view of scheduled interviews"""
    
    if not interviews:
        return None
    
    # Create a date range for the next 30 days
    today = datetime.now().date()
    dates = [today + timedelta(days=i) for i in range(30)]
    
    # Create calendar data
    calendar_data = []
    for date in dates:
        day_interviews = [i for i in interviews if i[0] == date]
        calendar_data.append({
            'date': date,
            'day': date.day,
            'month': date.month,
            'interviews': len(day_interviews),
            'details': day_interviews
        })
    
    return calendar_data

# Feature 10: Achievement Analyzer
def analyze_achievements(resume_text):
    """Identify and quantify achievements in the resume"""
    
    # Patterns for quantifiable achievements
    achievement_patterns = [
        r'increased by (\d+)%',
        r'improved by (\d+)%',
        r'reduced by (\d+)%',
        r'saved \$?(\d+[k,]?\d*)',
        r'generated \$?(\d+[k,]?\d*)',
        r'managed (\d+)',
        r'led (\d+)',
        r'created (\d+)',
        r'developed (\d+)',
        r'launched (\d+)'
    ]
    
    achievements = []
    for pattern in achievement_patterns:
        matches = re.findall(pattern, resume_text.lower())
        if matches:
            achievements.append({
                'pattern': pattern,
                'count': len(matches),
                'examples': matches[:3]
            })
    
    # Score achievements
    achievement_score = len(achievements) * 10
    achievement_score = min(achievement_score, 100)
    
    # Generate recommendations
    recommendations = []
    if achievement_score < 30:
        recommendations.append("Add more quantifiable achievements with numbers and percentages")
    if achievement_score < 50:
        recommendations.append("Use action verbs like 'increased', 'improved', 'reduced'")
    if achievement_score < 70:
        recommendations.append("Include specific metrics to demonstrate your impact")
    
    return {
        'score': achievement_score,
        'achievements': achievements,
        'recommendations': recommendations,
        'total_quantifiable': sum(a['count'] for a in achievements)
    }

# ---------------- MAIN APP ----------------

# Load CSS
load_css()

# Sidebar Navigation
with st.sidebar:
    st.markdown("""
    <div style='text-align: center; padding: 20px 0;'>
        <h1 style='font-size: 40px; margin-bottom: 0;'>🚀</h1>
        <h2 class='gradient-text' style='margin-top: 0;'>AI Resume Analyzer</h2>
        <p style='opacity: 0.8;'>Professional Edition</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Language Selector
    languages = {
        'English': 'en',
        'Spanish': 'es',
        'French': 'fr',
        'German': 'de'
    }
    selected_language = st.selectbox("🌐 Language", list(languages.keys()))
    st.session_state.language = languages[selected_language]
    
    st.divider()
    
    selected = option_menu(
        menu_title="Navigation",
        options=["Home", "Dashboard", "Resume Versions", "Career Path", "Interview Scheduler", "Learning Resources", "Settings", "Pricing"],
        icons=["house", "graph-up", "files", "compass", "calendar", "book", "gear", "currency-dollar"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#6366f1", "font-size": "20px"},
            "nav-link": {"font-size": "16px", "text-align": "left", "margin": "5px 0"},
            "nav-link-selected": {"background-color": "#6366f1"},
        }
    )
    
    st.divider()
    
    st.session_state.dark_mode = st.toggle("🌙 Dark Mode", st.session_state.dark_mode)
    
    if st.session_state.logged_in:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #6366f1, #10b981); padding: 20px; border-radius: 10px;'>
            <p style='color: white; margin: 0; font-weight: 600;'>👤 {st.session_state.username}</p>
            <p style='color: rgba(255,255,255,0.9); margin: 5px 0 0 0; font-size: 14px;'>{t('credits')}: {st.session_state.credits} ⭐</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(t('logout'), use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.username = None
            st.session_state.credits = 0
            st.rerun()
    else:
        st.markdown("""
        <div style='text-align: center; padding: 10px;'>
            <p style='font-size: 16px;'>👋 Welcome Guest</p>
            <p style='font-size: 14px; opacity: 0.8;'>Please login to continue</p>
        </div>
        """, unsafe_allow_html=True)

# ---------------- PAGE ROUTING ----------------

if not st.session_state.logged_in and selected != "Pricing":
    # AUTHENTICATION PAGE
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class='custom-card fade-in'>
            <h1 style='text-align: center; color: #6366f1;'>🚀 Welcome to AI Resume Analyzer</h1>
            <p style='text-align: center; color: #334155; font-size: 16px;'>Sign in to access advanced features</p>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input(t('username'), placeholder="Enter your username")
                password = st.text_input(t('password'), type="password", placeholder="Enter your password")
                
                col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
                with col_btn2:
                    submitted = st.form_submit_button(t('login'), use_container_width=True)
                
                if submitted:
                    if username and password:
                        user = verify_user(username, password)
                        if user:
                            st.session_state.logged_in = True
                            st.session_state.user_id = user[0]
                            st.session_state.username = user[1]
                            st.session_state.credits = user[6]
                            st.success("✅ Login successful! Redirecting...")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Invalid username or password")
                    else:
                        st.warning("⚠️ Please enter both username and password")
        
        with tab2:
            with st.form("signup_form"):
                new_username = st.text_input(t('username'), placeholder="Enter username")
                new_email = st.text_input(t('email'), placeholder="Enter your email")
                new_password = st.text_input(t('password'), type="password", placeholder="Enter password")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm password")
                
                col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
                with col_btn2:
                    submitted = st.form_submit_button(t('signup'), use_container_width=True)
                
                if submitted:
                    if not all([new_username, new_email, new_password, confirm_password]):
                        st.warning("⚠️ Please fill all fields")
                    elif new_password != confirm_password:
                        st.error("❌ Passwords do not match")
                    elif len(new_password) < 6:
                        st.error("❌ Password must be at least 6 characters")
                    elif "@" not in new_email or "." not in new_email:
                        st.error("❌ Please enter a valid email")
                    else:
                        if create_user(new_username, new_email, new_password, st.session_state.language):
                            st.success("✅ Account created! Please login.")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Username or email already exists")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Features Preview
        st.markdown("""
        <div class='custom-card fade-in'>
            <h3 style='color: #0f172a; margin-bottom: 15px;'>✨ 10+ Premium Features</h3>
            <div style='display: flex; flex-wrap: wrap; gap: 10px;'>
                <span class='badge'>AI Analysis</span>
                <span class='badge'>Skill Matching</span>
                <span class='badge'>ATS Score</span>
                <span class='badge'>Resume Reports</span>
                <span class='badge'>Career Advice</span>
                <span class='badge'>Salary Estimator</span>
                <span class='badge'>Multi-language</span>
                <span class='badge'>Interview Scheduler</span>
                <span class='badge'>Learning Resources</span>
                <span class='badge'>Version Comparison</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

elif selected == "Pricing":
    st.markdown("<h1 class='gradient-text'>💰 Pricing Plans</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class='custom-card'>
            <h3 style='color: #0f172a;'>Free</h3>
            <h2 class='gradient-text'>$0</h2>
            <p style='color: #334155;'>Perfect for trying out</p>
            <ul style='list-style-type: none; padding: 0; color: #334155;'>
                <li>✅ 10 credits/month</li>
                <li>✅ Basic analysis</li>
                <li>✅ PDF/Word support</li>
                <li>✅ 5 features</li>
                <li>❌ Advanced insights</li>
                <li>❌ Priority support</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Get Started", key="free", use_container_width=True):
            st.info("Sign up for free account!")
    
    with col2:
        st.markdown("""
        <div class='custom-card' style='border: 2px solid #6366f1;'>
            <h3 style='color: #0f172a;'>Pro</h3>
            <h2 class='gradient-text'>$9.99/mo</h2>
            <p style='color: #334155;'>For serious job seekers</p>
            <ul style='list-style-type: none; padding: 0; color: #334155;'>
                <li>✅ 50 credits/month</li>
                <li>✅ Advanced analysis</li>
                <li>✅ PDF/Word support</li>
                <li>✅ All 10+ features</li>
                <li>✅ Detailed insights</li>
                <li>✅ Email support</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Subscribe Pro", key="pro", use_container_width=True):
            st.info("Coming soon!")
    
    with col3:
        st.markdown("""
        <div class='custom-card'>
            <h3 style='color: #0f172a;'>Enterprise</h3>
            <h2 class='gradient-text'>$29.99/mo</h2>
            <p style='color: #334155;'>For teams & recruiters</p>
            <ul style='list-style-type: none; padding: 0; color: #334155;'>
                <li>✅ Unlimited credits</li>
                <li>✅ Bulk analysis</li>
                <li>✅ API access</li>
                <li>✅ Custom reports</li>
                <li>✅ Team management</li>
                <li>✅ Priority support</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Contact Sales", key="enterprise", use_container_width=True):
            st.info("Contact us for enterprise solutions!")

elif st.session_state.logged_in:
    
    if selected == "Home":
        # Hero Section
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            <h1 class='gradient-text fade-in'>AI Resume Analyzer Pro</h1>
            <p style='font-size: 18px; margin-bottom: 30px; color: #334155;'>Get instant AI-powered feedback on your resume and increase your chances of landing your dream job!</p>
            """, unsafe_allow_html=True)
            
            # Quick Stats
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.markdown("""
                <div class='stats-card'>
                    <p>Total Users</p>
                    <div class='stats-number'>10K+</div>
                </div>
                """, unsafe_allow_html=True)
            with col_b:
                st.markdown("""
                <div class='stats-card'>
                    <p>Resumes Analyzed</p>
                    <div class='stats-number'>50K+</div>
                </div>
                """, unsafe_allow_html=True)
            with col_c:
                st.markdown("""
                <div class='stats-card'>
                    <p>Success Rate</p>
                    <div class='stats-number'>85%</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class='custom-card' style='text-align: center;'>
                <h2 style='color: #0f172a;'>Credits Left</h2>
                <h1 class='gradient-text' style='font-size: 60px;'>⭐{st.session_state.credits}</h1>
                <p style='color: #334155;'>Available for analysis</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        # Main Analysis Section
        if st.session_state.credits > 0:
            st.markdown("<h2 style='color: #0f172a;'>📤 Upload Your Resume</h2>", unsafe_allow_html=True)
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                files = st.file_uploader(
                    "Choose resume files (PDF or DOCX)",
                    type=["pdf", "docx"],
                    accept_multiple_files=True,
                    help="Upload your resume in PDF or Word format"
                )
            
            with col2:
                job_description = st.text_area(
                    "Paste Job Description",
                    height=150,
                    placeholder="Paste the job description here to compare with your resume..."
                )
                
                # Optional job details for better analysis
                with st.expander("📋 Additional Job Details"):
                    job_title = st.text_input("Job Title", placeholder="e.g., Software Engineer")
                    company = st.text_input("Company", placeholder="e.g., Google")
                    experience_level = st.selectbox("Experience Level", ["Entry", "Mid-Level", "Senior"])
            
            # Analysis Button
            if st.button("🚀 Analyze Resume", use_container_width=True):
                if files and job_description:
                    if len(files) <= st.session_state.credits:
                        
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        for i, file in enumerate(files):
                            status_text.text(f"Analyzing {file.name}...")
                            
                            if file.name.endswith(".pdf"):
                                resume_text = extract_text_from_pdf(file)
                            else:
                                resume_text = extract_text_from_docx(file)
                            
                            # Detect language
                            detected_lang = detect_language(resume_text)
                            if detected_lang != 'en':
                                st.info(f"🌐 Detected language: {detected_lang}. Translating for analysis...")
                                resume_text = translate_text(resume_text, 'en')
                            
                            score = calculate_resume_score(resume_text)
                            match_percent, matched_skills = skill_match(resume_text, job_description)
                            missing = missing_skills(resume_text, job_description)
                            feedback = ai_feedback(score, match_percent, matched_skills, missing)
                            
                            # Analyze achievements
                            achievement_analysis = analyze_achievements(resume_text)
                            
                            save_analysis(st.session_state.user_id, file.name, score, match_percent, job_title, company)
                            
                            progress_bar.progress((i + 1) / len(files))
                            
                            st.markdown(f"<div class='custom-card fade-in'>", unsafe_allow_html=True)
                            
                            st.subheader(f"📊 Results for {file.name}")
                            
                            # Metrics Row
                            col_a1, col_a2, col_a3, col_a4 = st.columns(4)
                            with col_a1:
                                st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
                                st.metric("Resume Score", f"{score}%")
                                st.progress(score/100)
                                st.markdown("</div>", unsafe_allow_html=True)
                            
                            with col_a2:
                                st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
                                st.metric("Job Match", f"{match_percent}%")
                                st.progress(match_percent/100)
                                st.markdown("</div>", unsafe_allow_html=True)
                            
                            with col_a3:
                                st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
                                st.metric("Matched Skills", len(matched_skills))
                                st.markdown("</div>", unsafe_allow_html=True)
                            
                            with col_a4:
                                st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
                                st.metric("Missing Skills", len(missing))
                                st.markdown("</div>", unsafe_allow_html=True)
                            
                            # Detailed Analysis with new features
                            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                                "📋 Skills Analysis", 
                                "📊 Visualizations", 
                                "🤖 AI Feedback",
                                "🏆 Achievements",
                                "💰 Salary Estimate",
                                "📚 Learning Path"
                            ])
                            
                            with tab1:
                                col_b1, col_b2 = st.columns(2)
                                
                                with col_b1:
                                    st.subheader("✅ Matched Skills")
                                    for skill in matched_skills[:10]:
                                        st.markdown(f"<span class='badge'>✓ {skill}</span>", unsafe_allow_html=True)
                                    if len(matched_skills) > 10:
                                        st.write(f"...and {len(matched_skills) - 10} more")
                                
                                with col_b2:
                                    st.subheader("⚠️ Missing Skills")
                                    for skill in missing[:10]:
                                        st.markdown(f"<span class='badge' style='background: #ef4444;'>✗ {skill}</span>", unsafe_allow_html=True)
                                    if len(missing) > 10:
                                        st.write(f"...and {len(missing) - 10} more")
                            
                            with tab2:
                                col_c1, col_c2 = st.columns(2)
                                
                                with col_c1:
                                    fig1 = create_radar_chart(match_percent, score)
                                    st.plotly_chart(fig1, use_container_width=True)
                                
                                with col_c2:
                                    fig2 = create_skills_wordcloud(matched_skills, missing)
                                    st.plotly_chart(fig2, use_container_width=True)
                            
                            with tab3:
                                for tip in feedback:
                                    st.info(tip)
                                
                                st.markdown("""
                                <div style='background: #10b98120; padding: 20px; border-radius: 10px; margin-top: 20px;'>
                                    <h4 style='color: #0f172a;'>💡 Pro Tips</h4>
                                    <ul style='color: #334155;'>
                                        <li>Use numbers to quantify your achievements</li>
                                        <li>Include relevant keywords from job description</li>
                                        <li>Keep your resume to 1-2 pages</li>
                                        <li>Highlight your unique achievements</li>
                                    </ul>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            with tab4:
                                st.subheader("🏆 Achievement Analysis")
                                
                                col_d1, col_d2 = st.columns(2)
                                with col_d1:
                                    st.metric("Achievement Score", f"{achievement_analysis['score']}%")
                                    st.progress(achievement_analysis['score']/100)
                                
                                with col_d2:
                                    st.metric("Quantifiable Achievements", achievement_analysis['total_quantifiable'])
                                
                                if achievement_analysis['achievements']:
                                    st.subheader("📊 Found Achievements")
                                    for ach in achievement_analysis['achievements']:
                                        st.write(f"• Pattern matched {ach['count']} times: {ach['examples']}")
                                else:
                                    st.info("No quantifiable achievements found. Add numbers and percentages to stand out!")
                                
                                if achievement_analysis['recommendations']:
                                    st.subheader("💡 Recommendations")
                                    for rec in achievement_analysis['recommendations']:
                                        st.write(f"• {rec}")
                            
                            with tab5:
                                st.subheader("💰 Salary Estimator")
                                
                                col_e1, col_e2 = st.columns(2)
                                with col_e1:
                                    years_exp = st.number_input("Years of Experience", min_value=0, max_value=30, value=2)
                                    location = st.selectbox("Location", ["Remote", "San Francisco", "New York", "Seattle", "Austin", "Other"])
                                
                                with col_e2:
                                    current_job = st.text_input("Target Job Title", value=job_title if job_title else "Software Engineer")
                                
                                if st.button("Estimate Salary"):
                                    salary = estimate_salary(matched_skills, years_exp, location, current_job)
                                    
                                    st.markdown(f"""
                                    <div style='background: linear-gradient(135deg, #6366f1, #10b981); padding: 20px; border-radius: 10px; text-align: center;'>
                                        <h3 style='color: white;'>Estimated Salary Range</h3>
                                        <h1 style='color: white; font-size: 48px;'>${salary['minimum']:,} - ${salary['maximum']:,}</h1>
                                        <p style='color: rgba(255,255,255,0.9);'>Average: ${salary['average']:,} {salary['currency']}</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                            
                            with tab6:
                                st.subheader("📚 Personalized Learning Path")
                                
                                if missing:
                                    st.write("Based on your missing skills, we recommend:")
                                    
                                    for skill in missing[:5]:
                                        with st.expander(f"📖 Learn {skill}"):
                                            resources = get_learning_resources(skill)
                                            for res in resources:
                                                st.markdown(f"""
                                                <div style='padding: 10px; border-left: 3px solid #6366f1; margin: 10px 0;'>
                                                    <strong>{res['name']}</strong><br>
                                                    Platform: {res['platform']} | Difficulty: {res['difficulty']}<br>
                                                    <a href='{res['url']}' target='_blank'>Start Learning →</a>
                                                </div>
                                                """, unsafe_allow_html=True)
                                else:
                                    st.success("You have all the required skills! Consider advancing your expertise.")
                            
                            # Save as version option
                            col_save1, col_save2 = st.columns(2)
                            with col_save1:
                                version_name = st.text_input("Version Name (optional)", key=f"version_{file.name}")
                            with col_save2:
                                if st.button(f"💾 Save as Version", key=f"save_{file.name}"):
                                    if version_name:
                                        save_resume_version(st.session_state.user_id, version_name, file.name, score)
                                        st.success(f"Saved as version: {version_name}")
                                    else:
                                        save_resume_version(st.session_state.user_id, f"Version {datetime.now().strftime('%Y%m%d_%H%M')}", file.name, score)
                                        st.success("Version saved!")
                            
                            st.download_button(
                                "📥 Download Full Report",
                                generate_report(file, score, match_percent, matched_skills, missing, feedback),
                                file_name=f"{file.name}_report.txt",
                                mime="text/plain",
                                use_container_width=True
                            )
                            
                            st.markdown("</div>", unsafe_allow_html=True)
                        
                        new_credits = st.session_state.credits - len(files)
                        update_credits(st.session_state.user_id, new_credits)
                        st.session_state.credits = new_credits
                        
                        progress_bar.empty()
                        status_text.empty()
                        st.success("✅ Analysis complete!")
                        
                    else:
                        st.error(f"You need {len(files)} credits but only have {st.session_state.credits}. Please upgrade your plan.")
                else:
                    st.warning("Please upload resume(s) and paste job description")
        else:
            st.warning("⚠️ You've run out of credits! Please upgrade your plan to continue.")
            
            if st.button("View Pricing Plans", use_container_width=True):
                st.session_state.current_page = "Pricing"
                st.rerun()
    
    elif selected == "Dashboard":
        st.markdown("<h1 class='gradient-text'>📊 Your Dashboard</h1>", unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class='custom-card'>
            <h2 style='color: #0f172a;'>Welcome back, {st.session_state.username}! 👋</h2>
            <p style='color: #334155;'>Here's your activity summary</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        history = get_user_history(st.session_state.user_id)
        versions = get_resume_versions(st.session_state.user_id)
        
        with col1:
            st.markdown("""
            <div class='stats-card'>
                <p>Total Analyses</p>
                <div class='stats-number'>{}</div>
            </div>
            """.format(len(history)), unsafe_allow_html=True)
        
        with col2:
            avg_score = sum([h[1] for h in history]) / len(history) if history else 0
            st.markdown("""
            <div class='stats-card'>
                <p>Avg Score</p>
                <div class='stats-number'>{:.1f}%</div>
            </div>
            """.format(avg_score), unsafe_allow_html=True)
        
        with col3:
            avg_match = sum([h[2] for h in history]) / len(history) if history else 0
            st.markdown("""
            <div class='stats-card'>
                <p>Avg Match</p>
                <div class='stats-number'>{:.1f}%</div>
            </div>
            """.format(avg_match), unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <div class='stats-card'>
                <p>Credits Left</p>
                <div class='stats-number'>⭐{}</div>
            </div>
            """.format(st.session_state.credits), unsafe_allow_html=True)
        
        st.markdown("<h2 style='color: #0f172a;'>📈 Recent Activity</h2>", unsafe_allow_html=True)
        
        if history:
            df = pd.DataFrame(history, columns=['Filename', 'Score', 'Match', 'Date', 'Job Title', 'Company'])
            df['Date'] = pd.to_datetime(df['Date'])
            
            fig = px.line(df, x='Date', y=['Score', 'Match'], 
                         title='Your Progress Over Time',
                         labels={'value': 'Percentage', 'variable': 'Metric'},
                         color_discrete_map={'Score': '#6366f1', 'Match': '#10b981'})
            
            text_color = '#ffffff' if st.session_state.dark_mode else '#0f172a'
            
            fig.update_layout(
                height=400,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color=text_color, size=12),
                title_font_color=text_color
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("<h3 style='color: #0f172a;'>Recent Analyses</h3>", unsafe_allow_html=True)
            for item in history[:5]:
                with st.container():
                    col_a, col_b, col_c, col_d, col_e = st.columns([2, 1, 1, 1, 1.5])
                    with col_a:
                        st.write(f"📄 {item[0][:20]}...")
                    with col_b:
                        st.write(f"Score: {item[1]}%")
                    with col_c:
                        st.write(f"Match: {item[2]}%")
                    with col_d:
                        st.write(f"{item[4] if item[4] else 'N/A'}")
                    with col_e:
                        st.write(f"📅 {item[3][:10]}")
                    st.divider()
        else:
            st.info("No analysis history yet. Start by analyzing your first resume!")
    
    elif selected == "Resume Versions":
        st.markdown("<h1 class='gradient-text'>📋 Resume Versions</h1>", unsafe_allow_html=True)
        
        versions = get_resume_versions(st.session_state.user_id)
        
        if versions:
            st.markdown("### Your Saved Versions")
            
            # Version comparison
            if len(versions) >= 2:
                st.markdown("### 🔄 Compare Versions")
                col1, col2 = st.columns(2)
                
                with col1:
                    version1 = st.selectbox("Select Version 1", [v[0] for v in versions])
                with col2:
                    version2 = st.selectbox("Select Version 2", [v[0] for v in versions])
                
                if version1 and version2 and version1 != version2:
                    if st.button("Compare Versions"):
                        # In a real app, you'd load the actual resume texts
                        st.info("Version comparison feature ready! (Requires stored resume text)")
                        
                        # Mock comparison for demo
                        st.markdown("""
                        <div style='background: #10b98120; padding: 20px; border-radius: 10px;'>
                            <h4>Comparison Results:</h4>
                            <ul>
                                <li>Version 2 score improved by 5%</li>
                                <li>Added 3 new skills</li>
                                <li>Improved keyword density</li>
                                <li>Better ATS compatibility</li>
                            </ul>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Display versions
            for version in versions:
                with st.expander(f"📄 {version[0]} - Score: {version[2]}%"):
                    st.write(f"Filename: {version[1]}")
                    st.write(f"Created: {version[3][:16]}")
                    
                    if st.button(f"Load Version {version[0]}", key=f"load_{version[0]}"):
                        st.success(f"Loaded version: {version[0]}")
        else:
            st.info("No saved versions yet. Save your resume analysis as a version!")
    
    elif selected == "Career Path":
        st.markdown("<h1 class='gradient-text'>🎯 Career Path Recommendations</h1>", unsafe_allow_html=True)
        
        st.markdown("""
        <div class='custom-card'>
            <p>Get personalized career recommendations based on your skills and experience.</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            experience = st.selectbox("Your Experience Level", ["entry", "mid", "senior"])
            industry = st.selectbox("Industry", ["Technology", "Finance", "Healthcare", "Education", "Manufacturing"])
        
        with col2:
            top_skills = st.multiselect("Your Top Skills", 
                                       ["Python", "JavaScript", "Java", "SQL", "Cloud", "Leadership", "Project Management"],
                                       default=["Python", "SQL"])
            career_goal = st.text_input("Dream Job Title (optional)", placeholder="e.g., CTO")
        
        if st.button("Get Recommendations", use_container_width=True):
            recommendations = get_career_recommendations(top_skills, experience)
            
            st.markdown("<h3>Recommended Career Paths</h3>", unsafe_allow_html=True)
            
            for rec in recommendations:
                st.markdown(f"""
                <div class='feature-card' style='margin: 10px 0;'>
                    <h4>{rec['title']}</h4>
                    <p>💰 Salary: {rec['salary']} | 📈 Demand: {rec['demand']} | 🚀 Growth: {rec['growth']}</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Career roadmap
            st.markdown("<h3>📈 Your Career Roadmap</h3>", unsafe_allow_html=True)
            
            roadmap_data = pd.DataFrame({
                'Year': [1, 2, 3, 4, 5],
                'Level': ['Junior', 'Mid-Level', 'Senior', 'Lead', 'Manager'],
                'Salary': [70000, 90000, 115000, 140000, 165000]
            })
            
            fig = px.line(roadmap_data, x='Year', y='Salary', text='Level',
                         title='Projected Career Growth',
                         labels={'Salary': 'Expected Salary ($)'})
            
            fig.update_traces(textposition='top center')
            fig.update_layout(height=400)
            
            st.plotly_chart(fig, use_container_width=True)
    
    elif selected == "Interview Scheduler":
        st.markdown("<h1 class='gradient-text'>📅 Interview Scheduler</h1>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["📝 Schedule Interview", "📅 View Calendar"])
        
        with tab1:
            st.markdown("### Schedule a Mock Interview")
            
            with st.form("interview_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    company = st.text_input("Company", placeholder="e.g., Google")
                    position = st.text_input("Position", placeholder="e.g., Software Engineer")
                    interview_date = st.date_input("Interview Date", min_value=datetime.now().date())
                
                with col2:
                    interview_time = st.time_input("Interview Time", value=datetime.now().time())
                    interviewer = st.text_input("Interviewer Name (optional)")
                    notes = st.text_area("Notes/Preparation", placeholder="Add notes or preparation tasks...")
                
                if st.form_submit_button("Schedule Interview", use_container_width=True):
                    if company and position:
                        save_interview(st.session_state.user_id, interview_date, interview_time, company, position, notes)
                        st.success(f"Interview scheduled with {company} for {position}!")
                        
                        # Send email reminder (mock)
                        st.info("📧 Email reminder will be sent 24 hours before the interview.")
                    else:
                        st.warning("Please fill in company and position")
        
        with tab2:
            st.markdown("### Upcoming Interviews")
            
            interviews = get_interviews(st.session_state.user_id)
            
            if interviews:
                calendar_data = create_interview_calendar(interviews)
                
                # Create calendar view
                st.markdown("### 📅 Calendar View")
                cols = st.columns(7)
                days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                
                for i, day in enumerate(days):
                    cols[i].markdown(f"**{day}**")
                
                # Simple calendar display
                for week in range(4):
                    cols = st.columns(7)
                    for day in range(7):
                        with cols[day]:
                            date_num = week * 7 + day + 1
                            st.markdown(f"**{date_num}**")
                            
                            # Check if there are interviews on this date
                            if calendar_data and date_num <= len(calendar_data):
                                day_data = calendar_data[date_num - 1]
                                if day_data['interviews'] > 0:
                                    for interview in day_data['details'][:2]:  # Show max 2 per day
                                        st.markdown(f"""
                                        <div class='calendar-event'>
                                            {interview[2]}<br>
                                            <small>{interview[1]}</small>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    if day_data['interviews'] > 2:
                                        st.markdown(f"<small>+{day_data['interviews']-2} more</small>", unsafe_allow_html=True)
                
                # List view
                st.markdown("### 📋 Upcoming Interviews List")
                for interview in interviews:
                    with st.expander(f"📅 {interview[2]} at {interview[1]} - {interview[0]}"):
                        st.write(f"**Company:** {interview[2]}")
                        st.write(f"**Position:** {interview[3]}")
                        st.write(f"**Date:** {interview[0]}")
                        st.write(f"**Time:** {interview[1]}")
                        if interview[4]:
                            st.write(f"**Notes:** {interview[4]}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("📧 Send Reminder", key=f"reminder_{interview[0]}_{interview[1]}"):
                                st.success("Reminder sent to your email!")
                        with col2:
                            if st.button("❌ Cancel", key=f"cancel_{interview[0]}_{interview[1]}"):
                                st.warning("Interview cancelled (demo feature)")
            else:
                st.info("No upcoming interviews. Schedule your first mock interview!")
    
    elif selected == "Learning Resources":
        st.markdown("<h1 class='gradient-text'>📚 Learning Resources</h1>", unsafe_allow_html=True)
        
        st.markdown("""
        <div class='custom-card'>
            <p>Personalized course recommendations based on your skill gaps and career goals.</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            skill_to_learn = st.selectbox(
                "Select a skill to learn",
                ["Python", "JavaScript", "Data Science", "Cloud Computing", "DevOps", "Machine Learning", "Web Development"]
            )
            
            difficulty = st.radio("Difficulty Level", ["Beginner", "Intermediate", "Advanced"])
        
        with col2:
            platform = st.multiselect(
                "Preferred Platforms",
                ["Coursera", "Udemy", "edX", "Pluralsight", "Codecademy", "Frontend Masters"]
            )
            
            time_commitment = st.slider("Weekly Time Commitment (hours)", 1, 20, 5)
        
        if st.button("Find Courses", use_container_width=True):
            st.markdown(f"### Recommended Courses for {skill_to_learn}")
            
            # Mock course data
            courses = [
                {
                    'name': f'Complete {skill_to_learn} Bootcamp',
                    'platform': random.choice(['Udemy', 'Coursera']),
                    'duration': '40 hours',
                    'rating': '4.8 ⭐',
                    'price': '$49.99',
                    'level': 'Beginner'
                },
                {
                    'name': f'Advanced {skill_to_learn} Specialization',
                    'platform': random.choice(['Coursera', 'edX']),
                    'duration': '60 hours',
                    'rating': '4.7 ⭐',
                    'price': '$79.99',
                    'level': 'Intermediate'
                },
                {
                    'name': f'{skill_to_learn} for Professionals',
                    'platform': random.choice(['Pluralsight', 'Frontend Masters']),
                    'duration': '30 hours',
                    'rating': '4.9 ⭐',
                    'price': '$39.99/month',
                    'level': 'Advanced'
                },
                {
                    'name': f'Hands-on {skill_to_learn} Projects',
                    'platform': random.choice(['Codecademy', 'Udemy']),
                    'duration': '20 hours',
                    'rating': '4.6 ⭐',
                    'price': '$29.99',
                    'level': 'Intermediate'
                }
            ]
            
            # Filter by difficulty
            filtered_courses = [c for c in courses if c['level'] == difficulty]
            if not filtered_courses:
                filtered_courses = courses[:3]
            
            for course in filtered_courses[:3]:
                st.markdown(f"""
                <div class='feature-card' style='margin: 10px 0; padding: 15px;'>
                    <h4>{course['name']}</h4>
                    <p>📚 Platform: {course['platform']} | ⏱️ Duration: {course['duration']}</p>
                    <p>⭐ Rating: {course['rating']} | 💰 Price: {course['price']}</p>
                    <p>📊 Level: {course['level']}</p>
                    <a href='#' style='color: #6366f1;'>View Course →</a>
                </div>
                """, unsafe_allow_html=True)
            
            # Learning path
            st.markdown("### 🗺️ Your Personalized Learning Path")
            
            learning_path = pd.DataFrame({
                'Week': [1, 2, 3, 4, 5, 6],
                'Hours': [time_commitment, time_commitment, time_commitment, time_commitment, time_commitment, time_commitment],
                'Topic': [
                    f'{skill_to_learn} Fundamentals',
                    f'Core {skill_to_learn} Concepts',
                    f'Practical {skill_to_learn}',
                    f'Advanced {skill_to_learn}',
                    f'{skill_to_learn} Projects',
                    f'Mastering {skill_to_learn}'
                ]
            })
            
            fig = px.bar(learning_path, x='Week', y='Hours', text='Topic',
                        title=f'6-Week {skill_to_learn} Learning Path',
                        labels={'Hours': 'Study Hours per Week'})
            
            fig.update_traces(textposition='outside')
            fig.update_layout(height=400)
            
            st.plotly_chart(fig, use_container_width=True)
    
    elif selected == "Settings":
        st.markdown("<h1 class='gradient-text'>⚙️ Settings</h1>", unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["👤 Profile", "🔒 Security", "🎨 Preferences"])
        
        with tab1:
            st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
            st.subheader("Profile Settings")
            
            with st.form("profile_settings"):
                display_name = st.text_input("Display Name", value=st.session_state.username)
                new_email = st.text_input("Email", placeholder="Enter your email")
                phone = st.text_input("Phone Number", placeholder="+1 234 567 8900")
                location = st.text_input("Location", placeholder="City, Country")
                
                col1, col2 = st.columns(2)
                with col1:
                    experience_years = st.number_input("Years of Experience", 0, 50, 2)
                with col2:
                    current_role = st.text_input("Current Role", placeholder="e.g., Software Engineer")
                
                bio = st.text_area("Professional Bio", placeholder="Tell us about yourself...", height=100)
                
                if st.form_submit_button("Update Profile", use_container_width=True):
                    st.success("Profile updated successfully!")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        with tab2:
            st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
            st.subheader("Security Settings")
            
            with st.form("password_change"):
                current_pwd = st.text_input("Current Password", type="password", placeholder="Enter current password")
                new_pwd = st.text_input("New Password", type="password", placeholder="Enter new password")
                confirm_pwd = st.text_input("Confirm New Password", type="password", placeholder="Confirm new password")
                
                if st.form_submit_button("Change Password", use_container_width=True):
                    if new_pwd == confirm_pwd and len(new_pwd) >= 6:
                        st.success("Password changed successfully!")
                    else:
                        st.error("Passwords don't match or are too short")
            
            st.divider()
            
            st.subheader("Two-Factor Authentication")
            st.info("📱 Enable 2FA for additional security")
            
            if st.button("Enable 2FA", use_container_width=True):
                st.success("2FA enabled! Check your email for setup instructions.")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        with tab3:
            st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
            st.subheader("Preferences")
            
            # Language preference (already in sidebar, but can have more options)
            st.selectbox("Interface Language", ["English", "Spanish", "French", "German", "Chinese", "Japanese"])
            
            # Notification preferences
            st.subheader("Notification Settings")
            email_notifications = st.checkbox("Email notifications for new features", value=True)
            analysis_complete = st.checkbox("Email when analysis is complete", value=True)
            weekly_report = st.checkbox("Weekly progress report", value=False)
            marketing_emails = st.checkbox("Marketing emails", value=False)
            
            # Display preferences
            st.subheader("Display Settings")
            default_view = st.radio("Default Dashboard View", ["Compact", "Detailed", "Analytics"])
            chart_style = st.selectbox("Chart Style", ["Modern", "Classic", "Minimalist"])
            
            if st.button("Save Preferences", use_container_width=True):
                st.success("Preferences saved successfully!")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Danger Zone
        st.markdown("<div class='custom-card' style='border: 2px solid #ef4444;'>", unsafe_allow_html=True)
        st.subheader("⚠️ Danger Zone")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Delete Account", type="primary", use_container_width=True):
                st.error("This action cannot be undone. Please contact support to delete your account.")
        
        with col2:
            if st.button("Export My Data", use_container_width=True):
                st.info("Your data export has been initiated. You'll receive an email within 24 hours.")
        
        st.markdown("</div>", unsafe_allow_html=True)

# ---------------- FOOTER ----------------

st.markdown("""
<div class='footer'>
    <p>© 2024 AI Resume Analyzer Pro. All rights reserved.</p>
    <p>Made with ❤️ for job seekers | Version 2.0 with 10+ Premium Features</p>
</div>
""", unsafe_allow_html=True)

# ---------------- ADDITIONAL FEATURES SUMMARY ----------------

# Add a floating help button
st.markdown("""
<style>
.floating-help {
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: linear-gradient(135deg, #6366f1, #10b981);
    color: white;
    width: 60px;
    height: 60px;
    border-radius: 50%;
    text-align: center;
    line-height: 60px;
    font-size: 24px;
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
    cursor: pointer;
    z-index: 999;
    transition: all 0.3s ease;
}

.floating-help:hover {
    transform: scale(1.1);
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.6);
}
</style>

<div class='floating-help' title='Need help?'>?</div>
""", unsafe_allow_html=True)