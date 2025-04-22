import streamlit as st
import requests
import json
import time
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="Master Grief - Assessment Tool",
    page_icon="❤️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #4a4a4a;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #6a6a6a;
        margin-bottom: 1rem;
    }
    .question-text {
        font-size: 1.2rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
    }
    .info-box {
        background-color: #f0f7ff;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .story-box {
        background-color: #f9f9f9;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 5px solid #9370DB;
    }
    .results-container {
        background-color: #f9f9f9;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-top: 1rem;
        border-left: 5px solid #6495ED;
    }
    .resource-card {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.8rem;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .resource-title {
        font-weight: 600;
        color: #4a4a4a;
    }
    .section-divider {
        margin: 1.5rem 0;
        border-top: 1px solid #e0e0e0;
    }
    .progress-container {
        margin: 1rem 0;
    }
    .char-counter {
        color: #6a6a6a;
        font-size: 0.8rem;
        text-align: right;
    }
</style>
""", unsafe_allow_html=True)

# Assessment questions
GRIEF_ASSESSMENT_QUESTIONS = {
    "personalStory": [
        {
            "id": "ps1",
            "question": "Please share your grief experience with us. What loss are you going through? This could be the loss of a loved one, a relationship, a job, or any other significant loss in your life.",
            "type": "text_area",
            "max_chars": 1000
        }
    ],
    "emotionalState": [
        {
            "id": "e1",
            "question": "How would you describe your predominant emotional state in the past week?",
            "options": [
                "Mostly numb, feeling very little",
                "Predominantly sad, tearful, or depressed",
                "Primarily angry or irritable",
                "Anxious or worried most of the time",
                "Experiencing guilt or regret frequently",
                "Having moments of peace alongside grief",
                "Finding some positive emotions returning"
            ],
            "values": [1, 2, 3, 4, 5, 6, 7]
        },
        {
            "id": "e2",
            "question": "How often do intense waves of grief overtake you?",
            "options": [
                "Almost constantly throughout the day",
                "Several times a day",
                "Once or twice daily",
                "A few times a week",
                "Occasionally, but less frequently than before"
            ],
            "values": [1, 2, 3, 4, 5]
        },
        {
            "id": "e3",
            "question": "How would you describe your ability to experience positive emotions?",
            "options": [
                "I cannot feel any positive emotions at all",
                "I rarely experience positive feelings",
                "I occasionally have brief moments of positive emotions",
                "I can experience positive emotions but they're often tinged with guilt",
                "I'm beginning to experience genuine positive emotions again"
            ],
            "values": [1, 2, 3, 4, 5]
        }
    ],
    
    "griefProcessing": [
        {
            "id": "g1",
            "question": "How do you currently relate to the reality of your loss?",
            "options": [
                "I still find it hard to believe this has actually happened",
                "I intellectually understand the loss but emotionally it doesn't feel real",
                "I'm beginning to accept the reality but it's very painful",
                "I've mostly accepted that this loss is permanent and real",
                "I've fully integrated the reality of this loss into my life"
            ],
            "values": [1, 2, 3, 4, 5]
        },
        {
            "id": "g2",
            "question": "How often do you find yourself thinking about or reviewing memories of your loved one?",
            "options": [
                "I avoid thinking about them because it's too painful",
                "I'm consumed by thoughts and memories most of the time",
                "I think about them frequently but can also focus on other things",
                "I can now reflect on memories with a mixture of sadness and appreciation",
                "I've found a comfortable way to keep their memory present in my life"
            ],
            "values": [1, 2, 3, 4, 5]
        },
        {
            "id": "g3",
            "question": "How would you describe your sense of purpose or meaning since your loss?",
            "options": [
                "Life feels completely meaningless now",
                "I'm struggling to find any purpose",
                "I'm beginning to search for new meaning",
                "I'm starting to develop new purposes and goals",
                "I've found ways to create meaning that honors my loss"
            ],
            "values": [1, 2, 3, 4, 5]
        }
    ],
    
    "coping": [
        {
            "id": "c1",
            "question": "What strategies do you most often use to cope with painful feelings? (Select all that apply)",
            "options": [
                "Talking with supportive people",
                "Journaling or creative expression",
                "Physical exercise or movement",
                "Mindfulness or meditation",
                "Keeping busy with activities or work",
                "Taking time alone to process feelings",
                "Using alcohol or substances to numb feelings",
                "Avoiding reminders of the loss entirely",
                "Working excessively to avoid feelings"
            ],
            "values": [
                "healthy", "healthy", "healthy", "healthy", 
                "neutral", "neutral",
                "unhealthy", "unhealthy", "unhealthy"
            ],
            "multiSelect": True
        },
        {
            "id": "c2",
            "question": "How are you taking care of your basic needs?",
            "options": [
                "I'm struggling significantly with sleep, eating, and self-care",
                "I'm inconsistent with basic self-care",
                "I'm making efforts but still struggling in some areas",
                "I'm managing most basic needs adequately",
                "I'm consistently maintaining healthy routines"
            ],
            "values": [1, 2, 3, 4, 5]
        }
    ],
    
    "socialSupport": [
        {
            "id": "s1",
            "question": "How would you describe your support system?",
            "options": [
                "I feel completely isolated with no support",
                "I have very limited support",
                "I have some support but it's not always helpful",
                "I have a reliable support network I can turn to",
                "I have strong, consistent support from multiple people"
            ],
            "values": [1, 2, 3, 4, 5]
        },
        {
            "id": "s2",
            "question": "How comfortable do you feel expressing your grief to others?",
            "options": [
                "I don't share my grief with anyone",
                "I rarely feel comfortable showing my grief",
                "I can express grief with select trusted people",
                "I'm generally comfortable expressing my grief when needed",
                "I can authentically share my grief experience with others"
            ],
            "values": [1, 2, 3, 4, 5]
        }
    ],
    
    "functionalImpact": [
        {
            "id": "f1",
            "question": "How is your grief affecting your daily functioning?",
            "options": [
                "I'm unable to maintain basic daily responsibilities",
                "I'm struggling significantly with daily tasks",
                "I manage essential tasks but with difficulty",
                "I'm functioning adequately in most areas",
                "I'm maintaining daily functioning well"
            ],
            "values": [1, 2, 3, 4, 5]
        },
        {
            "id": "f2",
            "question": "How would you describe your ability to find moments of respite from grief?",
            "options": [
                "Grief is constant with no breaks",
                "Rarely get any relief from grief",
                "Occasionally find brief periods of respite",
                "Regularly experience periods without active grief",
                "Balance grief with significant periods of normal functioning"
            ],
            "values": [1, 2, 3, 4, 5]
        }
    ],
    
    "timeContext": [
        {
            "id": "t1",
            "question": "How long has it been since your loss?",
            "options": [
                "Less than 1 month",
                "1-3 months",
                "3-6 months",
                "6-12 months",
                "1-2 years",
                "2-5 years",
                "More than 5 years"
            ]
        }
    ],
    
    "additionalFactors": [
        {
            "id": "a1",
            "question": "Are there any additional factors complicating your grief? (Select all that apply)",
            "options": [
                "The death was sudden or unexpected",
                "The death was traumatic or violent",
                "I had a complex or ambivalent relationship with the deceased",
                "This loss has triggered memories of previous losses",
                "I'm experiencing significant financial strain because of this loss",
                "I have limited time for grief due to caregiving responsibilities",
                "I'm experiencing significant health issues of my own",
                "None of these apply to my situation"
            ],
            "multiSelect": True
        }
    ]
}

# Grok API key - load from environment variable
GROK_API_KEY = os.getenv("GROQ_API_KEY")

def initialize_session_state():
    """Initialize session state variables if they don't exist"""
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 'intro'
    
    if 'responses' not in st.session_state:
        st.session_state.responses = {}
    
    if 'results' not in st.session_state:
        st.session_state.results = None
        
    if 'assessment_history' not in st.session_state:
        st.session_state.assessment_history = []
        
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False

def display_intro():
    """Display introduction screen"""
    st.markdown("<h1 class='main-header'>Master Grief Assessment</h1>", unsafe_allow_html=True)
    
    st.markdown("<div class='info-box'>", unsafe_allow_html=True)
    st.markdown("""
    ### Welcome to Your Grief Assessment
    
    This assessment will help us understand where you are in your grief journey and 
    provide personalized recommendations to support your healing process.
    
    **What to expect:**
    - The assessment takes about 5-7 minutes to complete
    - You'll have the opportunity to share your grief story
    - All responses are confidential
    - There are no right or wrong answers
    - You can retake this assessment anytime to track your progress
    
    Remember, grief is unique and non-linear. This tool is designed to support you 
    exactly where you are today.
    """)
    st.markdown("</div>", unsafe_allow_html=True)
    
    if st.button("Begin Assessment", key="begin_button", use_container_width=True):
        st.session_state.current_step = 'assessment'
        st.session_state.current_category = 'personalStory'  # Start with personal story
        st.session_state.current_question_index = 0
        st.session_state.total_questions = sum(len(questions) for questions in GRIEF_ASSESSMENT_QUESTIONS.values())
        st.session_state.questions_answered = 0
        st.session_state.responses = {}
        st.rerun()

def display_assessment():
    """Display assessment questions"""
    # Calculate progress
    progress = st.session_state.questions_answered / st.session_state.total_questions
    current_category = st.session_state.current_category
    current_index = st.session_state.current_question_index
    
    # Get current question
    question_data = GRIEF_ASSESSMENT_QUESTIONS[current_category][current_index]
    
    # Display progress
    st.markdown("<div class='progress-container'>", unsafe_allow_html=True)
    st.progress(progress)
    st.markdown(f"Question {st.session_state.questions_answered + 1} of {st.session_state.total_questions}")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Display question
    st.markdown(f"<p class='question-text'>{question_data['question']}</p>", unsafe_allow_html=True)
    
    # Get response based on question type
    if question_data.get('type') == 'text_area':
        # Special handling for personal story
        max_chars = question_data.get('max_chars', 1000)
        user_story = st.text_area(
            "Your story",
            height=200,
            max_chars=max_chars,
            key=f"q_{question_data['id']}",
            help=f"Max {max_chars} characters"
        )
        st.markdown(f"<p class='char-counter'>{len(user_story)}/{max_chars} characters</p>", unsafe_allow_html=True)
        
        # Store response when button is clicked
        response_value = user_story
    elif question_data.get('multiSelect', False):
        options = question_data['options']
        selected_options = st.multiselect("Select all that apply", options, key=f"q_{question_data['id']}")
        
        # Store response when button is clicked
        if 'values' in question_data:
            response_values = []
            for selected in selected_options:
                idx = options.index(selected)
                response_values.append(question_data['values'][idx])
        else:
            response_values = selected_options
    else:
        options = question_data['options']
        selected_option = st.radio("Select one option", options, key=f"q_{question_data['id']}")
        
        # Store value associated with selected option
        if 'values' in question_data:
            idx = options.index(selected_option)
            response_value = question_data['values'][idx]
        else:
            response_value = selected_option
    
    # Navigation buttons
    cols = st.columns(2)
    with cols[0]:
        if not (current_category == 'personalStory' and current_index == 0):
            if st.button("Previous", use_container_width=True):
                go_to_previous_question()
                st.rerun()
        else:
            st.empty()
            
    with cols[1]:
        if st.button("Next", key=f"next_{current_category}_{current_index}", use_container_width=True):
            # Save response
            if question_data.get('type') == 'text_area':
                st.session_state.responses.setdefault(current_category, {})[question_data['id']] = {
                    'question': question_data['question'],
                    'response_text': response_value
                }
            elif question_data.get('multiSelect', False):
                st.session_state.responses.setdefault(current_category, {})[question_data['id']] = {
                    'question': question_data['question'],
                    'selected_options': selected_options,
                    'values': response_values
                }
            else:
                st.session_state.responses.setdefault(current_category, {})[question_data['id']] = {
                    'question': question_data['question'],
                    'selected_option': selected_option,
                    'value': response_value if 'values' in question_data else None
                }
            
            # Move to next question
            go_to_next_question()
            st.rerun()

def go_to_next_question():
    """Navigate to the next question or category"""
    st.session_state.questions_answered += 1
    categories = list(GRIEF_ASSESSMENT_QUESTIONS.keys())
    current_cat_index = categories.index(st.session_state.current_category)
    current_q_index = st.session_state.current_question_index
    
    # Check if there are more questions in current category
    if current_q_index < len(GRIEF_ASSESSMENT_QUESTIONS[st.session_state.current_category]) - 1:
        st.session_state.current_question_index += 1
    # Move to next category
    elif current_cat_index < len(categories) - 1:
        st.session_state.current_category = categories[current_cat_index + 1]
        st.session_state.current_question_index = 0
    # Assessment complete
    else:
        # Reset processing flag when starting a new assessment
        st.session_state.processing_complete = False
        st.session_state.current_step = 'processing'

def go_to_previous_question():
    """Navigate to the previous question or category"""
    st.session_state.questions_answered -= 1
    categories = list(GRIEF_ASSESSMENT_QUESTIONS.keys())
    current_cat_index = categories.index(st.session_state.current_category)
    current_q_index = st.session_state.current_question_index
    
    # Check if at first question of category
    if current_q_index > 0:
        st.session_state.current_question_index -= 1
    # Move to previous category
    elif current_cat_index > 0:
        st.session_state.current_category = categories[current_cat_index - 1]
        st.session_state.current_question_index = len(GRIEF_ASSESSMENT_QUESTIONS[categories[current_cat_index - 1]]) - 1

def process_assessment():
    """Process assessment responses using Groq API"""
    st.markdown("<h1 class='main-header'>Analyzing Your Responses</h1>", unsafe_allow_html=True)
    
    # Skip processing if it's already done 
    if st.session_state.processing_complete and st.session_state.results is not None:
        # Just display the results directly here
        display_assessment_results(st.session_state.results)
        return
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Simulate processing steps
    for i in range(5):
        status_text.text(f"Processing assessment data... {i*25}%")
        progress_bar.progress(i * 0.25)
        time.sleep(0.5)
    
    # Prepare data 
    user_data = {}
    for category, responses in st.session_state.responses.items():
        user_data[category] = responses
    
    # Extract personal story if available
    personal_story = ""
    if 'personalStory' in st.session_state.responses and 'ps1' in st.session_state.responses['personalStory']:
        personal_story = st.session_state.responses['personalStory']['ps1'].get('response_text', '')
    
    # Create prompt for Groq
    prompt_template = """
    You are an empathetic grief counselor providing compassionate, personalized guidance based on assessment results. 
    You offer specific, tailored support for the unique grief experience each person is going through.
    
    Analyze the following grief assessment responses and provide personalized support. The user has shared their grief story and answered assessment questions.
    
    USER'S PERSONAL GRIEF STORY:
    "{personal_story}"
    
    ASSESSMENT RESPONSES:
    {assessment_data}
    
    Based on this information, please provide:
    
    1. EMOTIONAL SUPPORT: A compassionate, empathetic response that acknowledges their specific loss and emotional experience
    
    2. ASSESSMENT INSIGHTS: An assessment of their grief journey, including:
       - What stage of grief they appear to be experiencing
       - Key strengths identified in their responses
       - Areas where they might need additional support
    
    3. PERSONALIZED RECOMMENDATIONS: 
       - 3-5 specific coping strategies tailored to their situation
       - Self-care practices that would be most beneficial
       - Suggestions for meaningful ways to honor their loss (if applicable)
    
    4. RESOURCE SUGGESTIONS: Specific types of resources from the Master Grief app that would be most helpful:
       - Relevant journal prompts
       - Meditation or audio content
       - Community support options
       - Articles or guides
    
    5. MOTIVATIONAL MESSAGE: A closing message offering hope and encouragement that's specific to their situation
    
    Important considerations:
    - Be warm, compassionate and non-judgmental
    - Acknowledge the unique aspects of their specific loss
    - Recognize that grief is not linear and doesn't follow rigid stages
    - Focus on supporting the person where they are now
    - Offer practical, actionable suggestions
    - Use warm, supportive language rather than clinical terms
    """
    
    # Start with API service
    error_occurred = False
    sentiment = None
    
    try:
        status_text.text("Connecting to AI analysis service...")
        
        # Format the assessment data
        assessment_data = json.dumps({k:v for k,v in user_data.items() if k != 'personalStory'}, indent=2)
        
        # Initialize Groq Chat model
        groq_chat = ChatGroq(
            groq_api_key=GROK_API_KEY,
            model_name="meta-llama/llama-4-scout-17b-16e-instruct"
        )
        
        # Create chat prompt template
        groq_prompt = ChatPromptTemplate.from_template(prompt_template)
        
        # Get response from Groq
        chain = groq_prompt | groq_chat
        response = chain.invoke({
            "personal_story": personal_story,
            "assessment_data": assessment_data
        })
        
        # Extract content from the response
        if hasattr(response, 'content'):
            sentiment = response.content
        elif isinstance(response, dict) and 'content' in response:
            sentiment = response['content']
        else:
            sentiment = str(response)
            
    except Exception as e:
        error_occurred = True
        st.error(f"Error connecting to AI service: {str(e)}")
        st.warning("Using our backup assessment method instead.")
        time.sleep(2)
    
    # If API failed or returned empty results, use fallback
    if error_occurred or not sentiment:
        sentiment = generate_fallback_analysis(personal_story)
    
    # Calculate raw scores
    raw_scores = calculate_raw_scores()
    
    # Store results
    st.session_state.results = {
        'sentiment': sentiment,  # Store as sentiment
        'analysis': sentiment,   # Keep analysis for backward compatibility
        'raw_scores': raw_scores,
        'personal_story': personal_story,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Add to history
    st.session_state.assessment_history.append(st.session_state.results)
    
    # Mark processing as complete
    st.session_state.processing_complete = True
    
    status_text.text("Analysis complete!")
    progress_bar.progress(1.0)
    
    # Clear the progress elements
    time.sleep(1)
    status_text.empty()
    progress_bar.empty()
    
    # Display the results directly here
    display_assessment_results(st.session_state.results)

def display_assessment_results(results):
    """Display assessment results directly"""
    st.markdown("<h1 class='main-header'>Your Grief Assessment Results</h1>", unsafe_allow_html=True)
    
    # Display personal story if available
    if results['personal_story']:
        st.markdown("<div class='story-box'>", unsafe_allow_html=True)
        st.markdown("### Your Grief Story")
        st.markdown(results['personal_story'])
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Display sentiment/analysis
    st.markdown("<div class='results-container'>", unsafe_allow_html=True)
    sentiment = results.get('sentiment') or results.get('analysis')
    st.markdown(sentiment)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Display visual representation of scores
    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
    st.markdown("### Your Assessment Profile")
    
    # Create dataframe for visualization
    scores_data = {}
    for category, score in results['raw_scores'].items():
        if category != 'overall' and category != 'coping':
            if score is not None:
                scores_data[category] = score
    
    if scores_data:
        # Convert to dataframe
        df = pd.DataFrame({
            'Category': list(scores_data.keys()),
            'Score': list(scores_data.values())
        })
        
        # Map category names to more user-friendly labels
        category_labels = {
            'emotionalState': 'Emotional Well-being',
            'griefProcessing': 'Grief Processing',
            'socialSupport': 'Social Support',
            'functionalImpact': 'Daily Functioning'
        }
        
        df['Category'] = df['Category'].map(lambda x: category_labels.get(x, x))
        
        # Create horizontal bar chart
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.set_style("whitegrid")
        
        bars = sns.barplot(x='Score', y='Category', data=df, 
                  palette='viridis', orient='h', ax=ax)
        
        # Add value labels
        for i, v in enumerate(df['Score']):
            ax.text(v + 0.1, i, f"{v:.1f}", va='center')
        
        # Set limits and labels
        ax.set_xlim(0, 5.5)
        ax.set_xlabel('Score (1-5 scale)')
        ax.set_ylabel('')
        ax.set_title('Your Grief Assessment Profile')
        
        # Display the plot
        st.pyplot(fig)
        
        # Display overall wellness score
        if 'overall' in results['raw_scores'] and results['raw_scores']['overall'] is not None:
            overall_score = results['raw_scores']['overall']
            
            # Display overall score with gauge
            st.markdown("### Overall Wellness Score")
            cols = st.columns([1, 3, 1])
            with cols[1]:
                st.markdown(f"""
                <div style="text-align:center">
                    <div style="margin: 0 auto; width: 80%; background-color: #f2f2f2; border-radius: 10px; height: 30px; position: relative;">
                        <div style="position: absolute; left: 0; top: 0; background-color: #6495ED; width: {min(overall_score/5 * 100, 100)}%; height: 30px; border-radius: 10px;"></div>
                        <div style="position: absolute; left: 0; top: 0; width: 100%; text-align: center; line-height: 30px; color: #333; font-weight: bold;">
                            {overall_score:.1f} / 5.0
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    # Display action buttons
    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Results", use_container_width=True):
            # In a real app, this would save to a database
            st.success("Results saved successfully!")
            
    with col2:
        if st.button("Take Assessment Again", use_container_width=True):
            st.session_state.current_step = 'intro'
            st.session_state.processing_complete = False
            st.rerun()
            
def display_results():
    """Display assessment results to the user"""
    if st.session_state.results is None:
        st.error("No results available. Please complete the assessment first.")
        if st.button("Return to Assessment"):
            st.session_state.current_step = 'intro'
            st.session_state.processing_complete = False
            st.rerun()
        return
    
    # Use the common display function
    display_assessment_results(st.session_state.results)

def generate_fallback_analysis(personal_story):
    """Generate a fallback analysis if the API fails"""
    # Calculate raw scores for the fallback
    raw_scores = calculate_raw_scores()
    
    # Determine grief stage based on grief processing score
    grief_processing_score = raw_scores.get('griefProcessing', 3)
    
    if grief_processing_score < 2:
        grief_stage = "Early grief"
        message = f"""
        # Your Personalized Grief Support
        
        ## Emotional Support
        
        Thank you for sharing your story with us. I can see that you're experiencing the intense, raw emotions that often come in the early stages of grief. During this time, emotions can be overwhelming, and the reality of the loss may feel surreal or impossible to accept fully. This is a normal and valid part of the grieving process.
        
        Your responses indicate that you're dealing with significant emotional intensity right now. Remember that there's no timeline for grief, and what you're feeling is completely valid. Focus on basic self-care and allow yourself to experience your emotions without judgment. Be gentle with yourself during this difficult time.
        
        ## Your Grief Journey: {grief_stage}
        
        ### Key Strengths
        - You've taken an important step by seeking support through this assessment
        - You're showing awareness of your grief process
        - You're open to learning new ways to navigate this challenging time
        
        ### Areas for Support
        - Finding ways to manage the intensity of emotions
        - Developing healthy coping strategies for the difficult moments
        - Creating a support network that understands your grief needs
        
        ## Personalized Recommendations
        
        1. **Focus on basic self-care**: Ensure you're getting adequate rest, nutrition, and gentle movement
        2. **Create small pockets of respite**: Find brief activities that offer moments of peace
        3. **Connect with supportive people**: Identify those who can simply be present with you without trying to "fix" your grief
        4. **Use guided meditations**: Try the grief-specific meditations in our app's audio library
        5. **Consider joining a support group**: Connect with others in early grief who understand what you're experiencing
        
        ## Suggested Resources
        
        1. **Journal Prompts**: "Exploring My Emotions Today", "Moments When I Need Support"
        2. **Meditations**: "Gentle Healing for Grief", "Finding Moments of Peace"
        3. **Community Support**: Join our "Early Grief Support Circle"
        4. **Articles**: "Understanding the Early Stages of Grief", "Self-Care During Intense Grief"
        
        ## Motivational Message
        
        Remember that grief is not a linear journey, and there will be both difficult days and moments of respite. Each small step you take in caring for yourself matters. You're not alone on this path, and the courage you've shown in facing your grief is remarkable. Your capacity for healing is greater than you may realize right now.
        """
        
    elif grief_processing_score < 3.5:
        grief_stage = "Active grief processing"
        message = f"""
        # Your Personalized Grief Support
        
        ## Emotional Support
        
        Thank you for sharing your grief journey with us. Based on what you've shared, it appears you're in an active grief processing phase. During this time, you're working through the reality of your loss and beginning to find ways to adjust to a changed world. The pain may still be quite significant, but you're developing coping strategies.
        
        Your responses suggest you're engaging with your grief and beginning to find ways to integrate this experience. This work is challenging but vital. Continue to be patient with yourself as you navigate this terrain.
        
        ## Your Grief Journey: {grief_stage}
        
        ### Key Strengths
        - You're actively engaging with your grief rather than avoiding it
        - You're developing coping mechanisms that help you function
        - You're beginning to find moments where grief isn't all-consuming
        
        ### Areas for Support
        - Building more consistent self-care routines
        - Expanding your emotional support network
        - Finding meaningful ways to honor your loss
        
        ## Personalized Recommendations
        
        1. **Practice regular journaling**: Use the app's reflection prompts to process emotions
        2. **Establish grief rituals**: Create meaningful practices that honor your feelings
        3. **Connect with others who understand**: Find people who can relate to similar losses
        4. **Explore creative expression**: Use art, music, or writing to process emotions
        5. **Consider grief coaching**: One-on-one support might be beneficial at this stage
        
        ## Suggested Resources
        
        1. **Journal Prompts**: "Processing My Grief Journey", "Finding Meaning in Loss"
        2. **Meditations**: "Navigating Difficult Emotions", "Creating Space for Healing"
        3. **Community Support**: Connect with our "Grief Processing Circle"
        4. **Articles**: "The Middle Path of Grief", "Building Resilience Through Loss"
        
        ## Motivational Message
        
        The work you're doing now—processing your grief, developing coping strategies, and learning to live with loss—takes tremendous courage. Though the path isn't always clear or easy, each step you take helps you build the strength and resilience to carry this grief. Trust that while grief may always be part of your life, it will not always be this overwhelming. You are doing the important work of healing.
        """
        
    else:
        grief_stage = "Integration and adaptation"
        message = f"""
        # Your Personalized Grief Support
        
        ## Emotional Support
        
        Thank you for sharing your grief journey with us. From what you've shared, it appears you're in an integration and adaptation phase of grief. This doesn't mean your grief is "over" but rather that you're finding ways to carry your grief while reengaging with life.
        
        Your responses indicate that you've been developing ways to live alongside your grief. You're likely finding that grief now comes in waves rather than being constant, and you're discovering a new normal. This represents significant emotional work and resilience.
        
        ## Your Grief Journey: {grief_stage}
        
        ### Key Strengths
        - You've developed effective ways to cope with your grief
        - You're able to experience positive emotions alongside your grief
        - You're finding meaning and purpose as you move forward
        
        ### Areas for Support
        - Navigating grief triggers and anniversaries
        - Maintaining connections to your loved one while living forward
        - Finding ways to use your grief experience to help others
        
        ## Personalized Recommendations
        
        1. **Explore meaningful legacy projects**: Find ways to honor what mattered to your loved one
        2. **Set goals aligned with your values**: Create meaningful pursuits that incorporate what you've learned
        3. **Consider ways to support others**: Your experience might help those in earlier grief stages
        4. **Practice mindful reflection**: Acknowledge how this loss has shaped your perspective and growth
        5. **Develop comfort with your evolving grief**: Recognize that grief can still arise intensely at times
        
        ## Suggested Resources
        
        1. **Journal Prompts**: "My Grief Journey Reflections", "Creating Meaningful Legacies"
        2. **Meditations**: "Embracing Life After Loss", "Honoring Continuing Bonds"
        3. **Community Support**: Consider our "Grief Mentors Circle"
        4. **Articles**: "Living Forward While Carrying Grief", "Finding Post-Traumatic Growth"
        
        ## Motivational Message
        
        The way you've learned to carry your grief while finding space for joy and meaning again shows tremendous strength and resilience. Though your life has been forever changed by this loss, you're creating a path forward that honors both what you've lost and what remains. The wisdom you've gained through this journey has profound value, not only for your continued healing but potentially for others who are earlier in their grief. Be proud of how far you've come.
        """
    
    # Add personalization if personal story is available
    if personal_story:
        # Simple personalization - simply acknowledge they shared their story
        message = message.replace("Thank you for sharing your", 
                                 "Thank you for sharing your personal story. Your experiences with")
    
    return message

def calculate_raw_scores():
    """Calculate raw scores for different categories"""
    scores = {}
    
    # Calculate average scores for each category
    for category in ['emotionalState', 'griefProcessing', 'socialSupport', 'functionalImpact']:
        if category in st.session_state.responses:
            values = []
            for q_id, response in st.session_state.responses[category].items():
                if 'value' in response and response['value'] is not None:
                    values.append(response['value'])
            
            if values:
                scores[category] = sum(values) / len(values)
            else:
                scores[category] = None
    
    # Special handling for coping
    if 'coping' in st.session_state.responses:
        coping_values = []
        healthy_strategies = 0
        unhealthy_strategies = 0
        
        for q_id, response in st.session_state.responses['coping'].items():
            if 'value' in response and response['value'] is not None:
                coping_values.append(response['value'])
            
            # Count strategies for multi-select questions
            if 'values' in response:
                for value in response['values']:
                    if value == 'healthy':
                        healthy_strategies += 1
                    elif value == 'unhealthy':
                        unhealthy_strategies += 1
        
        scores['coping'] = {
            'score': sum(coping_values) / len(coping_values) if coping_values else None,
            'healthy_strategies': healthy_strategies,
            'unhealthy_strategies': unhealthy_strategies
        }
    
    # Calculate overall score (weighted average)
    category_weights = {
        'emotionalState': 0.2,
        'griefProcessing': 0.3,
        'socialSupport': 0.15,
        'functionalImpact': 0.15
    }
    
    weighted_sum = 0
    weight_sum = 0
    
    for category, weight in category_weights.items():
        if category in scores and scores[category] is not None:
            if category == 'coping':
                weighted_sum += scores[category]['score'] * weight
            else:
                weighted_sum += scores[category] * weight
            weight_sum += weight
    
    if weight_sum > 0:
        scores['overall'] = weighted_sum / weight_sum
    else:
        scores['overall'] = None
    
    return scores

def display_history():
    """Display assessment history"""
    st.markdown("<h1 class='main-header'>Your Assessment History</h1>", unsafe_allow_html=True)
    
    if not st.session_state.assessment_history:
        st.info("You haven't completed any assessments yet.")
        return
    
    # Display list of past assessments
    st.markdown("### Previous Assessments")
    
    for i, assessment in enumerate(reversed(st.session_state.assessment_history)):
        st.markdown(f"""
        <div style="padding: 1rem; border: 1px solid #e0e0e0; border-radius: 0.5rem; margin-bottom: 1rem;">
            <h4>Assessment {len(st.session_state.assessment_history) - i}</h4>
            <p>Date: {assessment['timestamp']}</p>
            <p>Overall Score: {assessment['raw_scores'].get('overall', 'N/A'):.1f}/5.0</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Option to view trends
    if len(st.session_state.assessment_history) > 1:
        st.markdown("### Your Progress Over Time")
        
        # Create dataframe with scores over time
        trend_data = []
        for assessment in st.session_state.assessment_history:
            timestamp = assessment['timestamp']
            scores = assessment['raw_scores']
            
            data_point = {
                'timestamp': timestamp,
                'overall': scores.get('overall', None)
            }
            
            # Add individual category scores
            for category in ['emotionalState', 'griefProcessing', 'socialSupport', 'functionalImpact']:
                if category in scores:
                    data_point[category] = scores[category]
            
            trend_data.append(data_point)
        
        # Convert to DataFrame
        df = pd.DataFrame(trend_data)
        
        # Create line chart of overall score
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.set_style("whitegrid")
        
        sns.lineplot(x=range(len(df)), y='overall', data=df, marker='o', linewidth=2.5, ax=ax)
        
        # Set labels
        ax.set_xlabel('Assessment')
        ax.set_ylabel('Overall Score')
        ax.set_title('Your Overall Well-being Progress')
        ax.set_ylim(0, 5.5)
        ax.set_xticks(range(len(df)))
        ax.set_xticklabels([f"#{i+1}" for i in range(len(df))])
        
        # Display the plot
        st.pyplot(fig)
        
        # Add interpretation
        latest = df['overall'].iloc[-1]
        first = df['overall'].iloc[0]
        
        if latest > first:
            st.markdown("""
            📈 **Your Progress**: Your overall well-being score has improved since your first assessment.
            This suggests that your grief journey is progressing and your coping strategies are working.
            """)
        elif latest < first:
            st.markdown("""
            📉 **Your Journey**: Your overall well-being score has decreased since your first assessment.
            Remember that grief is not linear, and it's normal to have ups and downs along the way.
            """)
        else:
            st.markdown("""
            📊 **Your Journey**: Your overall well-being score has remained stable since your first assessment.
            Grief takes time, and stability can be a sign of resilience.
            """)

def main():
    """Main function to run the app"""
    # Initialize session state
    initialize_session_state()
    
    # Sidebar navigation
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/4207/4207244.png", width=100)
        st.markdown("# Master Grief")
        st.markdown("#### Your Personal Grief Support")
        
        # Add navigation options
        if st.session_state.current_step == 'results' or st.session_state.assessment_history:
            nav = st.radio("Navigation", ["New Assessment", "Current Results", "Assessment History"])
            
            if nav == "New Assessment" and st.session_state.current_step != 'intro':
                st.session_state.current_step = 'intro'
                st.rerun()
            elif nav == "Current Results" and st.session_state.results is not None and st.session_state.current_step != 'results':
                st.session_state.current_step = 'results'
                st.rerun()
            elif nav == "Assessment History" and st.session_state.current_step != 'history':
                st.session_state.current_step = 'history'
                st.rerun()
        
        # Debug info (remove in production)
        with st.expander("Debug Info"):
            st.write(f"Current Step: {st.session_state.current_step}")
            st.write(f"Processing Complete: {st.session_state.get('processing_complete', False)}")
            st.write(f"Results Available: {st.session_state.results is not None}")
            if st.button("Force Results View"):
                if st.session_state.results is not None:
                    st.session_state.current_step = 'results'
                    st.rerun()
        
        # Add help information
        with st.expander("About this assessment"):
            st.markdown("""
            This assessment tool helps identify where you are in your grief journey and provides personalized recommendations.
            
            - Take as much time as you need
            - Answer honestly - there are no right or wrong answers
            - You can retake the assessment anytime
            """)
    
    # Display current step
    if st.session_state.current_step == 'intro':
        display_intro()
    elif st.session_state.current_step == 'assessment':
        display_assessment()
    elif st.session_state.current_step == 'processing':
        process_assessment()
    elif st.session_state.current_step == 'results':
        # If we have results, display them
        if st.session_state.results is not None:
            display_results()
        # Otherwise redirect to processing if we have responses
        elif st.session_state.responses:
            st.session_state.current_step = 'processing'
            st.session_state.processing_complete = False
            st.rerun()
        # Otherwise go back to intro
        else:
            st.session_state.current_step = 'intro'
            st.rerun()
    elif st.session_state.current_step == 'history':
        display_history()

if __name__ == "__main__":
    main()