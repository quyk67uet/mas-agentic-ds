import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional
import graphviz

from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

# Import project modules
from src.utils.workflow import create_assessment_workflow
from src.utils.transcript_processor import get_transcript_from_json, extract_word_scores_from_json
from src.database.db_connector import DatabaseConnector

# Load environment variables
load_dotenv()

# Set page config
st.set_page_config(
    page_title="LingLooma - IELTS Speaking Assessment",
    page_icon="🎤",
    layout="wide"
)

# Initialize session state
if "workflow" not in st.session_state:
    st.session_state.workflow = None
if "transcript" not in st.session_state:
    st.session_state.transcript = None
if "student_id" not in st.session_state:
    st.session_state.student_id = None
if "assessment_in_progress" not in st.session_state:
    st.session_state.assessment_in_progress = False
if "assessment_completed" not in st.session_state:
    st.session_state.assessment_completed = False
if "feedback_result" not in st.session_state:
    st.session_state.feedback_result = None
if "graph_state" not in st.session_state:
    st.session_state.graph_state = None
if "message_history" not in st.session_state:
    st.session_state.message_history = []
if "teacher_feedback" not in st.session_state:
    st.session_state.teacher_feedback = ""
if "problem_words" not in st.session_state:
    st.session_state.problem_words = []

# Header
st.title("🎤 LingLooma - IELTS Speaking Assessment")
st.markdown("### AI-powered assessment for IELTS Speaking")

# Sidebar
st.sidebar.title("Assessment Options")

# Check for OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key or api_key == "your_openai_api_key":
    st.sidebar.warning("⚠️ OpenAI API key not set. Please add it to your .env file.")
else:
    st.sidebar.success("✅ OpenAI API key is set")

# Model selection
model_options = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]
selected_model = st.sidebar.selectbox("Select LLM Model", model_options, index=1)

# Add workflow visualization in sidebar
st.sidebar.markdown("### Assessment Workflow")

# Create workflow visualization using graphviz
graph = graphviz.Digraph()
graph.attr(rankdir='TB', size='8,8', ratio='fill')
graph.attr('node', shape='box', style='filled', fillcolor='lightblue', fontname='Arial')
graph.attr('edge', arrowsize='0.5')

# Add nodes with different colors for different types
graph.node('Input', 'Input Transcript', fillcolor='lightgreen')
graph.node('FC', 'Fluency & Coherence\nAssessment', fillcolor='#add8e6')
graph.node('LR', 'Lexical Resource\nAssessment', fillcolor='#add8e6')
graph.node('GR', 'Grammatical Range\nAssessment', fillcolor='#add8e6')
graph.node('PR', 'Pronunciation\nAssessment', fillcolor='#add8e6')
graph.node('FB', 'Generate Feedback', fillcolor='#ffb6c1')
graph.node('FN', 'Final Assessment', fillcolor='#98fb98')

# Add edges - remove Teacher Feedback node
graph.edge('Input', 'FC')
graph.edge('FC', 'LR')
graph.edge('LR', 'GR')
graph.edge('GR', 'PR')
graph.edge('PR', 'FB')
graph.edge('FB', 'FN')

# Add visualization to sidebar
st.sidebar.graphviz_chart(graph)

# Add explanation for the colors
st.sidebar.markdown("""
**Workflow stages:**
- 🟢 Input data
- 🔵 AI assessments 
- 🟣 AI feedback generation
- 🟩 Final assessment
""")

# Main layout
col1, col2 = st.columns([2, 3])

with col1:
    st.markdown("### Input")
    
    # File upload
    uploaded_file = st.file_uploader("Upload speaking response JSON file", type=["json"])
    
    # Student ID input
    student_id = st.number_input("Student ID", min_value=1, step=1, value=1)
    st.session_state.student_id = student_id
    
    # Process uploaded file
    if uploaded_file is not None:
        try:
            # Read and parse the JSON file
            json_data = json.load(uploaded_file)
            
            # Extract transcript
            transcript = get_transcript_from_json(json_data)
            
            if transcript:
                st.session_state.transcript = transcript
                
                # Extract word scores for pronunciation analysis
                word_score_data = extract_word_scores_from_json(json_data)
                if word_score_data and "problem_words" in word_score_data:
                    st.session_state.problem_words = word_score_data["problem_words"]
                
                st.success("✅ Transcript extracted successfully")
                
                with st.expander("Preview Transcript"):
                    st.write(transcript)
                    
                # Check if the student exists in the database
                db = DatabaseConnector()
                student_history = db.fetch_student_history(student_id)
                
                if student_history:
                    st.info(f"📚 Found {len(student_history)} previous assessment(s) for student {student_id}")
                else:
                    st.info("🆕 No previous assessments found for this student")
            else:
                st.error("❌ No transcript found in the uploaded file")
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")

    # Start assessment button
    if st.session_state.transcript and not st.session_state.assessment_in_progress:
        if st.button("Start Assessment"):
            with st.spinner("Initializing assessment workflow..."):
                # Create the workflow
                workflow = create_assessment_workflow(model_name=selected_model)
                st.session_state.workflow = workflow
                
                # Initial inputs for the workflow
                inputs = {
                    "messages": [{"role": "user", "content": json.dumps({"transcript": st.session_state.transcript})}],
                    "student_id": st.session_state.student_id,
                    "history": [],
                    "error": None
                }
                
                # Start the workflow - simplified to process the entire assessment at once
                st.session_state.graph_state = st.session_state.workflow.invoke(inputs)
                
                # Check if there was an error
                if st.session_state.graph_state.get("error"):
                    st.error(f"❌ Error during assessment: {st.session_state.graph_state['error']}")
                
                # Set assessment_completed directly since there's no human-in-the-loop now
                if st.session_state.graph_state.get("feedback_result"):
                    st.session_state.feedback_result = st.session_state.graph_state["feedback_result"]
                    st.session_state.assessment_completed = True
                    st.rerun()

