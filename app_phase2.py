"""
FAU Smart Academic Assistant - PHASE 2 COMPLETE
Features: Auto-fill, Email, Voice, Calendar, Multi-language, Analytics
"""
import streamlit as st
import os
import json
from datetime import date, datetime, timedelta
from database import (
    init_database, get_student, check_student_login, check_admin_login,
    save_submission, get_db_connection
)
from autofill_agent import auto_fill_form
from email_automation import EmailAutomation, generate_email_preview
from voice_agent_complete import process_voice_command, AppointmentScheduler
from calendar_integration import CalendarIntegration, book_appointment_with_calendar
from dotenv import load_dotenv
import plotly.express as px
import pandas as pd

# Load environment variables
load_dotenv()

# Initialize database
if not os.path.exists("database/fau_streamlit.db"):
    init_database()

# Page config
st.set_page_config(
    page_title="FAU Smart Academic Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session state
if "role" not in st.session_state:
    st.session_state["role"] = None
if "znumber" not in st.session_state:
    st.session_state["znumber"] = None
if "form_data" not in st.session_state:
    st.session_state["form_data"] = {}
if "validation" not in st.session_state:
    st.session_state["validation"] = {}
if "language" not in st.session_state:
    st.session_state["language"] = "en"
if "email_config" not in st.session_state:
    st.session_state["email_config"] = {
        "address": os.getenv("GMAIL_ADDRESS", ""),
        "password": os.getenv("GMAIL_APP_PASSWORD", "")
    }
if "appointments" not in st.session_state:
    st.session_state["appointments"] = []

# Load language
LANG_DIR = "lang"
os.makedirs(LANG_DIR, exist_ok=True)

# Create default English lang file if not exists
if not os.path.exists(f"{LANG_DIR}/en.json"):
    default_lang = {
        "app_title": "FAU Smart Academic Assistant",
        "student_login": "Student Login",
        "admin_login": "Admin Login",
        "znumber": "Z-Number",
        "password": "Password",
        "logout": "Logout",
        "forms": "Forms",
        "voice_agent": "Voice Agent",
        "reminders": "Reminders",
        "submit_form": "Submit Form"
    }
    with open(f"{LANG_DIR}/en.json", "w") as f:
        json.dump(default_lang, f)

# Load current language
try:
    with open(f"{LANG_DIR}/{st.session_state['language']}.json", "r", encoding="utf-8") as f:
        L = json.load(f)
except:
    L = {}

def get_text(key, default=None):
    """Get translated text with fallback"""
    return L.get(key, default or key)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #003366 0%, #0066cc 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .confidence-high { border-left: 4px solid #28a745; padding: 10px; background: #d4edda; }
    .confidence-medium { border-left: 4px solid #ffc107; padding: 10px; background: #fff3cd; }
    .confidence-low { border-left: 4px solid #dc3545; padding: 10px; background: #f8d7da; }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# LOGIN PAGE
# ============================================================
if st.session_state["role"] is None:
    
    # Language selector at top
    col1, col2, col3 = st.columns([2, 1, 1])
    with col3:
        languages = {"English": "en", "Español": "es"}
        selected_lang = st.selectbox("🌍 Language", list(languages.keys()), key="login_lang_selector")
        if languages[selected_lang] != st.session_state["language"]:
            st.session_state["language"] = languages[selected_lang]
            st.rerun()
    
    st.markdown('<div class="main-header"><h1>🎓 FAU Smart Academic Assistant</h1><p>Intelligent Form Auto-Fill with AI, Voice, and Email Automation</p></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"👨‍🎓 {get_text('student_login', 'Student Login')}")
        znumber = st.text_input(get_text("znumber", "Z-Number"), placeholder="Z1000001", key="login_student_z")
        password = st.text_input(get_text("password", "Password"), type="password", placeholder="password123", key="login_student_pw")
        
        if st.button(get_text("student_login", "Login as Student"), type="primary", use_container_width=True):
            if check_student_login(znumber, password):
                st.session_state["role"] = "student"
                st.session_state["znumber"] = znumber
                st.success("✅ Login successful!")
                st.rerun()
            else:
                st.error("❌ Invalid credentials")
        
        with st.expander("📚 Demo Accounts"):
            st.markdown("""
            **Test Accounts:**
            - `Z1000001` / `password123` - John (Senior, ready to graduate)
            - `Z1000002` / `password123` - Emily (Junior)
            - `Z1000003` / `password123` - Michael (Senior)
            - `Z1000004` / `password123` - Sarah (Sophomore, low GPA)
            """)
    
    with col2:
        st.subheader(f"👨‍💼 {get_text('admin_login', 'Admin Login')}")
        admin_user = st.text_input("Username", placeholder="admin", key="login_admin_u")
        admin_pass = st.text_input(get_text("password", "Password"), type="password", placeholder="admin123", key="login_admin_p")
        
        if st.button(get_text("admin_login", "Login as Admin"), use_container_width=True):
            if check_admin_login(admin_user, admin_pass):
                st.session_state["role"] = "admin"
                st.success("✅ Admin login successful!")
                st.rerun()
            else:
                st.error("❌ Invalid credentials")
        
        st.info("**Admin:** `admin` / `admin123`")

# ============================================================
# STUDENT DASHBOARD
# ============================================================
elif st.session_state["role"] == "student":
    student = get_student(st.session_state["znumber"])
    
    if not student:
        st.error("❌ Student not found")
        st.stop()
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 👤 Profile")
        st.write(f"**{student['first_name']} {student['last_name']}**")
        st.write(f"📧 {student['email']}")
        st.write(f"🎓 {student['major']}")
        st.write(f"📊 GPA: {student['gpa']:.2f}")
        st.write(f"📚 Credits: {student['total_credits']}")
        
        st.markdown("---")
        
        # Language selector
        languages = {"English": "en", "Español": "es"}
        current_lang_name = [k for k, v in languages.items() if v == st.session_state["language"]][0]
        selected_lang = st.selectbox("🌍 Language", list(languages.keys()), index=list(languages.keys()).index(current_lang_name), key="sidebar_lang_selector")
        if languages[selected_lang] != st.session_state["language"]:
            st.session_state["language"] = languages[selected_lang]
            st.rerun()
        
        st.markdown("---")
        
        if st.button(f"🚪 {get_text('logout', 'Logout')}", use_container_width=True):
            st.session_state["role"] = None
            st.session_state["znumber"] = None
            st.rerun()
    
    # Header
    st.markdown(f'<div class="main-header"><h2>Welcome, {student["first_name"]} {student["last_name"]}!</h2><p>{student["major"]} | GPA: {student["gpa"]:.2f} | Credits: {student["total_credits"]}</p></div>', unsafe_allow_html=True)
    
    # Main tabs
    tabs = st.tabs([
        f"📝 {get_text('forms', 'Forms')}", 
        f"🎤 {get_text('voice_agent', 'Voice Agent')}", 
        f"📧 Email", 
        f"📅 Calendar"
    ])
    
    # ========== TAB 1: FORMS ==========
    with tabs[0]:
        st.markdown("## 📝 Smart Academic Forms")
        
        form_type = st.selectbox(
            "Select a form:",
            ["Graduation Application", "Change of Major", "Course Override"],
            key="form_type_selector"
        )
        
        st.markdown("---")
        
        col_form, col_ai = st.columns([2, 1])
        
        with col_ai:
            st.markdown("### 🤖 AI Assistant")
            
            # Auto-fill button
            auto_fill_clicked = False
            
            if form_type == "Graduation Application":
                if st.button("✨ Auto-Fill Form", type="primary", use_container_width=True):
                    auto_fill_clicked = True
            
            elif form_type == "Change of Major":
                new_major_input = st.text_input("New Major (optional)", key="new_major_input_autofill")
                if st.button("✨ Auto-Fill Form", type="primary", use_container_width=True, key="autofill_change_major"):
                    auto_fill_clicked = True
            
            elif form_type == "Course Override":
                course_code_input = st.text_input("Course Code*", key="course_code_input_autofill")
                reason_type_input = st.selectbox("Reason", ["prerequisite", "time_conflict", "course_full", "graduation_requirement"], key="reason_type_input_autofill")
                if st.button("✨ Auto-Fill Form", type="primary", use_container_width=True, key="autofill_course_override"):
                    if course_code_input:
                        auto_fill_clicked = True
                    else:
                        st.error("Please enter course code")
            
            if auto_fill_clicked:
                with st.spinner("🤖 Analyzing your record..."):
                    kwargs = {}
                    if form_type == "Change of Major" and new_major_input:
                        kwargs["new_major"] = new_major_input
                    elif form_type == "Course Override":
                        kwargs["course_code"] = course_code_input
                        kwargs["reason_type"] = reason_type_input
                    
                    filled_data, validation = auto_fill_form(st.session_state["znumber"], form_type, **kwargs)
                    st.session_state["form_data"] = filled_data
                    st.session_state["validation"] = validation
                    st.success(f"✅ Form filled with {int(filled_data.get('overall_confidence', 0)*100)}% confidence!")
                    st.rerun()
            
            # Show confidence
            if st.session_state["form_data"]:
                st.markdown("---")
                confidence = st.session_state["form_data"].get("overall_confidence", 0)
                st.markdown(f"### 📊 Confidence: {int(confidence*100)}%")
                st.progress(confidence)
                
                if confidence >= 0.9:
                    st.success("🟢 High confidence")
                elif confidence >= 0.7:
                    st.warning("🟡 Medium confidence")
                else:
                    st.error("🔴 Low confidence")
            
            # Validation results
            if st.session_state["validation"]:
                st.markdown("---")
                st.markdown("### ✅ Validation")
                validation = st.session_state["validation"]
                
                for error in validation.get("errors", []):
                    st.error(error)
                for warning in validation.get("warnings", []):
                    st.warning(warning)
                for rec in validation.get("recommendations", []):
                    st.info(rec)
        
        with col_form:
            st.markdown(f"### {form_type}")
            
            data = st.session_state.get("form_data", {})
            
            # Form fields
            if form_type == "Graduation Application":
                term = st.text_input("Graduation Term*", value=data.get("term", ""), key="grad_term")
                catalog_year = st.text_input("Catalog Year*", value=data.get("catalog_year", student["catalog_year"]), key="grad_catalog_year")
                st.checkbox("I confirm requirements", value=data.get("catalog_year_ok", False), key="grad_confirm_reqs")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("GPA", data.get("current_gpa", student["gpa"]))
                with col2:
                    st.metric("Credits", data.get("total_credits", student["total_credits"]))
                
                signature = st.text_input("Sign (full name)*", value=data.get("student_signature", ""), key="grad_signature")
            
            elif form_type == "Change of Major":
                st.text_input("Current Major", value=data.get("current_major", student["major"]), disabled=True, key="change_major_current")
                new_major = st.text_input("New Major*", value=data.get("new_major", ""), key="change_major_new")
                effective_term = st.text_input("Effective Term*", value=data.get("effective_term", ""), key="change_major_effective_term")
                reason = st.text_area("Reason*", value=data.get("reason", ""), height=150, key="change_major_reason")
            
            elif form_type == "Course Override":
                col1, col2 = st.columns(2)
                with col1:
                    course_code = st.text_input("Course Code*", value=data.get("course_code", ""), key="course_override_code")
                with col2:
                    section = st.text_input("Section", value=data.get("section", "001"), key="course_override_section")
                
                course_title = st.text_input("Course Title", value=data.get("course_title", ""), disabled=True, key="course_override_title")
                semester = st.text_input("Semester*", value=data.get("semester", ""), key="course_override_semester")
                reason = st.text_area("Reason*", value=data.get("reason", ""), height=200, key="course_override_reason")
            
            # Submit button
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📤 Submit", type="primary", use_container_width=True, key="form_submit_button"):
                    if st.session_state.get("validation", {}).get("is_valid"):
                        save_submission(
                            st.session_state["znumber"],
                            form_type,
                            st.session_state["form_data"],
                            auto_filled=True,
                            confidence_score=st.session_state["form_data"].get("overall_confidence", 0)
                        )
                        st.success("✅ Submitted!")
                        st.balloons()
                    else:
                        st.error("❌ Fix errors first")
            
            with col2:
                if st.button("🔄 Clear", use_container_width=True, key="form_clear_button"):
                    st.session_state["form_data"] = {}
                    st.session_state["validation"] = {}
                    st.rerun()
    
    # ========== TAB 2: VOICE AGENT ==========
    with tabs[1]:
        st.markdown("## 🎤 Voice Assistant")
        st.markdown("Say things like: *'Book an appointment with my advisor next Tuesday at 2pm'*")
        
        uploaded_audio = st.file_uploader("Upload audio (wav/mp3/m4a)", type=["wav", "mp3", "m4a"])
        
        st.markdown("---")
        st.markdown("### Or use your microphone in real-time:")
        
        if st.button("🎙️ Start Listening (Mic Click)", type="primary", use_container_width=True, key="process_mic_command_button"):
            with st.spinner("🎧 Listening for your command..."):
                result = process_voice_command(language="en-US", student_znumber=st.session_state["znumber"])
                
                st.session_state["last_voice_result"] = result # Store result in session state
                st.rerun() # Rerun to display results
        
        if uploaded_audio:
            with st.spinner("🎧 Processing uploaded audio..."):
                result = process_voice_command(uploaded_audio, "en-US", st.session_state["znumber"])
                st.session_state["last_voice_result"] = result
                st.rerun()

        if "last_voice_result" in st.session_state and st.session_state["last_voice_result"]:
            result = st.session_state["last_voice_result"]
            st.markdown("### 📝 Transcription")
            st.info(result["transcription"])
            
            st.markdown("### 💬 AI Response")
            st.success(result["response"])
            
            if result.get("audio_response_path"):
                st.audio(result["audio_response_path"], key="audio_response_player")
            
            # If appointment intent, show calendar
            if result.get("action") == "show_calendar":
                st.markdown("### 📅 Available Slots")
                entities = result.get("entities", {})
                if entities.get("preferred_date"):
                    calendar = CalendarIntegration()
                    slots = calendar.check_availability(entities["preferred_date"])
                    
                    if slots:
                        st.write(f"Available slots for {entities['preferred_date']}:")
                        for i, slot in enumerate(slots[:5]):
                            if st.button(f"📍 {slot['time']} with {slot['advisor']}", key=f"slot_{slot['time']}_{i}"):
                                appt = book_appointment_with_calendar(
                                    student=student,
                                    advisor={"name": slot["advisor"], "email": "advisor@fau.edu"}, # Placeholder email
                                    date=entities["preferred_date"],
                                    time=slot["time"],
                                    reason=entities.get("reason", "Advising meeting")
                                )
                                st.session_state["appointments"].append(appt) # Add to session state
                                st.success(f"✅ Appointment booked for {appt['date']} at {appt['time']} with {appt['advisor']['name']}!")
                                if appt.get("zoom_link"):
                                    st.info(f"🔗 Zoom: {appt['zoom_link']}")
                                del st.session_state["last_voice_result"] # Clear result after booking
                                st.rerun()
                    else:
                        st.info(f"No available slots found for {entities['preferred_date']}.")
            elif result.get("action") == "fill_form":
                st.info(f"Redirecting to forms to help you with {result['entities'].get('form_type', 'a form')}.")
                # In a real app, you might programmatically switch tabs here
            
            st.markdown("---")
            if st.button("Clear Voice Result", key="clear_voice_result_button"):
                del st.session_state["last_voice_result"]
                st.rerun()
    
    # ========== TAB 3: EMAIL ==========
    with tabs[2]:
        st.markdown("## 📧 AI-Powered Email Generation")
        
        if st.session_state["form_data"]:
            st.success("✅ Form data ready! AI will generate your professional email.")
            
            # Generate email button
            col1, col2 = st.columns([1, 3])
            with col1:
                generate_clicked = st.button("🤖 Generate Email with AI", type="primary", use_container_width=True)
            with col2:
                st.caption("AI will write a professional email based on your form data")
            
            if generate_clicked or "generated_email" in st.session_state:
                with st.spinner("🤖 AI is writing your email..."):
                    # Get OpenAI API key
                    api_key = st.session_state.get("email_config", {}).get("openai_key") or os.getenv("OPENAI_API_KEY")
                    
                    # Generate email
                    email_data = generate_email_preview(
                        form_type,
                        student,
                        st.session_state["form_data"],
                        api_key=api_key
                    )
                    
                    st.session_state["generated_email"] = email_data
                
                email_data = st.session_state["generated_email"]
                
                # Show generation method
                if email_data.get("generated_by") == "AI":
                    st.success("🤖 **AI-Generated Email** - Personalized and professional!")
                else:
                    st.info("📝 **Template-Based Email** - Add OpenAI API key for AI generation")
                
                st.markdown("---")
                
                # Email details (editable)
                st.markdown("### ✉️ Email Details")
                
                subject = st.text_input(
                    "Subject:", 
                    value=email_data["subject"], 
                    key="email_subject_edit",
                    help="You can edit the subject if needed"
                )
                
                col_to, col_cc = st.columns(2)
                with col_to:
                    to_email = st.text_input("To:", value=email_data["recipients"]["to"], key="email_to_edit")
                with col_cc:
                    cc_emails = st.text_input("CC:", value=", ".join(email_data["recipients"]["cc"]), key="email_cc_edit")
                
                st.markdown("---")
                
                # Email preview
                st.markdown("### 👁️ Email Preview")
                
                # Render HTML preview
                st.components.v1.html(email_data["html_body"], height=500, scrolling=True)
                
                st.markdown("---")
                
                # Email settings
                with st.expander("⚙️ Email Settings"):
                    st.markdown("##### Gmail Configuration (for real sending)")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        gmail_address = st.text_input(
                            "Gmail Address", 
                            value=st.session_state.get("email_config", {}).get("address", ""),
                            key="gmail_addr"
                        )
                    with col2:
                        gmail_password = st.text_input(
                            "App Password", 
                            type="password",
                            value=st.session_state.get("email_config", {}).get("password", ""),
                            key="gmail_pass",
                            help="16-character app password from Google"
                        )
                    
                    st.markdown("##### OpenAI Configuration (for AI generation)")
                    openai_key = st.text_input(
                        "OpenAI API Key (optional)", 
                        type="password",
                        value=st.session_state.get("email_config", {}).get("openai_key", ""),
                        key="openai_key_input",
                        help="Required for AI-generated emails"
                    )
                    
                    if st.button("💾 Save Configuration", key="save_email_config_button"):
                        st.session_state["email_config"] = {
                            "address": gmail_address,
                            "password": gmail_password,
                            "openai_key": openai_key
                        }
                        st.success("✅ Configuration saved!")
                
                st.markdown("---")
                
                # Send options
                st.markdown("### 📤 Send Options")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    send_mode = st.radio(
                        "Mode:",
                        ["Demo (Preview Only)", "Real Email"],
                        key="email_send_mode_radio",
                        help="Choose Demo to see the email without sending"
                    )
                
                with col2:
                    if st.button("📤 Send Email", type="primary", use_container_width=True, key="send_email_button"):
                        if send_mode == "Real Email":
                            if gmail_address and gmail_password:
                                try:
                                    email_sender = EmailAutomation(gmail_address, gmail_password)
                                    success, msg = email_sender.send_email(
                                        to_email=to_email,
                                        subject=subject,
                                        body=email_data["html_body"],
                                        cc=cc_emails.split(",") if cc_emails else []
                                    )
                                    if success:
                                        st.success("✅ Email sent successfully!")
                                        st.balloons()
                                    else:
                                        st.error(msg)
                                except Exception as e:
                                    st.error(f"❌ Error: {str(e)}")
                            else:
                                st.warning("⚠️ Please configure Gmail settings first!")
                        else:
                            st.info("✅ Email preview ready! Switch to 'Real Email' mode to send.")
                
                with col3:
                    if st.button("🔄 Regenerate", use_container_width=True, key="regenerate_email_button"):
                        if "generated_email" in st.session_state:
                            del st.session_state["generated_email"]
                        st.rerun()
        
        else:
            st.info("👈 **First, fill out a form using the Forms tab, then come back here to generate the email!**")
            
            st.markdown("---")
            st.markdown("### 🤖 How AI Email Generation Works")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                **With OpenAI API Key:**
                1. ✨ AI analyzes your form data
                2. 📝 Writes personalized, professional email
                3. 🎨 Formats in beautiful HTML
                4. 📧 Ready to send!
                """)
            
            with col2:
                st.markdown("""
                **Without API Key:**
                1. 📋 Uses professional templates
                2. ✏️ Fills in your information
                3. 🎨 Formatted professionally
                4. 📧 Still looks great!
                """)
            
            st.markdown("---")
            st.info("💡 **Tip:** Add your OpenAI API key in Email Settings for AI-powered generation!")
    
    # ========== TAB 4: CALENDAR ==========
    with tabs[3]:
        st.markdown("## 📅 My Appointments")
        
        if len(st.session_state["appointments"]) == 0:
            st.info("No appointments yet. Use Voice Agent to book one!")
        else:
            for appt in st.session_state["appointments"]:
                with st.expander(f"📍 {appt['date']} at {appt['time']}"):
                    st.write(f"**Type:** {appt['meeting_type']}")
                    st.write(f"**With:** {appt['advisor']['name']}")
                    st.write(f"**Reason:** {appt.get('reason', 'N/A')}")
                    if appt.get('zoom_link'):
                        st.write(f"**Zoom:** {appt['zoom_link']}")

# ============================================================
# ADMIN DASHBOARD
# ============================================================
elif st.session_state["role"] == "admin":
    st.title("👨‍💼 Admin Dashboard")
    
    with st.sidebar:
        if st.button("🚪 Logout", use_container_width=True, key="admin_logout_button"):
            st.session_state["role"] = None
            st.rerun()
    
    # Metrics
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM students")
    total_students = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM submissions")
    total_submissions = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM submissions WHERE auto_filled=1")
    auto_filled = c.fetchone()[0]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Students", total_students)
    col2.metric("Total Submissions", total_submissions)
    col3.metric("Auto-Filled", auto_filled)
    
    # Analytics
    st.markdown("### 📊 Analytics")
    
    c.execute("""
        SELECT form_name, COUNT(*) as count 
        FROM submissions 
        GROUP BY form_name
    """)
    form_data = c.fetchall()
    
    if form_data:
        df = pd.DataFrame(form_data, columns=["Form", "Count"])
        fig = px.bar(df, x="Form", y="Count", title="Forms by Type")
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent submissions
    st.markdown("### 📋 Recent Submissions")
    
    c.execute("""
        SELECT s.id, s.znumber, st.first_name, st.last_name, 
               s.form_name, s.date, s.auto_filled, s.confidence_score
        FROM submissions s
        JOIN students st ON s.znumber = st.znumber
        ORDER BY s.date DESC
        LIMIT 10
    """)
    
    rows = c.fetchall()
    conn.close()
    
    for row in rows:
        col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
        col1.write(f"**#{row[0]}**")
        col2.write(f"{row[2]} {row[3]}")
        col3.write(f"{row[4]} - {row[5]}")
        if row[6]:
            col4.success(f"🤖 {int(row[7]*100)}%")
        else:
            col4.info("✍️ Manual")

st.markdown("---")
st.caption("🎓 FAU Smart Academic Assistant | Phase 2 Complete | Powered by AI")
