# voice_interview.py
import speech_recognition as sr
import pyttsx3
import threading
import queue
import time
import random

class VoiceInterviewer:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Initialize text-to-speech
        try:
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 150)
            self.tts_engine.setProperty('volume', 0.9)
        except:
            self.tts_engine = None
        
        self.is_recording = False
        self.audio_queue = queue.Queue()
        
        # Interview metrics
        self.filler_words = ['um', 'uh', 'like', 'you know', 'actually', 'basically', 'sort of']
    
    def speak(self, text):
        """Convert text to speech"""
        if self.tts_engine:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        else:
            print(f"AI: {text}")
    
    def listen(self, timeout=5):
        """Listen for user speech"""
        with self.microphone as source:
            print("Listening...")
            self.recognizer.adjust_for_ambient_noise(source)
            try:
                audio = self.recognizer.listen(source, timeout=timeout)
                return audio
            except sr.WaitTimeoutError:
                return None
    
    def recognize_speech(self, audio):
        """Convert speech to text"""
        if not audio:
            return None, 0
        
        try:
            # Try Google Speech Recognition
            text = self.recognizer.recognize_google(audio)
            confidence = 80  # Mock confidence
            return text, confidence
        except sr.UnknownValueError:
            return "Could not understand audio", 0
        except sr.RequestError:
            return "Speech service unavailable", 0
    
    def record_and_transcribe(self, duration=5):
        """Record audio and transcribe"""
        print(f"Recording for {duration} seconds...")
        
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
            try:
                audio = self.recognizer.record(source, duration=duration)
                text = self.recognizer.recognize_google(audio)
                
                # Calculate confidence (simplified)
                confidence = min(100, int(len(text) / duration * 20))
                
                return text, confidence
            except sr.UnknownValueError:
                return "Could not understand audio", 0
            except sr.RequestError:
                return "Speech service unavailable", 0
            except Exception as e:
                return f"Error: {str(e)}", 0
    
    def analyze_speech(self, text, confidence):
        """Analyze speech quality"""
        words = text.lower().split()
        
        # Count filler words
        filler_count = sum(1 for word in words if word in self.filler_words)
        
        # Calculate speaking pace (words per second approximation)
        pace = len(words) / 5  # Assuming 5 seconds of speaking
        
        # Calculate clarity based on confidence and filler words
        clarity = max(0, confidence - (filler_count * 5))
        
        # Detect filler words used
        used_fillers = [word for word in words if word in self.filler_words]
        
        return {
            'confidence': confidence,
            'clarity': min(100, clarity),
            'pace': 'Good' if 120 < pace * 60 < 160 else 'Too fast' if pace * 60 > 160 else 'Too slow',
            'filler_words': used_fillers[:5],
            'word_count': len(words)
        }
    
    def conduct_interview(self, questions):
        """Conduct a complete interview"""
        responses = []
        
        for i, question in enumerate(questions, 1):
            print(f"\nQuestion {i}: {question}")
            self.speak(question)
            
            # Give user time to think
            time.sleep(2)
            
            # Listen for response
            audio = self.listen(timeout=10)
            text, confidence = self.recognize_speech(audio) if audio else (None, 0)
            
            if text:
                print(f"You: {text}")
                analysis = self.analyze_speech(text, confidence)
                responses.append({
                    'question': question,
                    'answer': text,
                    'confidence': confidence,
                    'analysis': analysis
                })
            else:
                print("No response detected")
                responses.append({
                    'question': question,
                    'answer': None,
                    'confidence': 0,
                    'analysis': None
                })
        
        return responses
    
    def provide_feedback(self, responses):
        """Provide interview feedback"""
        feedback = []
        
        total_confidence = 0
        total_clarity = 0
        total_fillers = 0
        response_count = 0
        
        for r in responses:
            if r['answer']:
                response_count += 1
                total_confidence += r['confidence']
                if r['analysis']:
                    total_clarity += r['analysis']['clarity']
                    total_fillers += len(r['analysis']['filler_words'])
        
        if response_count > 0:
            avg_confidence = total_confidence / response_count
            avg_clarity = total_clarity / response_count
            
            feedback.append(f"Average Confidence: {avg_confidence:.1f}%")
            feedback.append(f"Average Clarity: {avg_clarity:.1f}%")
            feedback.append(f"Total Filler Words: {total_fillers}")
            
            if avg_confidence > 80:
                feedback.append("Excellent confidence level!")
            elif avg_confidence > 60:
                feedback.append("Good confidence, but could improve.")
            else:
                feedback.append("Work on speaking with more confidence.")
            
            if total_fillers > 5:
                feedback.append(f"Try to reduce filler words (used {total_fillers} times).")
            else:
                feedback.append("Great job minimizing filler words!")
        else:
            feedback.append("No responses recorded.")
        
        return feedback