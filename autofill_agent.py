"""
Auto-Fill Agent for FAU Smart Academic Forms
Intelligently fills form fields using student data and business logic
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from database import (
    get_student, get_student_transcript, calculate_gpa, 
    get_course_info, get_db_connection
)
import os
from dotenv import load_dotenv

# OpenAI for AI text generation
try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI not installed. Using template-based text generation in autofill_agent.")

load_dotenv() # Load environment variables


class AutoFillAgent:
    """
    Intelligent form auto-fill agent
    """
    
    def __init__(self, znumber: str):
        self.znumber = znumber
        self.student = get_student(znumber)
        self.transcript = get_student_transcript(znumber)
        
        if not self.student:
            raise ValueError(f"Student {znumber} not found")
        
        # Calculate additional metrics
        self.calculated_gpa = calculate_gpa(self.transcript) if self.transcript else 0.0
        self.total_credits = sum(c["credits"] for c in self.transcript)

        self.api_key = os.getenv("OPENAI_API_KEY")
        if self.api_key and OPENAI_AVAILABLE:
            self.client = OpenAI(api_key=self.api_key)
            self.use_ai = True
        else:
            self.use_ai = False
            print("⚠️ OpenAI API key not found in autofill_agent. Using template-based text generation.")
        
    def auto_fill_graduation_application(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Auto-fill Graduation Application
        Returns: (filled_data, validation_result)
        """
        print(f"\n🤖 Auto-filling Graduation Application for {self.student['first_name']} {self.student['last_name']}")
        
        # Calculate credits including current semester (estimate 15 credits in progress)
        in_progress_credits = 15  # Assumption for current semester
        total_after_semester = self.total_credits + in_progress_credits
        
        # Determine graduation term
        graduation_term = self._calculate_graduation_term(total_after_semester)
        
        # Check requirements
        meets_credits = total_after_semester >= 120
        meets_gpa = self.calculated_gpa >= 2.0
        major_gpa = self.calculated_gpa  # Simplified - would need major-specific calculation
        meets_major_gpa = major_gpa >= 2.0
        
        # Calculate confidence scores for each field
        confidence = {
            "term": 0.95 if meets_credits else 0.70,
            "catalog_year": 1.0,  # Always accurate from database
            "current_gpa": 1.0,
            "total_credits": 1.0,
            "meets_requirements": 0.95 if (meets_credits and meets_gpa) else 0.60,
            "advisor_approved": 0.75,  # Can't be sure without confirmation
        }
        
        overall_confidence = sum(confidence.values()) / len(confidence)
        
        filled_data = {
            "term": graduation_term,
            "catalog_year": self.student["catalog_year"],
            "catalog_year_ok": True,
            "current_gpa": round(self.calculated_gpa, 2),
            "major_gpa": round(major_gpa, 2),
            "total_credits": self.total_credits,
            "credits_in_progress": in_progress_credits,
            "expected_credits_at_graduation": total_after_semester,
            "meets_credit_requirement": meets_credits,
            "meets_gpa_requirement": meets_gpa and meets_major_gpa,
            "advisor_name": self.student["advisor_name"],
            "advisor_email": self.student["advisor_email"],
            "student_signature": f"{self.student['first_name']} {self.student['last_name']}",
            "date_signed": datetime.now().strftime("%Y-%m-%d"),
            "confidence_scores": confidence,
            "overall_confidence": round(overall_confidence, 2)
        }
        
        # Validate the data
        validation = self._validate_graduation_application(filled_data)
        
        print(f"  ✓ Form filled with {int(overall_confidence*100)}% confidence")
        
        return filled_data, validation
    
    def auto_fill_change_of_major(self, new_major: Optional[str] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Auto-fill Change of Major form
        Returns: (filled_data, validation_result)
        """
        print(f"\n🤖 Auto-filling Change of Major for {self.student['first_name']} {self.student['last_name']}")
        
        current_major = self.student["major"]
        
        # If new major not specified, suggest a compatible one
        if not new_major:
            new_major = self._suggest_compatible_major(current_major)
            confidence_new_major = 0.50  # Low confidence on suggestion
        else:
            confidence_new_major = 1.0  # User specified
        
        # Check requirements for new major
        meets_requirements, requirement_details = self._check_major_requirements(new_major)
        
        # Determine effective term (next semester)
        effective_term = self._get_next_term()
        
        # Generate reason for major change
        reason = self._generate_major_change_reason(current_major, new_major)
        
        confidence = {
            "current_major": 1.0,
            "new_major": confidence_new_major,
            "effective_term": 0.95,
            "reason": 0.85,
            "meets_requirements": 0.90 if meets_requirements else 0.60,
        }
        
        overall_confidence = sum(confidence.values()) / len(confidence)
        
        filled_data = {
            "current_major": current_major,
            "new_major": new_major,
            "effective_term": effective_term,
            "reason": reason,
            "current_gpa": round(self.calculated_gpa, 2),
            "credits_completed": self.total_credits,
            "meets_entry_requirements": meets_requirements,
            "requirement_details": requirement_details,
            "advisor_approval_required": True,
            "advisor_name": self.student["advisor_name"],
            "advisor_email": self.student["advisor_email"],
            "date_submitted": datetime.now().strftime("%Y-%m-%d"),
            "confidence_scores": confidence,
            "overall_confidence": round(overall_confidence, 2)
        }
        
        validation = self._validate_change_of_major(filled_data)
        
        print(f"  ✓ Form filled with {int(overall_confidence*100)}% confidence")
        
        return filled_data, validation
    
    def auto_fill_course_override(self, course_code: str, reason_type: str = "prerequisite") -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Auto-fill Course Override form
        Returns: (filled_data, validation_result)
        """
        print(f"\n🤖 Auto-filling Course Override for {course_code}")
        
        # Get course information
        course_info = get_course_info(course_code)
        
        if not course_info:
            course_info = {
                "title": f"Course {course_code}",
                "credits": 3,
                "prerequisites": "Unknown",
                "instructor": "TBD",
                "department": "Unknown"
            }
            confidence_course_info = 0.50
        else:
            confidence_course_info = 1.0
        
        # Generate appropriate reason based on type
        reason = self._generate_override_reason(course_code, course_info, reason_type)
        
        confidence = {
            "course_code": confidence_course_info,
            "section": 0.70,  # Usually not auto-fillable
            "semester": 0.95,
            "reason": 0.85,
            "student_info": 1.0,
        }
        
        overall_confidence = sum(confidence.values()) / len(confidence)
        
        filled_data = {
            "course_code": course_code,
            "course_title": course_info["title"],
            "section": "001",  # Default section
            "semester": self._get_next_term(),
            "reason_type": reason_type,
            "reason": reason,
            "current_gpa": round(self.calculated_gpa, 2),
            "major": self.student["major"],
            "classification": self.student["classification"],
            "total_credits": self.total_credits,
            "instructor_name": course_info.get("instructor", ""),
            "student_email": self.student["email"],
            "student_phone": "",  # Not typically in database
            "date_submitted": datetime.now().strftime("%Y-%m-%d"),
            "confidence_scores": confidence,
            "overall_confidence": round(overall_confidence, 2)
        }
        
        validation = self._validate_course_override(filled_data)
        
        print(f"  ✓ Form filled with {int(overall_confidence*100)}% confidence")
        
        return filled_data, validation
    
    # ========== HELPER METHODS ==========
    
    def _calculate_graduation_term(self, expected_credits: int) -> str:
        """Calculate appropriate graduation term"""
        if expected_credits >= 120:
            # Ready to graduate next term
            return self._get_next_term()
        else:
            # Need more time
            remaining = 120 - expected_credits
            semesters_needed = (remaining // 15) + 1
            return self._get_future_term(semesters_needed)
    
    def _get_next_term(self) -> str:
        """Get next academic term"""
        now = datetime.now()
        month = now.month
        year = now.year
        
        if 1 <= month <= 4:
            return f"Summer {year}"
        elif 5 <= month <= 7:
            return f"Fall {year}"
        else:
            return f"Spring {year + 1}"
    
    def _get_future_term(self, semesters_ahead: int) -> str:
        """Get term N semesters in the future"""
        now = datetime.now()
        year = now.year
        month = now.month
        
        # Determine current term index (0=Spring, 1=Summer, 2=Fall)
        if 1 <= month <= 4:
            current_term_idx = 1  # Summer
        elif 5 <= month <= 7:
            current_term_idx = 2  # Fall
        else:
            current_term_idx = 0  # Spring of next year
            year += 1
        
        # Calculate future term
        future_term_idx = (current_term_idx + semesters_ahead) % 3
        years_to_add = (current_term_idx + semesters_ahead) // 3
        
        terms = ["Spring", "Summer", "Fall"]
        return f"{terms[future_term_idx]} {year + years_to_add}"
    
    def _suggest_compatible_major(self, current_major: str) -> str:
        """Suggest a compatible major based on current major"""
        suggestions = {
            "Computer Science": "Computer Engineering",
            "Computer Engineering": "Computer Science",
            "Mechanical Engineering": "Electrical Engineering",
            "Electrical Engineering": "Mechanical Engineering",
            "Biology": "Biochemistry",
            "Psychology": "Cognitive Science",
            "Business Administration": "Marketing",
            "Marketing": "Business Administration"
        }
        return suggestions.get(current_major, "Undeclared")
    
    def _check_major_requirements(self, major_name: str) -> Tuple[bool, str]:
        """Check if student meets requirements for new major"""
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("""
            SELECT min_gpa, min_credits FROM major_requirements WHERE major_name=?
        """, (major_name,))
        row = c.fetchone()
        conn.close()
        
        if not row:
            return False, f"Requirements for {major_name} not found in database"
        
        required_gpa, required_credits = row
        
        meets_gpa = self.calculated_gpa >= required_gpa
        meets_credits = self.total_credits >= required_credits
        
        details = []
        if not meets_gpa:
            details.append(f"GPA requirement: {required_gpa} (you have {self.calculated_gpa:.2f})")
        if not meets_credits:
            details.append(f"Credit requirement: {required_credits} (you have {self.total_credits})")
        
        meets_all = meets_gpa and meets_credits
        
        if meets_all:
            return True, "All requirements met"
        else:
            return False, "; ".join(details)
    
    def _generate_major_change_reason(self, old_major: str, new_major: str) -> str:
        """Generate appropriate reason for major change using AI or template"""
        if self.use_ai:
            try:
                prompt = f"""Generate a concise and professional reason for a student to change their major from {old_major} to {new_major}.
                The reason should highlight academic interest, career goals, and commitment to the new path.
                Student's current GPA: {self.calculated_gpa:.2f}.
                Return only the reason, no salutations or closings."""
                
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an academic advisor assistant. Generate professional and convincing reasons for major changes."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=200
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                print(f"⚠️ AI generation for major change reason failed: {e}. Using template.")
        
        return f"""After careful consideration and academic exploration, I have discovered a stronger passion and aptitude for {new_major}. My coursework in {old_major} has provided valuable foundational knowledge, and I believe transitioning to {new_major} aligns better with my career goals and academic interests. I have researched the curriculum requirements and am committed to succeeding in this new path."""
    
    def _generate_override_reason(self, course_code: str, course_info: Dict, reason_type: str) -> str:
        """Generate appropriate override justification using AI or template"""
        gpa = self.calculated_gpa
        
        if self.use_ai:
            try:
                base_prompt = f"""Generate a concise and professional reason for a course override request for course {course_code} (Title: {course_info['title']}).
                Student's current GPA: {gpa:.2f}.
                The reason type is '{reason_type.replace('_', ' ')}'.
                Return only the reason, no salutations or closings."""
                
                if reason_type == "prerequisite":
                    specific_prompt = base_prompt + " Emphasize relevant background and commitment to success despite not meeting formal prerequisites."
                elif reason_type == "time_conflict":
                    specific_prompt = base_prompt + " Explain the scheduling conflict, the course's importance for graduation, and willingness to work with the instructor."
                elif reason_type == "course_full":
                    specific_prompt = base_prompt + " State that the course is full, it's a major requirement, and express commitment to attending and completing coursework."
                elif reason_type == "graduation_requirement":
                    specific_prompt = base_prompt + " Highlight that the course is essential for degree completion and graduation timeline, with advisor support."
                else:
                    specific_prompt = base_prompt + " Provide a general professional justification."
                
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an academic advisor assistant. Generate professional and convincing reasons for course override requests."},
                        {"role": "user", "content": specific_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=250
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                print(f"⚠️ AI generation for course override reason failed: {e}. Using template.")
        
        reasons = {
            "prerequisite": f"""I am requesting an override for {course_code} prerequisite requirements. Although I have not completed all formal prerequisites, I have relevant background through related coursework and self-study. My current GPA of {gpa:.2f} demonstrates my academic capability, and I am confident I can succeed in this course. This course is critical for my degree completion timeline.""",
            
            "time_conflict": f"""I am experiencing a scheduling conflict with {course_code}. This course is required for my major and only offered this semester. I have explored all available sections and alternative courses, but this is the only option that allows me to stay on track for graduation. I am willing to work with the instructor to manage any attendance conflicts.""",
            
            "course_full": f"""I am requesting enrollment in {course_code}, which is currently at capacity. This course is a major requirement and critical for my graduation timeline. I have been monitoring registration closely and would greatly appreciate consideration for an override. I am fully committed to attending all classes and completing all coursework to the best of my ability.""",
            
            "graduation_requirement": f"""I am requesting an override for {course_code} as it is a required course for my degree completion. I am on track to graduate next semester, and this course is essential to meeting my degree requirements. I have already met with my advisor regarding my academic plan, and they support this request."""
        }
        
        return reasons.get(reason_type, reasons["prerequisite"])
    
    # ========== VALIDATION METHODS ==========
    
    def _validate_graduation_application(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate graduation application data"""
        validation = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "recommendations": []
        }
        
        # Critical checks
        if not data["meets_credit_requirement"]:
            validation["errors"].append(
                f"❌ Insufficient credits: You have {data['total_credits']} credits, "
                f"need {data['expected_credits_at_graduation']} by graduation (120 minimum required)"
            )
            validation["is_valid"] = False
        
        if not data["meets_gpa_requirement"]:
            validation["errors"].append(
                f"❌ GPA below minimum: Current GPA is {data['current_gpa']:.2f}, "
                "minimum 2.0 required"
            )
            validation["is_valid"] = False
        
        # Warnings
        if data["current_gpa"] < 3.0:
            validation["warnings"].append(
                f"⚠️ GPA is {data['current_gpa']:.2f}. Consider retaking courses to improve."
            )
        
        if data["expected_credits_at_graduation"] < 125:
            validation["warnings"].append(
                "⚠️ Cutting it close on credits. Ensure all courses are completed."
            )
        
        # Recommendations
        if validation["is_valid"]:
            validation["recommendations"].append(
                "✅ You appear ready to apply for graduation! Review with your advisor."
            )
        else:
            validation["recommendations"].append(
                "💡 Meet with your advisor to create a plan to meet graduation requirements."
            )
        
        return validation
    
    def _validate_change_of_major(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate change of major data"""
        validation = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "recommendations": []
        }
        
        if not data["new_major"]:
            validation["errors"].append("❌ New major must be specified")
            validation["is_valid"] = False
        
        if not data["meets_entry_requirements"]:
            validation["warnings"].append(
                f"⚠️ May not meet entry requirements: {data['requirement_details']}"
            )
        
        if data["current_major"] == data["new_major"]:
            validation["errors"].append("❌ New major cannot be the same as current major")
            validation["is_valid"] = False
        
        if validation["is_valid"]:
            validation["recommendations"].append(
                "✅ Review the new major's curriculum with your advisor before submitting."
            )
        
        return validation
    
    def _validate_course_override(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate course override data"""
        validation = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "recommendations": []
        }
        
        if not data["course_code"]:
            validation["errors"].append("❌ Course code is required")
            validation["is_valid"] = False
        
        if not data["reason"]:
            validation["errors"].append("❌ Reason for override is required")
            validation["is_valid"] = False
        
        if data["current_gpa"] < 2.5:
            validation["warnings"].append(
                f"⚠️ GPA of {data['current_gpa']:.2f} may affect approval chances. "
                "Emphasize your commitment in the reason."
            )
        
        if validation["is_valid"]:
            validation["recommendations"].append(
                "✅ Consider contacting the instructor directly to discuss the override."
            )
        
        return validation


# Convenience function for easy integration
def auto_fill_form(znumber: str, form_type: str, **kwargs) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Main entry point for auto-filling forms
    
    Args:
        znumber: Student Z-number
        form_type: "Graduation Application", "Change of Major", or "Course Override"
        **kwargs: Additional parameters (e.g., new_major, course_code)
    
    Returns:
        (filled_data, validation_result)
    """
    try:
        agent = AutoFillAgent(znumber)
        
        if form_type == "Graduation Application":
            return agent.auto_fill_graduation_application()
        
        elif form_type == "Change of Major":
            new_major = kwargs.get("new_major")
            return agent.auto_fill_change_of_major(new_major)
        
        elif form_type == "Course Override":
            course_code = kwargs.get("course_code", "")
            reason_type = kwargs.get("reason_type", "prerequisite")
            if not course_code:
                raise ValueError("course_code is required for Course Override")
            return agent.auto_fill_course_override(course_code, reason_type)
        
        else:
            raise ValueError(f"Unknown form type: {form_type}")
    
    except Exception as e:
        return {}, {
            "is_valid": False,
            "errors": [f"❌ Auto-fill failed: {str(e)}"],
            "warnings": [],
            "recommendations": ["Try filling the form manually or contact support."]
        }
