# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import hashlib
import json
import sqlite3
import os
import base64
import time
from pathlib import Path
import re
import io

# Import all feature modules (with error handling)
from database import DatabaseManager
from resume_parser import ResumeParser
from ats_checker import ATSChecker
from job_matcher import JobMatcher
from interview_generator import InterviewGenerator
from coding_practice import CodingPractice

# Try to import voice module, but continue if it fails
try:
    from voice_interview import VoiceInterviewer
    VOICE_AVAILABLE = True
    print("✅ Voice features enabled")
except ImportError as e:
    VOICE_AVAILABLE = False
    print(f"⚠️ Voice features disabled: {e}")
    print("   To enable voice, run: pip install sounddevice")
    # Create a dummy class as fallback
    class VoiceInterviewer:
        def __init__(self):
            pass
        def record_and_transcribe(self, *args, **kwargs):
            return "Voice features not installed", 0
        def analyze_speech(self, *args, **kwargs):
            return {'confidence': 0, 'clarity': 0, 'pace': 'N/A', 'filler_words': [], 'word_count': 0}
        def speak(self, text):
            print(f"AI would say: {text}")

# Page configuration
st.set_page_config(
    page_title="DossierAI Pro | Ultimate Career Assistant",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize all managers
db = DatabaseManager()
parser = ResumeParser()
ats_checker = ATSChecker()
job_matcher = JobMatcher()
interview_gen = InterviewGenerator()
coding_practice = CodingPractice()
voice_interviewer = VoiceInterviewer() if VOICE_AVAILABLE else VoiceInterviewer()

# Session state initialization
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'resume_data' not in st.session_state:
    st.session_state.resume_data = None
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = True
if 'page' not in st.session_state:
    st.session_state.page = "Home"
if 'comparison_results' not in st.session_state:
    st.session_state.comparison_results = None
if 'interview_history' not in st.session_state:
    st.session_state.interview_history = []

# Custom CSS for stunning UI
def load_css():
    if st.session_state.dark_mode:
        bg_color = "#0a0a0a"
        card_bg = "#1a1a1a"
        text_color = "#ffffff"
        secondary_text = "#b0b0b0"
        accent = "#00ff88"
        border = "1px solid #333"
    else:
        bg_color = "#f5f5f5"
        card_bg = "#ffffff"
        text_color = "#000000"
        secondary_text = "#666666"
        accent = "#0066cc"
        border = "1px solid #ddd"
    
    st.markdown(f"""
    <style>
        /* Global Styles */
        .stApp {{
            background-color: {bg_color};
            color: {text_color};
            font-family: 'Inter', sans-serif;
        }}
        
        /* Cards */
        .feature-card {{
            background-color: {card_bg};
            padding: 1.8rem;
            border-radius: 15px;
            margin: 1rem 0;
            border: {border};
            box-shadow: 0 8px 20px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }}
        .feature-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 12px 30px rgba(0,255,136,0.2);
            border-color: {accent};
        }}
        
        /* Skill Badges */
        .skill-badge {{
            background: linear-gradient(135deg, {accent}, #00a8ff);
            color: white;
            padding: 0.4rem 1.2rem;
            border-radius: 25px;
            margin: 0.3rem;
            display: inline-block;
            font-size: 0.9rem;
            font-weight: 500;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }}
        
        /* Score Indicators */
        .score-high {{
            color: #00ff88;
            font-weight: bold;
            font-size: 1.2rem;
        }}
        .score-medium {{
            color: #ffaa00;
            font-weight: bold;
            font-size: 1.2rem;
        }}
        .score-low {{
            color: #ff4444;
            font-weight: bold;
            font-size: 1.2rem;
        }}
        
        /* Progress Bars */
        .progress-container {{
            background-color: {card_bg};
            border-radius: 10px;
            height: 10px;
            margin: 0.5rem 0;
        }}
        .progress-fill {{
            background: linear-gradient(90deg, {accent}, #00a8ff);
            height: 10px;
            border-radius: 10px;
            transition: width 0.5s ease;
        }}
        
        /* Buttons */
        .stButton > button {{
            background: linear-gradient(135deg, {accent}, #00a8ff);
            color: white;
            border: none;
            padding: 0.6rem 1.5rem;
            border-radius: 25px;
            font-weight: 600;
            transition: all 0.3s ease;
            width: 100%;
        }}
        .stButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,255,136,0.4);
        }}
        
        /* Metrics */
        .metric-card {{
            background: linear-gradient(135deg, {card_bg}, {bg_color});
            padding: 1.5rem;
            border-radius: 12px;
            border-left: 4px solid {accent};
            text-align: center;
        }}
        .metric-value {{
            font-size: 2.5rem;
            font-weight: bold;
            color: {accent};
        }}
        .metric-label {{
            color: {secondary_text};
            font-size: 0.9rem;
        }}
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 2rem;
            background-color: {card_bg};
            padding: 0.5rem;
            border-radius: 10px;
        }}
        .stTabs [data-baseweb="tab"] {{
            color: {text_color};
            font-weight: 500;
        }}
        .stTabs [aria-selected="true"] {{
            color: {accent} !important;
            border-bottom: 2px solid {accent};
        }}
        
        /* Headers */
        h1, h2, h3 {{
            color: {text_color} !important;
            font-weight: 600 !important;
        }}
        h1 {{
            background: linear-gradient(135deg, {accent}, #00a8ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 3rem !important;
        }}
        
        /* Animations */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .fade-in {{
            animation: fadeIn 0.8s ease;
        }}
        
        /* Footer */
        .footer {{
            text-align: center;
            padding: 2rem;
            color: {secondary_text};
            border-top: {border};
            margin-top: 3rem;
        }}
    </style>
    """, unsafe_allow_html=True)

load_css()

# Authentication Functions
def login_signup():
    st.markdown("<h1 style='text-align: center;'>🚀 Welcome to DossierAI Pro</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2rem;'>Your Ultimate AI-Powered Career Assistant</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                
                if st.form_submit_button("Login", use_container_width=True):
                    if username and password:
                        user = db.verify_user(username, password)
                        if user:
                            st.session_state.authenticated = True
                            st.session_state.user_id = user['id']
                            st.session_state.username = user['username']
                            st.success("Login successful!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Invalid username or password!")
                    else:
                        st.warning("Please fill in all fields!")
        
        with tab2:
            with st.form("signup_form"):
                new_username = st.text_input("Username", placeholder="Choose a username")
                new_email = st.text_input("Email", placeholder="Enter your email")
                new_password = st.text_input("Password", type="password", placeholder="Choose a password")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
                
                if st.form_submit_button("Sign Up", use_container_width=True):
                    if new_username and new_email and new_password and confirm_password:
                        if new_password != confirm_password:
                            st.error("Passwords don't match!")
                        elif len(new_password) < 6:
                            st.warning("Password must be at least 6 characters!")
                        else:
                            if db.create_user(new_username, new_email, new_password):
                                st.success("Account created successfully! Please login.")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Username or email already exists!")
                    else:
                        st.warning("Please fill in all fields!")

# Main App Navigation
def main_app():
    # Sidebar
    with st.sidebar:
        st.markdown(f"""
        <div style='text-align: center; padding: 1rem; background: {card_bg}; border-radius: 10px; margin-bottom: 1rem;'>
            <h3>👋 Welcome, {st.session_state.username}!</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Navigation Menu
        menu_options = {
            "🏠 Home": "Home",
            "📄 Resume Analysis": "Resume Analysis",
            "🎯 Job Matcher": "Job Matcher",
            "💼 Mock Interview": "Mock Interview",
            "📚 Coding Practice": "Coding Practice",
            "📊 Performance Dashboard": "Dashboard",
            "⚙️ Settings": "Settings"
        }
        
        for label, page in menu_options.items():
            if st.button(label, use_container_width=True):
                st.session_state.page = page
                st.rerun()
        
        # Quick Stats
        st.markdown("---")
        stats = db.get_user_stats(st.session_state.user_id)
        if stats:
            st.markdown("### 📊 Your Stats")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Resumes", stats['total_analyses'])
            with col2:
                st.metric("Avg Score", f"{stats['avg_score']}%")
        
        # Theme Toggle
        st.markdown("---")
        if st.button("🌓 Toggle " + ("Light" if st.session_state.dark_mode else "Dark") + " Mode", use_container_width=True):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()
        
        # Logout
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()
    
    # Main Content based on selected page
    if st.session_state.page == "Home":
        show_home()
    elif st.session_state.page == "Resume Analysis":
        show_resume_analysis()
    elif st.session_state.page == "Job Matcher":
        show_job_matcher()
    elif st.session_state.page == "Mock Interview":
        show_mock_interview()
    elif st.session_state.page == "Coding Practice":
        show_coding_practice()
    elif st.session_state.page == "Dashboard":
        show_dashboard()
    elif st.session_state.page == "Settings":
        show_settings()

# Home Page
def show_home():
    st.markdown("<h1 class='fade-in'>🚀 Welcome to DossierAI Pro</h1>", unsafe_allow_html=True)
    st.markdown("<p class='fade-in' style='font-size: 1.2rem;'>Your Complete AI-Powered Career Assistant</p>", unsafe_allow_html=True)
    
    # Stats Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
        <div class='metric-card'>
            <div class='metric-value'>10K+</div>
            <div class='metric-label'>Resumes Analyzed</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class='metric-card'>
            <div class='metric-value'>95%</div>
            <div class='metric-label'>Success Rate</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class='metric-card'>
            <div class='metric-value'>500+</div>
            <div class='metric-label'>Companies</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown("""
        <div class='metric-card'>
            <div class='metric-value'>24/7</div>
            <div class='metric-label'>AI Support</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Features Grid
    st.markdown("## ✨ Powerful Features")
    
    features = [
        ("📄 Smart Resume Parsing", "Extract name, email, skills, education, experience automatically"),
        ("🎯 ATS Compatibility", "Check if your resume passes ATS systems with detailed analysis"),
        ("💼 Job Matching", "Find perfect jobs and identify skill gaps"),
        ("🤖 AI Mock Interview", "HR and Technical interviews with voice support"),
        ("📚 Coding Practice", "Personalized coding questions based on job requirements"),
        ("📊 Multi-Resume Comparison", "Compare multiple resumes side by side"),
        ("🏆 Leaderboard", "Compete with other users and track progress"),
        ("🎤 Voice Interview", "Practice interviews with voice recognition"),
        ("📈 Performance Dashboard", "Track your improvement over time")
    ]
    
    for i in range(0, len(features), 3):
        cols = st.columns(3)
        for j, col in enumerate(cols):
            if i + j < len(features):
                with col:
                    st.markdown(f"""
                    <div class='feature-card'>
                        <h3>{features[i+j][0]}</h3>
                        <p>{features[i+j][1]}</p>
                    </div>
                    """, unsafe_allow_html=True)

# Resume Analysis Page
def show_resume_analysis():
    st.markdown("<h1>📄 Smart Resume Analysis</h1>", unsafe_allow_html=True)
    
    # File Upload Section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Upload Resume (PDF/DOCX/TXT)",
            type=['pdf', 'docx', 'txt'],
            accept_multiple_files=False,
            help="Drag and drop or click to upload"
        )
    
    with col2:
        st.markdown("### 📊 Quick Tips")
        st.info("""
        • Use clear formatting
        • Include keywords from job description
        • Quantify achievements with numbers
        • Keep it to 1-2 pages
        • Save as PDF for best results
        """)
    
    if uploaded_file:
        with st.spinner("🔍 Analyzing resume... This may take a few seconds..."):
            # Extract data
            resume_data = parser.extract_all(uploaded_file)
            st.session_state.resume_data = resume_data
            
            # ATS check
            ats_result = ats_checker.analyze(resume_data)
            
            # Save to database
            db.save_analysis(st.session_state.user_id, uploaded_file.name, 
                           ats_result['score'], resume_data)
            
            # Display results in tabs
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "📋 Extracted Info", "🎯 ATS Analysis", 
                "💡 Suggestions", "📊 Visual Report", "🔄 Compare"
            ])
            
            with tab1:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 👤 Personal Information")
                    st.write(f"**Name:** {resume_data.get('name', 'Not found')}")
                    st.write(f"**Email:** {resume_data.get('email', 'Not found')}")
                    st.write(f"**Phone:** {resume_data.get('phone', 'Not found')}")
                    
                    st.markdown("### 🎓 Education")
                    for edu in resume_data.get('education', []):
                        st.write(f"• {edu}")
                
                with col2:
                    st.markdown("### 💪 Skills")
                    skills = resume_data.get('skills', [])
                    for skill in skills:
                        st.markdown(f"<span class='skill-badge'>{skill}</span>", 
                                  unsafe_allow_html=True)
                    
                    st.markdown("### 💼 Work Experience")
                    for exp in resume_data.get('experience', [])[:3]:
                        st.write(f"• {exp}")
                    
                    st.markdown("### 🚀 Projects")
                    for proj in resume_data.get('projects', [])[:3]:
                        st.write(f"• {proj}")
            
            with tab2:
                st.markdown(f"### 📈 ATS Compatibility Score")
                
                # Score with color
                score = ats_result['score']
                if score >= 80:
                    st.markdown(f"<h2 class='score-high'>{score}% - Excellent!</h2>", unsafe_allow_html=True)
                elif score >= 60:
                    st.markdown(f"<h2 class='score-medium'>{score}% - Good</h2>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<h2 class='score-low'>{score}% - Needs Improvement</h2>", unsafe_allow_html=True)
                
                # Progress bar
                st.markdown(f"""
                <div class='progress-container'>
                    <div class='progress-fill' style='width: {score}%;'></div>
                </div>
                """, unsafe_allow_html=True)
                
                # Detailed metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Keywords Found", ats_result['keywords_found'])
                with col2:
                    st.metric("Formatting Score", f"{ats_result['formatting_score']}%")
                with col3:
                    st.metric("Section Completeness", f"{ats_result['sections_score']}%")
                
                # Issues
                if ats_result['issues']:
                    st.markdown("### ⚠️ Issues Found")
                    for issue in ats_result['issues']:
                        if issue['severity'] == 'high':
                            st.error(f"🔴 {issue['message']}")
                        elif issue['severity'] == 'medium':
                            st.warning(f"🟡 {issue['message']}")
                        else:
                            st.info(f"🟢 {issue['message']}")
            
            with tab3:
                st.markdown("### 💡 Improvement Suggestions")
                
                suggestions = ats_result['suggestions']
                for i, suggestion in enumerate(suggestions, 1):
                    with st.expander(f"{i}. {suggestion['title']}"):
                        st.write(suggestion['description'])
                        st.markdown(f"**Action:** {suggestion['action']}")
                        
                        if 'example' in suggestion:
                            st.code(suggestion['example'])
                
                # Download improved version
                if st.button("📥 Generate Improved Resume", use_container_width=True):
                    with st.spinner("Generating optimized resume..."):
                        improved_content = parser.generate_improved(resume_data, ats_result)
                        st.download_button(
                            label="📄 Download Optimized Resume",
                            data=improved_content,
                            file_name=f"optimized_resume_{datetime.now().strftime('%Y%m%d')}.pdf",
                            mime="application/pdf"
                        )
            
            with tab4:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Skills distribution
                    skills_data = pd.DataFrame({
                        'Category': ['Technical', 'Soft Skills', 'Tools', 'Languages'],
                        'Count': [
                            len([s for s in resume_data.get('skills', []) if s in parser.tech_skills]),
                            len([s for s in resume_data.get('skills', []) if s in parser.soft_skills]),
                            0, 0
                        ]
                    })
                    
                    fig = px.pie(skills_data, values='Count', names='Category',
                                title='Skills Distribution', hole=0.4)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Experience timeline
                    exp_data = pd.DataFrame({
                        'Year': ['2023', '2022', '2021', '2020'],
                        'Experience': [3, 2, 1, 0]
                    })
                    fig = px.area(exp_data, x='Year', y='Experience',
                                 title='Experience Growth')
                    st.plotly_chart(fig, use_container_width=True)
                
                # Score radar
                categories = ['Keywords', 'Formatting', 'Sections', 'Skills', 'Experience']
                values = [
                    ats_result['keywords_found'] * 10,
                    ats_result['formatting_score'],
                    ats_result['sections_score'],
                    min(len(resume_data.get('skills', [])) * 10, 100),
                    min(len(resume_data.get('experience', [])) * 20, 100)
                ]
                
                fig = go.Figure(data=go.Scatterpolar(
                    r=values,
                    theta=categories,
                    fill='toself',
                    marker=dict(color='rgba(0,255,136,0.3)'),
                    line=dict(color='#00ff88', width=2)
                ))
                fig.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                    showlegend=False,
                    title='Resume Strength Radar',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white' if st.session_state.dark_mode else 'black')
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with tab5:
                st.markdown("### 🔄 Multi-Resume Comparison")
                
                more_files = st.file_uploader(
                    "Upload more resumes to compare",
                    type=['pdf', 'docx', 'txt'],
                    accept_multiple_files=True,
                    key="compare_upload"
                )
                
                if more_files:
                    all_files = [uploaded_file] + list(more_files)
                    comparison_data = []
                    
                    with st.spinner("Comparing resumes..."):
                        for file in all_files:
                            data = parser.extract_all(file)
                            ats = ats_checker.analyze(data)
                            comparison_data.append({
                                'Filename': file.name,
                                'Name': data.get('name', 'N/A'),
                                'Score': ats['score'],
                                'Skills': len(data.get('skills', [])),
                                'Experience': len(data.get('experience', []))
                            })
                    
                    df = pd.DataFrame(comparison_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # Comparison chart
                    fig = px.bar(df, x='Filename', y='Score', 
                                title='Resume Comparison',
                                color='Score',
                                color_continuous_scale=['red', 'yellow', 'green'])
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.session_state.comparison_results = df

# Job Matcher Page
def show_job_matcher():
    st.markdown("<h1>🎯 Smart Job Matcher</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📝 Job Description")
        job_description = st.text_area(
            "Paste job description here",
            height=250,
            placeholder="e.g., Looking for a Senior Python Developer with 5+ years experience in Django, REST APIs, and AWS..."
        )
        
        st.markdown("### 🎯 Or Select from Common Roles")
        common_roles = [
            "Software Engineer", "Data Scientist", "Frontend Developer",
            "Backend Developer", "Full Stack Developer", "DevOps Engineer",
            "Machine Learning Engineer", "Product Manager", "Data Analyst"
        ]
        selected_role = st.selectbox("Quick select", ["Custom"] + common_roles)
    
    with col2:
        if st.session_state.resume_data:
            st.markdown("### 📄 Your Resume Skills")
            skills = st.session_state.resume_data.get('skills', [])
            for skill in skills:
                st.markdown(f"<span class='skill-badge'>{skill}</span>",
                          unsafe_allow_html=True)
            
            st.markdown("### 💼 Your Experience")
            for exp in st.session_state.resume_data.get('experience', [])[:3]:
                st.write(f"• {exp}")
        else:
            st.warning("⚠️ No resume data found. Please analyze your resume first.")
    
    if st.button("🔍 Analyze Job Match", use_container_width=True) and job_description:
        with st.spinner("Analyzing job requirements and matching with your profile..."):
            # Get resume skills
            resume_skills = st.session_state.resume_data.get('skills', []) if st.session_state.resume_data else []
            
            # Analyze match
            match_result = job_matcher.analyze_match(resume_skills, job_description)
            
            # Display results
            st.markdown("---")
            st.markdown("## 📊 Match Analysis Results")
            
            # Score cards
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Overall Match", f"{match_result['match_score']}%")
            with col2:
                st.metric("Skills Match", f"{match_result['matched_skills']}/{match_result['total_skills']}")
            with col3:
                st.metric("Missing Skills", match_result['missing_skills_count'])
            with col4:
                st.metric("Experience Match", f"{match_result.get('exp_match', 0)}%")
            
            # Skills analysis
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### ✅ Matched Skills")
                if match_result.get('matched', []):
                    for skill in match_result['matched']:
                        st.markdown(f"<span class='skill-badge' style='background: #00ff88;'>{skill}</span>",
                                  unsafe_allow_html=True)
                else:
                    st.info("No matching skills found")
            
            with col2:
                st.markdown("### ❌ Missing Skills (Need to Learn)")
                if match_result.get('missing', []):
                    for skill in match_result['missing']:
                        st.markdown(f"<span class='skill-badge' style='background: #ff4444;'>{skill}</span>",
                                  unsafe_allow_html=True)
                        
                        # Learning resources
                        with st.expander(f"📚 Learn {skill}"):
                            resources = coding_practice.get_learning_resources(skill)
                            for platform, url in resources.items():
                                st.markdown(f"- [{platform}]({url})")
                else:
                    st.success("Great! You have all required skills!")
            
            # Job recommendations
            st.markdown("---")
            st.markdown("## 🎯 Recommended Jobs")
            
            jobs = job_matcher.get_job_recommendations(match_result.get('matched', []), job_description)
            
            for job in jobs:
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                    with col1:
                        st.markdown(f"**{job['title']}** at **{job['company']}**")
                        st.caption(f"📍 {job['location']} | 💰 {job['salary']}")
                    with col2:
                        st.markdown(f"<h3 style='color: {'#00ff88' if job['match']>70 else '#ffaa00'};'>{job['match']}%</h3>", 
                                  unsafe_allow_html=True)
                    with col3:
                        st.markdown(f"⏰ {job['type']}")
                    with col4:
                        if st.button(f"Apply Now", key=job['title']):
                            st.info(f"Application link: {job.get('apply_url', '#')}")
                    st.markdown("---")

# Mock Interview Page
def show_mock_interview():
    st.markdown("<h1>💼 AI Mock Interview</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "👩‍💼 HR Interview", 
        "💻 Technical Interview", 
        "🎤 Voice Interview",
        "📊 Interview History"
    ])
    
    with tab1:
        st.markdown("### 👩‍💼 HR Interview Questions")
        
        if st.session_state.resume_data:
            # Generate HR questions based on resume
            questions = interview_gen.generate_hr_questions(st.session_state.resume_data)
            
            for i, q in enumerate(questions, 1):
                with st.expander(f"**Q{i}: {q['question']}**"):
                    st.markdown(f"*Tip: {q['tip']}*")
                    
                    # Answer input
                    answer = st.text_area(f"Your Answer", key=f"hr_answer_{i}", height=100)
                    
                    if st.button(f"Submit Answer", key=f"hr_submit_{i}"):
                        # Analyze answer
                        feedback = interview_gen.analyze_hr_answer(answer, q)
                        st.session_state.interview_history.append({
                            'type': 'HR',
                            'question': q['question'],
                            'answer': answer,
                            'feedback': feedback,
                            'date': datetime.now()
                        })
                        
                        if feedback['score'] > 70:
                            st.success(f"✅ Good answer! Score: {feedback['score']}%")
                            st.info(f"💡 {feedback['tip']}")
                        else:
                            st.warning(f"⚠️ Could be improved. Score: {feedback['score']}%")
                            st.info(f"💡 {feedback['suggestion']}")
        else:
            st.warning("⚠️ Please upload your resume first in the Resume Analysis section")
    
    with tab2:
        st.markdown("### 💻 Technical Interview Questions")
        
        if st.session_state.resume_data:
            skills = st.session_state.resume_data.get('skills', [])
            
            if skills:
                # Select skill for technical questions
                selected_skill = st.selectbox("Select Skill for Technical Questions", skills)
                difficulty = st.select_slider("Difficulty Level", 
                                             options=["Beginner", "Intermediate", "Advanced", "Expert"])
                
                # Generate technical questions
                tech_questions = interview_gen.generate_technical_questions(
                    selected_skill, difficulty, st.session_state.resume_data
                )
                
                for i, q in enumerate(tech_questions, 1):
                    with st.expander(f"**Q{i}: {q['question']}** (Difficulty: {q['difficulty']})"):
                        if 'code' in q:
                            st.code(q['code'], language=q.get('language', 'python'))
                        
                        st.markdown(f"*Expected Answer:* {q.get('expected', 'No expected answer provided')}")
                        
                        # Answer input
                        answer = st.text_area(f"Your Answer", key=f"tech_answer_{i}", height=150)
                        
                        if st.button(f"Check Answer", key=f"tech_check_{i}"):
                            feedback = interview_gen.evaluate_technical_answer(answer, q)
                            
                            if feedback['correct']:
                                st.success(f"✅ Correct! {feedback.get('explanation', 'Good job!')}")
                            else:
                                st.error(f"❌ Not quite. {feedback.get('hint', 'Try again!')}")
            else:
                st.warning("No skills found in your resume")
        else:
            st.warning("⚠️ Please upload your resume first")
    
    with tab3:
        st.markdown("### 🎤 Voice Interview")
        
        if VOICE_AVAILABLE:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🎯 Interview Settings")
                interview_type = st.radio("Interview Type", ["HR", "Technical", "Mixed"])
                duration = st.slider("Duration (minutes)", 5, 30, 10)
                
                if st.button("🎤 Start Voice Interview", use_container_width=True):
                    st.session_state.voice_interview_active = True
            
            with col2:
                st.markdown("#### 📊 Voice Analysis")
                st.markdown("""
                The AI will analyze:
                • Confidence Level
                • Speech Clarity
                • Pace of Speaking
                • Filler Words
                """)
            
            if st.session_state.get('voice_interview_active', False):
                st.markdown("---")
                st.markdown("### 🎙️ Live Interview Session")
                
                # Get questions based on resume
                if st.session_state.resume_data:
                    questions = interview_gen.generate_interview_questions(
                        st.session_state.resume_data, interview_type
                    )
                else:
                    questions = interview_gen.generate_general_questions(interview_type)
                
                # Interview interface
                for i, q in enumerate(questions[:5]):  # Limit to 5 questions
                    st.markdown(f"**Question {i+1}:** {q if isinstance(q, str) else q.get('question', str(q))}")
                    
                    # Voice recording button
                    if st.button(f"🎤 Record Answer {i+1}", key=f"record_{i}"):
                        with st.spinner("Recording... Speak now (5 seconds)"):
                            # Record and transcribe
                            text, confidence = voice_interviewer.record_and_transcribe(duration=5)
                            
                            if text:
                                st.success(f"You said: {text}")
                                
                                # Analyze response
                                analysis = voice_interviewer.analyze_speech(text, confidence)
                                
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Confidence", f"{analysis['confidence']}%")
                                with col2:
                                    st.metric("Clarity", f"{analysis['clarity']}%")
                                with col3:
                                    st.metric("Pace", analysis['pace'])
                                
                                if analysis.get('filler_words'):
                                    st.warning(f"Filler words detected: {', '.join(analysis['filler_words'])}")
                                
                                # Save to history
                                st.session_state.interview_history.append({
                                    'type': 'Voice',
                                    'question': q,
                                    'answer': text,
                                    'analysis': analysis,
                                    'date': datetime.now()
                                })
                
                if st.button("⏹️ End Interview"):
                    st.session_state.voice_interview_active = False
                    st.success("Interview completed! Check your history for feedback.")
        else:
            st.warning("🎤 Voice interview feature requires additional setup.")
            st.info("Run this command in your terminal to enable voice features:")
            st.code("pip install sounddevice")
            st.info("Or continue using text-based interviews in the other tabs.")
    
    with tab4:
        st.markdown("### 📊 Interview History")
        
        if st.session_state.interview_history:
            for i, interview in enumerate(reversed(st.session_state.interview_history[-10:])):
                with st.expander(f"📅 {interview['date'].strftime('%Y-%m-%d %H:%M')} - {interview['type']}"):
                    st.markdown(f"**Q:** {interview['question']}")
                    st.markdown(f"**A:** {interview['answer']}")
                    
                    if 'feedback' in interview:
                        st.markdown(f"**Score:** {interview['feedback'].get('score', 'N/A')}%")
                        st.markdown(f"**Feedback:** {interview['feedback'].get('tip', 'N/A')}")
                    
                    if 'analysis' in interview:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Confidence", f"{interview['analysis'].get('confidence', 0)}%")
                        with col2:
                            st.metric("Clarity", f"{interview['analysis'].get('clarity', 0)}%")
                        with col3:
                            st.metric("Pace", interview['analysis'].get('pace', 'N/A'))
        else:
            st.info("No interview history yet. Start a mock interview to see results!")

