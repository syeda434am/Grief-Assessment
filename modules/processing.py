import streamlit as st
import time
import json
import datetime
from services.ai_service import get_assessment_result

def process_assessment():
    """Process the assessment and generate results"""
    # Check if we have responses
    if 'responses' not in st.session_state or not st.session_state.responses:
        st.error("No assessment responses found. Please complete the assessment first.")
        if st.button("Go to Assessment"):
            st.session_state.current_step = "assessment"
            st.rerun()
        return
    
    # Check if processing is already complete
    if 'processing_complete' in st.session_state and st.session_state.processing_complete:
        # Move to results page
        st.session_state.current_step = "results"
        st.rerun()
        return
    
    # Display processing UI
    st.title("Analyzing Your Responses")
    
    # Show progress bar and messages
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Step 1: Prepare data (20%)
    status_text.text("Preparing your assessment data...")
    progress_bar.progress(0.1)
    time.sleep(0.5)
    progress_bar.progress(0.2)
    
    # Step 2: Analyze responses (50%)
    status_text.text("Analyzing your responses...")
    progress_bar.progress(0.3)
    time.sleep(0.5)
    progress_bar.progress(0.4)
    time.sleep(0.5)
    progress_bar.progress(0.5)
    
    # Step 3: Generate insights (80%)
    status_text.text("Generating personalized insights...")
    progress_bar.progress(0.6)
    time.sleep(0.5)
    progress_bar.progress(0.7)
    time.sleep(0.5)
    progress_bar.progress(0.8)
    
    # Step 4: Prepare results (100%)
    status_text.text("Preparing your results...")
    
    # Generate the actual results using AI service
    try:
        # Add current timestamp
        st.session_state.current_timestamp = datetime.datetime.now().isoformat()
        
        # Process responses with AI
        results = get_assessment_result(st.session_state.responses)
        
        # Add timestamp to results
        results["timestamp"] = st.session_state.current_timestamp
        results["responses"] = st.session_state.responses
        
        # Save results to session state
        st.session_state.results = results
        st.session_state.processing_complete = True
        
        # Add to assessment history
        save_assessment_to_history(results)
        
        progress_bar.progress(1.0)
        status_text.text("Analysis complete!")
        
        # Show success message
        st.success("Your assessment has been successfully processed!")
        
        # Redirect to results after a short delay
        time.sleep(1)
        st.session_state.current_step = "results"
        st.rerun()
        
    except Exception as e:
        # Handle any errors during processing
        progress_bar.progress(1.0)
        status_text.text("Analysis complete with limited results.")
        
        st.error(f"We encountered an issue processing your assessment: {str(e)}")
        st.info("We've created simplified results based on your responses.")
        
        # Create fallback results
        results = generate_fallback_results(st.session_state.responses)
        results["timestamp"] = datetime.datetime.now().isoformat()
        results["responses"] = st.session_state.responses
        
        # Save fallback results
        st.session_state.results = results
        st.session_state.processing_complete = True
        save_assessment_to_history(results)
        
        # Continue button
        if st.button("View Results"):
            st.session_state.current_step = "results"
            st.rerun()

def save_assessment_to_history(results):
    """Save the completed assessment to history"""
    # Create assessment history entry
    assessment_entry = {
        "id": str(datetime.datetime.now().timestamp()),
        "date": results.get("timestamp", datetime.datetime.now().isoformat()),
        "results": results,
        "guide": st.session_state.get("guide", None)
    }
    
    # Initialize history if it doesn't exist
    if 'assessment_history' not in st.session_state:
        st.session_state.assessment_history = []
    
    # Add to history (at the beginning for reverse chronological order)
    st.session_state.assessment_history.insert(0, assessment_entry)
    
    # Save to file system if needed
    save_to_file(assessment_entry)

def save_to_file(assessment_data):
    """Save assessment data to file system"""
    try:
        import os
        # Create data directory if it doesn't exist
        os.makedirs('data/assessments', exist_ok=True)
        
        # Save to file
        filename = f"data/assessments/assessment_{assessment_data['id']}.json"
        with open(filename, 'w') as f:
            json.dump(assessment_data, f, indent=2)
    except Exception as e:
        # Log error but continue - this is not critical
        print(f"Error saving assessment to file: {str(e)}")

def generate_fallback_results(responses):
    """Generate basic results when AI processing fails"""
    # Create a basic summary
    summary = "Based on your responses, we can see you're navigating a grief experience. " \
              "While we couldn't generate a complete analysis, we can provide some general guidance."
    
    # Create generalized scores
    scores = {
        "grief_intensity": 5,
        "coping_ability": 5,
        "support_network": 5
    }
    
    # Create generalized recommendations
    recommendations = [
        "Consider connecting with a grief support group in your area",
        "Practice daily self-care activities that help you feel grounded",
        "Allow yourself to experience your emotions without judgment",
        "Reach out to trusted friends or family members for support",
        "Consider speaking with a mental health professional who specializes in grief"
    ]
    
    # Create fallback result structure
    fallback_result = {
        "summary": summary,
        "scores": scores,
        "recommendations": recommendations,
        "risk_factors": ["Unable to determine specific risk factors"],
        "is_fallback": True
    }
    
    return fallback_result 