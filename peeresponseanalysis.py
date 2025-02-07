import streamlit as st
import pdfplumber
import openai
import google.auth
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import os


# Load environment variables (set in Streamlit Cloud)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SENDER_EMAIL = st.secrets["SENDER_EMAIL"]
GMAIL_APP_PASSWORD = st.secrets["GMAIL_APP_PASSWORD"]
TEACHER_EMAIL = st.secrets["TEACHER_EMAIL"]


# Define the marking criteria
criteria = {
    "Exceeding": ["proficiently use knowledge", "precise quotes", "intelligent conclusions",
                  "perceptive comments about language", "effect on the reader"],
    "Accomplished": ["spot a range of ideas", "relevant quotes", "intelligent conclusions",
                     "examples of language", "language tricks"],
    "Expected": ["find and understand main ideas", "support comments with good quotes",
                 "begin developing comments", "describe the effect of word choices"],
    "Emerging": ["find main ideas", "simple comments", "find quotes to prove ideas",
                 "simple comments about language"]
}

# Function to extract content from PDF
def extract_pdf_content(file):
    """Extracts student responses (Point, Evidence, Explanation) from uploaded PDF."""
    try:
        with pdfplumber.open(file) as pdf:
            text = "".join(page.extract_text() for page in pdf.pages if page.extract_text())
            lines = [line.strip() for line in text.split("\n") if line.strip()]

            name = next((line.split(" ", 1)[-1].strip() for line in lines if line.lower().startswith("name")), None)
            email = next((line.split(" ", 1)[-1].strip() for line in lines if line.lower().startswith("email")), None)

            response = {"Point": None, "Evidence": None, "Explanation": None}
            keywords = {"1. Point": "Point", "2. Evidence": "Evidence", "3. Explanation": "Explanation"}

            for i, line in enumerate(lines):
                for keyword, key in keywords.items():
                    if line.lower().startswith(keyword.lower()):
                        response[key] = lines[i + 1].strip() if i + 1 < len(lines) else None

            return {"name": name, "email": email, "response": response}
    except Exception as e:
        st.error(f"Error extracting content from PDF: {e}")
        return None

# Function to generate AI feedback and mark
def generate_feedback_and_mark(response):
    """Generates feedback using OpenAI and assigns a grade based on the marking criteria."""

    openai.api_key = st.secrets["OPENAI_API_KEY"]


    prompt = f"""
    Provide feedback for the following response:

    Point: {response.get('Point', 'N/A')}
    Evidence: {response.get('Evidence', 'N/A')}
    Explanation: {response.get('Explanation', 'N/A')}

    Feedback should:
    1. Be clear and simple enough for an 11-year-old to understand.
    2. Be encouraging, highlighting strengths.
    3. Be constructive, offering suggestions for improvement.
    """

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7
        )
        feedback = completion['choices'][0]['message']['content'].strip()

        grade = "Emerging"
        response_text = f"{response.get('Point', '')} {response.get('Evidence', '')} {response.get('Explanation', '')}".lower()
        for level, phrases in criteria.items():
            if any(phrase in response_text for phrase in phrases):
                grade = level
                break

        feedback += f"\n\nGrade: {grade}"
        return feedback, grade
    except openai.error.OpenAIError as e:
        st.error(f"OpenAI API error: {e}")
        return None, None

# Function to send email
import smtplib
from email.mime.text import MIMEText

def send_email(name, student_email, feedback):
    """Sends feedback email to the teacher for approval before sending it to students."""
    
    SENDER_EMAIL = st.secrets["SENDER_EMAIL"]
    GMAIL_APP_PASSWORD = st.secrets["GMAIL_APP_PASSWORD"]
    TEACHER_EMAIL = st.secrets["TEACHER_EMAIL"]
    
    subject = f"Approval Request: Feedback for {name}'s PEE Writing"
    body = f"""
    Dear Teacher,

    Below is the feedback generated for {name} based on their PEE writing task:

    Feedback:
    {feedback}

    Student's Email: {student_email}

    Please review and approve this feedback.

    Best regards,
    Your Automated System
    """

    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = TEACHER_EMAIL

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, GMAIL_APP_PASSWORD)
            server.sendmail(SENDER_EMAIL, TEACHER_EMAIL, msg.as_string())
            
        st.success(f"✅ Feedback sent to teacher for approval: {TEACHER_EMAIL}")
    
    except Exception as e:
        st.error(f"❌ Error sending email: {e}")


# Streamlit UI
st.title("PEE Writing Feedback System")
st.write("Upload a student's response in PDF format to generate feedback and a grade.")

uploaded_file = st.file_uploader("Upload PDF", type="pdf")

if uploaded_file:
    st.write("Processing file...")
    extracted_content = extract_pdf_content(uploaded_file)
    
    if extracted_content:
        name, email, response = extracted_content.get("name"), extracted_content.get("email"), extracted_content.get("response")
        st.write(f"Extracted Name: {name}, Email: {email}")
        if name and email and response:
            feedback, grade = generate_feedback_and_mark(response)
            if feedback:
                st.subheader("Generated Feedback")
                st.write(feedback)
                
                if st.button("Send Feedback for Approval"):
                    send_email(name, email, feedback)