with col2:
    st.markdown("### Assessment Results")
    
    # Display assessment results - simplified to just show completed assessment since there's no "in progress" state
    if st.session_state.assessment_completed and st.session_state.feedback_result:
        st.success("✅ Assessment completed successfully!")
        
        # Display final feedback
        feedback_result = st.session_state.feedback_result
        
        with st.expander("Assessment Results", expanded=True):
            # Sidebar for score summary
            score_col1, score_col2 = st.columns([1, 3])
            
            with score_col1:
                # Overall score with color based on score level
                overall_score = feedback_result.get("overall_score", 0)
                score_color = "#ff4b4b" if overall_score < 5 else "#faa307" if overall_score < 6.5 else "#0ec93e"
                
                st.markdown(f"""
                <div style="background-color: {score_color}; padding: 20px; border-radius: 10px; text-align: center; color: white;">
                    <h1 style="margin: 0; font-size: 48px;">{overall_score}</h1>
                    <p style="margin: 0;">Overall Band Score</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Individual scores with visual indicators
                st.markdown("### Criterion Scores")
                
                criteria = [
                    ("Fluency & Coherence", feedback_result.get("fc_score", 0)),
                    ("Lexical Resource", feedback_result.get("lr_score", 0)),
                    ("Grammar", feedback_result.get("gr_score", 0)),
                    ("Pronunciation", feedback_result.get("pr_score", 0))
                ]
                
                for name, score in criteria:
                    # Generate stars based on score (0-9 band score)
                    stars = "★" * int(score) + "☆" * (9 - int(score))
                    st.markdown(f"**{name}**: {score} {stars}")
            
            with score_col2:
                # Overall feedback in a nice box
                st.markdown("### Summary Feedback")
                st.markdown(f"""
                <div style="background-color: #f0f2f6; padding: 15px; border-radius: 5px; border-left: 5px solid #4b8bbe;">
                    {feedback_result.get("overall_feedback", "")}
                </div>
                """, unsafe_allow_html=True)
                
                # Detailed feedback in tabs
                st.markdown("### Detailed Assessment")
                detailed_feedback = feedback_result.get("detailed_feedback", {})
                
                tabs = st.tabs(["Fluency & Coherence", "Lexical Resource", "Grammar", "Pronunciation"])
                
                tab_icons = ["🗣️", "📚", "🔤", "🔊"]
                tab_colors = ["#4b8bbe", "#306998", "#FFD43B", "#646464"]
                
                for i, (tab, label) in enumerate(zip(tabs, ["fluency_coherence", "lexical_resource", "grammatical_range", "pronunciation"])):
                    with tab:
                        feedback_text = detailed_feedback.get(label, "No detailed feedback available")
                        st.markdown(f"""
                        <div style="border-left: 5px solid {tab_colors[i]}; padding-left: 15px;">
                            <h4>{tab_icons[i]} {label.replace('_', ' ').title()}</h4>
                            {feedback_text}
                        </div>
                        """, unsafe_allow_html=True)
                
                # Display problem words if available (only in pronunciation tab)
                if st.session_state.problem_words:
                    with tabs[3]:  # Pronunciation tab
                        st.markdown("#### Problematic Words")
                        problem_df = pd.DataFrame(st.session_state.problem_words)
                        problem_df = problem_df.sort_values(by="score", ascending=True)
                        
                        # Add color coding to the dataframe
                        def color_score(val):
                            color = "red" if val < 0.5 else "orange" if val < 0.7 else "green"
                            return f'background-color: {color}; color: white'
                        
                        st.dataframe(
                            problem_df.style.applymap(color_score, subset=["score"]),
                            use_container_width=True
                        )
        
        # Reset button
        if st.button("Start New Assessment"):
            # Reset session state
            st.session_state.workflow = None
            st.session_state.transcript = None
            st.session_state.assessment_completed = False
            st.session_state.feedback_result = None
            st.session_state.graph_state = None
            st.session_state.message_history = []
            st.session_state.problem_words = []
            st.rerun()
    else:
        st.info("Upload a speaking response JSON file and start the assessment to see results here.") 