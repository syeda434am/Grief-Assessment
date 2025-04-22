import streamlit as st
import uuid
import datetime
import json
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import numpy as np
import io
from PIL import Image
from services.ai_service import get_assessment_result, get_emotion_scores
from services.guide_service import generate_guide
from config.questions import get_assessment_questions, get_dynamic_questions, get_emotion_labels
import seaborn as sns

# Define the fixed list of grief emotions that will be analyzed - ensuring we have 10-15 emotions
GRIEF_EMOTIONS = [
    "Sadness", "Yearning/Missing", "Guilt", "Anger", "Denial", 
    "Anxiety", "Loneliness", "Depression", "Numbness", "Shock", 
    "Regret", "Despair", "Resentment", "Acceptance", "Hope"
]

# Parrot image color palette
PARROT_COLORS = [
    "#051341",  # Dark navy blue
    "#1501A1",  # Vibrant blue 
    "#FF4801",  # Bright orange
    "#DB2C1D",  # Red
    "#FFC000",  # Yellow (from parrot's eye)
    "#3273DC",  # Lighter blue
    "#E5693A",  # Orange-red
    "#7D43BB",  # Purple
    "#1C5FAA",  # Medium blue
    "#FF7456",  # Coral
    "#5936AC",  # Indigo
    "#FFA420",  # Light orange
    "#8A1B1B",  # Dark red
    "#357DED",  # Royal blue
    "#FF9966"   # Peach
]

def init_assessment_session():
    """Initialize the assessment session state variables"""
    if 'assessment_id' not in st.session_state:
        st.session_state.assessment_id = str(uuid.uuid4())
    
    if 'current_question_index' not in st.session_state:
        st.session_state.current_question_index = 0
    
    if 'responses' not in st.session_state:
        st.session_state.responses = {}
    
    if 'assessment_complete' not in st.session_state:
        st.session_state.assessment_complete = False
    
    if 'assessment_result' not in st.session_state:
        st.session_state.assessment_result = None
        
    if 'guide_generated' not in st.session_state:
        st.session_state.guide_generated = False
        
    if 'dynamic_questions' not in st.session_state:
        st.session_state.dynamic_questions = []

def render_assessment():
    """Render the assessment questions and process responses"""
    init_assessment_session()
    
    st.title("Grief Assessment")
    
    # Get base questions
    questions = get_assessment_questions()
    
    # If we have enough responses, get dynamic questions
    if len(st.session_state.responses) >= 3 and not st.session_state.dynamic_questions:
        st.session_state.dynamic_questions = get_dynamic_questions(st.session_state.responses)
    
    # Combine base and dynamic questions
    all_questions = questions + st.session_state.dynamic_questions
    
    if st.session_state.assessment_complete:
        render_assessment_results()
        return
    
    # Display progress
    total_questions = len(all_questions)
    progress = min(1.0, st.session_state.current_question_index / total_questions)
    
    st.progress(progress)
    st.write(f"Question {st.session_state.current_question_index + 1} of {total_questions}")
    
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
        
        # Container for navigation buttons
        st.container()
        
        # Add some space before the buttons
        st.write("")
        st.write("")
        
        # Navigation buttons in two columns
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.session_state.current_question_index > 0:
                if st.button("← Previous", key="prev_btn", use_container_width=True):
                    # Save the current response before moving back
                    save_response(current_q, question_id, response)
                    # Move to previous question
                    st.session_state.current_question_index -= 1
                    st.rerun()
        
        with col2:
            next_button_label = "Next →"
            if st.session_state.current_question_index == total_questions - 1:
                next_button_label = "Complete Assessment"
                
            if st.button(next_button_label, key="next_btn", type="primary", use_container_width=True):
                # Save response
                save_response(current_q, question_id, response)
                
                if st.session_state.current_question_index == total_questions - 1:
                    # Complete the assessment
                    # Create a placeholder for loading message
                    with st.spinner("Processing your assessment..."):
                        # Set complete flag before processing to prevent double submissions
                        st.session_state.assessment_complete = True
                        # Process the assessment
                        try:
                            complete_assessment()
                            # Force rerun to show results immediately
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error processing assessment: {str(e)}")
                            # If there's an error, still keep complete flag true but show error
                            st.session_state.assessment_result = generate_fallback_result()
                            st.rerun()
                else:
                    # Move to next question
                    st.session_state.current_question_index += 1
                    st.rerun()
    
    # Add fixed Next button to bottom right
    with st.container():
        st.markdown(
            """
            <style>
            .fixed-button {
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 1000;
                border-radius: 50%;
                width: 60px;
                height: 60px;
                font-size: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
                background-color: #4CAF50;
                color: white;
                border: none;
                cursor: pointer;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            }
            </style>
            """,
            unsafe_allow_html=True
        )

