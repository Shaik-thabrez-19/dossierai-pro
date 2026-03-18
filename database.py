# database.py
import sqlite3
import hashlib
import json
from datetime import datetime
import pandas as pd

class DatabaseManager:
    def __init__(self, db_path='dossierai.db'):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        # Users table
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                email TEXT UNIQUE,
                password TEXT,
                name TEXT,
                phone TEXT,
                linkedin TEXT,
                github TEXT,
                portfolio TEXT,
                created_at TIMESTAMP,
                last_login TIMESTAMP,
                preferences TEXT DEFAULT '{}'
            )
        ''')
        
        # Resume analyses table
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                filename TEXT,
                date TIMESTAMP,
                score INTEGER,
                skills TEXT,
                experience TEXT,
                education TEXT,
                suggestions TEXT,
                ats_data TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Interview history table
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS interviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT,
                date TIMESTAMP,
                questions TEXT,
                answers TEXT,
                feedback TEXT,
                score INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Coding practice table
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS coding_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date DATE,
                problems_solved INTEGER,
                topics TEXT,
                streak INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Job applications table
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS job_applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                job_title TEXT,
                company TEXT,
                applied_date DATE,
                status TEXT,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        self.conn.commit()
    
    def verify_user(self, username, password):
        hashed_pwd = hashlib.sha256(password.encode()).hexdigest()
        cursor = self.conn.execute(
            "SELECT id, username FROM users WHERE (username=? OR email=?) AND password=?",
            (username, username, hashed_pwd)
        )
        user = cursor.fetchone()
        
        if user:
            # Update last login
            self.conn.execute(
                "UPDATE users SET last_login=? WHERE id=?",
                (datetime.now(), user[0])
            )
            self.conn.commit()
            return {'id': user[0], 'username': user[1]}
        return None
    
    def create_user(self, username, email, password):
        try:
            hashed_pwd = hashlib.sha256(password.encode()).hexdigest()
            self.conn.execute(
                "INSERT INTO users (username, email, password, created_at) VALUES (?, ?, ?, ?)",
                (username, email, hashed_pwd, datetime.now())
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error creating user: {e}")
            return False
    
    def save_analysis(self, user_id, filename, score, resume_data):
        try:
            self.conn.execute('''
                INSERT INTO analyses 
                (user_id, filename, date, score, skills, experience, education, ats_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, filename, datetime.now(), score,
                json.dumps(resume_data.get('skills', [])),
                json.dumps(resume_data.get('experience', [])),
                json.dumps(resume_data.get('education', [])),
                json.dumps(resume_data.get('ats_data', {}))
            ))
            self.conn.commit()
        except Exception as e:
            print(f"Error saving analysis: {e}")
    
    def get_user_stats(self, user_id):
        cursor = self.conn.execute('''
            SELECT 
                COUNT(*) as total,
                AVG(score) as avg_score,
                MAX(score) as max_score,
                MIN(score) as min_score
            FROM analyses 
            WHERE user_id=?
        ''', (user_id,))
        
        row = cursor.fetchone()
        if row and row[0] > 0:
            return {
                'total_analyses': row[0],
                'avg_score': round(row[1], 1),
                'max_score': row[2],
                'min_score': row[3]
            }
        return {
            'total_analyses': 0,
            'avg_score': 0,
            'max_score': 0,
            'min_score': 0
        }
    
    def get_user_history(self, user_id):
        cursor = self.conn.execute('''
            SELECT date, filename, score, skills, experience, education
            FROM analyses 
            WHERE user_id=? 
            ORDER BY date DESC
        ''', (user_id,))
        
        rows = cursor.fetchall()
        return [{
            'date': r[0],
            'filename': r[1],
            'score': r[2],
            'skills': json.loads(r[3]) if r[3] else [],
            'experience': json.loads(r[4]) if r[4] else [],
            'education': json.loads(r[5]) if r[5] else []
        } for r in rows]
    
    def get_user_data(self, user_id):
        cursor = self.conn.execute('''
            SELECT username, email, name, phone, linkedin, github, portfolio
            FROM users WHERE id=?
        ''', (user_id,))
        
        row = cursor.fetchone()
        if row:
            return {
                'username': row[0],
                'email': row[1],
                'name': row[2] or '',
                'phone': row[3] or '',
                'linkedin': row[4] or '',
                'github': row[5] or '',
                'portfolio': row[6] or ''
            }
        return {}
    
    def update_profile(self, user_id, data):
        try:
            self.conn.execute('''
                UPDATE users 
                SET name=?, email=?, phone=?, linkedin=?, github=?, portfolio=?
                WHERE id=?
            ''', (
                data.get('name', ''),
                data.get('email', ''),
                data.get('phone', ''),
                data.get('linkedin', ''),
                data.get('github', ''),
                data.get('portfolio', ''),
                user_id
            ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error updating profile: {e}")
            return False
    
    def change_password(self, user_id, current_pwd, new_pwd):
        try:
            # Verify current password
            hashed_current = hashlib.sha256(current_pwd.encode()).hexdigest()
            cursor = self.conn.execute(
                "SELECT id FROM users WHERE id=? AND password=?",
                (user_id, hashed_current)
            )
            if not cursor.fetchone():
                return False
            
            # Update password
            hashed_new = hashlib.sha256(new_pwd.encode()).hexdigest()
            self.conn.execute(
                "UPDATE users SET password=? WHERE id=?",
                (hashed_new, user_id)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error changing password: {e}")
            return False
    
    def get_leaderboard(self):
        cursor = self.conn.execute('''
            SELECT 
                u.username,
                AVG(a.score) as avg_score,
                COUNT(a.id) as total,
                RANK() OVER (ORDER BY AVG(a.score) DESC) as rank
            FROM users u
            JOIN analyses a ON u.id = a.user_id
            GROUP BY u.id
            HAVING COUNT(a.id) >= 3
            ORDER BY avg_score DESC
            LIMIT 50
        ''')
        
        rows = cursor.fetchall()
        return [{
            'rank': r[3],
            'username': r[0],
            'avg_score': round(r[1], 1),
            'total_analyses': r[2]
        } for r in rows]
    
    def save_interview(self, user_id, interview_data):
        try:
            self.conn.execute('''
                INSERT INTO interviews 
                (user_id, type, date, questions, answers, feedback, score)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                interview_data['type'],
                datetime.now(),
                json.dumps(interview_data['questions']),
                json.dumps(interview_data['answers']),
                json.dumps(interview_data['feedback']),
                interview_data.get('score', 0)
            ))
            self.conn.commit()
        except Exception as e:
            print(f"Error saving interview: {e}")
    
    def get_interviews(self, user_id):
        cursor = self.conn.execute('''
            SELECT type, date, score, feedback
            FROM interviews
            WHERE user_id=?
            ORDER BY date DESC
            LIMIT 20
        ''', (user_id,))
        
        rows = cursor.fetchall()
        return [{
            'type': r[0],
            'date': r[1],
            'score': r[2],
            'feedback': json.loads(r[3]) if r[3] else {}
        } for r in rows]
    
    def save_coding_progress(self, user_id, problems_solved, topics):
        today = datetime.now().date()
        
        # Check if entry exists for today
        cursor = self.conn.execute('''
            SELECT id, streak FROM coding_progress
            WHERE user_id=? AND date=?
        ''', (user_id, today))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing
            self.conn.execute('''
                UPDATE coding_progress
                SET problems_solved=?, topics=?
                WHERE id=?
            ''', (problems_solved, json.dumps(topics), existing[0]))
        else:
            # Calculate streak
            cursor = self.conn.execute('''
                SELECT date FROM coding_progress
                WHERE user_id=?
                ORDER BY date DESC
                LIMIT 1
            ''', (user_id,))
            
            last_date = cursor.fetchone()
            streak = 1
            if last_date:
                last = datetime.strptime(last_date[0], '%Y-%m-%d').date()
                if (today - last).days == 1:
                    streak = existing[1] + 1 if existing else 1
            
            self.conn.execute('''
                INSERT INTO coding_progress (user_id, date, problems_solved, topics, streak)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, today, problems_solved, json.dumps(topics), streak))
        
        self.conn.commit()
    
    def get_coding_progress(self, user_id):
        cursor = self.conn.execute('''
            SELECT date, problems_solved, topics, streak
            FROM coding_progress
            WHERE user_id=?
            ORDER BY date DESC
            LIMIT 30
        ''', (user_id,))
        
        rows = cursor.fetchall()
        return [{
            'date': r[0],
            'solved': r[1],
            'topics': json.loads(r[2]) if r[2] else [],
            'streak': r[3]
        } for r in rows]
    
    def save_job_application(self, user_id, job_data):
        try:
            self.conn.execute('''
                INSERT INTO job_applications
                (user_id, job_title, company, applied_date, status, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                job_data['title'],
                job_data['company'],
                job_data.get('date', datetime.now().date()),
                job_data.get('status', 'Applied'),
                job_data.get('notes', '')
            ))
            self.conn.commit()
        except Exception as e:
            print(f"Error saving job application: {e}")
    
    def get_job_applications(self, user_id):
        cursor = self.conn.execute('''
            SELECT job_title, company, applied_date, status, notes
            FROM job_applications
            WHERE user_id=?
            ORDER BY applied_date DESC
        ''', (user_id,))
        
        rows = cursor.fetchall()
        return [{
            'title': r[0],
            'company': r[1],
            'date': r[2],
            'status': r[3],
            'notes': r[4]
        } for r in rows]
    
    def export_user_data(self, user_id):
        data = {
            'profile': self.get_user_data(user_id),
            'analyses': self.get_user_history(user_id),
            'interviews': self.get_interviews(user_id),
            'coding': self.get_coding_progress(user_id),
            'jobs': self.get_job_applications(user_id)
        }
        return data
    
    def clear_history(self, user_id):
        self.conn.execute("DELETE FROM analyses WHERE user_id=?", (user_id,))
        self.conn.execute("DELETE FROM interviews WHERE user_id=?", (user_id,))
        self.conn.execute("DELETE FROM coding_progress WHERE user_id=?", (user_id,))
        self.conn.commit()
    
    def delete_account(self, user_id):
        self.clear_history(user_id)
        self.conn.execute("DELETE FROM users WHERE id=?", (user_id,))
        self.conn.commit()