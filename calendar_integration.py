"""
Google Calendar Integration for FAU Smart Academic Assistant
Book appointments directly into Google Calendar (FREE API!)
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import os
import pickle
from ics import Calendar, Event as ICSEvent
import tempfile

# Google Calendar API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_CALENDAR_AVAILABLE = True
except ImportError:
    GOOGLE_CALENDAR_AVAILABLE = False
    print("⚠️  Google Calendar libraries not installed. Using fallback mode.")


class CalendarIntegration:
    """
    Google Calendar integration with fallback to .ics files
    """
    
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self, credentials_path: str = "credentials.json"):
        """
        Initialize calendar integration
        
        Args:
            credentials_path: Path to Google OAuth credentials JSON
        """
        self.credentials_path = credentials_path
        self.token_path = "token.pickle"
        self.service = None
        self.use_google_calendar = False
        
        if GOOGLE_CALENDAR_AVAILABLE and os.path.exists(credentials_path):
            try:
                self.service = self._get_calendar_service()
                self.use_google_calendar = True
                print("✅ Google Calendar connected!")
            except Exception as e:
                print(f"⚠️  Google Calendar connection failed: {e}")
                print("📅 Using .ics file fallback mode")
    
    def _get_calendar_service(self):
        """Authenticate and return Google Calendar service"""
        creds = None
        
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        return build('calendar', 'v3', credentials=creds)
    
    def create_appointment(self,
                          title: str,
                          start_datetime: datetime,
                          end_datetime: datetime,
                          description: str = "",
                          location: str = "",
                          attendees: Optional[List[str]] = None,
                          add_zoom_link: bool = True) -> Dict[str, Any]:
        """
        Create calendar appointment
        
        Returns:
            {
                "success": bool,
                "event_id": str,
                "calendar_link": str,
                "ics_file": str (if Google Calendar unavailable),
                "zoom_link": str (if requested)
            }
        """
        
        # Generate Zoom link (mock for demo)
        zoom_link = ""
        if add_zoom_link:
            meeting_id = str(hash(start_datetime.isoformat()))[-10:]
            zoom_link = f"https://fau.zoom.us/j/{meeting_id}"
            description += f"\n\nZoom Link: {zoom_link}"
        
        # Try Google Calendar first
        if self.use_google_calendar and self.service:
            try:
                result = self._create_google_calendar_event(
                    title, start_datetime, end_datetime, 
                    description, location, attendees, zoom_link
                )
                return result
            except Exception as e:
                print(f"❌ Google Calendar failed: {e}")
                print("📅 Falling back to .ics file")
        
        # Fallback: Create .ics file
        return self._create_ics_file(
            title, start_datetime, end_datetime,
            description, location, attendees, zoom_link
        )
    
    def _create_google_calendar_event(self, title, start_dt, end_dt, 
                                     description, location, attendees, zoom_link):
        """Create event in Google Calendar"""
        
        event = {
            'summary': title,
            'location': location,
            'description': description,
            'start': {
                'dateTime': start_dt.isoformat(),
                'timeZone': 'America/New_York',
            },
            'end': {
                'dateTime': end_dt.isoformat(),
                'timeZone': 'America/New_York',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 30},
                ],
            },
        }
        
        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]
        
        created_event = self.service.events().insert(
            calendarId='primary',
            body=event
        ).execute()
        
        return {
            "success": True,
            "event_id": created_event['id'],
            "calendar_link": created_event.get('htmlLink', ''),
            "zoom_link": zoom_link,
            "ics_file": None,
            "method": "google_calendar"
        }
    
    def _create_ics_file(self, title, start_dt, end_dt, 
                        description, location, attendees, zoom_link):
        """Create .ics calendar file (fallback method)"""
        
        cal = Calendar()
        event = ICSEvent()
        event.name = title
        event.begin = start_dt
        event.end = end_dt
        event.description = description
        event.location = location if not zoom_link else f"Online: {zoom_link}"
        
        cal.events.add(event)
        
        filename = f"appointment_{start_dt.strftime('%Y%m%d_%H%M')}.ics"
        filepath = os.path.join(tempfile.gettempdir(), filename)
        
        with open(filepath, 'w') as f:
            f.writelines(cal)
        
        return {
            "success": True,
            "event_id": f"local_{hash(start_dt)}",
            "calendar_link": None,
            "zoom_link": zoom_link,
            "ics_file": filepath,
            "method": "ics_file"
        }
    
    def check_availability(self, date: str, duration_minutes: int = 30) -> List[Dict]:
        """Check available time slots for a given date"""
        
        if self.use_google_calendar and self.service:
            try:
                return self._check_google_calendar_availability(date, duration_minutes)
            except Exception as e:
                print(f"⚠️  Error checking Google Calendar: {e}")
        
        return self._get_mock_availability(date, duration_minutes)
    
    def _get_mock_availability(self, date: str, duration_minutes: int):
        """Return mock availability (for demo)"""
        
        target_date = datetime.strptime(date, "%Y-%m-%d")
        
        times = [
            "9:00 AM", "9:30 AM", "10:00 AM", "10:30 AM", "11:00 AM",
            "1:00 PM", "1:30 PM", "2:00 PM", "2:30 PM", "3:00 PM",
            "3:30 PM", "4:00 PM", "4:30 PM"
        ]
        
        import random
        random.seed(hash(date))
        
        slots = []
        for time_str in times:
            time_obj = datetime.strptime(f"{date} {time_str}", "%Y-%m-%d %I:%M %p")
            slots.append({
                "time": time_str,
                "datetime": time_obj.isoformat(),
                "duration": duration_minutes,
                "available": random.random() > 0.3
            })
        
        return [slot for slot in slots if slot["available"]]


def book_appointment_with_calendar(
    student: Dict[str, Any],
    advisor: Dict[str, Any],
    date: str,
    time: str,
    meeting_type: str = "Advising Appointment",
    reason: str = "",
    duration_minutes: int = 30,
    add_zoom: bool = True
) -> Dict[str, Any]:
    """Complete appointment booking with calendar integration"""
    
    datetime_str = f"{date} {time}"
    start_dt = datetime.strptime(datetime_str, "%Y-%m-%d %I:%M %p")
    end_dt = start_dt + timedelta(minutes=duration_minutes)
    
    title = f"{meeting_type}: {student.get('first_name')} {student.get('last_name')}"
    description = f"""
    Student: {student.get('first_name')} {student.get('last_name')}
    Z-Number: {student.get('znumber')}
    Email: {student.get('email')}
    Major: {student.get('major', 'N/A')}
    
    Advisor: {advisor.get('name', 'TBD')}
    Email: {advisor.get('email', '')}
    
    Reason: {reason or 'General advising'}
    
    ---
    Scheduled via FAU Smart Academic Assistant
    """
    
    calendar = CalendarIntegration()
    
    result = calendar.create_appointment(
        title=title,
        start_datetime=start_dt,
        end_datetime=end_dt,
        description=description,
        location="Advisor Office" if not add_zoom else "Online",
        attendees=[student.get('email', ''), advisor.get('email', '')],
        add_zoom_link=add_zoom
    )
    
    appointment = {
        "id": result.get("event_id"),
        "student": student,
        "advisor": advisor,
        "date": date,
        "time": time,
        "start_datetime": start_dt.isoformat(),
        "end_datetime": end_dt.isoformat(),
        "meeting_type": meeting_type,
        "reason": reason,
        "duration_minutes": duration_minutes,
        "zoom_link": result.get("zoom_link"),
        "calendar_link": result.get("calendar_link"),
        "ics_file": result.get("ics_file"),
        "status": "confirmed",
        "method": result.get("method"),
        "created_at": datetime.now().isoformat()
    }
    
    return appointment