# voice_interview.py
import time
import threading
import queue
import random

# Try to import optional dependencies; set flags accordingly
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    sr = None
    SPEECH_RECOGNITION_AVAILABLE = False

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    pyttsx3 = None
    TTS_AVAILABLE = False

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    sd = None
    SOUNDDEVICE_AVAILABLE = False


class VoiceInterviewer:
    def __init__(self):
        # Initialize components only if dependencies are available
        self.recognizer = None
        self.microphone = None
        self.tts_engine = None

        if SPEECH_RECOGNITION_AVAILABLE:
            try:
                self.recognizer = sr.Recognizer()
                self.microphone = sr.Microphone()
            except Exception as e:
                print(f"⚠️ Could not initialize speech recognition: {e}")
                self.recognizer = None
                self.microphone = None

        if TTS_AVAILABLE:
            try:
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty('rate', 150)
                self.tts_engine.setProperty('volume', 0.9)
            except Exception as e:
                print(f"⚠️ Could not initialize text-to-speech: {e}")
                self.tts_engine = None

        self.sample_rate = 16000
        self.audio_queue = queue.Queue()
        self.is_recording = False

        self.filler_words = ['um', 'uh', 'like', 'you know', 'actually', 'basically']

    def speak(self, text):
        """Convert text to speech (if available)"""
        if self.tts_engine:
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except Exception as e:
                print(f"TTS error: {e}")
        else:
            print(f"AI would say: {text}")

    def record_audio(self, duration=5):
        """Record audio using sounddevice (if available)"""
        if SOUNDDEVICE_AVAILABLE:
            try:
                print(f"Recording for {duration} seconds...")
                recording = sd.rec(int(duration * self.sample_rate),
                                   samplerate=self.sample_rate,
                                   channels=1,
                                   dtype='int16')
                sd.wait()
                return recording
            except Exception as e:
                print(f"Recording error: {e}")
                return None
        return None

    def audio_to_text(self, audio_data):
        """Convert audio bytes to text using speech_recognition (if available)"""
        if not SPEECH_RECOGNITION_AVAILABLE or not self.recognizer:
            return "Speech recognition not available", 0

        try:
            if hasattr(audio_data, 'tobytes'):
                audio_bytes = audio_data.tobytes()
            else:
                audio_bytes = audio_data

            audio = sr.AudioData(audio_bytes, self.sample_rate, 2)
            text = self.recognizer.recognize_google(audio)
            return text, 85
        except sr.UnknownValueError:
            return "Could not understand audio", 0
        except sr.RequestError:
            return "Speech service unavailable", 0
        except Exception as e:
            return f"Error: {str(e)}", 0

    def record_and_transcribe(self, duration=5):
        """Record and transcribe (fallback if not available)"""
        if not SOUNDDEVICE_AVAILABLE or not SPEECH_RECOGNITION_AVAILABLE:
            return "Voice features not installed", 0

        audio_data = self.record_audio(duration)
        if audio_data is None:
            return "Recording failed", 0

        text, confidence = self.audio_to_text(audio_data)
        return text, confidence

    def analyze_speech(self, text, confidence):
        """Analyze speech quality (always available)"""
        words = text.lower().split()
        filler_count = sum(1 for word in words if word in self.filler_words)
        pace = len(words) / 5 if len(words) > 0 else 0
        clarity = max(0, confidence - (filler_count * 5))
        used_fillers = [word for word in words if word in self.filler_words]

        return {
            'confidence': confidence,
            'clarity': min(100, clarity),
            'pace': 'Good' if 120 < pace * 60 < 160 else 'Too fast' if pace * 60 > 160 else 'Too slow',
            'filler_words': used_fillers[:5],
            'word_count': len(words)
        }

    def conduct_interview(self, questions):
        """Simulate a full interview (for demo)"""
        responses = []
        for i, q in enumerate(questions, 1):
            print(f"\nQuestion {i}: {q}")
            self.speak(q)
            time.sleep(2)
            responses.append({
                'question': q,
                'answer': "Simulated answer",
                'confidence': 80,
                'analysis': self.analyze_speech("Simulated answer", 80)
            })
        return responses

    def provide_feedback(self, responses):
        """Provide interview feedback"""
        return ["Interview completed. Install voice dependencies for detailed analysis."]