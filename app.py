import streamlit as st
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from config.settings import get_groq_api_key
from config.questions import get_assessment_questions, get_dynamic_questions
from services.guide_service import generate_guide, generate_followup_response
from services.ai_service import get_assessment_result

# Load environment variables
load_dotenv()

# Check for Groq API key
if not get_groq_api_key():
    st.warning("""
    **Groq API Key Not Found**
    
    This application requires a Groq API key to generate personalized grief assessments and guides.
    
    Please:
    1. Create a `.env` file in the root directory 
    2. Add your Groq API key: `GROQ_API_KEY=your_key_here`
    3. Restart the application
    
    If you don't have a Groq API key, you can get one at https://console.groq.com/
    """, icon="⚠️")

# Set page config
st.set_page_config(
    page_title="Grief Compass",
    page_icon="🕊️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom styles
def apply_custom_styles():
    """Apply custom styles to the app to make it look more like ChatGPT"""
    st.markdown("""
    <style>
    /* Main container */
    .main {
        background-color: #f9f9f9;
    }
    
    /* Sidebar */
    .sidebar .sidebar-content {
        background-color: #202123;
        color: white;
    }
    
    /* Chat-like message containers */
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .chat-message.user {
        background-color: #f7f7f8;
        border: 1px solid #e5e5e5;
    }
    .chat-message.ai {
        background-color: white;
        border: 1px solid #e5e5e5;
    }
    
    /* Make buttons look more like ChatGPT */
    .stButton > button {
        background-color: #f7f7f8;
        color: #202123;
        border: 1px solid #e5e5e5;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        font-size: 0.9rem;
        transition: background-color 0.3s;
        width: 100%;
        margin-bottom: 0.5rem;
    }
    .stButton > button:hover {
        background-color: #e5e5e5;
    }
    
    /* Primary buttons */
    .stButton > button[data-baseweb="button"][kind="primary"] {
        background-color: #10A37F;
        color: white;
    }
    .stButton > button[data-baseweb="button"][kind="primary"]:hover {
        background-color: #0D8C6D;
    }
    
    /* Chat input */
    .stTextArea textarea {
        border-radius: 0.5rem;
        border: 1px solid #e5e5e5;
        padding: 1rem;
    }
    
    /* Customize chat input container */
    #chat-input-container {
        position: fixed;
        bottom: 0;
        left: 25%;
        right: 3rem;
        background-color: white;
        padding: 1rem;
        border-top: 1px solid #e5e5e5;
        z-index: 100;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
if 'current_view' not in st.session_state:
    st.session_state.current_view = "home"
    
if 'assessment_history' not in st.session_state:
    st.session_state.assessment_history = []
    
if 'responses' not in st.session_state:
    st.session_state.responses = {}
    
if 'current_question_index' not in st.session_state:
    st.session_state.current_question_index = 0
    
if 'guide' not in st.session_state:
    st.session_state.guide = None
    
if 'guidance_conversation' not in st.session_state:
    st.session_state.guidance_conversation = []

def main():
    """Main application entry point"""
    # Apply custom styles
    apply_custom_styles()
    
    # Set up sidebar navigation
    with st.sidebar:
        st.title("Grief Compass")
        
        # Navigation buttons
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.current_view = "home"
            st.rerun()
            
        if st.button("📋 New Assessment", use_container_width=True):
            # Reset assessment state
            st.session_state.current_view = "story"
            st.session_state.current_question_index = 0
            st.session_state.responses = {}
            st.session_state.guide = None
            st.session_state.guidance_conversation = []
            st.session_state.results = None
            st.rerun()
        
        # Show history if available
        if st.session_state.assessment_history:
            st.markdown("---")
            st.markdown("### Previous Assessments")
            
            # Loop through history (most recent first)
            for i, assessment in enumerate(st.session_state.assessment_history):
                # Get date
                date_str = "Assessment"
                if "date" in assessment:
                    try:
                        date_obj = datetime.fromisoformat(assessment["date"])
                        date_str = date_obj.strftime("%b %d, %Y")
                    except:
                        pass
                
                # Get title or default
                title = f"Assessment {i+1}"
                if "title" in assessment:
                    title = assessment["title"]
                elif "responses" in assessment and "grief_story" in assessment["responses"]:
                    story = assessment["responses"]["grief_story"].get("response", "")
                    if story:
                        # Use first 40 chars of story as title
                        title = story[:40] + "..." if len(story) > 40 else story
                
                # Create history button
                if st.button(f"📝 {date_str} - {title}", key=f"history_{i}", use_container_width=True):
                    # Load this assessment
                    st.session_state.current_view = "results"
                    st.session_state.responses = assessment.get("responses", {})
                    st.session_state.results = assessment.get("results", {})
                    st.session_state.guide = assessment.get("guide", None)
                    st.session_state.guidance_conversation = assessment.get("guidance_conversation", [])
                    st.rerun()
        
        # Footer
        st.markdown("---")
        st.caption("© 2023 Grief Compass")
    
    # Main content area
    if st.session_state.current_view == "home":
        render_home_view()
    elif st.session_state.current_view == "story":
        render_story_view()
    elif st.session_state.current_view == "assessment":
        render_assessment_view()
    elif st.session_state.current_view == "processing":
        render_processing_view()
    elif st.session_state.current_view == "results":
        render_results_view()

def render_home_view():
    """Render the home/intro view"""
    st.title("Welcome to Grief Compass")
    
    st.markdown("""
    Grief Compass helps you understand and navigate your unique grief journey through:
    
    - **Personalized assessment** of your grief experience
    - **AI-generated guidance** tailored to your specific situation
    - **Ongoing support** through interactive conversation
    
    Your responses and all generated guidance are private and secure.
    """)
    
    # Call to action
    if st.button("Start Your Grief Assessment", type="primary", use_container_width=False):
        st.session_state.current_view = "story"
        st.rerun()

def render_story_view():
    """Render the initial story collection view"""
    st.title("Share Your Grief Experience")
    
    st.markdown("""
    Please share a bit about your grief experience. This helps us understand your unique situation and provide personalized guidance.
    
    You can share as much or as little as you feel comfortable with.
    """)
    
    # Get grief story
    grief_story = st.text_area(
        "What loss are you experiencing? What would you like guidance with?", 
        height=200
    )
    
    # Optional title
    assessment_title = st.text_input("Give this assessment a title (optional)")
    
    # Next button
    if st.button("Continue to Assessment", type="primary"):
        if not grief_story:
            st.error("Please share some information about your grief experience before continuing.")
            return
        
        # Save story and title
        st.session_state.responses["grief_story"] = {
            "question_id": "grief_story",
            "question_text": "What loss are you experiencing? What would you like guidance with?",
            "response": grief_story,
            "timestamp": datetime.now().isoformat()
        }
        
        if assessment_title:
            st.session_state.responses["assessment_title"] = {
                "question_id": "assessment_title",
                "question_text": "Assessment Title",
                "response": assessment_title,
                "timestamp": datetime.now().isoformat()
            }
        
        # Move to assessment
        st.session_state.current_view = "assessment"
        st.rerun()

def render_assessment_view():
    """Render the assessment questions"""
    st.title("Grief Assessment")
    
    # Get base questions
    questions = get_assessment_questions()
    
    # Add dynamic questions if we have enough responses
    if len(st.session_state.responses) >= 3 and "dynamic_questions" not in st.session_state:
        st.session_state.dynamic_questions = get_dynamic_questions(st.session_state.responses)
    
    # Use dynamic questions if available
    if "dynamic_questions" in st.session_state:
        all_questions = questions + st.session_state.dynamic_questions
    else:
        all_questions = questions
    
    # Show progress
    total_questions = len(all_questions)
    progress = min(1.0, st.session_state.current_question_index / total_questions)
    
    st.progress(progress)
    st.caption(f"Question {st.session_state.current_question_index + 1} of {total_questions}")
    
    # Display current question
    if st.session_state.current_question_index < total_questions:
        current_q = all_questions[st.session_state.current_question_index]
        question_id = current_q["id"]
        
        st.subheader(current_q["question"])
        
        # Default response value
        response = None
        
        # Handle different question types
        if current_q["type"] == "multiple_choice":
            options = current_q.get("options", [])
            # Check if there's a previous response to use as default
            default_index = 0
            if question_id in st.session_state.responses:
                prev_response = st.session_state.responses[question_id].get("response")
                if prev_response in options:
                    default_index = options.index(prev_response)
            
            response = st.radio(
                "Select one:", 
                options,
                index=default_index,
                help=current_q.get("help_text", "")
            )
            
        elif current_q["type"] == "multiselect":
            options = current_q.get("options", [])
            # Check if there's a previous response to use as default
            default = []
            if question_id in st.session_state.responses:
                prev_response = st.session_state.responses[question_id].get("response", [])
                if isinstance(prev_response, list):
                    default = prev_response
            
            response = st.multiselect(
                "Select all that apply:", 
                options,
                default=default,
                help=current_q.get("help_text", "")
            )
            
        elif current_q["type"] == "scale":
            min_val = current_q.get("min", 1)
            max_val = current_q.get("max", 10)
            default_val = current_q.get("default", (min_val + max_val) // 2)
            
            # Check if there's a previous response to use as default
            if question_id in st.session_state.responses:
                prev_response = st.session_state.responses[question_id].get("response")
                if isinstance(prev_response, (int, float)):
                    default_val = prev_response
            
            response = st.slider(
                "Select your response:", 
                min_value=min_val, 
                max_value=max_val, 
                value=default_val,
                help=current_q.get("help_text", "")
            )
                
        elif current_q["type"] == "text":
            # Check if there's a previous response to use as default
            default_text = ""
            if question_id in st.session_state.responses:
                prev_response = st.session_state.responses[question_id].get("response", "")
                if isinstance(prev_response, str):
                    default_text = prev_response
                    
            response = st.text_area(
                "Your response:", 
                value=default_text,
                height=150,
                help=current_q.get("help_text", "")
            )
        
        # Navigation buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.session_state.current_question_index > 0:
                if st.button("← Previous", key="prev_btn"):
                    # Save current response
                    save_response(current_q, question_id, response)
                    # Go back
                    st.session_state.current_question_index -= 1
                    st.rerun()
        
        with col2:
            next_button_label = "Next →"
            if st.session_state.current_question_index == total_questions - 1:
                next_button_label = "Complete Assessment"
                
            if st.button(next_button_label, key="next_btn", type="primary"):
                # Save response
                save_response(current_q, question_id, response)
                
                if st.session_state.current_question_index == total_questions - 1:
                    # Move to processing
                    st.session_state.current_view = "processing"
                    st.rerun()
                else:
                    # Next question
                    st.session_state.current_question_index += 1
                    st.rerun()

def save_response(question, question_id, response_value):
    """Save a response to the session state"""
    if question["type"] == "multiselect" or response_value:
        st.session_state.responses[question_id] = {
            "question_id": question_id,
            "question_text": question["question"],
            "question_type": question["type"],
            "response": response_value,
            "timestamp": datetime.now().isoformat()
        }

def render_processing_view():
    """Process assessment and generate results"""
    st.title("Processing Your Assessment")
    
    # Show processing message
    with st.spinner("Analyzing your responses and generating personalized guidance..."):
        try:
            # Get assessment result
            st.session_state.results = get_assessment_result(st.session_state.responses)
            
            # Generate guide
            st.session_state.guide = generate_guide(
                st.session_state.responses,
                st.session_state.results
            )
            
            # Save to history
            save_to_history()
            
            # Move to results
            st.session_state.current_view = "results"
            st.rerun()
            
        except Exception as e:
            st.error(f"Error processing your assessment: {str(e)}")
            st.write("Please try again or contact support if the issue persists.")
            
            # Add a retry button
            if st.button("Try Again", type="primary"):
                st.session_state.current_view = "processing"
                st.rerun()

def save_to_history():
    """Save the completed assessment to history"""
    # Create history entry
    # Use the user-provided title or default to the grief story
    title = st.session_state.responses.get("assessment_title", {}).get("response", "")
    if not title and "grief_story" in st.session_state.responses:
        # Use the first 50 characters of grief story as title if not provided
        grief_story = st.session_state.responses["grief_story"].get("response", "")
        title = grief_story[:50] + "..." if len(grief_story) > 50 else grief_story
    
    if not title:
        title = "Grief Assessment"
    
    history_entry = {
        "id": str(datetime.now().timestamp()),
        "date": datetime.now().isoformat(),
        "title": title,
        "responses": st.session_state.responses,
        "results": st.session_state.results,
        "guide": st.session_state.guide,
        "guidance_conversation": st.session_state.guidance_conversation
    }
    
    # Add to history (at beginning to show most recent first)
    st.session_state.assessment_history.insert(0, history_entry)

def render_results_view():
    """Render assessment results and guidance in a single view"""
    # Check if we have results
    if not st.session_state.results or not st.session_state.guide:
        st.error("No assessment results available. Please complete an assessment first.")
        
        if st.button("Start New Assessment", type="primary"):
            st.session_state.current_view = "story"
            st.rerun()
        return
    
    # Main title
    st.title("Your Personalized Grief Assessment")
    
    # Basic info about the loss
    cause = st.session_state.responses.get("cause_of_death", {}).get("response", "Not specified")
    relationship = st.session_state.responses.get("relationship", {}).get("response", "Not specified")
    time_period = st.session_state.responses.get("time_since_loss", {}).get("response", "Not specified")
    
    # Display in columns
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Relationship", relationship)
    with col2:
        st.metric("Cause", cause)
    with col3:
        st.metric("Time Since Loss", time_period)
    
    # Assessment Summary - Detailed section
    st.header("Assessment Summary")
    st.write(st.session_state.results.get("summary", ""))
    
    # Display emotional assessment visualization
    st.header("Emotional Assessment")
    
    # Extract emotion data from AI analysis, not from user responses
    emotion_analysis = None
    if "emotion_analysis" in st.session_state.results:
        emotion_analysis = st.session_state.results.get("emotion_analysis", {})
    
    # Check if we have emotion data
    if emotion_analysis and "emotions" in emotion_analysis:
        try:
            import plotly.express as px
            import pandas as pd
            import plotly.graph_objects as go
            
            # Extract emotions and intensities from the AI analysis
            emotions = []
            intensities = []
            reasons = []
            
            for emotion_data in emotion_analysis["emotions"]:
                emotions.append(emotion_data["name"])
                intensities.append(emotion_data["intensity"])
                reasons.append(emotion_data.get("reasoning", ""))
            
            if emotions and intensities:
                # Create dataframe for plotting
                df = pd.DataFrame({
                    'Emotion': emotions,
                    'Intensity': intensities,
                    'Reason': reasons
                })
                
                # Sort by intensity for the bar chart
                df_sorted = df.sort_values('Intensity', ascending=False)
                
                # Create visualization - use full width instead of columns since we're removing the radar chart
                
                # Create bar chart
                fig_bar = px.bar(
                    df_sorted, 
                    x='Emotion', 
                    y='Intensity',
                    color='Intensity',
                    color_continuous_scale='Viridis',
                    title="Emotion Intensity",
                    height=400
                )
                
                fig_bar.update_layout(
                    xaxis_title="",
                    yaxis_title="Intensity (0-10)",
                    coloraxis_showscale=False
                )
                
                st.plotly_chart(fig_bar, use_container_width=True)
                
                # Add explanation of emotion profile
                st.markdown("**Understanding Your Emotion Profile**: This visualization shows the key emotions our AI has detected in your grief journey and their relative intensities. Recognizing these emotions is an important step in processing grief.")
                
                # Display the reasoning for each emotion
                st.subheader("Emotion Analysis Details")
                for i, (emotion, intensity, reason) in enumerate(zip(df_sorted['Emotion'], df_sorted['Intensity'], df_sorted['Reason'])):
                    st.markdown(f"**{emotion}** (Intensity: {intensity}/10): {reason}")
        except Exception as e:
            st.error(f"Could not generate emotion visualization: {str(e)}")
            st.info("Our AI system was still able to analyze your emotions, but we couldn't create the visualization.")
    else:
        st.info("We weren't able to generate an emotional analysis. This could be due to limited information in your responses.")
    
    # Recommendations
    st.header("Key Recommendations")
    for rec in st.session_state.results.get("recommendations", []):
        st.write(f"• {rec}")
    
    # Display guide
    st.header("Your Personalized Grief Guide")
    guide = st.session_state.guide
    
    # Guide title and introduction
    st.subheader(guide.get('title', 'Your Grief Support Guide'))
    st.write(guide.get("introduction", ""))
    
    # Weekly Plan section
    st.subheader("Your 7-Day Healing Plan")
    st.write("This weekly routine is designed specifically for your grief journey.")
    
    # Display daily routines without nesting expanders
    daily_routines = guide.get("weekly_routine", {})
    
    for day, routines in daily_routines.items():
        st.markdown(f"**Day {day}: {routines.get('key_focus', '')}**")
        st.markdown("---")
        
        if "hourly_schedule" in routines:
            hourly_schedule = routines["hourly_schedule"]
            for hour, activity in hourly_schedule.items():
                st.markdown(f"**{hour}:** {activity}")
        
        # Add space between days
        st.markdown("<br>", unsafe_allow_html=True)
    
    # Self-Care Strategies
    st.header("Self-Care Strategies")
    self_care = guide.get("self_care", {})
    
    with st.expander("Physical Self-Care", expanded=True):
        st.markdown("#### Physical Activity")
        st.write(self_care.get("physical_activity", ""))
    
    with st.expander("Nutritional Self-Care", expanded=True):
        st.markdown("#### Nourishing Meal")
        st.write(self_care.get("nourishing_meal", ""))
    
    with st.expander("Evening Self-Care", expanded=True):
        st.markdown("#### Evening Ritual")
        st.write(self_care.get("evening_ritual", ""))
    
    # Resources
    st.header("Resources & Support")
    resources = guide.get("resources", {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Support groups
        st.subheader("Support Groups")
        if "support_groups" in resources and resources["support_groups"]:
            for group in resources["support_groups"]:
                st.markdown(f"- **[{group.get('name')}]({group.get('url')}):** {group.get('description')}")
        else:
            st.write("No specific support groups were identified for your situation.")
    
    with col2:
        # Hotlines
        st.subheader("Hotlines & Crisis Support")
        if "hotlines" in resources and resources["hotlines"]:
            for hotline in resources["hotlines"]:
                st.markdown(f"- **{hotline.get('name')}:** {hotline.get('number')} - {hotline.get('description')}")
        else:
            st.write("No specific hotlines were identified for your situation.")
    
    # Books
    st.subheader("Recommended Reading")
    if "books" in resources and resources["books"]:
        book_cols = st.columns(min(3, len(resources["books"])))
        for i, book in enumerate(resources["books"]):
            with book_cols[i % len(book_cols)]:
                st.markdown(f"**{book.get('title')}**")
                st.markdown(f"by {book.get('author')}")
                st.markdown(f"_{book.get('description')}_")
    else:
        st.write("No specific books were identified for your situation.")
    
    # Download options
    st.header("Download Your Guide")
    
    if st.button("Download as PDF", type="primary", key="pdf_download"):
        try:
            from ui.components import create_guide_pdf
            pdf_bytes = create_guide_pdf(guide)
            
            if pdf_bytes:
                import base64
                b64 = base64.b64encode(pdf_bytes).decode()
                href = f'<a href="data:application/pdf;base64,{b64}" download="grief_guide.pdf">Click here if download doesn\'t start automatically</a>'
                
                st.markdown(href, unsafe_allow_html=True)
                st.success("Download initiated!")
            else:
                st.error("Could not generate PDF. Please try again later.")
        except Exception as e:
            st.error(f"Error generating PDF: {str(e)}")
            st.info("PDF generation is not available. Please try again later.")
    
    # Interactive guidance chat
    st.markdown("---")
    st.header("Interactive Grief Support")
    st.subheader("Ask for Additional Guidance")
    st.write("If you need more specific guidance or have questions about your grief journey, ask below.")
    
    # Display previous conversation
    if st.session_state.guidance_conversation:
        st.markdown("### Previous Conversation")
        for exchange in st.session_state.guidance_conversation:
            with st.chat_message("user"):
                st.write(exchange.get("user_message", ""))
            with st.chat_message("assistant"):
                st.write(exchange.get("ai_response", ""))
    
    # Input for new guidance questions
    user_question = st.chat_input("Ask your question here...")
    
    if user_question:
        # Display user message
        with st.chat_message("user"):
            st.write(user_question)
        
        # Generate and display AI response
        with st.chat_message("assistant"):
            with st.spinner("Generating guidance..."):
                try:
                    ai_response = generate_followup_response(user_question, guide)
                    st.write(ai_response)
                    
                    # Save to conversation history
                    st.session_state.guidance_conversation.append({
                        "user_message": user_question,
                        "ai_response": ai_response,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Update in history
                    for entry in st.session_state.assessment_history:
                        if (entry.get("responses") == st.session_state.responses and 
                            entry.get("results") == st.session_state.results):
                            entry["guidance_conversation"] = st.session_state.guidance_conversation
                except Exception as e:
                    st.error(f"Error generating response: {str(e)}")
                    st.write("I apologize, but I couldn't generate a response at this time. Please try again later.")

if __name__ == "__main__":
    main() 