import streamlit as st
import json
import openai  # Make sure openai is imported

st.set_page_config(page_title="Feedback Generator")

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

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

st.title("AI Feedback API for Wix")
st.write("✅ Ready to receive AI feedback requests.")

# 1. Handle GET requests (Query Parameters)
query_params = st.experimental_get_query_params()
if "data" in query_params:
    try:
        json_data = query_params["data"][0]
        data = json.loads(json_data)
        response = data.get("response", {})
        feedback, grade = generate_feedback_and_mark(response)
        st.success(f"✅ Feedback Generated:\n{feedback}")
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        st.error(f"❌ Error processing WIX data: {e}")


# 2. Handle POST requests (Simulated for testing)
if "posted_data" not in st.session_state:
    st.session_state.posted_data = None

if st.experimental_get_query_params().get("process_post", [False])[0]:
    try:
        if st.session_state.posted_data:
            request_data = st.session_state.posted_data
            response = request_data.get("response", {})
            if not response:
                st.error("❌ Error: No response data received.")
                st.json({"error": "Missing response data."})
            else:
                feedback, grade = generate_feedback_and_mark(response)
                result = {"feedback": feedback, "grade": grade}
                st.success("✅ Feedback generated successfully!")
                st.json(result)
            st.session_state.posted_data = None
    except (json.JSONDecodeError, KeyError) as e:
        st.error(f"❌ Error processing request: {e}")
        st.json({"error": str(e)})

# Simulate a POST Request (for testing within Streamlit):
st.subheader("Simulate POST Request")
post_data_input = st.text_area("Enter JSON data for POST request (as a string):", height=150)
if st.button("Simulate POST"):
    try:
        st.session_state.posted_data = json.loads(post_data_input)
        st.experimental_set_query_params({"process_post": True})
        st.experimental_rerun()
    except json.JSONDecodeError as e:
        st.error(f"Invalid JSON: {e}")