# Coding Practice Page
def show_coding_practice():
    st.markdown("<h1>📚 Coding Practice</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📘 Daily Challenge", "🎯 Skill-Based", "📊 Progress"])
    
    with tab1:
        st.markdown("### 📅 Daily Coding Challenge")
        
        # Get daily challenge
        challenge = coding_practice.get_daily_challenge()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"## {challenge['title']}")
            st.markdown(f"**Difficulty:** {challenge['difficulty']}")
            st.markdown(f"**Topic:** {challenge['topic']}")
            st.markdown(f"**Estimated Time:** {challenge['time']} minutes")
            
            st.markdown("### Problem Description")
            st.markdown(challenge['description'])
            
            st.markdown("### Examples")
            for ex in challenge.get('examples', []):
                st.code(f"Input: {ex.get('input', 'N/A')}\nOutput: {ex.get('output', 'N/A')}")
            
            # Code editor
            st.markdown("### Your Solution")
            code = st.text_area("Write your code here:", height=200, 
                               value=challenge.get('starter_code', ''))
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("▶️ Run Code", use_container_width=True):
                    result = coding_practice.run_code(code, challenge.get('test_cases', []))
                    if result.get('passed', False):
                        st.success(f"✅ All tests passed! ({result.get('runtime', 0)}ms)")
                    else:
                        st.error(f"❌ Tests failed: {result.get('error', 'Unknown error')}")
            
            with col2:
                if st.button("💡 Hint", use_container_width=True):
                    st.info(challenge.get('hint', 'Think about the optimal approach.'))
            
            with col3:
                if st.button("✅ Mark Complete", use_container_width=True):
                    coding_practice.mark_complete(st.session_state.user_id, challenge.get('id', 0))
                    st.success("Great job! Challenge completed!")
        
        with col2:
            st.markdown("### 📊 Challenge Stats")
            st.metric("Completed Today", f"{challenge.get('completed_today', 0)}/1")
            st.metric("Streak", f"{challenge.get('streak', 0)} days")
            st.metric("Total Solved", challenge.get('total_solved', 0))
            
            st.markdown("### 🎯 Recommended for You")
            recommendations = coding_practice.get_recommendations(st.session_state.resume_data)
            for rec in recommendations:
                st.markdown(f"- {rec}")
    
    with tab2:
        st.markdown("### 🎯 Practice by Skill")
        
        if st.session_state.resume_data:
            skills = st.session_state.resume_data.get('skills', [])
            
            if skills:
                col1, col2 = st.columns(2)
                
                with col1:
                    selected_skill = st.selectbox("Select Skill to Practice", skills)
                    difficulty = st.select_slider("Difficulty", 
                                                 options=["Easy", "Medium", "Hard", "Expert"])
                
                with col2:
                    platform = st.multiselect("Platform", 
                                             ["LeetCode", "HackerRank", "CodeChef", "GeeksforGeeks"],
                                             default=["LeetCode"])
                
                if st.button("Get Practice Problems", use_container_width=True):
                    problems = coding_practice.get_problems_by_skill(selected_skill, difficulty, platform)
                    
                    for prob in problems:
                        with st.container():
                            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                            with col1:
                                st.markdown(f"**{prob['title']}**")
                                st.caption(prob.get('description', '')[:100] + "...")
                            with col2:
                                st.markdown(f"⭐ {prob['difficulty']}")
                            with col3:
                                st.markdown(f"⏱️ {prob.get('time', 'N/A')}min")
                            with col4:
                                st.markdown(f"[Solve]({prob.get('url', '#')})")
                            st.markdown("---")
            else:
                st.warning("No skills found in your resume")
        else:
            st.warning("Please analyze your resume first to get personalized recommendations")
    
    with tab3:
        st.markdown("### 📊 Your Coding Progress")
        
        progress = coding_practice.get_user_progress(st.session_state.user_id)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Problems Solved", progress.get('total_solved', 0))
        with col2:
            st.metric("Current Streak", f"{progress.get('streak', 0)} days")
        with col3:
            st.metric("Success Rate", f"{progress.get('success_rate', 0)}%")
        with col4:
            st.metric("Rank", f"#{progress.get('rank', 0)}")
        
        # Progress over time
        if progress.get('history'):
            df = pd.DataFrame(progress['history'])
            fig = px.line(df, x='date', y='solved', title='Problems Solved Over Time')
            st.plotly_chart(fig, use_container_width=True)
        
        # Skill breakdown
        if progress.get('skill_breakdown'):
            skills_data = pd.DataFrame(progress['skill_breakdown'])
            fig = px.pie(skills_data, values='count', names='skill', 
                        title='Problems by Skill')
            st.plotly_chart(fig, use_container_width=True)

