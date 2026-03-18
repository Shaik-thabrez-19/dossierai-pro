# resume_parser.py
import re
import PyPDF2
import docx
from datetime import datetime
import json
import nltk
from nltk.tokenize import sent_tokenize

# Handle spacy import with fallback
SPACY_AVAILABLE = False
try:
    import spacy
    SPACY_AVAILABLE = True
    print("✅ spaCy loaded successfully")
except ImportError:
    print("⚠️ spaCy not available - using basic parsing (install spacy for better results)")
except Exception as e:
    print(f"⚠️ Error loading spaCy: {e} - using basic parsing")

class ResumeParser:
    def __init__(self):
        # Load spaCy model if available
        self.nlp = None
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                print("✅ spaCy model loaded")
            except:
                try:
                    import subprocess
                    print("Downloading spaCy model...")
                    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], check=True)
                    self.nlp = spacy.load("en_core_web_sm")
                except Exception as e:
                    print(f"⚠️ Could not load spaCy model: {e}")
                    self.nlp = None
        
        # Download NLTK data if needed
        try:
            nltk.data.find('tokenizers/punkt')
        except:
            nltk.download('punkt', quiet=True)
        
        # Skill databases
        self.tech_skills = {
            'python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php', 'swift',
            'kotlin', 'go', 'rust', 'typescript', 'html', 'css', 'react', 'angular',
            'vue', 'node.js', 'django', 'flask', 'spring', 'express', 'mongodb',
            'mysql', 'postgresql', 'oracle', 'sqlite', 'redis', 'elasticsearch',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git',
            'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'pandas', 'numpy',
            'tableau', 'power bi', 'hadoop', 'spark', 'kafka', 'airflow'
        }
        
        self.soft_skills = {
            'communication', 'leadership', 'teamwork', 'problem-solving',
            'critical thinking', 'time management', 'adaptability', 'creativity',
            'emotional intelligence', 'conflict resolution', 'negotiation',
            'presentation', 'public speaking', 'writing', 'collaboration'
        }
        
        self.tools = {
            'jira', 'confluence', 'slack', 'teams', 'trello', 'asana',
            'photoshop', 'illustrator', 'figma', 'sketch', 'invision',
            'excel', 'word', 'powerpoint', 'outlook', 'sharepoint',
            'salesforce', 'hubspot', 'zoho', 'sap', 'oracle'
        }
        
        self.languages = {
            'english', 'spanish', 'french', 'german', 'chinese', 'japanese',
            'korean', 'russian', 'arabic', 'portuguese', 'italian', 'dutch'
        }
    
    def extract_text_from_pdf(self, file):
        """Extract text from PDF file"""
        try:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            return f"Error reading PDF: {str(e)}"
    
    def extract_text_from_docx(self, file):
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(file)
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"
            return text
        except Exception as e:
            return f"Error reading DOCX: {str(e)}"
    
    def extract_email(self, text):
        """Extract email addresses"""
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(pattern, text)
        return emails[0] if emails else None
    
    def extract_phone(self, text):
        """Extract phone numbers"""
        patterns = [
            r'\+\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}'
        ]
        
        for pattern in patterns:
            phones = re.findall(pattern, text)
            if phones:
                return phones[0]
        return None
    
    def extract_name(self, text):
        """Extract person name - simplified version without spaCy"""
        # Simple heuristic: look for capitalized words at the beginning
        lines = text.split('\n')
        for line in lines[:5]:
            words = line.strip().split()
            if len(words) >= 2:
                # Check if first two words are capitalized
                if all(w and w[0].isupper() for w in words[:2] if w):
                    return ' '.join(words[:2])
        
        # Try using spaCy if available
        if self.nlp and len(text) < 10000:
            try:
                doc = self.nlp(text[:2000])
                for ent in doc.ents:
                    if ent.label_ == "PERSON":
                        return ent.text
            except:
                pass
        
        return None
    
    def extract_skills(self, text):
        """Extract skills from text"""
        text_lower = text.lower()
        found_skills = set()
        
        # Check technical skills
        for skill in self.tech_skills:
            if skill in text_lower:
                found_skills.add(skill)
        
        # Check soft skills
        for skill in self.soft_skills:
            if skill in text_lower:
                found_skills.add(skill)
        
        # Check tools
        for tool in self.tools:
            if tool in text_lower:
                found_skills.add(tool)
        
        # Check languages
        for lang in self.languages:
            if lang in text_lower:
                found_skills.add(lang)
        
        return list(found_skills)
    
    def extract_education(self, text):
        """Extract education information"""
        education = []
        
        edu_keywords = [
            'bachelor', 'master', 'phd', 'doctorate', 'b.tech', 'm.tech',
            'b.e', 'm.e', 'b.sc', 'm.sc', 'b.a', 'm.a', 'b.com', 'm.com',
            'high school', 'secondary', 'diploma', 'degree', 'university',
            'college', 'institute', 'school'
        ]
        
        lines = text.split('\n')
        for line in lines:
            line_lower = line.lower()
            for keyword in edu_keywords:
                if keyword in line_lower:
                    edu = line.strip()
                    if 10 < len(edu) < 200:
                        education.append(edu)
                    break
        
        return list(set(education))[:5]
    
    def extract_experience(self, text):
        """Extract work experience"""
        experience = []
        
        exp_keywords = [
            'experience', 'work', 'employment', 'job', 'career',
            'professional', 'position', 'role', 'responsibilities'
        ]
        
        lines = text.split('\n')
        current_exp = []
        in_exp_section = False
        
        for line in lines:
            line_lower = line.lower()
            
            if any(keyword in line_lower for keyword in exp_keywords) and not in_exp_section:
                in_exp_section = True
                continue
            
            if in_exp_section:
                if line.strip() and len(line.strip()) > 10:
                    current_exp.append(line.strip())
                elif len(current_exp) > 0:
                    if current_exp:
                        experience.append(' '.join(current_exp))
                    current_exp = []
                    in_exp_section = False
        
        if current_exp:
            experience.append(' '.join(current_exp))
        
        return experience[:10]
    
    def extract_projects(self, text):
        """Extract project information"""
        projects = []
        
        proj_keywords = ['project', 'projects', 'portfolio', 'github']
        
        lines = text.split('\n')
        in_proj_section = False
        current_proj = []
        
        for line in lines:
            line_lower = line.lower()
            
            if any(keyword in line_lower for keyword in proj_keywords) and not in_proj_section:
                in_proj_section = True
                continue
            
            if in_proj_section:
                if line.strip() and len(line.strip()) > 10:
                    current_proj.append(line.strip())
                elif len(current_proj) > 0:
                    projects.append(' '.join(current_proj))
                    current_proj = []
                    in_proj_section = False
        
        if current_proj:
            projects.append(' '.join(current_proj))
        
        return projects[:5]
    
    def extract_all(self, file):
        """Extract all information from resume"""
        # Extract text based on file type
        text = ""
        if file.name.endswith('.pdf'):
            text = self.extract_text_from_pdf(file)
        elif file.name.endswith('.docx'):
            text = self.extract_text_from_docx(file)
        else:  # txt
            try:
                text = file.getvalue().decode('utf-8', errors='ignore')
            except:
                text = ""
        
        if not text:
            return {
                'name': None,
                'email': None,
                'phone': None,
                'skills': [],
                'education': [],
                'experience': [],
                'projects': [],
                'raw_text': ""
            }
        
        # Extract all fields
        resume_data = {
            'name': self.extract_name(text),
            'email': self.extract_email(text),
            'phone': self.extract_phone(text),
            'skills': self.extract_skills(text),
            'education': self.extract_education(text),
            'experience': self.extract_experience(text),
            'projects': self.extract_projects(text),
            'raw_text': text[:5000]
        }
        
        return resume_data
    
    def generate_improved(self, resume_data, ats_result):
        """Generate improved resume content"""
        name = resume_data.get('name', 'Your Name')
        email = resume_data.get('email', 'email@example.com')
        phone = resume_data.get('phone', 'phone')
        skills = resume_data.get('skills', [])
        
        # Safe handling of skills summary (no multi-line f-string expressions)
        skills_text = ', '.join(skills[:5]) if skills else 'various technologies'
        skills_list = ', '.join(skills) if skills else '• Python\n• Java\n• SQL\n• JavaScript'
        
        # Experience lines
        if resume_data.get('experience'):
            exp_lines = '\n'.join(['• ' + exp for exp in resume_data['experience'][:3]])
        else:
            exp_lines = '• Senior Developer at Tech Company (2020-Present)\n• Developer at Startup (2018-2020)'
        
        # Education lines
        if resume_data.get('education'):
            edu_lines = '\n'.join(['• ' + edu for edu in resume_data['education'][:2]])
        else:
            edu_lines = '• Bachelor of Technology in Computer Science\n• High School Diploma'
        
        # Projects lines
        if resume_data.get('projects'):
            proj_lines = '\n'.join(['• ' + proj for proj in resume_data['projects'][:3]])
        else:
            proj_lines = '• Resume Analyzer - AI-powered tool\n• E-commerce Website - Full stack application'
        
        improved = f"""{name}
{email} | {phone}

PROFESSIONAL SUMMARY
----------------------------------------------------------------
Experienced professional with expertise in {skills_text}. 
Proven track record of delivering results and driving innovation.

TECHNICAL SKILLS
----------------------------------------------------------------
{skills_list}

PROFESSIONAL EXPERIENCE
----------------------------------------------------------------
{exp_lines}

EDUCATION
----------------------------------------------------------------
{edu_lines}

PROJECTS
----------------------------------------------------------------
{proj_lines}

ACHIEVEMENTS
----------------------------------------------------------------
• Increased efficiency by 20% through process optimization
• Led team of 5 developers to successful project delivery
• Reduced costs by 15% through innovative solutions
"""
        return improved