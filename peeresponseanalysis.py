import streamlit as st
import pdfplumber
import openai
import os
import json

# Load API Keys from Streamlit secrets
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

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

# 📌 Step 1: Accept JSON data from WIX (Alternative to Flask)
st.title("WIX API Integration for Feedback Generation")

if "wix_data" not in st.session_state:
    st.session_state["wix_data"] = None

# Handle incoming data
if st.button("Process Data from WIX"):
    try:
        json_data = st.text_area("Paste JSON from WIX here", "")
        if json_data:
            data = json.loads(json_data)
            response = data.get("response", {})
            feedback, grade = generate_feedback_and_mark(response)
            st.success(f"Feedback Generated:\n{feedback}")
    except Exception as e:
        st.error(f"Error processing WIX data: {e}")


import streamlit.components.v1 as components

# 📌 Step 2: Expose an API-like endpoint for Wix
query_params = st.experimental_get_query_params()

if "trigger" in query_params:
    try:
        json_data = query_params.get("data", ["{}"])[0]  # Extract JSON data from query
        data = json.loads(json_data)
        response = data.get("response", {})
        feedback, grade = generate_feedback_and_mark(response)

        st.write("✅ AI Feedback Processed!")
        st.json({"feedback": feedback, "grade": grade})  # Return JSON response
    except Exception as e:
        st.error(f"Error processing WIX data: {e}")

# Display UI Message for Manual Testing
st.write("✅ Ready to receive WIX requests.")
components.html("<script>console.log('WIX API Ready');</script>", height=10)