# Performance Dashboard
def show_dashboard():
    st.markdown("<h1>📊 Performance Dashboard</h1>", unsafe_allow_html=True)
    
    # Get user data
    history = db.get_user_history(st.session_state.user_id)
    stats = db.get_user_stats(st.session_state.user_id)
    leaderboard = db.get_leaderboard()
    
    if history:
        # Convert to DataFrame
        df = pd.DataFrame(history)
        df['date'] = pd.to_datetime(df['date'])
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class='metric-card'>
                <div class='metric-value'>{}</div>
                <div class='metric-label'>Total Analyses</div>
            </div>
            """.format(stats['total_analyses']), unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class='metric-card'>
                <div class='metric-value'>{:.1f}%</div>
                <div class='metric-label'>Average Score</div>
            </div>
            """.format(stats['avg_score']), unsafe_allow_html=True)
        
        with col3:
            improvement = df['score'].iloc[-1] - df['score'].iloc[0] if len(df) > 1 else 0
            st.markdown("""
            <div class='metric-card'>
                <div class='metric-value'>{:+.1f}%</div>
                <div class='metric-label'>Improvement</div>
            </div>
            """.format(improvement), unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <div class='metric-card'>
                <div class='metric-value'>#{}</div>
                <div class='metric-label'>Global Rank</div>
            </div>
            """.format(stats.get('rank', 'N/A')), unsafe_allow_html=True)
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Score trend
            fig = px.line(df, x='date', y='score', 
                         title='📈 Resume Score Trend',
                         markers=True)
            fig.update_traces(line_color='#00ff88', line_width=3)
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white' if st.session_state.dark_mode else 'black')
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Score distribution
            fig = px.histogram(df, x='score', nbins=20,
                              title='📊 Score Distribution',
                              color_discrete_sequence=['#00ff88'])
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white' if st.session_state.dark_mode else 'black')
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Skills evolution
        st.markdown("### 💪 Skills Evolution")
        
        all_skills = []
        for item in history[-10:]:  # Last 10 analyses
            all_skills.extend(item.get('skills', []))
        
        if all_skills:
            skill_counts = pd.Series(all_skills).value_counts().head(10)
            fig = px.bar(x=skill_counts.index, y=skill_counts.values,
                        title='Top Skills in Your Resumes',
                        color_discrete_sequence=['#00ff88'])
            st.plotly_chart(fig, use_container_width=True)
        
        # Leaderboard
        st.markdown("### 🏆 Global Leaderboard")
        
        if leaderboard:
            leaderboard_df = pd.DataFrame(leaderboard)
            st.dataframe(
                leaderboard_df[['rank', 'username', 'avg_score', 'total_analyses']],
                use_container_width=True,
                hide_index=True
            )
        
        # Recent activity
        st.markdown("### 📋 Recent Activity")
        
        for item in history[:5]:
            with st.expander(f"📄 {item['filename']} - {item['date'][:10]}"):
                st.write(f"**Score:** {item['score']}%")
                if 'skills' in item:
                    st.write("**Skills:**", ', '.join(item['skills'][:5]))
    else:
        st.info("No data yet. Start by analyzing your first resume!")

# Settings Page
def show_settings():
    st.markdown("<h1>⚙️ Settings</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["👤 Profile", "🎨 Preferences", "🔒 Security", "📊 Data"])
    
    with tab1:
        st.markdown("### 👤 Profile Information")
        
        user_data = db.get_user_data(st.session_state.user_id)
        
        with st.form("profile_form"):
            name = st.text_input("Full Name", value=user_data.get('name', ''))
            email = st.text_input("Email", value=user_data.get('email', ''))
            phone = st.text_input("Phone", value=user_data.get('phone', ''))
            linkedin = st.text_input("LinkedIn URL", value=user_data.get('linkedin', ''))
            github = st.text_input("GitHub URL", value=user_data.get('github', ''))
            
            if st.form_submit_button("Update Profile", use_container_width=True):
                db.update_profile(st.session_state.user_id, {
                    'name': name,
                    'email': email,
                    'phone': phone,
                    'linkedin': linkedin,
                    'github': github
                })
                st.success("Profile updated successfully!")
    
    with tab2:
        st.markdown("### 🎨 Appearance Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            theme = st.selectbox("Theme", ["Dark", "Light"], 
                                index=0 if st.session_state.dark_mode else 1)
            if theme == "Dark" and not st.session_state.dark_mode:
                st.session_state.dark_mode = True
                st.rerun()
            elif theme == "Light" and st.session_state.dark_mode:
                st.session_state.dark_mode = False
                st.rerun()
            
            language = st.selectbox("Language", ["English", "Spanish", "French", "German"])
            font_size = st.select_slider("Font Size", options=["Small", "Medium", "Large"], value="Medium")
        
        with col2:
            st.markdown("### 🔔 Notifications")
            email_notif = st.checkbox("Email Notifications", value=True)
            desktop_notif = st.checkbox("Desktop Notifications", value=False)
            interview_reminders = st.checkbox("Interview Reminders", value=True)
            practice_reminders = st.checkbox("Daily Practice Reminders", value=True)
        
        if st.button("Save Preferences", use_container_width=True):
            st.success("Preferences saved!")
    
    with tab3:
        st.markdown("### 🔒 Security Settings")
        
        with st.form("password_form"):
            current_pwd = st.text_input("Current Password", type="password")
            new_pwd = st.text_input("New Password", type="password")
            confirm_pwd = st.text_input("Confirm New Password", type="password")
            
            if st.form_submit_button("Change Password", use_container_width=True):
                if new_pwd == confirm_pwd:
                    if db.change_password(st.session_state.user_id, current_pwd, new_pwd):
                        st.success("Password changed successfully!")
                    else:
                        st.error("Current password is incorrect!")
                else:
                    st.error("New passwords don't match!")
    
    with tab4:
        st.markdown("### 📊 Data Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📥 Export Data")
            if st.button("Export All Data", use_container_width=True):
                data = db.export_user_data(st.session_state.user_id)
                st.download_button(
                    label="📄 Download JSON",
                    data=json.dumps(data, indent=2),
                    file_name=f"dossierai_export_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )
            
            if st.button("Export Resume History", use_container_width=True):
                history = db.get_user_history(st.session_state.user_id)
                df = pd.DataFrame(history)
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📊 Download CSV",
                    data=csv,
                    file_name=f"resume_history_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            st.markdown("#### 🗑️ Delete Data")
            st.warning("⚠️ These actions cannot be undone!")
            
            if st.button("Clear All History", use_container_width=True):
                if st.checkbox("I understand this will delete all my analysis history"):
                    db.clear_history(st.session_state.user_id)
                    st.success("History cleared!")
            
            if st.button("Delete Account", use_container_width=True):
                if st.checkbox("I understand this will permanently delete my account"):
                    db.delete_account(st.session_state.user_id)
                    st.session_state.authenticated = False
                    st.rerun()

# Main execution
if not st.session_state.authenticated:
    login_signup()
else:
    # Set card_bg for sidebar (needed for CSS)
    card_bg = "#1a1a1a" if st.session_state.dark_mode else "#ffffff"
    main_app()

# Footer
st.markdown("""
<div class='footer'>
    <p>🚀 DossierAI Pro | AI-Powered Career Assistant | Version 3.0</p>
    <p>© 2024 All Rights Reserved</p>
</div>
""", unsafe_allow_html=True)