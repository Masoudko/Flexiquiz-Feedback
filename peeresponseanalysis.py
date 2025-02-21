import streamlit as st
import pdfplumber  # Not used in this code, consider removing
import openai
import os  # Not used directly, but might be needed for secrets
import json

st.set_page_config(page_title="Feedback Generator")

# CORS fix (if needed, but might not be required with Streamlit sharing)
# st.write('<script>document.domain = "wixsite.com";</script>', unsafe_allow_html=True)  # Likely unnecessary

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

# ... (criteria definition remains the same)

def generate_feedback_and_mark(response):
    # ... (This function remains the same)

st.title("AI Feedback API for Wix")
st.write("✅ Ready to receive AI feedback requests.")

# 🛠 Fix: Handle GET and POST requests correctly (using st.experimental_get_query_params and st.session_state)

# 1. Handle GET requests (Query Parameters - for testing or very simple Wix integrations)
query_params = st.experimental_get_query_params()  # Correct way to get query params
if "data" in query_params:
    try:
        json_data = query_params["data"][0]  # Get the first element from the list of query parameter values
        data = json.loads(json_data)
        response = data.get("response", {})
        feedback, grade = generate_feedback_and_mark(response)
        st.success(f"✅ Feedback Generated:\n{feedback}")
    except (json.JSONDecodeError, KeyError, IndexError) as e: # Handle JSON errors
        st.error(f"❌ Error processing WIX data: {e}")

# 2. Handle POST requests (Wix Backend - using st.session_state for temporary data)
# Note: Streamlit's intended use is not as a direct backend API.  This is a workaround.
if "posted_data" not in st.session_state:  # Initialize session state
    st.session_state.posted_data = None

if st.experimental_get_query_params().get("process_post", [False])[0]: # Check for a query parameter to indicate a POST request
    try:
        if st.session_state.posted_data: # If we have data from a POST
          request_data = st.session_state.posted_data
          response = request_data.get("response", {})
          if not response:
              st.error("❌ Error: No response data received.")
              st.json({"error": "Missing response data."})
          else:
              feedback, grade = generate_feedback_and_mark(response)
              result = {"feedback": feedback, "grade": grade}
              st.success("✅ Feedback generated successfully!")
              st.json(result)  # Return structured JSON response
          st.session_state.posted_data = None # Clear after processing
    except (json.JSONDecodeError, KeyError) as e: # Handle JSON errors
        st.error(f"❌ Error processing request: {e}")
        st.json({"error": str(e)})

# Simulate a POST Request (for testing within Streamlit):
st.subheader("Simulate POST Request")
post_data_input = st.text_area("Enter JSON data for POST request (as a string):", height=150)
if st.button("Simulate POST"):
    try:
        st.session_state.posted_data = json.loads(post_data_input) # Store the posted data
        st.experimental_set_query_params({"process_post": True}) # Redirect to process the post
        st.experimental_rerun() # Rerun to process the post

    except json.JSONDecodeError as e:
        st.error(f"Invalid JSON: {e}")
