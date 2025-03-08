import streamlit as st
import google.generativeai as genai
import PyPDF2 as pdf
import json
import re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Arc
st.markdown("""
    <style>
        .stApp {
            background : rgb(255, 255, 255);
            font-family: "Times New Roman", Times, serif;
            color: grey;
            font-size: 20px;
        }
    </style>
    """,
    unsafe_allow_html=True)
# --- Function to call Gemini API ---
def generative_models(input_text):
    genai.configure(api_key="AIzaSyDhHs0iDhmXAsvBKRIsL1KUKbTVp19lqKc")  # Replace with actual API key
    model = genai.GenerativeModel(model_name="gemini-2.0-flash")  
    response = model.generate_content(input_text)
    return response.text if hasattr(response, "text") else str(response)  # Extract text safely

# --- Function to extract text from PDF ---
def input_pdf_text(uploaded_file):
    reader = pdf.PdfReader(uploaded_file)
    text = ""
    for page in range(len(reader.pages)):
        extracted_text = reader.pages[page].extract_text()
        if extracted_text:
            text += extracted_text + "\n"
    return text.strip()

# --- Function to clean JSON response ---
def clean_json_response(response_text):
    json_pattern = r"```json\s*(\{.*?\})\s*```"  
    match = re.search(json_pattern, response_text, re.DOTALL)
    if match:
        return match.group(1)  
    return response_text  

# --- ATS Prompt Template ---
input_prompt_template = """
You are an ATS (Applicant Tracking System) specializing in evaluating resumes for technical roles like Data Science, Software Engineering, and AI.

Evaluate the given resume against the provided job description and return the output **ONLY in JSON format**.

resume: "{resume}"
description: "{jd}"

Return response in **STRICT JSON format**:
{{
  "JD Match": "XX%",  
  "MissingKeywords": ["keyword1", "keyword2"],  
  "Profile Summary": "Short profile summary."
}}
"""

# --- Function to Draw a Natural-Looking Gauge ---
def draw_natural_gauge(score):
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-0.1, 1.2)

    # Background Arc (Gray)
    arc_bg = Arc((0, 0), 2, 2, angle=0, theta1=0, theta2=180, color="lightgray", lw=20)
    ax.add_patch(arc_bg)

    # Score Arc (Green)
    arc_score = Arc((0, 0), 2, 2, angle=0, theta1=0, theta2=score * 1.8, color="green", lw=20)
    ax.add_patch(arc_score)

    # Needle
    angle = np.radians((score / 100) * 180)
    x, y = np.cos(angle), np.sin(angle)
    ax.plot([0, x], [0, y], color="black", linewidth=3, marker="o", markersize=6)

    # Labels & Text
    ax.text(0, -0.3, f"{score}%", ha="center", fontsize=14, fontweight="bold")
    ax.text(-0.9, -0.2, "Poor", fontsize=10, color="red")
    ax.text(0.9, -0.2, "Excellent", fontsize=10, color="green")

    # Hide Axes
    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)

    st.pyplot(fig)

with st.sidebar:  # Use the sidebar for left-side placement
    st.header("📑 ATS Input Panel")
    jd = st.text_area("📌 Paste the Job Description Here",height=200)
    uploaded_file = st.file_uploader("📤 Upload Your Resume (PDF)", type="pdf")
    submit=st.button("🚀 Submit", use_container_width=True)

if submit:
    if uploaded_file and jd:
        resume_text = input_pdf_text(uploaded_file)

        if not resume_text:
            st.error("⚠️ Error: Could not extract text from the uploaded PDF. Try another file.")
        else:
            input_prompt = input_prompt_template.format(resume=resume_text, jd=jd)
            
            response = generative_models(input_prompt)  # Generate ATS response
            
            cleaned_response = clean_json_response(response)  # Clean JSON output

            try:
                response_data = json.loads(cleaned_response)  # Parse JSON
                ats_score = int(response_data.get("JD Match", "0").replace("%", ""))  # Convert score to integer
                missing_keywords = response_data.get("MissingKeywords", [])
                profile_summary = response_data.get("Profile Summary", "")

                st.success(f"✅ **AI-based ATS Score:** {ats_score}%")
                st.write("🛠️ **Missing Keywords:**", ", ".join(missing_keywords) if missing_keywords else "None")
                st.write("📌 **Profile Summary:**", profile_summary)

                # --- Display Natural Gauge Chart ---
                draw_natural_gauge(ats_score)

            except json.JSONDecodeError:
                st.error("❌ Error: Gemini returned an invalid JSON response. Try again.")
                st.write("**Debugging Response:**", response)
    else:
        st.warning("⚠️ Please upload a resume and enter a job description.")
