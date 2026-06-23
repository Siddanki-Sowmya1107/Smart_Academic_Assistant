# FAU Smart Academic Assistant

An agentic AI solution designed to simplify and automate complex academic forms and student support processes at Florida Atlantic University.

## Problem

Students often struggle with academic forms such as graduation applications, program changes, petitions, and advisor requests. These forms can be long, confusing, and error-prone. Even a small mistake can delay processing by days or weeks.

The main problems we identified were:

* Students are confused by academic terminology and form requirements
* Forms are static and not user-friendly
* Many processes depend on manual email communication
* Students often need repeated advisor clarification
* Deadlines and follow-ups are easy to miss

## Solution

FAU Smart Academic Assistant is a multi-agent AI system that guides students through academic processes step by step. It helps students understand form requirements, fill missing information, validate entries, generate advisor-ready emails, track reminders, and simulate advising appointment scheduling through voice interaction.

This is more than a chatbot. It is an agentic workflow that supports end-to-end task completion.

## Key Features

* Step-by-step academic form guidance
* Plain-English explanations of requirements
* Missing field detection and validation
* Auto-fill support with student consent
* Advisor-ready email generation
* Deadline tracking and reminders
* Voice-based appointment scheduling simulation
* Multilingual and accessibility-focused response design
* Streamlit-based interactive demo

## Multi-Agent Architecture

The system uses specialized agents that work together:

* **Form Assistant Agent**: Guides students through academic forms and explains requirements
* **Autofill Agent**: Fills known student details into form fields with consent
* **Validation Agent**: Checks for missing, incorrect, or inconsistent information
* **Email Automation Agent**: Generates advisor-ready submission emails
* **Calendar Agent**: Tracks deadlines, reminders, and simulated scheduling tasks
* **Voice Agent**: Supports natural speech interaction for appointment booking

Each agent performs a specific responsibility, making the workflow easier to test, improve, and scale.

## Workflow

1. Student selects an academic form or request type
2. The assistant explains requirements in plain English
3. The system asks follow-up questions for missing information
4. The Validation Agent checks the form for errors
5. The Autofill Agent fills known details with consent
6. The Email Automation Agent generates a complete advisor-ready email
7. The Calendar Agent creates reminders or scheduling support
8. The student receives a clear final output instantly

## Tech Stack

* Python
* Streamlit
* OpenAI GPT-4o-mini
* Prompt Engineering
* Multi-Agent Workflow Design
* SQLite for session and form state management
* Speech-to-Text and Text-to-Speech modules
* Email automation APIs
* Calendar APIs simulated for demo

## Why This Matters

The project improves the student experience by reducing confusion, form errors, and repetitive advisor communication. It also helps advisors save time by allowing students to submit clearer, more complete requests on the first attempt.

## Impact

This system can help:

* Reduce student errors and delays
* Save advisor time
* Improve accessibility through voice and plain-language support
* Provide 24/7 academic process guidance
* Create a scalable foundation for campus-wide academic automation

## Future Enhancements

* Integrate with FAU systems such as Banner or EAB
* Auto-fill forms using real student profiles
* Generate completed PDF forms
* Submit forms directly without email
* Expand support across all FAU colleges
* Add a personalized student dashboard
* Add real calendar integration
* Add analytics for advisor workload and student request patterns

## What I Learned

This project taught me that useful AI systems need more than a single prompt. Real value comes from breaking a complex process into smaller responsibilities, assigning each responsibility to a specialized agent, testing edge cases, validating outputs, and designing the workflow around real user pain points.

I also learned how important clarity, trust, consent, and accessibility are when building AI tools for student-facing processes.
