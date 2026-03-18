# interview_generator.py
import random
from datetime import datetime

class InterviewGenerator:
    def __init__(self):
        self.hr_questions = [
            {
                'question': 'Tell me about yourself.',
                'tip': 'Focus on professional journey, key achievements, and career goals. Keep it to 2-3 minutes.'
            },
            {
                'question': 'What are your greatest strengths?',
                'tip': 'Choose strengths relevant to the job and provide examples. Be honest and specific.'
            },
            {
                'question': 'What are your weaknesses?',
                'tip': 'Mention a real weakness and explain how you\'re working to improve it.'
            },
            {
                'question': 'Why do you want to work here?',
                'tip': 'Research the company and mention specific things you admire about them.'
            },
            {
                'question': 'Where do you see yourself in 5 years?',
                'tip': 'Show ambition but be realistic. Connect your goals with the company\'s growth.'
            },
            {
                'question': 'Why should we hire you?',
                'tip': 'Summarize your key qualifications and what unique value you bring.'
            },
            {
                'question': 'Tell me about a challenge you overcame.',
                'tip': 'Use the STAR method: Situation, Task, Action, Result.'
            },
            {
                'question': 'How do you handle pressure?',
                'tip': 'Give specific examples of working under deadline or handling multiple tasks.'
            },
            {
                'question': 'What\'s your ideal work environment?',
                'tip': 'Be honest but align with the company culture you\'re applying to.'
            },
            {
                'question': 'Do you have any questions for us?',
                'tip': 'Always have questions prepared. Ask about team, projects, growth opportunities.'
            }
        ]
        
        self.technical_questions = {
            'python': [
                {
                    'question': 'What is list comprehension in Python?',
                    'expected': 'List comprehension is a concise way to create lists. Syntax: [expression for item in iterable if condition]',
                    'difficulty': 'Beginner',
                    'code': 'squares = [x**2 for x in range(10)]'
                },
                {
                    'question': 'Explain the difference between lists and tuples.',
                    'expected': 'Lists are mutable, tuples are immutable. Lists use [], tuples use (). Tuples are faster.',
                    'difficulty': 'Beginner'
                },
                {
                    'question': 'What are decorators in Python?',
                    'expected': 'Decorators are functions that modify the behavior of other functions without changing their code.',
                    'difficulty': 'Intermediate'
                }
            ],
            'javascript': [
                {
                    'question': 'What is closure in JavaScript?',
                    'expected': 'A closure is a function that has access to its outer function scope even after the outer function has returned.',
                    'difficulty': 'Intermediate'
                },
                {
                    'question': 'Explain the event loop.',
                    'expected': 'The event loop is what allows JavaScript to perform non-blocking operations by offloading operations to the system.',
                    'difficulty': 'Advanced'
                }
            ],
            'sql': [
                {
                    'question': 'Write a query to find duplicate emails in a users table.',
                    'expected': 'SELECT email, COUNT(*) FROM users GROUP BY email HAVING COUNT(*) > 1',
                    'difficulty': 'Intermediate',
                    'code': 'SELECT email, COUNT(*) FROM users GROUP BY email HAVING COUNT(*) > 1'
                }
            ]
        }
    
    def generate_hr_questions(self, resume_data, count=10):
        """Generate HR questions based on resume"""
        questions = []
        
        # Add personalized questions based on resume
        if resume_data:
            skills = resume_data.get('skills', [])
            if skills:
                questions.append({
                    'question': f"I see you have experience with {skills[0]}. Can you tell me about a project where you used it?",
                    'tip': 'Describe the project, your role, and the impact you made.'
                })
            
            if resume_data.get('experience'):
                questions.append({
                    'question': f"Tell me about your experience at {resume_data['experience'][0][:30]}...",
                    'tip': 'Focus on achievements and lessons learned.'
                })
        
        # Add generic questions
        questions.extend(random.sample(self.hr_questions, min(count - len(questions), len(self.hr_questions))))
        
        return questions[:count]
    
    def generate_technical_questions(self, skill, difficulty, resume_data=None, count=5):
        """Generate technical questions for a specific skill"""
        questions = []
        
        if skill.lower() in self.technical_questions:
            skill_questions = self.technical_questions[skill.lower()]
            
            # Filter by difficulty
            filtered = [q for q in skill_questions if q['difficulty'].lower() == difficulty.lower()]
            if not filtered:
                filtered = skill_questions
            
            questions = random.sample(filtered, min(count, len(filtered)))
        
        # Add custom questions based on resume
        if resume_data and 'experience' in resume_data:
            questions.append({
                'question': f"Describe a challenging technical problem you solved in your previous role.",
                'expected': 'Use STAR method to structure your answer.',
                'difficulty': 'Intermediate'
            })
        
        return questions
    
    def generate_interview_questions(self, resume_data, interview_type, count=10):
        """Generate mix of questions for interview"""
        if interview_type == "HR":
            return self.generate_hr_questions(resume_data, count)
        elif interview_type == "Technical":
            skills = resume_data.get('skills', []) if resume_data else []
            questions = []
            for skill in skills[:3]:  # Top 3 skills
                questions.extend(self.generate_technical_questions(skill, 'Intermediate', resume_data, 3))
            return questions[:count]
        else:  # Mixed
            hr_count = count // 2
            tech_count = count - hr_count
            
            hr_questions = self.generate_hr_questions(resume_data, hr_count)
            tech_questions = []
            skills = resume_data.get('skills', []) if resume_data else []
            if skills:
                tech_questions = self.generate_technical_questions(skills[0], 'Intermediate', resume_data, tech_count)
            
            return hr_questions + tech_questions
    
    def generate_general_questions(self, interview_type):
        """Generate general questions without resume"""
        if interview_type == "HR":
            return [q['question'] for q in random.sample(self.hr_questions, 5)]
        else:
            return [
                "What programming languages are you proficient in?",
                "Explain the concept of object-oriented programming.",
                "What's your approach to debugging?",
                "How do you stay updated with new technologies?",
                "Describe your experience with version control systems."
            ]
    
    def analyze_hr_answer(self, answer, question):
        """Analyze HR interview answer"""
        word_count = len(answer.split())
        
        # Basic analysis
        score = min(100, int(word_count / 20 * 10))  # 20 words = 10%
        
        # Check for keywords
        keywords = ['experience', 'project', 'team', 'learn', 'achieve', 'solve', 'help']
        found_keywords = sum(1 for kw in keywords if kw in answer.lower())
        score += found_keywords * 5
        
        feedback = {
            'score': min(100, score),
            'word_count': word_count
        }
        
        if word_count < 20:
            feedback['tip'] = 'Your answer is too short. Provide more details.'
            feedback['suggestion'] = 'Try to elaborate with specific examples from your experience.'
        elif word_count < 50:
            feedback['tip'] = 'Good start, but could include more specific examples.'
            feedback['suggestion'] = 'Add details about what you learned or achieved.'
        else:
            feedback['tip'] = 'Great answer! Good length and detail.'
            feedback['suggestion'] = 'Perfect! Keep this format for other questions.'
        
        return feedback
    
    def evaluate_technical_answer(self, answer, question):
        """Evaluate technical interview answer"""
        # Simplified evaluation
        expected_keywords = question['expected'].lower().split()[:5]
        answer_lower = answer.lower()
        
        found_keywords = sum(1 for kw in expected_keywords if kw in answer_lower)
        accuracy = int((found_keywords / len(expected_keywords)) * 100)
        
        return {
            'correct': accuracy > 50,
            'accuracy': accuracy,
            'explanation': f'You covered {found_keywords}/{len(expected_keywords)} key points.',
            'hint': f'Consider mentioning: {", ".join(expected_keywords)}' if accuracy < 50 else ''
        }