import streamlit as st
import datetime

def display_story_entry():
    """Display the initial story entry page where users share their grief experience"""
    st.title("Share Your Grief Story")
    
    # Initialize story-related session state if not exists
    if 'grief_story' not in st.session_state:
        st.session_state.grief_story = ""
    
    # Introduction text
    st.markdown("""
    ## Before we begin the assessment
    
    Please share your grief experience with us. This helps us better understand your 
    journey and provide more personalized guidance.
    
    Tell us about:
    - What loss you're experiencing
    - Your relationship with the person/thing you've lost
    - How this loss has affected you
    
    Your story will be saved with your assessment and will help guide our recommendations.
    """)
    
    # Word counter function for JavaScript
    st.markdown("""
    <script>
    function countWords(text) {
        return text.trim().split(/\s+/).filter(Boolean).length;
    }
    
    function updateCounter(textarea) {
        const words = countWords(textarea.value);
        document.getElementById('word-counter').textContent = words + '/1000 words';
        
        if (words > 1000) {
            document.getElementById('word-counter').style.color = 'red';
        } else {
            document.getElementById('word-counter').style.color = '';
        }
    }
    </script>
    """, unsafe_allow_html=True)
    
    # Text area with custom styling for word counter
    st.markdown("""
    <style>
    .word-counter-container {
        display: flex;
        flex-direction: column;
    }
    .word-counter {
        align-self: flex-end;
        font-size: 0.8rem;
        color: #666;
        margin-top: 0.2rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Word counter display (Streamlit doesn't support JavaScript directly, so we'll use a workaround)
    # This creates a text area and calculates word count on the server side
    grief_story = st.text_area(
        "Your grief story:",
        value=st.session_state.grief_story,
        height=300,
        help="Write your grief story within 1000 words. This will help us provide personalized guidance."
    )
    
    # Count words and display counter
    words = len(grief_story.split()) if grief_story else 0
    word_count_color = "red" if words > 1000 else "#666"
    st.markdown(f"""<div style="text-align: right; font-size: 0.8rem; color: {word_count_color};">
        {words}/1000 words
    </div>""", unsafe_allow_html=True)
    
    # Save button and validation
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("← Back to Home", key="back_btn", use_container_width=True):
            st.session_state.current_step = "intro"
            st.rerun()
    
    with col2:
        continue_disabled = words == 0 or words > 1000
        
        if continue_disabled:
            st.markdown("""
            <div style="width: 100%; padding: 0.5rem; background-color: #f0f0f0; border-radius: 0.3rem; 
                 color: #888; text-align: center; cursor: not-allowed;">
                Continue to Assessment →
            </div>
            """, unsafe_allow_html=True)
            
            if words > 1000:
                st.error("Your story exceeds the 1000-word limit. Please shorten it to continue.")
            elif words == 0:
                st.warning("Please share your story to continue.")
        else:
            if st.button("Continue to Assessment →", key="continue_btn", type="primary", use_container_width=True):
                # Save the story to session state
                st.session_state.grief_story = grief_story
                
                # Create a title for the assessment
                title = generate_title_from_story(grief_story)
                st.session_state.assessment_title = title
                
                # Prepare for assessment
                prepare_assessment()
                
                # Move to assessment
                st.session_state.current_step = "assessment"
                st.rerun()

def generate_title_from_story(story):
    """Generate a title from the grief story"""
    # Simple implementation - use the first sentence or first few words
    if not story:
        return "Grief Assessment"
    
    # Try to get the first sentence
    first_sentence = story.split('.')[0].strip()
    
    # If first sentence is too long, use the first 50 characters
    if len(first_sentence) > 50:
        title = first_sentence[:47] + "..."
    else:
        title = first_sentence
    
    return title

def prepare_assessment():
    """Prepare session state for assessment after story is entered"""
    # Initialize assessment session variables
    if 'responses' not in st.session_state:
        st.session_state.responses = {}
    
    # Store the grief story as the first response
    st.session_state.responses["grief_story"] = {
        "question_id": "grief_story",
        "question_text": "Please share briefly about your loss and how it has affected you.",
        "question_type": "text",
        "response": st.session_state.grief_story,
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    # Initialize or reset other assessment variables
    st.session_state.current_question_index = 0
    st.session_state.assessment_complete = False
    st.session_state.dynamic_questions = [] 