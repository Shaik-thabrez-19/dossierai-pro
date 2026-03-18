# job_matcher.py
import re
from collections import Counter
import requests
from bs4 import BeautifulSoup
import json

class JobMatcher:
    def __init__(self):
        self.job_databases = {
            'linkedin': 'https://www.linkedin.com/jobs/search/?keywords={}',
            'indeed': 'https://www.indeed.com/q-{}-jobs.html',
            'glassdoor': 'https://www.glassdoor.com/Job/jobs.htm?sc.keyword={}'
        }
        
        self.skill_categories = {
            'programming': ['python', 'java', 'javascript', 'c++', 'ruby', 'php', 'swift'],
            'web': ['html', 'css', 'react', 'angular', 'vue', 'node.js', 'django'],
            'data': ['sql', 'mongodb', 'tensorflow', 'pytorch', 'pandas', 'numpy'],
            'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins'],
            'soft': ['communication', 'leadership', 'teamwork', 'problem-solving']
        }
    
    def analyze_match(self, resume_skills, job_description):
        """Analyze match between resume and job description"""
        
        # Extract skills from job description
        job_skills = self._extract_skills_from_jd(job_description)
        
        # Find matches and gaps
        resume_skills_lower = [s.lower() for s in resume_skills]
        job_skills_lower = [s.lower() for s in job_skills]
        
        matched = [s for s in resume_skills_lower if s in job_skills_lower]
        missing = [s for s in job_skills_lower if s not in resume_skills_lower]
        
        # Calculate scores
        match_score = int((len(matched) / max(len(job_skills_lower), 1)) * 100)
        
        # Experience match (simplified)
        exp_match = self._analyze_experience_match(job_description)
        
        # Education match
        edu_match = self._analyze_education_match(job_description)
        
        return {
            'match_score': match_score,
            'matched': matched,
            'missing': missing,
            'matched_skills': len(matched),
            'missing_skills_count': len(missing),
            'total_skills': len(job_skills_lower),
            'exp_match': exp_match,
            'edu_match': edu_match,
            'job_skills': job_skills,
            'recommendations': self._generate_recommendations(missing)
        }
    
    def _extract_skills_from_jd(self, job_description):
        """Extract skills from job description text"""
        text_lower = job_description.lower()
        found_skills = set()
        
        # Check all skill categories
        for category, skills in self.skill_categories.items():
            for skill in skills:
                if skill in text_lower:
                    found_skills.add(skill)
        
        # Check for common patterns
        patterns = [
            r'experience with ([^.,]+)',
            r'knowledge of ([^.,]+)',
            r'proficient in ([^.,]+)',
            r'skills?: ([^.,]+)',
            r'technologies?: ([^.,]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, job_description, re.IGNORECASE)
            for match in matches:
                # Split by commas, 'and', etc.
                parts = re.split(r'[,;&]|\sand\s|\sor\s', match)
                for part in parts:
                    skill = part.strip().lower()
                    if len(skill) > 2 and len(skill) < 30:
                        found_skills.add(skill)
        
        return list(found_skills)
    
    def _analyze_experience_match(self, job_description):
        """Analyze experience requirements match"""
        patterns = [
            r'(\d+)[+]?\s*years?',
            r'(\d+)[+]?\s*yr',
            r'experience:?\s*(\d+)[+]?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, job_description, re.IGNORECASE)
            if match:
                required_years = int(match.group(1))
                # Assume user has 3 years (would come from resume)
                user_years = 3
                return min(100, int((user_years / required_years) * 100))
        
        return 70  # Default if no explicit requirement
    
    def _analyze_education_match(self, job_description):
        """Analyze education requirements match"""
        edu_levels = {
            'phd': 100,
            'master': 80,
            'bachelor': 60,
            'associate': 40,
            'high school': 20
        }
        
        text_lower = job_description.lower()
        
        for level, score in edu_levels.items():
            if level in text_lower:
                # Assume user has bachelor's (would come from resume)
                user_level = 'bachelor'
                if user_level in edu_levels:
                    user_score = edu_levels[user_level]
                    if user_score >= score:
                        return 100
                    else:
                        return int((user_score / score) * 100)
        
        return 80  # Default if no explicit requirement
    
    def _generate_recommendations(self, missing_skills):
        """Generate learning recommendations for missing skills"""
        recommendations = []
        
        for skill in missing_skills[:5]:
            rec = {
                'skill': skill,
                'resources': [
                    {'platform': 'Coursera', 'url': f'https://www.coursera.org/courses?query={skill}'},
                    {'platform': 'Udemy', 'url': f'https://www.udemy.com/courses/search/?q={skill}'},
                    {'platform': 'YouTube', 'url': f'https://www.youtube.com/results?search_query={skill}+tutorial'},
                    {'platform': 'Documentation', 'url': f'https://www.google.com/search?q={skill}+documentation'}
                ],
                'estimated_time': self._estimate_learning_time(skill)
            }
            recommendations.append(rec)
        
        return recommendations
    
    def _estimate_learning_time(self, skill):
        """Estimate time to learn a skill"""
        difficulty_map = {
            'python': '2-3 months',
            'java': '3-4 months',
            'javascript': '2-3 months',
            'react': '1-2 months',
            'aws': '3-4 months',
            'docker': '1-2 weeks',
            'kubernetes': '2-3 weeks',
            'sql': '2-4 weeks',
            'machine learning': '4-6 months'
        }
        
        return difficulty_map.get(skill.lower(), '1-3 months')
    
    def get_job_recommendations(self, skills, job_description, limit=10):
        """Get job recommendations based on skills"""
        # This would normally call job APIs
        # For now, return mock data
        jobs = [
            {
                'title': 'Senior Python Developer',
                'company': 'Google',
                'location': 'Bangalore, India',
                'salary': '₹25-35 LPA',
                'type': 'Full-time',
                'match': 85,
                'apply_url': '#',
                'description': 'Looking for experienced Python developer...'
            },
            {
                'title': 'Data Scientist',
                'company': 'Amazon',
                'location': 'Hyderabad, India',
                'salary': '₹20-30 LPA',
                'type': 'Full-time',
                'match': 72,
                'apply_url': '#',
                'description': 'Seeking data scientist with ML experience...'
            },
            {
                'title': 'Full Stack Developer',
                'company': 'Microsoft',
                'location': 'Noida, India',
                'salary': '₹22-32 LPA',
                'type': 'Full-time',
                'match': 68,
                'apply_url': '#',
                'description': 'Full stack developer with React and Node.js...'
            },
            {
                'title': 'DevOps Engineer',
                'company': 'Netflix',
                'location': 'Remote',
                'salary': '$120-150K',
                'type': 'Remote',
                'match': 64,
                'apply_url': '#',
                'description': 'DevOps engineer with AWS and Kubernetes...'
            },
            {
                'title': 'Machine Learning Engineer',
                'company': 'Meta',
                'location': 'Bangalore, India',
                'salary': '₹30-40 LPA',
                'type': 'Full-time',
                'match': 60,
                'apply_url': '#',
                'description': 'ML engineer with deep learning experience...'
            }
        ]
        
        # Sort by match score
        jobs.sort(key=lambda x: x['match'], reverse=True)
        return jobs[:limit]