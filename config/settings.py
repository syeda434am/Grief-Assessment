import os
import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_openai_api_key():
    """Get the OpenAI API key from session state or environment variables"""
    # First check if it's in session state
    if "openai_api_key" in st.session_state and st.session_state.openai_api_key:
        return st.session_state.openai_api_key
    
    # Otherwise check environment variables
    return os.environ.get("OPENAI_API_KEY", "")

def get_groq_api_key():
    """Get the Groq API key from environment variables"""
    return os.environ.get("GROQ_API_KEY", "")

def is_debug_mode():
    """Check if debug mode is enabled"""
    return os.environ.get("DEBUG", "false").lower() == "true"

def get_app_environment():
    """Get the current application environment"""
    return os.environ.get("APP_ENV", "development")

def get_app_settings():
    """Get application settings from session state or defaults"""
    settings = {
        "app_name": "Grief Compass",
        "debug_mode": is_debug_mode(),
        "theme_color": "#4a86e8",  # Default theme color
        "max_history_items": 10,    # Maximum number of history items to display
        "default_model": "gpt-4-turbo", # Default AI model
        "guide_generation_model": "gpt-4-turbo" # Model for guide generation
    }
    
    # Override with session state values if they exist
    if "app_settings" in st.session_state:
        for key, value in st.session_state.app_settings.items():
            settings[key] = value
    
    return settings

def save_app_settings(settings):
    """Save application settings to session state"""
    if "app_settings" not in st.session_state:
        st.session_state.app_settings = {}
    
    # Update settings
    for key, value in settings.items():
        st.session_state.app_settings[key] = value

def display_settings_form():
    """Display a form for updating application settings"""
    st.title("Settings")
    
    # Get current settings
    settings = get_app_settings()
    
    # API keys section
    st.markdown("### API Keys")
    
    # OpenAI API key input
    openai_key = st.text_input(
        "OpenAI API Key", 
        value=get_openai_api_key(),
        type="password",
        help="Your OpenAI API key for generating assessment results and guides."
    )
    
    # Groq API key input
    groq_key = st.text_input(
        "Groq API Key", 
        value=get_groq_api_key(),
        type="password",
        help="Your Groq API key for alternative AI generation."
    )
    
    # Application settings
    st.markdown("### Application Settings")
    
    # Theme color
    theme_color = st.color_picker(
        "Theme Color", 
        value=settings.get("theme_color", "#4a86e8"),
        help="Main color theme for the application."
    )
    
    # Debug mode
    debug_mode = st.checkbox(
        "Debug Mode", 
        value=settings.get("debug_mode", False),
        help="Enable debug information and logging."
    )
    
    # History limit
    max_history = st.number_input(
        "Maximum History Items", 
        min_value=1, 
        max_value=100, 
        value=settings.get("max_history_items", 10),
        help="Maximum number of assessment history items to display."
    )
    
    # Model selection
    model_options = ["gpt-3.5-turbo", "gpt-4-turbo", "claude-3-haiku", "claude-3-opus"]
    default_model = st.selectbox(
        "Default AI Model", 
        options=model_options,
        index=model_options.index(settings.get("default_model", "gpt-4-turbo")) if settings.get("default_model") in model_options else 0,
        help="The default AI model to use for assessment analysis."
    )
    
    guide_model = st.selectbox(
        "Guide Generation Model", 
        options=model_options,
        index=model_options.index(settings.get("guide_generation_model", "gpt-4-turbo")) if settings.get("guide_generation_model") in model_options else 0,
        help="The AI model to use for guide generation."
    )
    
    # Save button
    if st.button("Save Settings", type="primary"):
        # Save API keys to session state
        st.session_state.openai_api_key = openai_key
        st.session_state.groq_api_key = groq_key
        
        # Update settings
        updated_settings = {
            "theme_color": theme_color,
            "debug_mode": debug_mode,
            "max_history_items": max_history,
            "default_model": default_model,
            "guide_generation_model": guide_model
        }
        
        save_app_settings(updated_settings)
        
        st.success("Settings saved successfully!")
        
    # Back button
    if st.button("Back to Home"):
        st.session_state.current_step = "intro"
        st.rerun() 