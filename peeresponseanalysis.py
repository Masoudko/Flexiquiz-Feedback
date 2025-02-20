import streamlit as st
import pdfplumber
import openai
import os
import json

# ✅ CORS FIX: Allow requests from Wix
st.set_page_config(page_title="Feedback Generator")

def add_cors_headers():
    """ Adds CORS headers to allow requests from Wix. """
    st.write('<script>document.domain = "wixsite.com";</script>', unsafe_allow_html=True)

add_cors_headers()

# Load API Key from Streamlit Secrets
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# Load API Key from Streamlit Secrets
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]  # ✅ Fixed API key retrieval

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

# Function to generate feedback
def generate_feedback_and_mark(response):
    openai.api_key = OPENAI_API_KEY

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
        return f"OpenAI API error: {e}", None

# ✅ Fix: Streamlit API to receive data from Wix
st.title("AI Feedback API for Wix")

# Listen for incoming Wix requests
st.write("✅ Ready to receive AI feedback requests.")

if st.request.method == "POST":
    try:
        data = st.request.json()  # ✅ Fix: Properly handle POST request
        response = data.get("response", {})

        # Validate input
        if not response:
            st.error("❌ Error: No response data received.")
            st.json({"error": "Missing response data."})
        else:
            feedback, grade = generate_feedback_and_mark(response)
            result = {
                "feedback": feedback,
                "grade": grade
            }
            st.success("✅ Feedback generated successfully!")
            st.json(result)  # ✅ Return structured JSON response
    except Exception as e:
        st.error(f"❌ Error processing request: {e}")
        st.json({"error": str(e)})
