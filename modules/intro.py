import streamlit as st

def display_intro():
    """Display the introduction page of the application"""
    st.title("Welcome to Grief Compass")
    
    # Introduction text
    st.markdown("""
    ## Your Personalized Grief Support Guide
    
    Grief is a deeply personal experience that affects each of us uniquely. 
    Grief Compass offers compassionate guidance on your journey through loss.
    """)
    
    # Features section
    st.markdown("### How Grief Compass Helps")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📋 Personalized Assessment")
        st.markdown("""
        Complete our assessment to help understand your unique grief experience.
        """)
        
        st.markdown("#### 📊 Tailored Insights")
        st.markdown("""
        Receive personalized insights about your grief process and needs.
        """)
    
    with col2:
        st.markdown("#### 📘 Custom Support Guide")
        st.markdown("""
        Get a personalized guide with coping strategies and support resources.
        """)
        
        st.markdown("#### 📈 Track Your Journey")
        st.markdown("""
        Save your assessments to track changes in your grief experience over time.
        """)
    
    # Call to action
    st.markdown("---")
    st.markdown("### Ready to Begin?")
    
    if st.button("Start Assessment", type="primary", use_container_width=True):
        st.session_state.current_step = "story"
        st.rerun()
    
    # Secondary call to action for returning users
    if len(st.session_state.get('assessment_history', [])) > 0:
        st.markdown("#### Previous Assessments")
        st.markdown("View your previous assessment results and guides.")
        
        if st.button("View History", use_container_width=True):
            st.session_state.current_step = "history"
            st.rerun()
    
    # Information about the application
    with st.expander("About Grief Compass"):
        st.markdown("""
        **Grief Compass** was created to provide personalized support for those navigating grief and loss.
        
        This tool uses assessment responses to understand your unique experience and provide tailored recommendations.
        All information you provide is kept private and not shared with third parties.
        
        While Grief Compass can provide support, it is not a substitute for professional mental health care.
        If you are experiencing severe distress, please contact a mental health professional.
        """) 