"""
AI-Powered Email Automation System for FAU Smart Academic Assistant
Uses OpenAI to generate professional, personalized emails automatically
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import os
from typing import Dict, Any, Optional, List
import streamlit.components.v1 as components

# OpenAI for AI email generation
try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI not installed. Using template-based emails.")


class EmailAutomation:
    """Handle email sending with Gmail SMTP"""
    
    def __init__(self, gmail_address: str, gmail_app_password: str):
        self.gmail_address = gmail_address
        self.gmail_app_password = gmail_app_password
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        
    def send_email(self, 
                   to_email: str,
                   subject: str,
                   body: str,
                   cc: Optional[List[str]] = None,
                   bcc: Optional[List[str]] = None,
                   attachments: Optional[List[str]] = None) -> tuple[bool, str]:
        """Send email via Gmail SMTP"""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.gmail_address
            msg['To'] = to_email
            msg['Subject'] = subject
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            if bcc:
                msg['Bcc'] = ', '.join(bcc)
            
            text_part = MIMEText(self._html_to_text(body), 'plain')
            html_part = MIMEText(body, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename={os.path.basename(file_path)}'
                            )
                            msg.attach(part)
            
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.gmail_address, self.gmail_app_password)
                
                recipients = [to_email]
                if cc:
                    recipients.extend(cc)
                if bcc:
                    recipients.extend(bcc)
                
                server.sendmail(self.gmail_address, recipients, msg.as_string())
            
            return True, "✅ Email sent successfully!"
        
        except smtplib.SMTPAuthenticationError:
            return False, "❌ Authentication failed. Check your Gmail app password."
        except Exception as e:
            return False, f"❌ Error: {str(e)}"
    
    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text"""
        import re
        text = re.sub('<[^<]+?>', '', html)
        text = re.sub(r'\s+', ' ', text).strip()
        return text


