import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

def display_history():
    """Display assessment history in a consistent format with the rest of the application"""
    st.title("Assessment History")
    
    # Check if there's any history to display
    if not st.session_state.assessment_history or len(st.session_state.assessment_history) == 0:
        st.info("You haven't completed any assessments yet. Start a new assessment to see your results here.")
        
        # Show button to start a new assessment
        if st.button("Start New Assessment", type="primary"):
            st.session_state.current_step = "story"
            st.rerun()
        return
    
    st.write("View your previous grief assessments. Click on any assessment to see full details.")
    
    # Display history as a list of clickable cards
    for i, assessment in enumerate(st.session_state.assessment_history):
        # Get date string
        date_str = "Assessment"
        if "date" in assessment:
            try:
                date_obj = datetime.fromisoformat(assessment["date"])
                date_str = date_obj.strftime("%B %d, %Y at %I:%M %p")
            except:
                pass
        
        # Get title
        title = f"Assessment {i+1}"
        if "title" in assessment:
            title = assessment["title"]
        
        # Create expander for each assessment
        with st.expander(f"{date_str} - {title}"):
            # Button to view full results
            if st.button("View Full Results", key=f"view_results_{i}"):
                st.session_state.current_assessment_index = i
                st.session_state.results = assessment.get("results", {})
                st.session_state.responses = assessment.get("responses", {})
                st.session_state.guide = assessment.get("guide", None)
                st.session_state.guide_generated = True if assessment.get("guide") else False
                st.session_state.processing_complete = True
                
                # Reset guidance conversation to empty list rather than deleting
                st.session_state.guidance_conversation = assessment.get("guidance_conversation", [])
                
                # Go to results page - this ensures we use the same view
                st.session_state.current_step = "results"
                st.rerun()
            
            # Display summary if available
            if "results" in assessment and "summary" in assessment["results"]:
                st.markdown("#### Summary")
                st.markdown(assessment["results"]["summary"])
            
            # Display key scores if available
            if "results" in assessment and "scores" in assessment["results"]:
                st.markdown("#### Key Scores")
                scores = assessment["results"]["scores"]
                
                # Create columns for score metrics
                cols = st.columns(len(scores))
                for j, (category, value) in enumerate(scores.items()):
                    with cols[j % len(cols)]:
                        display_name = category.replace("_", " ").title()
                        st.metric(label=display_name, value=value)

    # Add option to create a new assessment
    st.markdown("---")
    if st.button("Start New Assessment"):
        from modules.assessment import start_new_assessment
        start_new_assessment()
        st.rerun()

def display_progress_tracking(history):
    """Display progress tracking visualizations for multiple assessments"""
    st.markdown("### Progress Tracking")
    st.markdown("Track how your grief indicators have changed over time.")
    
    # Extract scores over time
    score_data = []
    dates = []
    
    for i, assessment in enumerate(history):
        # Skip if no results or scores
        if "results" not in assessment or "scores" not in assessment["results"]:
            continue
        
        # Get date
        date_str = f"Assessment {i+1}"
        if "timestamp" in assessment:
            try:
                date_obj = datetime.fromisoformat(assessment["timestamp"])
                date_str = date_obj.strftime("%b %d")
            except:
                pass
        elif "date" in assessment:
            try:
                date_obj = datetime.fromisoformat(assessment["date"])
                date_str = date_obj.strftime("%b %d")
            except:
                pass
        
        dates.append(date_str)
        
        # Add score data
        scores = assessment["results"]["scores"]
        for category, value in scores.items():
            # Convert to numeric if possible
            if isinstance(value, str):
                try:
                    value = float(value)
                except:
                    value = None
            
            if value is not None:
                score_data.append({
                    "date": date_str,
                    "category": category.replace("_", " ").title(),
                    "value": value,
                    "assessment_index": i
                })
    
    # Create line chart if we have data
    if score_data:
        df = pd.DataFrame(score_data)
        
        # Create line chart
        fig = px.line(
            df, 
            x="date", 
            y="value", 
            color="category",
            markers=True,
            title="Score Trends Over Time",
            labels={"value": "Score", "date": "Assessment Date", "category": "Category"}
        )
        
        # Update layout
        fig.update_layout(
            xaxis_title="Assessment Date",
            yaxis_title="Score",
            legend_title="Category",
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough data to display progress tracking yet. Complete more assessments to see trends.") 