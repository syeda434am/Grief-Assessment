import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from services.guidance_service import generate_followup_response, save_conversation_exchange
from modules.assessment import render_assessment_results
from services.ai_service import get_assessment_result
import json
import os

def display_results():
    """Display the assessment results, redirecting to the consistent render function"""
    
    # If results aren't already in session state, process the assessment
    if 'results' not in st.session_state or not st.session_state.results:
        # Check if we have responses to process
        if 'responses' not in st.session_state or not st.session_state.responses:
            st.error("No assessment responses found.")
            if st.button("Start New Assessment"):
                st.session_state.current_step = "story"
                st.rerun()
            return
        
        # Process assessment
        with st.spinner("Processing your assessment..."):
            try:
                # Get assessment result
                st.session_state.results = get_assessment_result(st.session_state.responses)
                st.session_state.processing_complete = True
            except Exception as e:
                st.error(f"Error processing assessment: {str(e)}")
                st.session_state.results = generate_fallback_result(st.session_state.responses)
    
    # Use the consistent render function from the assessment module
    render_assessment_results()

def generate_fallback_result(responses):
    """Generate a fallback result when assessment processing fails"""
    from modules.assessment import generate_fallback_summary, generate_scores, enhance_recommendations
    
    return {
        "summary": generate_fallback_summary(responses),
        "scores": generate_scores(responses),
        "recommendations": enhance_recommendations(responses, [
            "Speak with a mental health professional",
            "Consider joining a grief support group",
            "Practice self-care routines",
            "Maintain connections with supportive friends and family"
        ]),
        "risk_factors": []
    }

def display_summary(results):
    """Display the summary section of results"""
    st.markdown("### Assessment Summary")
    
    if "summary" in results:
        st.markdown(results["summary"])
    else:
        st.markdown("No summary information available.")
    
    # Display scores if available
    if "scores" in results:
        st.markdown("### Key Scores")
        
        # Create columns for metrics
        cols = st.columns(len(results["scores"]))
        
        # Display each score as a metric
        for i, (category, value) in enumerate(results["scores"].items()):
            with cols[i % len(cols)]:
                # Format the category name for display
                display_name = category.replace("_", " ").title()
                st.metric(label=display_name, value=value)

def display_detailed_results(results):
    """Display detailed assessment results with visualizations"""
    st.markdown("### Detailed Assessment Results")
    
    # Display scores as a bar chart if available
    if "scores" in results and len(results["scores"]) >= 3:
        st.markdown("#### Score Breakdown")
        
        # Get data
        categories = [k.replace("_", " ").title() for k in results["scores"].keys()]
        values = list(results["scores"].values())
        
        # Create dataframe for plotting
        df = pd.DataFrame({
            'Category': categories,
            'Value': values
        })
        
        # Sort by value for the bar chart
        df_sorted = df.sort_values('Value', ascending=False)
        
        # Create bar chart
        import plotly.express as px
        fig_bar = px.bar(
            df_sorted, 
            x='Category', 
            y='Value',
            color='Value',
            color_continuous_scale='Blues',
            title="Assessment Score Profile",
            height=400
        )
        
        fig_bar.update_layout(
            xaxis_title="",
            yaxis_title="Score (0-10)",
            coloraxis_showscale=False
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Display response details
    if "responses" in results:
        st.markdown("#### Your Responses")
        
        for question_id, response in results["responses"].items():
            if isinstance(response, dict) and "question_text" in response:
                with st.expander(response["question_text"]):
                    st.write(response["response"])
            elif isinstance(response, dict) and "text" in response:
                with st.expander(response["text"]):
                    st.write(response["value"])
            else:
                # Try to find question text from another source
                question_text = question_id.replace("_", " ").title()
                with st.expander(question_text):
                    st.write(response)

def display_recommendations(results):
    """Display recommendations based on assessment results"""
    st.markdown("### Recommendations")
    
    if "recommendations" in results and results["recommendations"]:
        for i, rec in enumerate(results["recommendations"], 1):
            st.markdown(f"{i}. {rec}")
    else:
        st.markdown("No specific recommendations available.")
    
    # Display risk factors if available
    if "risk_factors" in results and results["risk_factors"]:
        st.markdown("### Areas of Attention")
        st.markdown("The assessment identified these areas that may need particular attention:")
        
        for factor in results["risk_factors"]:
            st.markdown(f"- {factor}")

def display_guidance_section(results):
    """Display interactive guidance section for follow-up questions"""
    st.markdown("### Interactive Guidance")
    st.markdown("""
    This section allows you to ask follow-up questions about your grief journey 
    and receive personalized guidance based on your assessment results.
    """)
    
    # Display previous conversation if it exists
    if 'guidance_conversation' not in st.session_state:
        st.session_state.guidance_conversation = []
    
    if st.session_state.guidance_conversation:
        st.markdown("#### Previous Exchanges")
        
        for exchange in st.session_state.guidance_conversation:
            with st.chat_message("user"):
                st.markdown(exchange["user_message"])
            
            with st.chat_message("assistant"):
                st.markdown(exchange["ai_response"])
    
    # Input for new questions
    st.markdown("#### Ask a Question")
    user_question = st.text_area(
        "What would you like to know about managing your grief?",
        help="Ask anything about coping strategies, self-care, understanding your emotions, etc."
    )
    
    if st.button("Get Guidance", type="primary"):
        if not user_question:
            st.warning("Please enter a question to receive guidance.")
            return
        
        # Show spinner while generating response
        with st.spinner("Generating personalized guidance..."):
            # Get guide data if available
            guide_data = None
            if 'guide' in st.session_state:
                guide_data = st.session_state.guide
            elif 'current_guide' in st.session_state:
                guide_data = st.session_state.current_guide
            
            # Get previous conversation if it exists
            previous_conversation = st.session_state.get("guidance_conversation", [])
            
            # Generate follow-up response using guidance_service
            response_data = generate_followup_response(
                user_question, 
                guide_data, 
                previous_conversation
            )
            
            # Save to conversation history
            save_conversation_exchange(user_question, response_data["response"])
            
            # Force rerun to show the updated conversation
            st.rerun() 