def save_response(question, question_id, response_value):
    """Save a response to the session state"""
    if not response_value:
        # For multiselect, an empty list is a valid response
        if question["type"] == "multiselect" and response_value == []:
            pass
        # For other types, skip saving empty responses
        elif question["type"] != "multiselect":
            return
    
    # Create response data object
    response_data = {
        "question_id": question_id,
        "question_text": question["question"],
        "question_type": question["type"],
        "response": response_value,
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    # Save to session state
    st.session_state.responses[question_id] = response_data

def complete_assessment():
    """Process the completed assessment"""
    try:
        # Mark as complete if not already done
        if not st.session_state.assessment_complete:
            st.session_state.assessment_complete = True
        
        # Generate assessment result using AI
        st.session_state.assessment_result = get_assessment_result(st.session_state.responses)
        
        # Save assessment to history
        save_assessment_to_history()
        
    except Exception as e:
        # Log error but don't break the flow
        print(f"Error in complete_assessment: {str(e)}")
        st.session_state.assessment_result = generate_fallback_result()

def render_assessment_results():
    """Display assessment results from session state"""
    st.markdown("# Assessment Results")
    
    # Handle missing results
    if 'results' not in st.session_state or not st.session_state.results:
        st.error("No assessment results available. The Groq API may have failed to process your assessment.")
        st.warning("Please make sure your Groq API key is correctly set in the .env file (GROQ_API_KEY=your_api_key)")
        if st.button("Start New Assessment"):
            st.session_state.current_step = "story"
            st.rerun()
        return
    
    result = st.session_state.results
    
    # Display basic information
    st.subheader("Assessment Information")
    
    # Extract basic info from responses
    cause = st.session_state.responses.get("cause_of_death", {}).get("response", "Not specified")
    relationship = st.session_state.responses.get("relationship", {}).get("response", "Not specified")
    time_period = st.session_state.responses.get("time_since_loss", {}).get("response", "Not specified")
    employment = st.session_state.responses.get("employment_status", {}).get("response", "Not specified")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Cause", cause)
        st.metric("Relationship", relationship)
    with col2:
        st.metric("Time Since Loss", time_period)
        st.metric("Employment Status", employment)
    
    # Display scores if available
    if "scores" in result:
        st.subheader("Assessment Scores")
        scores = result["scores"]
        score_cols = st.columns(len(scores))
        for i, (category, score) in enumerate(scores.items()):
            with score_cols[i % len(score_cols)]:
                st.metric(label=category.replace("_", " ").title(), value=score)
    
    # Display emotion visualization using the new function
    render_emotion_visualization(st.session_state.responses)
    
    # Display recommendations
    st.subheader("Personalized Recommendations")
    
    # Enhance recommendations if they're limited
    recs = result.get("recommendations", [])
    if len(recs) < 5:
        recs = enhance_recommendations(st.session_state.responses, recs)
        result["recommendations"] = recs
    
    for rec in recs:
        st.write(f"• {rec}")
    
    # Display risk factors if available
    if "risk_factors" in result and result["risk_factors"]:
        st.subheader("Areas for Additional Support")
        st.write("Based on your responses, these areas may benefit from focused attention:")
        
        for factor in result["risk_factors"]:
            if "unable to determine" not in factor.lower():
                st.warning(factor)
    
    # Display guide
    st.subheader("Your Personalized Grief Guide")
    if st.session_state.guide_generated and hasattr(st.session_state, 'guide'):
        guide = st.session_state.guide

def generate_fallback_summary(responses):
    """Generate a meaningful summary based on the responses when AI processing fails"""
    # Extract key information
    cause = responses.get("cause_of_death", {}).get("response", "Not specified")
    time_period = responses.get("time_since_loss", {}).get("response", "Not specified") 
    relationship = responses.get("relationship", {}).get("response", "Not specified")
    current_feelings = responses.get("current_feelings", {}).get("response", "")
    
    # Create personalized summary
    summary = f"""
    Based on your responses, you're grieving the loss of your {relationship.lower()} due to {cause.lower()}. 
    It has been {time_period.lower()} since your loss.
    """
    
    # Add more context based on current feelings
    if current_feelings:
        if current_feelings == "Overwhelmed by intense emotions":
            summary += """
            You're currently experiencing overwhelming emotions, which is completely normal given your loss.
            Your grief is still very raw, and the intensity of your feelings reflects the significance of your relationship.
            """
        elif current_feelings == "Numb or emotionally disconnected":
            summary += """
            You're experiencing emotional numbness, which is a common protective response after a significant loss.
            This numbness is your mind's way of buffering you from overwhelming pain and is a normal part of grief.
            """
        elif current_feelings == "Up and down - emotional waves":
            summary += """
            You're experiencing emotional waves, with periods of intense grief alternating with calmer moments.
            This wave-like pattern is a very normal part of the grief process and reflects how our minds process loss.
            """
        elif current_feelings == "Functioning but struggling internally":
            summary += """
            While you're able to maintain daily functioning, you're experiencing significant internal struggle.
            This is common in grief - many people maintain an external appearance of coping while processing grief privately.
            """
        elif current_feelings == "Gradually finding new balance":
            summary += """
            You're beginning to find a new balance in your life after your loss. This doesn't mean you're "over" your grief,
            but rather that you're learning to integrate this loss into your ongoing life in a meaningful way.
            """
    
    summary += """
    The assessment indicates specific areas where support may be most helpful for you at this time.
    Your personalized recommendations and guide have been created to address these areas.
    """
    
    return summary

def generate_scores(responses):
    """Generate meaningful scores based on responses when AI processing fails"""
    # Default scores
    scores = {
        "grief_intensity": 0,
        "coping_ability": 0,
        "support_network": 0
    }
    
    # Calculate grief intensity (1-10)
    intensity = 5  # Default middle value
    
    # Adjust based on current feelings
    feelings = responses.get("current_feelings", {}).get("response", "")
    if feelings == "Overwhelmed by intense emotions":
        intensity += 3
    elif feelings == "Numb or emotionally disconnected":
        intensity += 2
    elif feelings == "Up and down - emotional waves":
        intensity += 1
    elif feelings == "Gradually finding new balance":
        intensity -= 1
    
    # Adjust based on daily functioning
    functioning = responses.get("daily_functioning", {}).get("response", "")
    if functioning == "I struggle to complete basic daily tasks":
        intensity += 2
    elif functioning == "I manage basic tasks but not much more":
        intensity += 1
    elif feelings == "I'm functioning well most days but grief is still present":
        intensity -= 1
    
    # Adjust based on sleep patterns
    sleep = responses.get("sleep_patterns", {}).get("response", "")
    if sleep == "Significant difficulty falling or staying asleep":
        intensity += 1
    elif sleep == "Disturbed by dreams or nightmares":
        intensity += 1
    
    # Ensure value is within range
    scores["grief_intensity"] = max(1, min(10, intensity))
    
    # Calculate coping ability (1-10)
    coping = 5  # Default middle value
    
    # Adjust based on coping strategies
    strategies = responses.get("coping_strategies", {}).get("response", [])
    coping += min(3, len(strategies) // 2)  # More strategies = better coping, max +3
    
    if "I haven't tried any strategies yet" in strategies:
        coping -= 2
    
    # Adjust based on daily functioning
    if functioning == "I'm functioning well most days but grief is still present":
        coping += 2
    elif functioning == "I function at work/school but it takes all my energy":
        coping += 1
    elif functioning == "I struggle to complete basic daily tasks":
        coping -= 2
    
    # Ensure value is within range
    scores["coping_ability"] = max(1, min(10, coping))
    
    # Calculate support network (1-10)
    support = 5  # Default middle value
    
    # Adjust based on support network
    network = responses.get("support_network", {}).get("response", [])
    support += min(3, len(network) // 2)  # More supporters = better network, max +3
    
    if "No one - I'm handling this alone" in network:
        support -= 3
    
    # Ensure value is within range
    scores["support_network"] = max(1, min(10, support))
    
    return scores

def enhance_recommendations(responses, existing_recs):
    """Enhance recommendations when they are limited or generic"""
    enhanced_recs = list(existing_recs)  # Start with existing recommendations
    
    # Add recommendations based on employment status
    employment = responses.get("employment_status", {}).get("response", "")
    if "Unemployed" in employment:
        enhanced_recs.append("Create a structured daily routine to provide stability during unemployment")
        enhanced_recs.append("Set small daily goals to maintain a sense of purpose and accomplishment")
    elif "Full-time" in employment or "Part-time" in employment:
        enhanced_recs.append("Consider whether to share your loss with colleagues and what boundaries you need")
        enhanced_recs.append("Schedule regular breaks during your workday to process emotions as they arise")
    elif "Student" in employment:
        enhanced_recs.append("Talk to your academic advisor about possible accommodations during this time")
        enhanced_recs.append("Find quiet study spaces where you can focus while managing grief emotions")
    
    # Add recommendations based on relationship type
    relationship = responses.get("relationship", {}).get("response", "")
    if relationship == "Spouse/Partner":
        enhanced_recs.append("Join a widow/widower support group to connect with others who understand your specific loss")
        enhanced_recs.append("Create new rituals to honor special dates and occasions you used to share")
    elif relationship == "Child":
        enhanced_recs.append("Connect with parent bereavement groups that specifically address the unique pain of losing a child")
    elif relationship == "Parent":
        enhanced_recs.append("Explore resources specifically for adults who have lost a parent at your life stage")
    elif relationship == "Pet":
        enhanced_recs.append("Honor your pet's memory through a memorial, photo album, or donation to an animal charity")
        enhanced_recs.append("Connect with pet loss support groups who understand the significant bond with animal companions")
    
    # Add recommendations based on current feelings
    feelings = responses.get("current_feelings", {}).get("response", "")
    if feelings == "Overwhelmed by intense emotions":
        enhanced_recs.append("Practice grounding techniques like deep breathing or the 5-4-3-2-1 sensory exercise when emotions feel overwhelming")
    elif feelings == "Numb or emotionally disconnected":
        enhanced_recs.append("Engage in gentle sensory activities like aromatherapy, warm baths, or textured fabrics to help reconnect with your body")
    
    # Add general recommendations if we still have too few
    if len(enhanced_recs) < 8:
        general_recs = [
            "Keep a grief journal to track your emotions and identify patterns or triggers",
            "Establish a simple self-care routine including basic nutrition, hydration, and rest",
            "Allow yourself to say no to social obligations when you need time for yourself",
            "Create a memory box or digital collection to honor your relationship with the deceased",
            "Try gentle movement like walking or stretching to help process grief physically",
            "Identify and reach out to at least one trusted person you can talk openly with",
            "Explore grief resources such as books, podcasts, or online forums"
        ]
        
        # Add general recommendations until we have at least 8
        for rec in general_recs:
            if rec not in enhanced_recs and len(enhanced_recs) < 8:
                enhanced_recs.append(rec)
    
    return enhanced_recs

def infer_emotions_from_responses(responses):
    """Infer emotions based on response patterns when not explicitly provided"""
    inferred_emotions = []
    
    # Check for mentions of numbness or shock
    grief_story = responses.get("grief_story", {}).get("response", "").lower()
    emotional_state = responses.get("emotional_state", {}).get("response", "").lower()
    current_feelings = responses.get("current_feelings", {}).get("response", "").lower()
    
    # Check for common emotional patterns
    if "numb" in grief_story or "numb" in emotional_state or "numb" in current_feelings:
        inferred_emotions.append("Numbness")
    
    if "shock" in grief_story or "shock" in emotional_state or "shock" in current_feelings or "can't believe" in grief_story:
        inferred_emotions.append("Shock")
    
    if "angry" in grief_story or "anger" in emotional_state or "angry" in current_feelings or "unfair" in grief_story:
        inferred_emotions.append("Anger")
    
    if "sad" in grief_story or "sadness" in emotional_state or "sad" in current_feelings or "sorrow" in grief_story:
        inferred_emotions.append("Sadness")
        
    if "miss" in grief_story or "longing" in emotional_state or "miss" in current_feelings:
        inferred_emotions.append("Yearning")
    
    if "guilt" in grief_story or "guilt" in emotional_state or "guilt" in current_feelings or "should have" in grief_story:
        inferred_emotions.append("Guilt")
    
    if "relief" in grief_story or "relief" in emotional_state or "relief" in current_feelings:
        inferred_emotions.append("Relief")
    
    if "accept" in grief_story or "acceptance" in emotional_state or "accept" in current_feelings:
        inferred_emotions.append("Acceptance")
    
    if "hope" in grief_story or "hope" in emotional_state or "hope" in current_feelings or "future" in grief_story:
        inferred_emotions.append("Hope")
    
    # If still no emotions, add general grief emotions
    if not inferred_emotions:
        inferred_emotions = ["Sadness", "Anger", "Guilt", "Yearning", "Numbness"]
    
    return inferred_emotions

def get_emotion_scores(responses):
    """Get emotion scores using Groq AI based on the user's responses"""
    from services.guide_service import init_groq_client
    from langchain_core.messages import SystemMessage, HumanMessage
    import json
    
    # Initialize Groq client
    client = init_groq_client()
    if not client:
        return None
    
    try:
        # Extract relevant text from responses for analysis
        grief_story = responses.get("grief_story", {}).get("response", "")
        emotional_state = responses.get("emotional_state", {}).get("response", "")
        current_feelings = responses.get("current_feelings", {}).get("response", "")
        relationship = responses.get("relationship", {}).get("response", "")
        cause_of_death = responses.get("cause_of_death", {}).get("response", "")
        time_since_loss = responses.get("time_since_loss", {}).get("response", "")
        
        # Create a combined text for analysis
        combined_text = f"""
        Grief Story: {grief_story}
        Relationship to Deceased: {relationship}
        Cause of Death: {cause_of_death}
        Time Since Loss: {time_since_loss}
        Emotional State: {emotional_state}
        Current Feelings: {current_feelings}
        """
        
        # Create prompt for emotion scoring
        prompt = f"""
        Based on this person's grief experience, analyze their emotional state and generate a score from 1-10 for each emotion present.
        Only include emotions that are reasonably present in their experience.
        
        {combined_text}
        
        Return ONLY a valid JSON object with emotion names as keys and intensity scores (1-10) as values. 
        The output should look like this: {{"Sadness": 8.5, "Anger": 4.2, "Guilt": 7.1}}
        
        IMPORTANT: Return ONLY the JSON object. No explanations or additional text.
        """
        
        # Get response from Groq
        response = client.invoke(
            [
                SystemMessage(content="""You are an expert in grief psychology with a specialization in detecting emotional states from text.
                Your task is to analyze grief narratives and identify the intensity of different emotions present.
                IMPORTANT: Always return VALID JSON with emotion names as keys and numeric scores as values. Do not include any explanations or text outside the JSON object."""),
                HumanMessage(content=prompt)
            ]
        )
        
        # Process the response
        response_content = response.content.strip()
        
        # Clean the response of any markdown code blocks
        import re
        response_content = re.sub(r'```json\s*|\s*```', '', response_content).strip()
        
        # Find the JSON object in the response
        start_idx = response_content.find('{')
        end_idx = response_content.rfind('}') + 1
        
        if start_idx >= 0 and end_idx > start_idx:
            response_content = response_content[start_idx:end_idx]
            
        # Parse JSON
        emotion_scores = json.loads(response_content)
        
        return emotion_scores
    
    except Exception as e:
        st.error(f"Error generating emotion scores: {str(e)}")
        return None

def display_guide():
    """Display the generated guide"""
    if not hasattr(st.session_state, 'guide') or not st.session_state.guide:
        st.warning("No guide has been generated yet")
        return
    
    guide = st.session_state.guide
    
    # Display guide sections
    st.markdown(f"### {guide.get('title', 'Your Personalized Grief Support Guide')}")
    
    # Overview section
    st.markdown("#### Overview")
    st.write(guide.get("introduction", ""))
    
    # Create tabs for different sections of the guide
    guide_tabs = st.tabs(["Weekly Routine", "Self-Care Strategies", "Resources", "Download"])
    
    # Weekly Routine
    with guide_tabs[0]:
        st.markdown("### Your 7-Day Healing Plan")
        st.write("This weekly routine is designed specifically for your grief journey.")
        
        # Display daily routines
        daily_routines = guide.get("weekly_routine", {})
        
        for day, routines in daily_routines.items():
            with st.expander(f"Day {day}: {routines.get('key_focus', '')}"):
                if "hourly_schedule" in routines:
                    hourly_schedule = routines["hourly_schedule"]
                    for hour, activity in hourly_schedule.items():
                        st.markdown(f"**{hour}:**")
                        st.write(activity)
                else:
                    # Fallback for old format
                    if "morning" in routines:
                        st.markdown("**Morning:**")
                        st.write(routines["morning"])
                    
                    if "afternoon" in routines:
                        st.markdown("**Afternoon:**")
                        st.write(routines["afternoon"])
                    
                    if "evening" in routines:
                        st.markdown("**Evening:**")
                        st.write(routines["evening"])
    
    # Self-Care Strategies
    with guide_tabs[1]:
        st.markdown("### Self-Care Strategies")
        st.write("These strategies are tailored to support your grief healing journey.")
        
        self_care = guide.get("self_care", {})
        
        # Physical activity
        st.markdown("#### Physical Activity")
        st.write(self_care.get("physical_activity", ""))
        
        # Nourishing meal
        st.markdown("#### Nourishing Meal")
        st.write(self_care.get("nourishing_meal", ""))
        
        # Evening ritual
        st.markdown("#### Evening Ritual")
        st.write(self_care.get("evening_ritual", ""))
    
    # Resources
    with guide_tabs[2]:
        st.markdown("### Resources")
        st.write("These resources have been curated to provide support for your specific situation.")
        
        resources = guide.get("resources", {})
        
        # Support groups
        if "support_groups" in resources:
            st.markdown("#### Support Groups")
            for group in resources["support_groups"]:
                st.markdown(f"- [{group.get('name')}]({group.get('url')}): {group.get('description')}")
        
        # Books
        if "books" in resources:
            st.markdown("#### Books")
            for book in resources["books"]:
                st.markdown(f"- **{book.get('title')}** by {book.get('author')}: {book.get('description')}")
        
        # Hotlines
        if "hotlines" in resources:
            st.markdown("#### Hotlines & Crisis Support")
            for hotline in resources["hotlines"]:
                st.markdown(f"- **{hotline.get('name')}**: {hotline.get('number')} - {hotline.get('description')}")
        
        # Professional services
        if "professional_services" in resources:
            st.markdown("#### Professional Services")
            for service in resources["professional_services"]:
                st.markdown(f"- **{service.get('name')}**: {service.get('description')}")
    
    # Download options
    with guide_tabs[3]:
        st.markdown("### Download Your Guide")
        st.write("Save your personalized guide in your preferred format.")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Download PDF", type="primary", use_container_width=True):
                st.info("PDF download functionality will be implemented in Phase 3.")
        
        with col2:
            if st.button("Download DOCX", use_container_width=True):
                st.info("DOCX download functionality will be implemented in Phase 3.")
        
        with col3:
            if st.button("Download TXT", use_container_width=True):
                st.info("TXT download functionality will be implemented in Phase 3.")

def save_assessment_to_history():
    """Save the completed assessment to history"""
    # Use existing assessment title if available, otherwise generate from grief story
    if 'assessment_title' in st.session_state:
        title = st.session_state.assessment_title
    else:
        # Generate a title for the session from the grief story
        grief_story = st.session_state.responses.get("grief_story", {}).get("response", "")
        title = "Grief Assessment"
        
        # Extract a title from the grief story if available
        if grief_story:
            # Use the first sentence or first 50 characters
            first_sentence = grief_story.split('.')[0].strip()
            if len(first_sentence) > 50:
                title = first_sentence[:47] + "..."
            else:
                title = first_sentence
    
    # Create assessment history entry
    history_entry = {
        "id": st.session_state.assessment_id,
        "title": title,
        "date": datetime.datetime.now().isoformat(),
        "responses": st.session_state.responses,
        "results": st.session_state.assessment_result,
        "guide": st.session_state.get("guide", None)
    }
    
    # Ensure assessment_history exists in session state
    if 'assessment_history' not in st.session_state:
        st.session_state.assessment_history = []
    
    # Add to history (insert at beginning for reverse chronological order)
    st.session_state.assessment_history.insert(0, history_entry)
    
    # Save to file system
    save_to_file(history_entry)

def save_to_file(assessment_data):
    """Save assessment data to file system"""
    # Create data directory if it doesn't exist
    os.makedirs('data/assessments', exist_ok=True)
    
    # Save to file
    filename = f"data/assessments/assessment_{assessment_data['id']}.json"
    with open(filename, 'w') as f:
        json.dump(assessment_data, f, indent=2)

def start_new_assessment():
    """Reset assessment-related session state for a new assessment"""
    # Generate new ID
    st.session_state.assessment_id = str(uuid.uuid4())
    st.session_state.current_question_index = 0
    st.session_state.responses = {}
    st.session_state.dynamic_questions = []
    st.session_state.assessment_complete = False
    st.session_state.assessment_result = None
    st.session_state.guide_generated = False
    
    # Clear story-related state
    if 'grief_story' in st.session_state:
        del st.session_state.grief_story
    if 'assessment_title' in st.session_state:
        del st.session_state.assessment_title
    
    if 'guide' in st.session_state:
        del st.session_state.guide
    
    # Set current step to story
    st.session_state.current_step = "story"

def generate_fallback_result():
    """Generate a fallback result when assessment processing fails"""
    return {
        "summary": generate_fallback_summary(st.session_state.responses),
        "scores": generate_scores(st.session_state.responses),
        "recommendations": enhance_recommendations(st.session_state.responses, [
            "Speak with a mental health professional",
            "Consider joining a grief support group",
            "Practice self-care routines",
            "Maintain connections with supportive friends and family"
        ]),
        "risk_factors": []
    }

def visualize_emotions(emotion_scores):
    """
    Create an attractive horizontal bar chart visualization of emotion scores
    using the parrot color palette.
    
    Args:
        emotion_scores (dict): Dictionary of emotions and their scores
        
    Returns:
        bytes: Image bytes of the visualization
    """
    # Always include all emotions from our fixed list
    emotions = []
    scores = []
    
    # Process emotions from the fixed list
    for emotion in GRIEF_EMOTIONS:
        # Look for exact or partial matches in the scores
        found = False
        for key, value in emotion_scores.items():
            if emotion.lower() in key.lower() or key.lower() in emotion.lower():
                emotions.append(emotion)
                scores.append(float(value))
                found = True
                break
        
        # If not found, add with zero score
        if not found:
            emotions.append(emotion)
            scores.append(0.1)  # Very tiny presence (for visibility)
    
    # Sort by score descending
    sorted_indices = np.argsort(scores)[::-1]
    emotions = [emotions[i] for i in sorted_indices]
    scores = [scores[i] for i in sorted_indices]
    
    # Create the visualization with white background
    plt.figure(figsize=(10, 8))
    
    # Set white background
    plt.rcParams['figure.facecolor'] = 'white'
    plt.rcParams['axes.facecolor'] = 'white'
    
    # Create the horizontal bar chart with parrot colors
    # Limit colors to the number of emotions we have
    colors = PARROT_COLORS[:len(emotions)]
    
    # Create horizontal bar chart with custom colors
    bars = plt.barh(emotions, scores, color=colors, alpha=0.9)
    
    # Add value labels to bars
    for i, v in enumerate(scores):
        if v > 0.5:  # Only add text if the bar is visible enough
            plt.text(v + 0.1, i, f'{v:.1f}', 
                     va='center', 
                     fontweight='bold', 
                     fontsize=11,
                     color='#333333')
    
    # Customize chart appearance
    plt.title('Grief Emotion Intensity', fontsize=18, fontweight='bold', pad=20)
    plt.xlabel('Intensity (1-10)', fontsize=12, labelpad=10)
    plt.xlim(0, 10.5)  # Make room for labels
    
    # Add a border box around the figure
    plt.box(True)
    
    # Remove top and right spines, keep left and bottom
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['left'].set_color('#dddddd')
    plt.gca().spines['bottom'].set_color('#dddddd')
    
    # Set subtle grid
    plt.grid(axis='x', linestyle='--', alpha=0.3, color='#cccccc')
    
    # Customize tick appearance
    plt.tick_params(axis='both', which='major', labelsize=11)
    plt.yticks(fontweight='bold')
    
    # Add explanation as a caption
    plt.figtext(0.5, 0.01, 
                'Intensity of emotions identified in your grief experience (1-10 scale)',
                ha='center', fontsize=10, style='italic')
    
    # Tight layout for better fit
    plt.tight_layout(rect=[0, 0.03, 1, 0.97])
    
    # Save to bytes
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    
    # Close the figure to free memory
    plt.close()
    
    return buf

def render_emotion_visualization(responses):
    """
    Render the emotion visualization section based on AI analysis of responses
    
    Args:
        responses (dict): Assessment responses
    """
    st.subheader("Grief Emotion Intensity Profile")
    
    # Try to get emotion scores using Groq AI
    try:
        emotion_scores = get_emotion_scores(responses)
        
        if emotion_scores and len(emotion_scores) > 0:
            # Generate visualization
            img_bytes = visualize_emotions(emotion_scores)
            
            # Display visualization
            st.image(Image.open(img_bytes), use_column_width=True)
            
            # Add some insight about the emotions
            primary_emotions = sorted(emotion_scores.items(), key=lambda x: x[1], reverse=True)[:3]
            
            st.markdown("### Key Insights")
            st.markdown(f"Your grief profile shows strongest presence of: **{', '.join([e[0] for e in primary_emotions])}**")
            
            # Add insights based on emotional patterns
            emotions_present = [e[0].lower() for e in primary_emotions]
            
            if any(e in ["guilt", "regret"] for e in emotions_present):
                st.info("The presence of guilt or regret is common in grief, especially when we wonder if we could have done more. Remember that hindsight gives us a perspective we couldn't have had at the time.")
            
            if any(e in ["anger", "resentment"] for e in emotions_present):
                st.info("Anger is a natural grief response and can be directed at the situation, others involved, or even the person who died. Acknowledging this anger without judgment is an important part of processing it.")
            
            if any(e in ["shock", "numbness", "denial"] for e in emotions_present):
                st.info("Emotional numbness and shock are protective responses that buffer us from overwhelming pain. This is your mind's way of processing grief gradually.")
            
            if any(e in ["sadness", "yearning", "missing", "loneliness"] for e in emotions_present):
                st.info("The sadness and yearning you feel reflect the depth of your attachment. These emotions honor the importance of your relationship and the significance of your loss.")
            
            if any(e in ["acceptance", "hope"] for e in emotions_present):
                st.info("The presence of acceptance or hope alongside other grief emotions suggests you're beginning to integrate this loss into your life narrative. This doesn't mean you're 'over it,' but that you're finding ways to carry it.")
            
            # Add information about how emotions may change
            st.markdown("### About Your Grief Journey")
            st.markdown("""
            Your emotional experience of grief is unique and will likely change over time. Some days may feel 
            more intense than others. All emotions are a valid part of grief - there is no 'right way' to grieve.
            
            This profile represents your emotional landscape at this moment in time. Revisiting this assessment 
            periodically can help you track changes in your grief journey.
            """)
        else:
            st.warning("We couldn't generate a detailed emotion analysis. This doesn't mean your emotions aren't valid - grief affects everyone differently.")
    except Exception as e:
        st.error(f"Error generating emotion visualization: {str(e)}")
        st.warning("We weren't able to generate an emotion profile visualization. This doesn't mean your emotions aren't valid - grief affects everyone differently.") 