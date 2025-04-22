import streamlit as st
import datetime
from services.guide_service import generate_guide

def display_guide_selection():
    """Display the guide selection page"""
    st.title("Create Your Personalized Grief Guide")
    
    if 'results' not in st.session_state or not st.session_state.results:
        st.error("Please complete an assessment first to generate a guide.")
        if st.button("Start New Assessment"):
            st.session_state.current_step = "assessment"
            st.rerun()
        return
    
    # Guide information
    st.markdown("""
    ### Your Personal Grief Support Guide
    
    Based on your assessment, we can create a personalized grief support guide 
    tailored to your specific situation and needs.
    
    Your guide will include:
    - Personalized support strategies 
    - Self-care practices
    - Reflection exercises
    - Resources matched to your needs
    - Daily practices to integrate into your routine
    """)
    
    # Selection options
    st.markdown("### Guide Options")
    
    guide_type = st.radio(
        "Select the type of guide you'd like to create:",
        ["Comprehensive Guide", "Focused Guide"],
        help="A comprehensive guide covers all aspects of grief support. A focused guide concentrates on specific areas of need."
    )
    
    if guide_type == "Focused Guide":
        focus_areas = st.multiselect(
            "Select areas to focus on:",
            ["Emotional Processing", "Coping Strategies", "Self-Care", "Finding Meaning", "Social Support", "Daily Routines"],
            default=["Emotional Processing", "Coping Strategies"],
            help="Choose the areas that feel most relevant to your current needs"
        )
    
    # Guide generation button
    st.markdown("### Create Your Guide")
    
    if 'guide_generation_started' not in st.session_state:
        st.session_state.guide_generation_started = False
    
    if not st.session_state.guide_generation_started:
        if st.button("Generate My Guide", type="primary", use_container_width=True):
            st.session_state.guide_generation_started = True
            
            # Setup guide options
            guide_options = {
                "type": guide_type,
                "focus_areas": focus_areas if guide_type == "Focused Guide" else []
            }
            
            # Set the guide options in session state
            st.session_state.guide_options = guide_options
            
            st.rerun()
    else:
        # Show spinner and generate guide
        with st.spinner("Creating your personalized guide... This may take a minute."):
            # Generate guide based on assessment results
            responses = st.session_state.results.get("responses", [])
            assessment_result = st.session_state.results
            guide_options = st.session_state.get("guide_options", {})
            
            st.session_state.guide = generate_guide(
                responses,
                assessment_result,
                guide_options
            )
            
            # Move to guide view step
            st.session_state.current_step = "guide_view"
            st.rerun()
    
    # Cancel button
    if st.button("Back to Results", use_container_width=True):
        st.session_state.current_step = "results"
        st.rerun()

def display_guide_view():
    """Display the generated guide"""
    if 'guide' not in st.session_state or not st.session_state.guide:
        st.error("No guide has been generated yet.")
        if st.button("Create a Guide"):
            st.session_state.current_step = "guide_selection"
            st.rerun()
        return
    
    guide = st.session_state.guide
    
    # Guide header
    st.title(guide.get("title", "Your Personalized Grief Support Guide"))
    
    # Introduction
    st.markdown("### Introduction")
    st.markdown(guide.get("introduction", ""))
    
    # Understanding grief section
    st.markdown("### Understanding Your Grief")
    st.markdown(guide.get("understanding_grief", ""))
    
    # Coping strategies
    st.markdown("### Coping Strategies")
    strategies = guide.get("coping_strategies", [])
    for strategy in strategies:
        st.markdown(f"- {strategy}")
    
    # Self-care practices
    st.markdown("### Self-Care Practices")
    practices = guide.get("self_care_practices", [])
    for practice in practices:
        st.markdown(f"- {practice}")
    
    # Support resources
    st.markdown("### Support Resources")
    resources = guide.get("support_resources", [])
    for resource in resources:
        st.markdown(f"- {resource}")
    
    # Daily practices
    st.markdown("### Daily Practices")
    daily_practices = guide.get("daily_practices", [])
    for practice in daily_practices:
        st.markdown(f"- {practice}")
    
    # Conclusion
    st.markdown("### Moving Forward")
    st.markdown(guide.get("conclusion", ""))
    
    # Display specific exercises if available
    if "exercises" in guide and guide["exercises"]:
        st.markdown("### Exercises")
        
        for i, exercise in enumerate(guide["exercises"], 1):
            with st.expander(f"Exercise {i}: {exercise.get('title', 'Reflection Exercise')}"):
                st.markdown(exercise.get("description", ""))
                
                if "steps" in exercise:
                    st.markdown("**Steps:**")
                    for step in exercise["steps"]:
                        st.markdown(f"1. {step}")
    
    # Navigation buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Back to Results", use_container_width=True):
            st.session_state.current_step = "results"
            st.rerun()
    
    with col2:
        if st.download_button(
            label="Download Guide (PDF)",
            data="Guide content would be generated as PDF here",
            file_name=f"grief_compass_guide_{datetime.datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True
        ):
            # In a real implementation, this would generate and provide the PDF
            pass 