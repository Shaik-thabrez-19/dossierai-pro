# coding_practice.py
import random
from datetime import datetime, timedelta

class CodingPractice:
    def __init__(self):
        # Initialize problems database
        self.problems_db = {
            'easy': [
                {
                    'id': 1,
                    'title': 'Two Sum',
                    'difficulty': 'Easy',
                    'topic': 'Arrays',
                    'time': 15,
                    'description': 'Given an array of integers nums and an integer target, return indices of the two numbers that add up to target.',
                    'examples': [
                        {
                            'input': 'nums = [2,7,11,15], target = 9',
                            'output': '[0,1]',
                            'explanation': 'Because nums[0] + nums[1] == 9'
                        },
                        {
                            'input': 'nums = [3,2,4], target = 6',
                            'output': '[1,2]',
                            'explanation': 'Because nums[1] + nums[2] == 6'
                        }
                    ],
                    'starter_code': 'def two_sum(nums, target):\n    # Write your code here\n    pass',
                    'hint': 'Use a dictionary to store numbers you have seen.',
                    'solution': 'def two_sum(nums, target):\n    seen = {}\n    for i, num in enumerate(nums):\n        complement = target - num\n        if complement in seen:\n            return [seen[complement], i]\n        seen[num] = i\n    return []',
                    'companies': ['Amazon', 'Google', 'Microsoft'],
                    'acceptance_rate': 85
                },
                {
                    'id': 2,
                    'title': 'Valid Parentheses',
                    'difficulty': 'Easy',
                    'topic': 'Strings',
                    'time': 20,
                    'description': 'Given a string s containing just the characters "(", ")", "{", "}", "[" and "]", determine if the input string is valid.',
                    'examples': [
                        {
                            'input': 's = "()"',
                            'output': 'true',
                            'explanation': 'The parentheses are properly closed.'
                        },
                        {
                            'input': 's = "()[]{}"',
                            'output': 'true',
                            'explanation': 'All brackets are properly matched.'
                        },
                        {
                            'input': 's = "(]"',
                            'output': 'false',
                            'explanation': 'The brackets are not properly matched.'
                        }
                    ],
                    'starter_code': 'def is_valid(s):\n    # Write your code here\n    pass',
                    'hint': 'Use a stack to keep track of opening brackets.',
                    'solution': 'def is_valid(s):\n    stack = []\n    mapping = {")": "(", "}": "{", "]": "["}\n    for char in s:\n        if char in mapping:\n            if not stack or stack[-1] != mapping[char]:\n                return False\n            stack.pop()\n        else:\n            stack.append(char)\n    return len(stack) == 0',
                    'companies': ['Facebook', 'Amazon', 'Microsoft'],
                    'acceptance_rate': 92
                },
                {
                    'id': 3,
                    'title': 'Merge Two Sorted Lists',
                    'difficulty': 'Easy',
                    'topic': 'Linked Lists',
                    'time': 20,
                    'description': 'Merge two sorted linked lists and return it as a sorted list.',
                    'examples': [
                        {
                            'input': 'list1 = [1,2,4], list2 = [1,3,4]',
                            'output': '[1,1,2,3,4,4]',
                            'explanation': 'The merged list should be sorted.'
                        }
                    ],
                    'starter_code': 'def merge_two_lists(list1, list2):\n    # Write your code here\n    pass',
                    'hint': 'Use a dummy node and compare values.',
                    'solution': 'def merge_two_lists(l1, l2):\n    dummy = ListNode(0)\n    curr = dummy\n    while l1 and l2:\n        if l1.val < l2.val:\n            curr.next = l1\n            l1 = l1.next\n        else:\n            curr.next = l2\n            l2 = l2.next\n        curr = curr.next\n    curr.next = l1 or l2\n    return dummy.next',
                    'companies': ['Amazon', 'Microsoft', 'Apple'],
                    'acceptance_rate': 88
                }
            ],
            'medium': [
                {
                    'id': 4,
                    'title': 'Add Two Numbers',
                    'difficulty': 'Medium',
                    'topic': 'Linked Lists',
                    'time': 30,
                    'description': 'You are given two non-empty linked lists representing two non-negative integers. Add the two numbers and return the sum as a linked list.',
                    'examples': [
                        {
                            'input': 'l1 = [2,4,3], l2 = [5,6,4]',
                            'output': '[7,0,8]',
                            'explanation': '342 + 465 = 807'
                        }
                    ],
                    'starter_code': 'def add_two_numbers(l1, l2):\n    # Write your code here\n    pass',
                    'hint': 'Traverse both lists and keep track of carry.',
                    'solution': 'def add_two_numbers(l1, l2):\n    dummy = ListNode(0)\n    curr = dummy\n    carry = 0\n    while l1 or l2 or carry:\n        val1 = l1.val if l1 else 0\n        val2 = l2.val if l2 else 0\n        total = val1 + val2 + carry\n        carry = total // 10\n        curr.next = ListNode(total % 10)\n        curr = curr.next\n        if l1: l1 = l1.next\n        if l2: l2 = l2.next\n    return dummy.next',
                    'companies': ['Amazon', 'Google', 'Microsoft'],
                    'acceptance_rate': 76
                },
                {
                    'id': 5,
                    'title': 'Longest Substring Without Repeating Characters',
                    'difficulty': 'Medium',
                    'topic': 'Strings',
                    'time': 35,
                    'description': 'Given a string s, find the length of the longest substring without repeating characters.',
                    'examples': [
                        {
                            'input': 's = "abcabcbb"',
                            'output': '3',
                            'explanation': 'The answer is "abc", with length 3.'
                        },
                        {
                            'input': 's = "bbbbb"',
                            'output': '1',
                            'explanation': 'The answer is "b", with length 1.'
                        }
                    ],
                    'starter_code': 'def length_of_longest_substring(s):\n    # Write your code here\n    pass',
                    'hint': 'Use sliding window technique with two pointers.',
                    'solution': 'def length_of_longest_substring(s):\n    char_set = set()\n    left = 0\n    max_length = 0\n    for right in range(len(s)):\n        while s[right] in char_set:\n            char_set.remove(s[left])\n            left += 1\n        char_set.add(s[right])\n        max_length = max(max_length, right - left + 1)\n    return max_length',
                    'companies': ['Amazon', 'Google', 'Microsoft'],
                    'acceptance_rate': 82
                }
            ],
            'hard': [
                {
                    'id': 6,
                    'title': 'Median of Two Sorted Arrays',
                    'difficulty': 'Hard',
                    'topic': 'Arrays',
                    'time': 45,
                    'description': 'Given two sorted arrays nums1 and nums2 of size m and n respectively, return the median of the two sorted arrays.',
                    'examples': [
                        {
                            'input': 'nums1 = [1,3], nums2 = [2]',
                            'output': '2.00000',
                            'explanation': 'Merged array = [1,2,3] and median is 2.'
                        }
                    ],
                    'starter_code': 'def find_median_sorted_arrays(nums1, nums2):\n    # Write your code here\n    pass',
                    'hint': 'Use binary search on the smaller array.',
                    'solution': 'def find_median_sorted_arrays(nums1, nums2):\n    if len(nums1) > len(nums2):\n        nums1, nums2 = nums2, nums1\n    m, n = len(nums1), len(nums2)\n    left, right = 0, m\n    while left <= right:\n        i = (left + right) // 2\n        j = (m + n + 1) // 2 - i\n        max_left1 = float("-inf") if i == 0 else nums1[i-1]\n        min_right1 = float("inf") if i == m else nums1[i]\n        max_left2 = float("-inf") if j == 0 else nums2[j-1]\n        min_right2 = float("inf") if j == n else nums2[j]\n        if max_left1 <= min_right2 and max_left2 <= min_right1:\n            if (m + n) % 2 == 0:\n                return (max(max_left1, max_left2) + min(min_right1, min_right2)) / 2\n            else:\n                return max(max_left1, max_left2)\n        elif max_left1 > min_right2:\n            right = i - 1\n        else:\n            left = i + 1',
                    'companies': ['Google', 'Amazon', 'Microsoft'],
                    'acceptance_rate': 71
                }
            ]
        }
        
        self.platforms = {
            'LeetCode': 'https://leetcode.com/problems/',
            'HackerRank': 'https://www.hackerrank.com/challenges/',
            'CodeChef': 'https://www.codechef.com/problems/',
            'GeeksforGeeks': 'https://practice.geeksforgeeks.org/problems/'
        }
        
        self.user_progress = {}  # In-memory storage for demo
    
    def get_daily_challenge(self):
        """Get daily coding challenge with safe defaults"""
        # Rotate through difficulties
        today = datetime.now().day
        difficulty_cycle = ['easy', 'medium', 'hard']
        today_difficulty = difficulty_cycle[today % 3]
        
        # Get random problem from today's difficulty
        problems = self.problems_db[today_difficulty]
        challenge = random.choice(problems).copy()
        
        # Add daily metadata
        challenge['completed_today'] = 0
        challenge['streak'] = 0
        challenge['total_solved'] = 0
        challenge['platform_links'] = self._get_platform_links(challenge['title'])
        
        return challenge
    
    def get_problems_by_skill(self, skill, difficulty, platforms, limit=10):
        """Get problems filtered by skill/topic and difficulty"""
        matching_problems = []
        
        # Normalize skill input
        skill_lower = skill.lower()
        
        # Map common skills to topics
        skill_to_topic = {
            'python': ['Arrays', 'Strings', 'Basic Programming'],
            'java': ['Arrays', 'Strings', 'OOP'],
            'javascript': ['Arrays', 'Strings', 'Basic Programming'],
            'sql': ['Database'],
            'react': ['Frontend'],
            'machine learning': ['Algorithms']
        }
        
        # Get related topics
        related_topics = skill_to_topic.get(skill_lower, [skill.capitalize()])
        
        # Search through problems
        for diff in self.problems_db:
            if difficulty != 'All' and diff.lower() != difficulty.lower():
                continue
            
            for problem in self.problems_db[diff]:
                # Check if problem matches skill topic
                if any(topic.lower() in problem['topic'].lower() for topic in related_topics):
                    problem_copy = problem.copy()
                    # Add platform links
                    problem_copy['platform_links'] = self._get_platform_links(problem['title'])
                    matching_problems.append(problem_copy)
        
        return matching_problems[:limit]
    
    def _get_platform_links(self, problem_title):
        """Generate platform links for a problem"""
        # Convert problem title to URL-friendly format
        url_title = problem_title.lower().replace(' ', '-')
        
        return {
            'LeetCode': f"{self.platforms['LeetCode']}{url_title}",
            'HackerRank': f"{self.platforms['HackerRank']}{url_title}",
            'GeeksforGeeks': f"{self.platforms['GeeksforGeeks']}{url_title}"
        }
    
    def get_recommendations(self, resume_data):
        """Get personalized recommendations based on resume"""
        recommendations = []
        
        if resume_data and isinstance(resume_data, dict):
            skills = resume_data.get('skills', [])
            
            # Map skills to problem topics
            skill_recommendations = {
                'python': ['Practice array problems', 'Try string manipulation', 'Work on algorithms'],
                'java': ['Practice OOP concepts', 'Try collections framework', 'Work on multithreading'],
                'javascript': ['Practice array methods', 'Try closure problems', 'Work on promises'],
                'sql': ['Practice complex queries', 'Try optimization problems', 'Work on database design'],
                'machine learning': ['Practice numpy problems', 'Try pandas exercises', 'Work on algorithms']
            }
            
            for skill in skills[:3]:
                skill_lower = skill.lower()
                if skill_lower in skill_recommendations:
                    recommendations.extend(skill_recommendations[skill_lower][:2])
        
        # Add default recommendations if none found
        if not recommendations:
            recommendations = [
                "Start with Easy array problems",
                "Practice two-pointer technique",
                "Learn basic data structures",
                "Try string manipulation challenges",
                "Work on dynamic programming basics"
            ]
        
        return recommendations[:5]
    
    def get_learning_resources(self, skill):
        """Get learning resources for a skill"""
        return {
            'Coursera': f'https://www.coursera.org/courses?query={skill}',
            'Udemy': f'https://www.udemy.com/courses/search/?q={skill}',
            'YouTube': f'https://www.youtube.com/results?search_query={skill}+tutorial',
            'Documentation': f'https://www.google.com/search?q={skill}+documentation',
            'Practice': f'https://www.google.com/search?q={skill}+practice+problems'
        }
    
    def run_code(self, code, test_cases):
        """Simulate running code (simplified - in production would use actual code execution)"""
        # This is a simulation - in a real app, you'd use something like Piston API or similar
        import random
        
        # Simple checks for demo purposes
        if not code or len(code.strip()) < 10:
            return {
                'passed': False,
                'runtime': 0,
                'error': 'Code is too short or empty'
            }
        
        # Check for obvious syntax errors
        if 'def ' not in code:
            return {
                'passed': False,
                'runtime': 0,
                'error': 'No function definition found'
            }
        
        # Simulate execution (70% chance of passing for demo)
        passed = random.random() > 0.3
        
        return {
            'passed': passed,
            'runtime': random.randint(50, 500),
            'error': None if passed else 'Test case 2 failed: expected 5 but got 4'
        }
    
    def mark_complete(self, user_id, problem_id):
        """Mark problem as completed and update progress"""
        if user_id not in self.user_progress:
            self.user_progress[user_id] = {
                'completed': [],
                'streak': 0,
                'last_solved': None
            }
        
        if problem_id not in self.user_progress[user_id]['completed']:
            self.user_progress[user_id]['completed'].append(problem_id)
            
            # Update streak
            today = datetime.now().date()
            if self.user_progress[user_id]['last_solved']:
                last = self.user_progress[user_id]['last_solved']
                if (today - last).days == 1:
                    self.user_progress[user_id]['streak'] += 1
                elif (today - last).days > 1:
                    self.user_progress[user_id]['streak'] = 1
            else:
                self.user_progress[user_id]['streak'] = 1
            
            self.user_progress[user_id]['last_solved'] = today
        
        return True
    
    def get_user_progress(self, user_id):
        """Get user's coding progress"""
        if user_id not in self.user_progress:
            return {
                'total_solved': 0,
                'streak': 0,
                'success_rate': 0,
                'rank': 0,
                'history': self._generate_mock_history(),
                'skill_breakdown': self._generate_mock_skill_breakdown()
            }
        
        progress = self.user_progress[user_id]
        completed = progress.get('completed', [])
        
        # Calculate statistics
        total_solved = len(completed)
        
        # Determine difficulty breakdown
        easy_count = sum(1 for pid in completed if pid <= 3)
        medium_count = sum(1 for pid in completed if 4 <= pid <= 5)
        hard_count = sum(1 for pid in completed if pid >= 6)
        
        return {
            'total_solved': total_solved,
            'streak': progress.get('streak', 0),
            'success_rate': min(100, total_solved * 10),  # Mock success rate
            'rank': max(1, 1000 - total_solved * 10),  # Mock rank
            'history': self._generate_mock_history(),
            'skill_breakdown': [
                {'skill': 'Arrays', 'count': easy_count},
                {'skill': 'Strings', 'count': medium_count},
                {'skill': 'Linked Lists', 'count': hard_count},
                {'skill': 'Trees', 'count': 0},
                {'skill': 'Dynamic Programming', 'count': 0}
            ]
        }
    
    def _generate_mock_history(self):
        """Generate mock history data for demonstration"""
        history = []
        for i in range(30, 0, -1):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            history.append({
                'date': date,
                'solved': random.randint(0, 3) if random.random() > 0.3 else 0
            })
        return history
    
    def _generate_mock_skill_breakdown(self):
        """Generate mock skill breakdown"""
        return [
            {'skill': 'Arrays', 'count': random.randint(5, 15)},
            {'skill': 'Strings', 'count': random.randint(3, 10)},
            {'skill': 'Linked Lists', 'count': random.randint(2, 8)},
            {'skill': 'Trees', 'count': random.randint(1, 5)},
            {'skill': 'Dynamic Programming', 'count': random.randint(0, 3)}
        ]
    
    def get_problem_by_id(self, problem_id):
        """Get a specific problem by ID"""
        for difficulty in self.problems_db:
            for problem in self.problems_db[difficulty]:
                if problem['id'] == problem_id:
                    return problem.copy()
        return None
    
    def get_problems_by_company(self, company):
        """Get problems frequently asked by a specific company"""
        company_problems = []
        
        for difficulty in self.problems_db:
            for problem in self.problems_db[difficulty]:
                if 'companies' in problem and company in problem['companies']:
                    company_problems.append(problem.copy())
        
        return company_problems[:10]
    
    def get_statistics(self):
        """Get overall platform statistics"""
        total_problems = sum(len(self.problems_db[diff]) for diff in self.problems_db)
        easy_count = len(self.problems_db['easy'])
        medium_count = len(self.problems_db['medium'])
        hard_count = len(self.problems_db['hard'])
        
        return {
            'total_problems': total_problems,
            'easy': easy_count,
            'medium': medium_count,
            'hard': hard_count,
            'companies': ['Amazon', 'Google', 'Microsoft', 'Facebook', 'Apple']
        }