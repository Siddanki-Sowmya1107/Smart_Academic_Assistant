"""
Complete Voice Agent for FAU Smart Academic Assistant
Features: Speech-to-Text, Intent Recognition, Appointment Booking, Text-to-Speech
"""
import speech_recognition as sr
from gtts import gTTS
import os
import json
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
import tempfile


class VoiceAgent:
    """Complete voice interaction agent"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.recognizer = sr.Recognizer()
        self.openai_api_key = openai_api_key
        
    def speech_to_text(self, audio_file=None, language="en-US") -> Tuple[Optional[str], Optional[str]]:
        """
        Convert speech to text
        
        Args:
            audio_file: Path to audio file or file-like object
            language: Language code (en-US, es-ES, fr-FR, de-DE)
        
        Returns:
            (transcribed_text, error_message)
        """
        try:
            if audio_file:
                # From uploaded file
                with sr.AudioFile(audio_file) as source:
                    audio_data = self.recognizer.record(source)
            else:
                return None, "❌ No audio file provided for speech-to-text. Use listen_for_command for microphone input."
            
            # Recognize speech using Google Speech Recognition (FREE!)
            text = self.recognizer.recognize_google(audio_data, language=language)
            return text, None
            
        except sr.WaitTimeoutError:
            return None, "⏱️ No speech detected. Please try again."
        except sr.UnknownValueError:
            return None, "❌ Could not understand audio. Please speak clearly."
        except sr.RequestError as e:
            return None, f"❌ Speech recognition service error: {e}"
        except Exception as e:
            return None, f"❌ Error processing audio file: {str(e)}"

    def listen_for_command(self, language="en-US") -> Tuple[Optional[str], Optional[str]]:
        """
        Listen for speech from the microphone in real-time, simulating a mic click.
        
        Returns:
            (transcribed_text, error_message)
        """
        with sr.Microphone() as source:
            print("🎤 Press Enter to start listening. Press Enter again to stop.")
            input() # Wait for user to press Enter to start
            print("🎤 Listening...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            audio_data = None
            try:
                # Listen for a phrase, with a timeout
                audio_data = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
                # Recognize speech using Google Speech Recognition (FREE!)
                text = self.recognizer.recognize_google(audio_data, language=language)
                return text, None
            except sr.WaitTimeoutError:
                return None, "⏱️ No speech detected. Please try again."
            except sr.UnknownValueError:
                return None, "❌ Could not understand audio. Please speak clearly."
            except sr.RequestError as e:
                return None, f"❌ Speech recognition service error: {e}"
            except Exception as e:
                return None, f"❌ Error during microphone input: {str(e)}"

    def text_to_speech(self, text: str, language="en", output_path: Optional[str] = None) -> Optional[str]:
        """
        Convert text to speech using gTTS (FREE!)
        
        Args:
            text: Text to convert
            language: Language code (en, es, fr, de)
            output_path: Where to save audio file
        
        Returns:
            Path to generated audio file
        """
        try:
            if not output_path:
                output_path = tempfile.mktemp(suffix=".mp3")
            
            tts = gTTS(text=text, lang=language, slow=False)
            tts.save(output_path)
            return output_path
            
        except Exception as e:
            print(f"❌ TTS Error: {e}")
            return None
    
    def understand_intent(self, text: str) -> Dict[str, Any]:
        """
        Parse user intent from text using pattern matching
        
        Detects:
        - Appointment booking requests
        - Form filling requests
        - Questions about procedures
        """
        text_lower = text.lower()
        
        intent = {
            "type": "unknown",
            "confidence": 0.0,
            "entities": {},
            "action": None
        }
        
        # Appointment booking patterns
        appointment_keywords = ["appointment", "meeting", "schedule", "book", "see advisor", "meet with"]
        if any(keyword in text_lower for keyword in appointment_keywords):
            intent["type"] = "book_appointment"
            intent["confidence"] = 0.9
            
            # Extract entities
            entities = self._extract_appointment_entities(text)
            intent["entities"] = entities
            intent["action"] = "show_calendar"
        
        # Form filling patterns
        form_keywords = ["form", "application", "graduate", "override", "fill out"]
        change_major_keywords = ["change major", "switch major", "update major"]

        if any(keyword in text_lower for keyword in change_major_keywords):
            intent["type"] = "fill_form"
            intent["confidence"] = 0.9
            intent["entities"]["form_type"] = "Change of Major"
            intent["action"] = "open_form"
        elif any(keyword in text_lower for keyword in form_keywords):
            intent["type"] = "fill_form"
            intent["confidence"] = 0.85
            
            # Determine form type
            if "graduat" in text_lower:
                intent["entities"]["form_type"] = "Graduation Application"
            elif "override" in text_lower or "course" in text_lower:
                intent["entities"]["form_type"] = "Course Override"
            
            intent["action"] = "open_form"
        
        # Question patterns
        question_keywords = ["how", "what", "when", "where", "can i", "do i need"]
        if any(keyword in text_lower for keyword in question_keywords):
            intent["type"] = "question"
            intent["confidence"] = 0.8
            intent["action"] = "answer_question"
        
        # Greeting patterns
        greeting_keywords = ["hello", "hi", "hey", "good morning", "good afternoon"]
        if any(keyword in text_lower for keyword in greeting_keywords):
            intent["type"] = "greeting"
            intent["confidence"] = 1.0
            intent["action"] = "greet"
        
        return intent
    
    def _extract_appointment_entities(self, text: str) -> Dict[str, Any]:
        """Extract appointment details from text"""
        entities = {
            "meeting_type": None,
            "preferred_date": None,
            "preferred_time": None,
            "advisor_name": None,
            "reason": None
        }
        
        text_lower = text.lower()
        
        # Meeting type
        if "advisor" in text_lower or "advising" in text_lower:
            entities["meeting_type"] = "advisor_meeting"
        elif "tutor" in text_lower:
            entities["meeting_type"] = "tutoring"
        elif "office hour" in text_lower:
            entities["meeting_type"] = "office_hours"
        
        # Date extraction (simple patterns)
        date_patterns = {
            "today": 0,
            "tomorrow": 1,
            "next week": 7,
            "monday": self._days_until_weekday(0),
            "tuesday": self._days_until_weekday(1),
            "wednesday": self._days_until_weekday(2),
            "thursday": self._days_until_weekday(3),
            "friday": self._days_until_weekday(4),
        }
        
        for pattern, days in date_patterns.items():
            if pattern in text_lower:
                target_date = datetime.now() + timedelta(days=days)
                entities["preferred_date"] = target_date.strftime("%Y-%m-%d")
                break
        
        # Time extraction (simple patterns)
        time_patterns = {
            r"(\d{1,2})\s*(am|pm)": lambda m: f"{m.group(1)}:00 {m.group(2).upper()}",
            r"(\d{1,2}):(\d{2})\s*(am|pm)": lambda m: f"{m.group(1)}:{m.group(2)} {m.group(3).upper()}",
            "morning": "10:00 AM",
            "afternoon": "2:00 PM",
            "evening": "5:00 PM",
        }
        
        for pattern, time_value in time_patterns.items():
            if isinstance(pattern, str) and pattern in text_lower:
                entities["preferred_time"] = time_value
                break
            elif isinstance(pattern, str) is False:
                match = re.search(pattern, text_lower)
                if match:
                    entities["preferred_time"] = time_value(match)
                    break
        
        # Reason extraction
        reason_match = re.search(r'(about|for|regarding)\s+(.+)', text, re.IGNORECASE)
        if reason_match:
            entities["reason"] = reason_match.group(2)[:100]
        
        return entities
    
    def _days_until_weekday(self, target_weekday: int) -> int:
        """Calculate days until next occurrence of weekday (0=Monday, 6=Sunday)"""
        today = datetime.now()
        current_weekday = today.weekday()
        days_ahead = target_weekday - current_weekday
        if days_ahead <= 0:
            days_ahead += 7
        return days_ahead
    
    def generate_response(self, intent: Dict[str, Any], context: Optional[Dict] = None) -> str:
        """Generate natural language response based on intent"""
        
        if intent["type"] == "greeting":
            return "Hello! I'm the FAU Smart Assistant. I can help you book appointments, fill out forms, or answer questions about academic procedures. What would you like to do?"
        
        elif intent["type"] == "book_appointment":
            entities = intent.get("entities", {})
            meeting_type = entities.get("meeting_type", "meeting")
            date = entities.get("preferred_date", "soon")
            time = entities.get("preferred_time", "at your convenience")
            
            if date != "soon" and time != "at your convenience":
                return f"I can help you schedule a {meeting_type.replace('_', ' ')} for {date} at {time}. Let me check the available slots."
            elif date != "soon":
                return f"I'll help you book a {meeting_type.replace('_', ' ')} on {date}. What time works best for you?"
            else:
                return f"I'll help you schedule a {meeting_type.replace('_', ' ')}. When would you like to meet?"
        
        elif intent["type"] == "fill_form":
            form_type = intent["entities"].get("form_type", "form")
            return f"I can help you fill out the {form_type}. I'll auto-fill it based on your academic record. Would you like me to do that now?"
        
        elif intent["type"] == "question":
            return "I'd be happy to help answer your question. Based on FAU policies and procedures, let me provide you with the most accurate information. Could you please be more specific about what you'd like to know?"
        
        else:
            return "I'm not sure I understood that. You can ask me to: book an appointment, fill out a form, or ask questions about academic procedures. What would you like to do?"


class AppointmentScheduler:
    """Handle appointment scheduling"""
    
    def __init__(self):
        self.appointments = []
    
    def find_available_slots(self, date: str, duration_minutes: int = 30) -> list:
        """Find available time slots for given date"""
        available_slots = [
            {"time": "9:00 AM", "advisor": "Dr. Smith", "available": True},
            {"time": "10:00 AM", "advisor": "Dr. Smith", "available": True},
            {"time": "11:00 AM", "advisor": "Dr. Smith", "available": False},
            {"time": "2:00 PM", "advisor": "Dr. Smith", "available": True},
            {"time": "3:00 PM", "advisor": "Dr. Smith", "available": True},
            {"time": "4:00 PM", "advisor": "Dr. Smith", "available": True},
        ]
        
        return [slot for slot in available_slots if slot["available"]]
    
    def book_appointment(self, student_znumber: str, date: str, time: str, 
                        meeting_type: str, advisor: str, reason: str = "") -> Dict[str, Any]:
        """Book an appointment"""
        appointment = {
            "id": f"APT-{len(self.appointments) + 1}",
            "student_znumber": student_znumber,
            "date": date,
            "time": time,
            "meeting_type": meeting_type,
            "advisor": advisor,
            "reason": reason,
            "status": "confirmed",
            "created_at": datetime.now().isoformat(),
            "zoom_link": f"https://fau.zoom.us/j/{str(hash(date + time))[-10:]}"
        }
        
        self.appointments.append(appointment)
        return appointment


def process_voice_command(audio_file=None, language: str = "en-US", 
                         student_znumber: Optional[str] = None) -> Dict[str, Any]:
    """
    Complete voice processing pipeline
    
    Returns:
        {
            "transcription": str,
            "intent": dict,
            "response": str,
            "action": str,
            "audio_response_path": str (optional)
        }
    """
    agent = VoiceAgent()
    
    # Step 1: Speech to text or listen for command
    transcription = None
    error = None
    if audio_file:
        transcription, error = agent.speech_to_text(audio_file, language)
    else:
        transcription, error = agent.listen_for_command(language)
    
    if error:
        return {
            "transcription": None,
            "intent": {"type": "error"},
            "response": error,
            "action": None,
            "audio_response_path": None,
            "entities": {}
        }
    
    # Step 2: Understand intent
    intent = agent.understand_intent(transcription)
    
    # Step 3: Generate response
    response = agent.generate_response(intent)
    
    # Step 4: Text to speech (optional)
    lang_code = language.split("-")[0]
    audio_response_path = agent.text_to_speech(response, language=lang_code)
    
    return {
        "transcription": transcription,
        "intent": intent,
        "response": response,
        "action": intent.get("action"),
        "audio_response_path": audio_response_path,
        "entities": intent.get("entities", {})
    }