class AIEmailGenerator:
    """AI-powered email content generator using OpenAI"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if self.api_key and OPENAI_AVAILABLE:
            self.client = OpenAI(api_key=self.api_key)
            self.use_ai = True
        else:
            self.use_ai = False
            print("⚠️ OpenAI API key not found. Using template-based emails.")
    
    def generate_email_content(self, form_type: str, student: Dict[str, Any], 
                              form_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate email subject and body using AI"""
        
        if self.use_ai:
            try:
                return self._generate_with_ai(form_type, student, form_data)
            except Exception as e:
                print(f"⚠️ AI generation failed: {e}. Using template.")
                return self._generate_with_template(form_type, student, form_data)
        else:
            return self._generate_with_template(form_type, student, form_data)
    
    def _generate_with_ai(self, form_type: str, student: Dict[str, Any], 
                         form_data: Dict[str, Any]) -> Dict[str, str]:
        """Use OpenAI to generate professional email"""
        
        # Create context for AI
        if form_type == "Graduation Application":
            prompt = f"""Write a professional email for a graduation application with the following details:

Student Information:
- Name: {student['first_name']} {student['last_name']}
- Z-Number: {student['znumber']}
- Major: {student['major']}
- Email: {student['email']}
- Current GPA: {form_data.get('current_gpa', 'N/A')}
- Total Credits: {form_data.get('total_credits', 'N/A')}
- Expected Credits at Graduation: {form_data.get('expected_credits_at_graduation', 'N/A')}

Graduation Details:
- Intended Graduation Term: {form_data.get('term', 'N/A')}
- Catalog Year: {form_data.get('catalog_year', 'N/A')}
- Advisor: {student.get('advisor_name', 'N/A')}

Write a formal email to the Registrar's Office requesting approval for graduation. The email should:
1. Be professional and concise
2. Include all relevant information in a clear format
3. Express confidence in meeting all requirements
4. Request confirmation of next steps

Format as plain text only, no HTML. Start with "Dear Registrar's Office," and end with the student's signature."""

        elif form_type == "Change of Major":
            prompt = f"""Write a professional email for a change of major request with the following details:

Student Information:
- Name: {student['first_name']} {student['last_name']}
- Z-Number: {student['znumber']}
- Email: {student['email']}
- Current GPA: {form_data.get('current_gpa', 'N/A')}
- Credits Completed: {form_data.get('credits_completed', 'N/A')}

Change Details:
- Current Major: {form_data.get('current_major', 'N/A')}
- Requested New Major: {form_data.get('new_major', 'N/A')}
- Effective Term: {form_data.get('effective_term', 'N/A')}
- Reason: {form_data.get('reason', 'N/A')}
- Advisor: {student.get('advisor_name', 'N/A')}

Write a formal email to the Academic Advising Office requesting a change of major. The email should:
1. Clearly state the current and desired major
2. Explain the reason for the change professionally
3. Show commitment to the new path
4. Request information about next steps

Format as plain text only, no HTML. Start with "Dear Academic Advising Office," and end with the student's signature."""

        else:  # Course Override
            prompt = f"""Write a professional email for a course override request with the following details:

Student Information:
- Name: {student['first_name']} {student['last_name']}
- Z-Number: {student['znumber']}
- Major: {student['major']}
- Classification: {form_data.get('classification', 'N/A')}
- Current GPA: {form_data.get('current_gpa', 'N/A')}

Course Details:
- Course Code: {form_data.get('course_code', 'N/A')}
- Course Title: {form_data.get('course_title', 'N/A')}
- Section: {form_data.get('section', 'N/A')}
- Semester: {form_data.get('semester', 'N/A')}
- Reason Type: {form_data.get('reason_type', 'N/A').replace('_', ' ')}

Justification:
{form_data.get('reason', 'N/A')}

Write a formal email to the instructor/department requesting a course override. The email should:
1. Clearly identify the course
2. Explain the reason for the override request
3. Show commitment to success in the course
4. Be respectful and professional

Format as plain text only, no HTML. Start with "Dear Instructor/Department Chair," and end with the student's signature."""

        # Call OpenAI API
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional academic email writer. Write clear, concise, and formal emails for university administrative purposes."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        email_body = response.choices[0].message.content.strip()
        
        # Generate subject
        subject_prompt = f"Generate a professional email subject line for a {form_type} from {student['first_name']} {student['last_name']} ({student['znumber']}). Keep it concise and formal. Return ONLY the subject line, nothing else."
        
        subject_response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You generate concise email subject lines."},
                {"role": "user", "content": subject_prompt}
            ],
            temperature=0.5,
            max_tokens=50
        )
        
        subject = subject_response.choices[0].message.content.strip()
        
        # Convert plain text to HTML
        html_body = self._text_to_html(email_body, form_type, student, form_data)
        
        return {
            "subject": subject,
            "plain_body": email_body,
            "html_body": html_body
        }
    
    def _text_to_html(self, text: str, form_type: str, student: Dict, form_data: Dict) -> str:
        """Convert AI-generated plain text to beautiful HTML"""
        
        # Split into paragraphs
        paragraphs = text.split('\n\n')
        html_paragraphs = ''.join([f'<p style="margin: 15px 0; line-height: 1.6;">{p.strip()}</p>' for p in paragraphs if p.strip()])
        
        # Get confidence badge
        confidence = int(form_data.get('overall_confidence', 0) * 100)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    background-color: #f5f5f5;
                }}
                .email-container {{
                    background-color: white;
                    margin: 20px;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #003366 0%, #0066cc 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                }}
                .header h2 {{
                    margin: 10px 0 0 0;
                    font-size: 18px;
                    font-weight: normal;
                    opacity: 0.9;
                }}
                .content {{
                    padding: 40px;
                    background-color: white;
                }}
                .ai-badge {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 8px 16px;
                    border-radius: 20px;
                    display: inline-block;
                    font-size: 13px;
                    margin-bottom: 20px;
                    font-weight: 600;
                }}
                .footer {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    font-size: 13px;
                    color: #666;
                    border-top: 1px solid #e0e0e0;
                }}
                .badge {{
                    display: inline-block;
                    padding: 4px 10px;
                    background-color: #28a745;
                    color: white;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: 600;
                    margin: 0 5px;
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <h1>🎓 Florida Atlantic University</h1>
                    <h2>{form_type}</h2>
                </div>
                
                <div class="content">
                    <div class="ai-badge">
                        🤖 AI-Generated Email
                    </div>
                    
                    {html_paragraphs}
                </div>
                
                <div class="footer">
                    <p style="margin: 5px 0;">
                        <strong>📧 Generated by FAU Smart Academic Assistant</strong>
                    </p>
                    <p style="margin: 5px 0;">
                        🤖 AI-Powered Email Generation | 
                        <span class="badge">{confidence}% Confidence</span>
                    </p>
                    <p style="margin: 10px 0; font-size: 11px; color: #999;">
                        {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_with_template(self, form_type: str, student: Dict[str, Any], 
                                form_data: Dict[str, Any]) -> Dict[str, str]:
        """Fallback: Generate email using templates (if AI unavailable)"""
        
        if form_type == "Graduation Application":
            subject = f"Graduation Application - {student['first_name']} {student['last_name']} ({student['znumber']})"
            
            body = f"""Dear Registrar's Office,

I am writing to submit my application for graduation. Below are my details:

Student Information:
- Name: {student['first_name']} {student['last_name']}
- Z-Number: {student['znumber']}
- Major: {student['major']}
- Current GPA: {form_data.get('current_gpa', 'N/A')}
- Total Credits Completed: {form_data.get('total_credits', 'N/A')}

Graduation Details:
- Intended Graduation Term: {form_data.get('term', 'N/A')}
- Catalog Year: {form_data.get('catalog_year', 'N/A')}
- Expected Credits at Graduation: {form_data.get('expected_credits_at_graduation', 'N/A')}

I have reviewed my degree audit and believe I have met all requirements for graduation. My academic advisor, {student.get('advisor_name', 'N/A')}, has been informed of my graduation plans.

Please confirm receipt of this application and let me know if any additional documentation is required.

Thank you for your assistance.

Sincerely,
{student['first_name']} {student['last_name']}
{student['email']}
{student['znumber']}"""

        elif form_type == "Change of Major":
            subject = f"Change of Major Request - {student['first_name']} {student['last_name']}"
            
            body = f"""Dear Academic Advising Office,

I am requesting a change of major with the following details:

Current Major: {form_data.get('current_major', 'N/A')}
Requested New Major: {form_data.get('new_major', 'N/A')}
Effective Term: {form_data.get('effective_term', 'N/A')}

Student Information:
- Name: {student['first_name']} {student['last_name']}
- Z-Number: {student['znumber']}
- Current GPA: {form_data.get('current_gpa', 'N/A')}
- Credits Completed: {form_data.get('credits_completed', 'N/A')}

Reason for Change:
{form_data.get('reason', 'N/A')}

I have carefully considered this decision and am committed to succeeding in {form_data.get('new_major', 'my new major')}. Please let me know the next steps in this process.

Thank you for your consideration.

Sincerely,
{student['first_name']} {student['last_name']}
{student['email']}
{student['znumber']}"""

        else:  # Course Override
            subject = f"Course Override Request - {form_data.get('course_code', 'Course')} - {student['first_name']} {student['last_name']}"
            
            body = f"""Dear Instructor/Department Chair,

I am requesting a course override for:

Course: {form_data.get('course_code', 'N/A')} - {form_data.get('course_title', 'N/A')}
Section: {form_data.get('section', 'N/A')}
Semester: {form_data.get('semester', 'N/A')}

Student Information:
- Name: {student['first_name']} {student['last_name']}
- Z-Number: {student['znumber']}
- Major: {student['major']}
- Classification: {form_data.get('classification', 'N/A')}
- Current GPA: {form_data.get('current_gpa', 'N/A')}

Reason for Override:
{form_data.get('reason', 'N/A')}

I am committed to succeeding in this course and would greatly appreciate your consideration of this request. Please let me know if you need any additional information.

Thank you for your time and consideration.

Sincerely,
{student['first_name']} {student['last_name']}
{student['email']}
{student['znumber']}"""

        # Convert to HTML
        html_body = self._text_to_html(body, form_type, student, form_data)
        
        return {
            "subject": subject,
            "plain_body": body,
            "html_body": html_body
        }


# Main function to generate email
def generate_email_preview(form_type: str, student: Dict[str, Any], 
                          form_data: Dict[str, Any], 
                          api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate email using AI or templates
    
    Returns:
        {
            "subject": str,
            "html_body": str,
            "plain_body": str,
            "recipients": dict
        }
    """
    
    # Initialize AI generator
    ai_generator = AIEmailGenerator(api_key)
    
    # Generate email content
    email_content = ai_generator.generate_email_content(form_type, student, form_data)
    
    # Determine recipients
    if form_type == "Graduation Application":
        recipients = {
            "to": "registrar@fau.edu",
            "cc": [student.get('advisor_email', ''), student['email']],
            "bcc": []
        }
    elif form_type == "Change of Major":
        recipients = {
            "to": "advising@fau.edu",
            "cc": [student.get('advisor_email', ''), student['email']],
            "bcc": []
        }
    else:  # Course Override
        recipients = {
            "to": form_data.get('instructor_email', 'department@fau.edu'),
            "cc": [student.get('advisor_email', ''), student['email']],
            "bcc": []
        }
    
    return {
        "subject": email_content["subject"],
        "html_body": email_content["html_body"],
        "plain_body": email_content.get("plain_body", ""),
        "recipients": recipients,
        "generated_by": "AI" if ai_generator.use_ai else "Template"
    }


# Helper function to render HTML in Streamlit
def render_email_preview(html_content: str, height: int = 600):
    """Render HTML email preview in Streamlit"""
    components.html(html_content, height=height, scrolling=True)
