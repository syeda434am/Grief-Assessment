def get_assessment_questions():
    """Returns the list of assessment questions related to grief"""
    return [
        {
            "id": "relationship",
            "question": "What was your relationship to the person who died?",
            "type": "multiple_choice",
            "options": [
                "Parent", 
                "Child", 
                "Spouse/Partner", 
                "Sibling", 
                "Grandparent",
                "Friend",
                "Other Family Member",
                "Colleague",
                "Pet"
            ],
            "help_text": "This helps us understand the nature of your loss."
        },
        
        {
            "id": "cause_of_death",
            "question": "What was the cause of death?",
            "type": "multiple_choice",
            "options": [
                "Illness/Disease",
                "Accident",
                "Suicide",
                "Homicide",
                "COVID-19",
                "Natural causes/Old age",
                "Sudden medical event (heart attack, stroke, etc.)",
                "Substance use/overdose",
                "I prefer not to specify"
            ],
            "help_text": "Different types of losses can involve different grief experiences."
        },
        
        {
            "id": "time_since_loss",
            "question": "How long has it been since your loss?",
            "type": "multiple_choice",
            "options": [
                "Less than 1 month",
                "1-3 months",
                "4-6 months",
                "7-11 months",
                "12-24 months",
                "Over 24 months"
            ],
            "help_text": "The timeline of grief can influence your current experience."
        },
        
        {
            "id": "meaningful_memories",
            "question": "What memories or qualities of the person/relationship do you find yourself reflecting on most?",
            "type": "text",
            "help_text": "Understanding what's most present for you helps provide personalized guidance."
        },
        
        {
            "id": "grief_impact",
            "question": "How has grief affected your daily life?",
            "type": "multiple_choice",
            "options": [
                "Unable to function in most areas of life",
                "Major disruption in work, sleep, and social activities",
                "Managing essential tasks but struggling significantly",
                "Some disruption but maintaining most responsibilities",
                "Minimal disruption to daily functioning",
                "Unsure/It varies significantly day to day"
            ],
            "help_text": "Select the option that best describes your experience."
        },
        
        {
            "id": "emotional_triggers",
            "question": "What situations, memories, or events tend to intensify your grief emotions?",
            "type": "text",
            "help_text": "Understanding your triggers can help create appropriate coping strategies."
        },
        
        {
            "id": "sleep_changes",
            "question": "Have you noticed changes in your sleep since your loss?",
            "type": "multiple_choice",
            "options": [
                "Severe difficulty falling or staying asleep",
                "Sleeping much more than usual",
                "Disturbing dreams or nightmares",
                "Mild sleep disturbances",
                "No significant changes to sleep",
                "It varies greatly from day to day"
            ],
            "help_text": "Sleep changes are common during grief."
        },
        
        {
            "id": "support_system",
            "question": "How would you describe your current support system?",
            "type": "multiple_choice",
            "options": [
                "Strong support from family and friends",
                "Some support, but not enough",
                "Support from professionals but limited personal support",
                "Very limited support from any source",
                "No current support system",
                "I prefer to grieve privately"
            ],
            "help_text": "This helps us understand your available support resources."
        },
        
        {
            "id": "coping_method",
            "question": "Which coping methods have you found most helpful? (Select all that apply)",
            "type": "multiselect",
            "options": [
                "Talking with supportive people",
                "Professional counseling",
                "Physical activity/exercise",
                "Creative expression (art, music, writing)",
                "Spiritual or religious practices",
                "Spending time in nature",
                "Keeping busy with activities",
                "Reading about grief",
                "Support groups",
                "Meditation or mindfulness",
                "Haven't found helpful methods yet"
            ],
            "help_text": "Select all methods that have provided some relief."
        }
    ]

def get_dynamic_questions(previous_responses):
    """
    Returns additional questions based on previous responses.
    This allows for a more personalized assessment experience.
    
    Args:
        previous_responses (dict): The user's responses to previous questions
        
    Returns:
        list: Additional questions based on user's specific situation
    """
    dynamic_questions = []
    
    # Example: Add specific questions based on cause of death
    cause = previous_responses.get("cause_of_death", {}).get("response", "")
    
    if cause == "COVID-19":
        dynamic_questions.append({
            "id": "covid_isolation",
            "question": "How has the public nature of the pandemic affected your grieving process?",
            "type": "text",
            "help_text": "Many COVID-19 loss survivors experience unique grief circumstances."
        })
    
    # Add question based on time since loss
    time_period = previous_responses.get("time_since_loss", {}).get("response", "")
    
    if time_period in ["Less than 1 month", "1-3 months"]:
        dynamic_questions.append({
            "id": "early_grief_needs",
            "question": "What immediate support would be most helpful to you right now?",
            "type": "text",
            "help_text": "Early grief often has specific practical and emotional needs."
        })
    
    elif time_period in ["12-24 months", "Over 24 months"]:
        dynamic_questions.append({
            "id": "grief_changes",
            "question": "How has your grief changed or evolved over time?",
            "type": "text",
            "help_text": "Grief often changes in nature as time passes."
        })
    
    # Add question based on relationship
    relationship = previous_responses.get("relationship", {}).get("response", "")
    
    if relationship == "Child":
        dynamic_questions.append({
            "id": "child_loss_specific",
            "question": "Have you found any particular resources or approaches helpful in coping with the loss of your child?",
            "type": "text",
            "help_text": "The loss of a child often involves unique grief needs."
        })
    
    elif relationship == "Spouse/Partner":
        dynamic_questions.append({
            "id": "partner_loss_challenges",
            "question": "What practical challenges have you faced since losing your partner?",
            "type": "text",
            "help_text": "Partner loss often involves both emotional grief and practical life changes."
        })
    
    return dynamic_questions

def get_emotion_labels():
    """Return the list of emotion labels for visualization"""
    return [
        "Sadness", 
        "Anger", 
        "Guilt", 
        "Regret",
        "Anxiety", 
        "Shock", 
        "Numbness",
        "Loneliness", 
        "Relief", 
        "Yearning",
        "Emptiness",
        "Confusion",
        "Overwhelm",
        "Depression", 
        "Hope",
        "Gratitude",
        "Peace"
    ] 