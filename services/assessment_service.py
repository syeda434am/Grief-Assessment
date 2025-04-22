"""
Assessment service for scoring and analyzing grief assessment responses
"""

def calculate_grief_score(responses):
    """
    Calculate the grief intensity score based on assessment responses.
    
    Args:
        responses (dict): Dictionary of question IDs to response values (typically 0-4)
        
    Returns:
        dict: Score results with overall score and subscales
    """
    # Initialize score tracking
    total_score = 0
    emotional_distress_score = 0
    social_disruption_score = 0
    traumatic_distress_score = 0
    
    # Track counts for calculating averages
    emotional_count = 0
    social_count = 0
    traumatic_count = 0
    
    # Categorize questions by domain
    emotional_questions = ['q1', 'q3', 'q5', 'q7', 'q9', 'q11', 'q13', 'q15']
    social_questions = ['q2', 'q6', 'q10', 'q14', 'q17', 'q19']
    traumatic_questions = ['q4', 'q8', 'q12', 'q16', 'q18', 'q20']
    
    # Sum scores for each dimension
    for question_id, response_value in responses.items():
        # Convert to integer if it's a string
        if isinstance(response_value, str) and response_value.isdigit():
            response_value = int(response_value)
        elif not isinstance(response_value, (int, float)):
            # Skip non-numeric responses
            continue
            
        total_score += response_value
        
        if question_id in emotional_questions:
            emotional_distress_score += response_value
            emotional_count += 1
        elif question_id in social_questions:
            social_disruption_score += response_value
            social_count += 1
        elif question_id in traumatic_questions:
            traumatic_distress_score += response_value
            traumatic_count += 1
    
    # Calculate average scores for each dimension (0-4 scale)
    avg_emotional_score = emotional_distress_score / max(emotional_count, 1)
    avg_social_score = social_disruption_score / max(social_count, 1)
    avg_traumatic_score = traumatic_distress_score / max(traumatic_count, 1)
    
    # Calculate overall average (0-4 scale)
    total_count = sum([emotional_count, social_count, traumatic_count])
    avg_total_score = total_score / max(total_count, 1)
    
    # Create result dictionary
    result = {
        "total_score": total_score,
        "average_score": round(avg_total_score, 2),
        "subscales": {
            "emotional_distress": {
                "score": emotional_distress_score,
                "average": round(avg_emotional_score, 2),
                "level": get_intensity_level(avg_emotional_score)
            },
            "social_disruption": {
                "score": social_disruption_score,
                "average": round(avg_social_score, 2),
                "level": get_intensity_level(avg_social_score)
            },
            "traumatic_distress": {
                "score": traumatic_distress_score,
                "average": round(avg_traumatic_score, 2),
                "level": get_intensity_level(avg_traumatic_score)
            }
        },
        "overall_intensity": get_intensity_level(avg_total_score),
        "risk_factors": identify_risk_factors(responses)
    }
    
    return result

def get_intensity_level(score):
    """
    Convert a numeric score to an intensity level.
    
    Args:
        score (float): Numeric score from 0-4
        
    Returns:
        str: Intensity level (Minimal, Mild, Moderate, Severe, or Extreme)
    """
    if score < 0.8:
        return "Minimal"
    elif score < 1.6:
        return "Mild"
    elif score < 2.4:
        return "Moderate"
    elif score < 3.2:
        return "Severe"
    else:
        return "Extreme"

def identify_risk_factors(responses):
    """
    Identify potential risk factors based on assessment responses.
    
    Args:
        responses (dict): Dictionary of question IDs to response values
        
    Returns:
        list: List of identified risk factors
    """
    risk_factors = []
    
    # Define risk thresholds (responses rated 3 or 4 indicate potential risks)
    high_risk_threshold = 3
    
    # Check specific questions for risk factors
    if responses.get('q4', 0) >= high_risk_threshold:
        risk_factors.append("Traumatic grief reactions")
    
    if responses.get('q8', 0) >= high_risk_threshold:
        risk_factors.append("Intrusive thoughts/memories")
    
    if responses.get('q12', 0) >= high_risk_threshold:
        risk_factors.append("Avoidance behaviors")
    
    if responses.get('q16', 0) >= high_risk_threshold or responses.get('q20', 0) >= high_risk_threshold:
        risk_factors.append("Complicated grief indicators")
    
    if responses.get('q7', 0) >= high_risk_threshold:
        risk_factors.append("Persistent sadness/depression")
    
    if responses.get('q19', 0) >= high_risk_threshold:
        risk_factors.append("Social isolation")
    
    if responses.get('q15', 0) >= high_risk_threshold:
        risk_factors.append("Difficulty finding meaning")
    
    return risk_factors 