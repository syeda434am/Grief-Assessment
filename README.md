# Grief Compass

A personalized grief assessment and support application that provides customized guidance for individuals navigating the grief journey.

## Overview

Grief Compass helps users understand and manage their grief by:

1. Collecting information about their grief experience through a streamlined assessment
2. Analyzing responses using AI to generate personalized insights
3. Creating a comprehensive guide tailored to their specific grief situation
4. Providing ongoing conversational support through an interactive chat interface
5. Allowing users to save and revisit previous assessments

All content is dynamically generated using the Groq API, providing personalized guidance rather than generic advice.

## Features

- **Intuitive Assessment Process**: Simple, conversational assessment flow
- **Personalized Guidance**: AI-generated content tailored to each person's grief experience
- **Emotional Visualization**: Visual representation of the user's emotion profile
- **Interactive Chat Support**: Ongoing conversational guidance to address specific aspects of grief
- **Downloadable Guides**: PDF export of the complete assessment results and guidance
- **History Management**: Save and access previous assessments and conversations

## Project Structure

The application is organized into modular components:

- `app.py`: Main Streamlit application entry point
- `modules/`: Core functional modules
  - `assessment.py`: Assessment flow and results display
  - `intro.py`: Introduction and welcome page
  - `story.py`: Initial grief story collection
  - `results.py`: Results processing and display
  - `history.py`: Assessment history management
- `services/`: Backend services
  - `guide_service.py`: AI guide generation using Groq
  - `ai_service.py`: AI assessment analysis
- `ui/`: UI components
  - `components.py`: Reusable UI elements and PDF generation
- `config/`: Configuration
  - `questions.py`: Assessment questions
  - `settings.py`: Application settings

## Setup and Running

1. Clone the repository
2. Install dependencies:
```
pip install -r requirements.txt
```
3. Set up environment variables in `.env`:
```
GROQ_API_KEY="your_groq_api_key_here"
```
4. Run the application:
```
streamlit run app.py
```

## User Flow

1. **Home**: Introduction to Grief Compass
2. **Story Entry**: Share the grief experience in user's own words
3. **Assessment**: Answer questions about grief experience
4. **Results**: View personalized analysis and guidance
5. **Conversation**: Ask follow-up questions to refine guidance
6. **History**: Access previous assessments and continue conversations

## Dependencies

- Streamlit: Web application framework
- Langchain & Groq: AI integration for personalized content
- Plotly: Data visualization
- FPDF: PDF generation

## Configuration

The application reads configuration from:
- `.env` file for API keys and environment variables
- `config/settings.py` for application settings
- `config/questions.py` for assessment questions

## Contributing

To contribute to this project:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request with your changes

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Streamlit](https://streamlit.io/) for the web application framework
- [Groq](https://groq.com/) for LLM API access
- All contributors to grief research and resources