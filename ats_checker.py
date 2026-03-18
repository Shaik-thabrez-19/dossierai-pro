# ats_checker.py
import re
from collections import Counter

class ATSChecker:
    def __init__(self):
        self.keyword_weights = {
            'python': 5, 'java': 5, 'javascript': 5, 'sql': 4,
            'aws': 4, 'docker': 4, 'kubernetes': 4, 'machine learning': 5,
            'data science': 5, 'agile': 3, 'scrum': 3, 'leadership': 4,
            'management': 4, 'communication': 3, 'teamwork': 3
        }
        
        self.required_sections = [
            'summary', 'experience', 'education', 'skills'
        ]
        
        self.action_verbs = [
            'achieved', 'improved', 'trained', 'managed', 'created',
            'resolved', 'developed', 'led', 'increased', 'decreased',
            'negotiated', 'launched', 'optimized', 'reduced', 'won'
        ]
    
    def analyze(self, resume_data):
        """Complete ATS analysis"""
        text = resume_data.get('raw_text', '').lower()
        
        # Calculate various scores
        keyword_score = self._analyze_keywords(text)
        formatting_score = self._analyze_formatting(text)
        sections_score = self._analyze_sections(text)
        achievement_score = self._analyze_achievements(text)
        contact_score = self._analyze_contact(resume_data)
        
        # Calculate weighted average
        total_score = int((
            keyword_score * 0.3 +
            formatting_score * 0.2 +
            sections_score * 0.2 +
            achievement_score * 0.15 +
            contact_score * 0.15
        ))
        
        # Find issues
        issues = self._find_issues(resume_data, {
            'keyword_score': keyword_score,
            'formatting_score': formatting_score,
            'sections_score': sections_score,
            'achievement_score': achievement_score,
            'contact_score': contact_score
        })
        
        # Generate suggestions
        suggestions = self._generate_suggestions(issues)
        
        return {
            'score': total_score,
            'keywords_found': self._count_keywords(text),
            'formatting_score': formatting_score,
            'sections_score': sections_score,
            'issues': issues,
            'suggestions': suggestions
        }
    
    def _analyze_keywords(self, text):
        """Analyze keyword density"""
        found_keywords = 0
        total_weight = 0
        
        for keyword, weight in self.keyword_weights.items():
            if keyword in text:
                found_keywords += weight
            total_weight += weight
        
        return int((found_keywords / total_weight) * 100) if total_weight > 0 else 0
    
    def _analyze_formatting(self, text):
        """Analyze formatting quality"""
        score = 100
        issues = []
        
        # Check for bullet points
        if '•' not in text and '-' not in text and '*' not in text:
            score -= 20
            issues.append("No bullet points found")
        
        # Check for consistent spacing
        if '\n\n\n' in text:
            score -= 10
            issues.append("Inconsistent spacing")
        
        # Check for proper capitalization
        sentences = re.split(r'[.!?]+', text)
        for sent in sentences[:10]:
            if sent and not sent[0].isupper():
                score -= 5
                issues.append("Inconsistent capitalization")
                break
        
        # Check for special characters
        if re.search(r'[^\w\s.,!?-]', text):
            score -= 10
            issues.append("Contains special characters")
        
        return max(0, score)
    
    def _analyze_sections(self, text):
        """Check for required sections"""
        found_sections = 0
        
        for section in self.required_sections:
            if section in text:
                found_sections += 1
        
        return int((found_sections / len(self.required_sections)) * 100)
    
    def _analyze_achievements(self, text):
        """Check for quantified achievements"""
        score = 0
        patterns = [
            r'\d+%',  # percentages
            r'\$\s*\d+[kKmMbB]?',  # money
            r'\d+\+?\s*(years?|months?)',  # time periods
            r'\d+\s*(people?|employees?|team members?)',  # people counts
        ]
        
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                score += 25
        
        # Check action verbs
        for verb in self.action_verbs:
            if verb in text:
                score += 5
        
        return min(100, score)
    
    def _analyze_contact(self, resume_data):
        """Check for contact information"""
        score = 0
        
        if resume_data.get('name'):
            score += 20
        if resume_data.get('email'):
            score += 20
        if resume_data.get('phone'):
            score += 20
        if resume_data.get('linkedin'):
            score += 20
        if resume_data.get('github'):
            score += 20
        
        return score
    
    def _count_keywords(self, text):
        """Count number of keywords found"""
        return sum(1 for keyword in self.keyword_weights if keyword in text)
    
    def _find_issues(self, resume_data, scores):
        """Find all issues with the resume"""
        issues = []
        
        # Check keyword score
        if scores['keyword_score'] < 50:
            issues.append({
                'severity': 'high',
                'message': 'Low keyword density. Add more industry keywords.'
            })
        elif scores['keyword_score'] < 70:
            issues.append({
                'severity': 'medium',
                'message': 'Keyword density could be improved.'
            })
        
        # Check formatting
        if scores['formatting_score'] < 60:
            issues.append({
                'severity': 'high',
                'message': 'Poor formatting. Use consistent bullet points and spacing.'
            })
        
        # Check sections
        if scores['sections_score'] < 50:
            issues.append({
                'severity': 'high',
                'message': 'Missing key sections. Add Summary, Experience, Education, and Skills.'
            })
        
        # Check achievements
        if scores['achievement_score'] < 40:
            issues.append({
                'severity': 'high',
                'message': 'Few quantified achievements. Add numbers and metrics.'
            })
        
        # Check contact info
        if scores['contact_score'] < 60:
            issues.append({
                'severity': 'medium',
                'message': 'Incomplete contact information.'
            })
        
        # Check length
        word_count = len(resume_data.get('raw_text', '').split())
        if word_count < 300:
            issues.append({
                'severity': 'medium',
                'message': f'Resume too short ({word_count} words). Aim for 400-600 words.'
            })
        elif word_count > 800:
            issues.append({
                'severity': 'low',
                'message': f'Resume too long ({word_count} words). Consider condensing.'
            })
        
        # Check skills
        if len(resume_data.get('skills', [])) < 5:
            issues.append({
                'severity': 'high',
                'message': 'Too few skills listed. Add more relevant skills.'
            })
        
        return issues
    
    def _generate_suggestions(self, issues):
        """Generate improvement suggestions"""
        suggestions = []
        
        for issue in issues:
            if 'keyword' in issue['message'].lower():
                suggestions.append({
                    'title': 'Add Industry Keywords',
                    'description': 'Include more relevant keywords from job descriptions.',
                    'action': 'Review job postings in your field and add common terms.',
                    'example': 'Add terms like "agile", "scrum", "python", "aws" etc.'
                })
            elif 'formatting' in issue['message'].lower():
                suggestions.append({
                    'title': 'Improve Formatting',
                    'description': 'Use consistent formatting throughout.',
                    'action': 'Use bullet points, consistent fonts, and proper spacing.',
                    'example': '• Used bullet points for achievements\n• Consistent spacing between sections'
                })
            elif 'section' in issue['message'].lower():
                suggestions.append({
                    'title': 'Add Missing Sections',
                    'description': 'Include all standard resume sections.',
                    'action': 'Add Professional Summary, Work Experience, Education, and Skills sections.',
                    'example': 'PROFESSIONAL SUMMARY\n[Your summary here]\n\nWORK EXPERIENCE\n[Your experience here]'
                })
            elif 'achievement' in issue['message'].lower():
                suggestions.append({
                    'title': 'Quantify Achievements',
                    'description': 'Add numbers and metrics to your achievements.',
                    'action': 'Use specific numbers, percentages, and timeframes.',
                    'example': '"Increased sales by 20%" instead of "Increased sales"'
                })
            elif 'skill' in issue['message'].lower():
                suggestions.append({
                    'title': 'Expand Skills Section',
                    'description': 'List more relevant technical and soft skills.',
                    'action': 'Include both technical skills and soft skills.',
                    'example': 'Technical: Python, SQL, AWS\nSoft: Leadership, Communication'
                })
        
        return suggestions