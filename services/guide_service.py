import langchain_groq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
import json
import streamlit as st
from config.settings import get_groq_api_key
from datetime import datetime

def init_groq_client():
    """Initialize the Groq client with API key"""
    api_key = get_groq_api_key()
    if not api_key:
        st.error("Groq API key not configured. Please set it in the .env file (GROQ_API_KEY=your_api_key)")
        return None
    
    # Simply initialize client without extra tests that might fail
    try:
        return langchain_groq.ChatGroq(
            api_key=api_key,
            model_name="llama3-70b-8192"
        )
    except Exception as e:
        error_message = str(e)
        st.error(f"Failed to initialize Groq client: {error_message}")
        return None

def generate_guide(responses, assessment_result, guide_options=None):
    """Generate a personalized grief support guide based on assessment results and options
    
    Args:
        responses (dict): User's responses from the assessment
        assessment_result (dict): Results from the assessment analysis
        guide_options (dict, optional): Options for customizing the guide
        
    Returns:
        dict: The generated guide data
    """
    client = init_groq_client()
    if not client:
        return generate_fallback_guide()
    
    try:
        # Create prompt for guide generation
        prompt = create_guide_prompt(assessment_result, responses, guide_options)
        
        # Get response from Groq
        response = client.invoke(
            [
                SystemMessage(content="""You are an expert in grief counseling and support. Create a compassionate, personalized guide for someone experiencing grief. Focus on practical strategies, validation of their experience, and resources for support.

IMPORTANT: Your response MUST be VALID JSON without any markdown formatting, explanations, or non-JSON text. Return ONLY the JSON object, nothing else.

Your responses must follow the exact JSON structure requested. Each field must be thoroughly developed with specific, actionable guidance tailored to this person's unique grief situation.

Be warm and empathetic in your writing, but also concrete and specific. Avoid generic platitudes. Instead, provide detailed routines, activities, and resources that directly address their particular loss circumstances, relationship, timeline, and emotional state.

The self-care strategies, recommended reading, and resources should be FULLY CUSTOMIZED to this specific person's grief experience and NOT generic. Make sure each resource, book, and recommendation directly relates to their specific type of loss, relationship to the deceased, and emotional state.

For resources, you should:
1. Include SPECIFIC support groups relevant to their specific grief type (e.g., child loss, suicide loss, etc.)
2. Recommend SPECIFIC books that address their exact grief situation
3. Include SPECIFIC hotlines and support services tailored to their needs
4. Ensure ALL recommendations are personalized, NOT generic

Every part of the guide must show clear evidence of customization for this individual based on the information provided."""),
                HumanMessage(content=prompt)
            ]
        )
        
        # Parse the response
        response_content = response.content
        
        # First clean the response of any markdown code blocks
        import re
        response_content = re.sub(r'```json\s*|\s*```', '', response_content).strip()
        
        # Try to fix common JSON issues
        try:
            # Method 1: Try to find where the JSON object starts and ends
            content = response_content
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                content = content[start_idx:end_idx]
                try:
                    guide = json.loads(content)
                    # Save current guide to session state for future reference
                    if 'current_guide' not in st.session_state:
                        st.session_state.current_guide = guide
                    return guide
                except json.JSONDecodeError:
                    # Try to clean up the JSON
                    cleaned_content = content.replace("'", '"')  # Replace single quotes with double quotes
                    cleaned_content = re.sub(r',\s*([}\]])', r'\1', cleaned_content)  # Remove trailing commas
                    cleaned_content = re.sub(r'([{,]\s*)([a-zA-Z0-9_]+)(\s*:)', r'\1"\2"\3', cleaned_content)  # Ensure keys have quotes
                    
                    try:
                        guide = json.loads(cleaned_content)
                        # Save current guide to session state for future reference
                        if 'current_guide' not in st.session_state:
                            st.session_state.current_guide = guide
                        return guide
                    except json.JSONDecodeError:
                        pass  # Continue to next method
            
            # Method 2: Try to extract JSON from markdown code blocks
            json_match = re.search(r'```(?:json)?\n(.*?)\n```', response_content, re.DOTALL)
            if json_match:
                try:
                    guide = json.loads(json_match.group(1))
                    # Save current guide to session state for future reference
                    if 'current_guide' not in st.session_state:
                        st.session_state.current_guide = guide
                    return guide
                except json.JSONDecodeError:
                    # Try cleaning extracted JSON
                    cleaned_content = json_match.group(1).replace("'", '"')
                    cleaned_content = re.sub(r',\s*([}\]])', r'\1', cleaned_content)
                    cleaned_content = re.sub(r'([{,]\s*)([a-zA-Z0-9_]+)(\s*:)', r'\1"\2"\3', cleaned_content)
                    
                    try:
                        guide = json.loads(cleaned_content)
                        # Save current guide to session state for future reference
                        if 'current_guide' not in st.session_state:
                            st.session_state.current_guide = guide
                        return guide
                    except json.JSONDecodeError:
                        pass  # Continue to next approach
            
            # Method 3: More aggressive JSON extraction - find anything between outermost { and }
            json_raw_match = re.search(r'(\{.+\})', response_content, re.DOTALL)
            if json_raw_match:
                try:
                    raw_json = json_raw_match.group(1)
                    # Clean up the JSON
                    raw_json = raw_json.replace("'", '"')
                    raw_json = re.sub(r',\s*([}\]])', r'\1', raw_json)
                    raw_json = re.sub(r'([{,]\s*)([a-zA-Z0-9_]+)(\s*:)', r'\1"\2"\3', raw_json)
                    
                    guide = json.loads(raw_json)
                    # Save current guide to session state for future reference
                    if 'current_guide' not in st.session_state:
                        st.session_state.current_guide = guide
                    return guide
                except json.JSONDecodeError:
                    pass  # Move to fallback
            
            # If all attempts fail, log the error and use fallback
            st.error(f"Could not parse guide response as JSON after multiple attempts")
            return generate_fallback_guide()
            
        except Exception as e:
            st.error(f"Error processing guide response: {str(e)}")
            return generate_fallback_guide()
    
    except Exception as e:
        st.error(f"Error generating personalized guide: {str(e)}")
        return generate_fallback_guide()

def create_guide_prompt(assessment_result, responses, guide_options=None):
    """Create a prompt for the guide generation
    
    Args:
        assessment_result (dict): Results from the assessment analysis
        responses (dict): User's responses from the assessment
        guide_options (dict, optional): Options for customizing the guide
        
    Returns:
        str: The formatted prompt for guide generation
    """
    prompt = "Please create a personalized grief support guide based on the following assessment information:\n\n"
    
    # Add basic information about the loss
    cause_of_death = responses.get("cause_of_death", {}).get("response", "Not specified")
    time_since_loss = responses.get("time_since_loss", {}).get("response", "Not specified")
    relationship = responses.get("relationship", {}).get("response", "Not specified")
    employment_status = responses.get("employment_status", {}).get("response", "Not specified")
    
    prompt += f"CAUSE OF DEATH: {cause_of_death}\n"
    prompt += f"TIME SINCE LOSS: {time_since_loss}\n"
    prompt += f"RELATIONSHIP TO DECEASED: {relationship}\n"
    prompt += f"EMPLOYMENT STATUS: {employment_status}\n\n"
    
    # Add grief story
    grief_story = responses.get("grief_story", {}).get("response", "")
    if grief_story:
        prompt += f"THEIR GRIEF STORY:\n{grief_story}\n\n"
    
    # Add current feelings and emotional information
    current_feelings = responses.get("current_feelings", {}).get("response", "")
    if current_feelings:
        prompt += f"CURRENT EMOTIONAL STATE: {current_feelings}\n"
    
    # Add emotions information
    emotions = responses.get("emotion_presence", {}).get("response", [])
    
    if emotions:
        prompt += f"DOMINANT EMOTIONS: {', '.join(emotions)}\n\n"
    
    # Add sleep patterns
    sleep_patterns = responses.get("sleep_patterns", {}).get("response", "")
    if sleep_patterns:
        prompt += f"SLEEP PATTERNS: {sleep_patterns}\n"
    
    # Add daily functioning
    daily_functioning = responses.get("daily_functioning", {}).get("response", "")
    if daily_functioning:
        prompt += f"DAILY FUNCTIONING: {daily_functioning}\n\n"
    
    # Add emotional triggers
    emotional_triggers = responses.get("emotional_triggers", {}).get("response", "")
    if emotional_triggers:
        prompt += f"EMOTIONAL TRIGGERS: {emotional_triggers}\n\n"
    
    # Add coping strategies
    coping_strategies = responses.get("coping_strategies", {}).get("response", [])
    if coping_strategies:
        prompt += f"COPING STRATEGIES USED: {', '.join(coping_strategies)}\n\n"
    
    # Add support network
    support_network = responses.get("support_network", {}).get("response", [])
    if support_network:
        prompt += f"SUPPORT NETWORK: {', '.join(support_network)}\n\n"
    
    # Add physical symptoms
    physical_symptoms = responses.get("physical_symptoms", {}).get("response", [])
    if physical_symptoms:
        prompt += f"PHYSICAL SYMPTOMS: {', '.join(physical_symptoms)}\n\n"
    
    # Add grief challenges
    grief_challenges = responses.get("grief_challenges", {}).get("response", "")
    if grief_challenges:
        prompt += f"SPECIFIC CHALLENGES: {grief_challenges}\n\n"
    
    # Add assessment summary
    prompt += f"ASSESSMENT SUMMARY: {assessment_result.get('summary', 'Not available')}\n\n"
    
    # Add recommendations
    recommendations = assessment_result.get('recommendations', [])
    if recommendations:
        prompt += "RECOMMENDATIONS:\n"
        for rec in recommendations:
            prompt += f"- {rec}\n"
        prompt += "\n"
    
    # Specify the desired output format
    prompt += """
Please provide a JSON response with the following structure:
{
    "title": "A compassionate, personalized title for the guide",
    "introduction": "A concise, empathetic overview tailored to their specific cause of death, timeframe, and relationship to the deceased. This should acknowledge their unique grief journey and validate their experience.",
    
    "weekly_routine": {
        "1": {
            "hourly_schedule": {
                "6:00 AM": "Detailed activity for this time (e.g., gentle wake-up routine with specific steps)",
                "7:00 AM": "Detailed activity for this time (e.g., specific breakfast with nutritional guidance)",
                "8:00 AM": "Detailed activity for this time",
                "9:00 AM": "Detailed activity for this time",
                "10:00 AM": "Detailed activity for this time",
                "11:00 AM": "Detailed activity for this time",
                "12:00 PM": "Detailed activity for this time",
                "1:00 PM": "Detailed activity for this time",
                "2:00 PM": "Detailed activity for this time",
                "3:00 PM": "Detailed activity for this time",
                "4:00 PM": "Detailed activity for this time",
                "5:00 PM": "Detailed activity for this time",
                "6:00 PM": "Detailed activity for this time",
                "7:00 PM": "Detailed activity for this time",
                "8:00 PM": "Detailed activity for this time",
                "9:00 PM": "Detailed activity for this time",
                "10:00 PM": "Detailed activity for this time"
            },
            "key_focus": "The emotional or healing focus for this day"
        },
        "2": {
            "hourly_schedule": {
                "6:00 AM": "Detailed activity for this time",
                "7:00 AM": "Detailed activity for this time",
                "8:00 AM": "Detailed activity for this time",
                "9:00 AM": "Detailed activity for this time",
                "10:00 AM": "Detailed activity for this time",
                "11:00 AM": "Detailed activity for this time",
                "12:00 PM": "Detailed activity for this time",
                "1:00 PM": "Detailed activity for this time",
                "2:00 PM": "Detailed activity for this time",
                "3:00 PM": "Detailed activity for this time",
                "4:00 PM": "Detailed activity for this time",
                "5:00 PM": "Detailed activity for this time",
                "6:00 PM": "Detailed activity for this time",
                "7:00 PM": "Detailed activity for this time",
                "8:00 PM": "Detailed activity for this time",
                "9:00 PM": "Detailed activity for this time",
                "10:00 PM": "Detailed activity for this time"
            },
            "key_focus": "The emotional or healing focus for this day"
        },
        "3": {
            "hourly_schedule": {
                "6:00 AM": "Detailed activity for this time",
                "7:00 AM": "Detailed activity for this time",
                "8:00 AM": "Detailed activity for this time",
                "9:00 AM": "Detailed activity for this time",
                "10:00 AM": "Detailed activity for this time",
                "11:00 AM": "Detailed activity for this time",
                "12:00 PM": "Detailed activity for this time",
                "1:00 PM": "Detailed activity for this time",
                "2:00 PM": "Detailed activity for this time",
                "3:00 PM": "Detailed activity for this time",
                "4:00 PM": "Detailed activity for this time",
                "5:00 PM": "Detailed activity for this time",
                "6:00 PM": "Detailed activity for this time",
                "7:00 PM": "Detailed activity for this time",
                "8:00 PM": "Detailed activity for this time",
                "9:00 PM": "Detailed activity for this time",
                "10:00 PM": "Detailed activity for this time"
            },
            "key_focus": "The emotional or healing focus for this day"
        },
        "4": {
            "hourly_schedule": {
                "6:00 AM": "Detailed activity for this time",
                "7:00 AM": "Detailed activity for this time",
                "8:00 AM": "Detailed activity for this time",
                "9:00 AM": "Detailed activity for this time",
                "10:00 AM": "Detailed activity for this time",
                "11:00 AM": "Detailed activity for this time",
                "12:00 PM": "Detailed activity for this time",
                "1:00 PM": "Detailed activity for this time",
                "2:00 PM": "Detailed activity for this time",
                "3:00 PM": "Detailed activity for this time",
                "4:00 PM": "Detailed activity for this time",
                "5:00 PM": "Detailed activity for this time",
                "6:00 PM": "Detailed activity for this time",
                "7:00 PM": "Detailed activity for this time",
                "8:00 PM": "Detailed activity for this time",
                "9:00 PM": "Detailed activity for this time",
                "10:00 PM": "Detailed activity for this time"
            },
            "key_focus": "The emotional or healing focus for this day"
        },
        "5": {
            "hourly_schedule": {
                "6:00 AM": "Detailed activity for this time",
                "7:00 AM": "Detailed activity for this time",
                "8:00 AM": "Detailed activity for this time",
                "9:00 AM": "Detailed activity for this time",
                "10:00 AM": "Detailed activity for this time",
                "11:00 AM": "Detailed activity for this time",
                "12:00 PM": "Detailed activity for this time",
                "1:00 PM": "Detailed activity for this time",
                "2:00 PM": "Detailed activity for this time",
                "3:00 PM": "Detailed activity for this time",
                "4:00 PM": "Detailed activity for this time",
                "5:00 PM": "Detailed activity for this time",
                "6:00 PM": "Detailed activity for this time",
                "7:00 PM": "Detailed activity for this time",
                "8:00 PM": "Detailed activity for this time",
                "9:00 PM": "Detailed activity for this time",
                "10:00 PM": "Detailed activity for this time"
            },
            "key_focus": "The emotional or healing focus for this day"
        },
        "6": {
            "hourly_schedule": {
                "6:00 AM": "Detailed activity for this time",
                "7:00 AM": "Detailed activity for this time",
                "8:00 AM": "Detailed activity for this time",
                "9:00 AM": "Detailed activity for this time",
                "10:00 AM": "Detailed activity for this time",
                "11:00 AM": "Detailed activity for this time",
                "12:00 PM": "Detailed activity for this time",
                "1:00 PM": "Detailed activity for this time",
                "2:00 PM": "Detailed activity for this time",
                "3:00 PM": "Detailed activity for this time",
                "4:00 PM": "Detailed activity for this time",
                "5:00 PM": "Detailed activity for this time",
                "6:00 PM": "Detailed activity for this time",
                "7:00 PM": "Detailed activity for this time",
                "8:00 PM": "Detailed activity for this time",
                "9:00 PM": "Detailed activity for this time",
                "10:00 PM": "Detailed activity for this time"
            },
            "key_focus": "The emotional or healing focus for this day"
        },
        "7": {
            "hourly_schedule": {
                "6:00 AM": "Detailed activity for this time",
                "7:00 AM": "Detailed activity for this time",
                "8:00 AM": "Detailed activity for this time",
                "9:00 AM": "Detailed activity for this time",
                "10:00 AM": "Detailed activity for this time",
                "11:00 AM": "Detailed activity for this time",
                "12:00 PM": "Detailed activity for this time",
                "1:00 PM": "Detailed activity for this time",
                "2:00 PM": "Detailed activity for this time",
                "3:00 PM": "Detailed activity for this time",
                "4:00 PM": "Detailed activity for this time",
                "5:00 PM": "Detailed activity for this time",
                "6:00 PM": "Detailed activity for this time",
                "7:00 PM": "Detailed activity for this time",
                "8:00 PM": "Detailed activity for this time",
                "9:00 PM": "Detailed activity for this time",
                "10:00 PM": "Detailed activity for this time"
            },
            "key_focus": "The emotional or healing focus for this day"
        }
    },
    
    "self_care": {
        "physical_activity": "A detailed description of one physical activity specifically chosen for their grief situation",
        "nourishing_meal": "A detailed description of one nourishing meal with ingredients and preparation notes",
        "evening_ritual": "A detailed description of one evening ritual designed to foster healing"
    },
    
    "resources": {
        "support_groups": [
            {
                "name": "Name of support group",
                "url": "URL to support group",
                "description": "Brief description of why this group is particularly relevant"
            }
        ],
        "books": [
            {
                "title": "Book title",
                "author": "Author name",
                "description": "Brief description of why this book is helpful for their situation"
            }
        ],
        "hotlines": [
            {
                "name": "Name of hotline or service",
                "number": "Phone number",
                "description": "Brief description of the service"
            }
        ],
        "professional_services": [
            {
                "name": "Type of professional service",
                "description": "Brief description of why this service may be helpful"
            }
        ]
    }
}

Important guidelines:
1. Be extremely specific and personalized to their unique grief situation, especially considering:
   - The cause of death (suicide, illness, accident, etc.)
   - Their relationship to the deceased (parent, child, spouse, etc.)
   - How long it's been since the loss
   - Their employment status - tailor routines to accommodate their work schedule or lack thereof
   - Their current emotional state and dominant feelings
   - Physical symptoms they're experiencing
   - Specific challenges they've mentioned

2. For the weekly routine with hourly schedules:
   - If they are employed (full-time or part-time), create separate WEEKDAY and WEEKEND hourly schedules
   - If they are unemployed or retired, create a structured hourly routine that provides purpose and healing
   - If they are a student, incorporate study time and campus-based resources
   - Include both grief processing activities and necessary daily functions
   - Each hourly activity should be SPECIFIC and DETAILED, not generic
   - Each day should have a clear emotional or healing focus
   - Include time for:
     * Self-care activities appropriate to their situation
     * Grief processing (journaling, remembrance, etc.)
     * Physical movement
     * Rest and reflection
     * Social connection when appropriate
     * Work/study obligations (if applicable)
     * Meals with nutritional guidance
     * Grief-specific coping strategies

3. Choose self-care activities that are:
   - Appropriate for their grief stage and emotional capacity
   - Realistic for their employment situation and daily responsibilities
   - Specifically helpful for their mentioned physical symptoms
   - Aligned with any coping strategies they've found helpful

4. Provide resources that are specifically chosen for their situation, including:
   - Support groups relevant to their specific loss (e.g., pet loss, child loss, etc.)
   - Resources appropriate for their employment status (e.g., workplace grief support)
   - Books by real authors addressing their specific relationship loss
   - Appropriate hotlines for their emotional needs

5. Write in a warm, compassionate tone throughout, while being concrete and actionable.
"""
    return prompt

def generate_followup_response(user_feedback, guide_data=None):
    """
    Generate a follow-up response to a user question about their grief guide
    
    Args:
        user_feedback (str): The user's question or feedback
        guide_data (dict, optional): The guide data to reference
        
    Returns:
        str: AI response to the user's question
    """
    client = init_groq_client()
    if not client:
        return "I'm unable to provide personalized guidance at the moment. Please make sure your Groq API key is set correctly in the .env file."
    
    try:
        # Use current guide from session state if not provided
        if not guide_data and 'current_guide' in st.session_state:
            guide_data = st.session_state.current_guide
        
        # Create context with available information
        context = ""
        
        # Add basic info if available
        if 'responses' in st.session_state:
            cause_of_death = st.session_state.responses.get("cause_of_death", {}).get("response", "Not specified")
            relationship = st.session_state.responses.get("relationship", {}).get("response", "Not specified")
            time_since_loss = st.session_state.responses.get("time_since_loss", {}).get("response", "Not specified")
            context += f"The person is grieving the loss of their {relationship} due to {cause_of_death}. It has been {time_since_loss} since the loss.\n\n"
        
        # Add guide information
        if guide_data:
            context += f"Guide title: {guide_data.get('title', 'Personal Grief Guide')}\n"
            context += f"Introduction: {guide_data.get('introduction', '')[:500]}...\n\n"
            
            # Add some self-care info
            if 'self_care' in guide_data:
                context += "Self-care recommendations include:\n"
                for key, value in guide_data.get('self_care', {}).items():
                    if isinstance(value, str):
                        context += f"- {key.replace('_', ' ').title()}: {value[:100]}...\n"
                context += "\n"
            
            # Add resources info
            if 'resources' in guide_data:
                context += "Resources recommended include:\n"
                for resource_type, resources in guide_data.get('resources', {}).items():
                    if isinstance(resources, list) and resources:
                        context += f"- {resource_type.replace('_', ' ').title()}: {len(resources)} items recommended\n"
                context += "\n"
        
        # Get previous conversation if available
        conversation_history = []
        if 'guidance_conversation' in st.session_state:
            conversation_history = st.session_state.guidance_conversation
        
        # Create messages array with system message
        messages = [
            SystemMessage(content="""You are an empathetic grief counselor providing personalized follow-up guidance. 
You are powered by Groq AI and should provide thoughtful, compassionate responses to questions about grief.
            
Do NOT mention that you are an AI, a language model, or any references to being a machine. Simply respond as a grief counselor.

Your responses should be compassionate, specific, and practical. Your goal is to help the person navigate their grief journey, 
providing tailored advice that responds directly to their question while being sensitive to their unique circumstances.

Some key guidelines:
1. Focus on their specific question or need while considering their overall grief context
2. Be compassionate but practical - offer concrete suggestions they can implement
3. Validate their grief experience and normalize their feelings
4. Avoid generic platitudes; provide thoughtful, specific guidance
5. If appropriate, suggest specific resources like books, support groups, or coping techniques
6. Keep responses conversational and personalized"""),
            HumanMessage(content=f"Context about the grief situation: {context}\n\nUser question: {user_feedback}")
        ]
        
        # Add brief conversation history if available
        if conversation_history:
            history_summary = "Previous messages included:\n"
            for i, entry in enumerate(conversation_history[-3:]):  # Just include the last 3 exchanges
                if 'user_message' in entry:
                    history_summary += f"User asked: {entry['user_message'][:100]}...\n"
                if 'ai_response' in entry:
                    history_summary += f"Response covered: {entry['ai_response'][:100]}...\n"
            
            # Add history as a separate message to avoid confusing the model
            messages.insert(1, HumanMessage(content=f"Conversation history for context: {history_summary}"))
        
        # Get response from Groq
        response = client.invoke(messages)
        
        # Save this exchange to conversation history
        if 'guidance_conversation' not in st.session_state:
            st.session_state.guidance_conversation = []
            
        st.session_state.guidance_conversation.append({
            "user_message": user_feedback,
            "ai_response": response.content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Return the response content
        return response.content
    
    except Exception as e:
        error_msg = str(e)
        st.error(f"Error generating follow-up response: {error_msg}")
        
        if "401" in error_msg or "invalid_api_key" in error_msg:
            return "I'm unable to provide a response due to an API authentication issue. Please check that your Groq API key is correctly set in the .env file."
        
        return "I'm sorry, I encountered an issue while generating a response to your question. Please try again in a moment."

def generate_generic_guidance_response(question):
    """Generate a generic response when no guide data is available
    
    Args:
        question (str): The user's question
        
    Returns:
        str: A generic but helpful response
    """
    client = init_groq_client()
    if not client:
        return "I'm unable to provide guidance at the moment. Please ensure your API key is configured correctly."
    
    try:
        # Create a generic prompt
        messages = [
            SystemMessage(content="You are a compassionate grief counselor providing general guidance. Without specific details about the person, offer thoughtful, broadly applicable advice for grief support. Be warm and supportive."),
            HumanMessage(content=f"Please provide general grief support guidance in response to this question: {question}")
        ]
        
        # Get response from Groq
        response = client.invoke(messages)
        
        return response.content
    
    except Exception as e:
        return "I'm sorry, I'm having trouble generating a response. Grief is a deeply personal journey, and it might be helpful to speak with a mental health professional for personalized guidance."

def generate_fallback_guide():
    """Generate a fallback guide when the main AI processing fails - but still use AI"""
    client = init_groq_client()
    if not client:
        # If we can't even get a client, return a minimal fallback
        return {
            "title": "Temporary Guide - Please Try Again Later",
            "introduction": "We're experiencing technical difficulties. Please try completing your assessment again for a fully personalized guide."
        }
    
    try:
        # Create a comprehensive prompt for the fallback guide
        prompt = """
        Please create a compassionate grief support guide that would be helpful for anyone experiencing grief.
        
        Since I don't have specific details about the individual's grief situation, please create a guide that:
        1. Addresses common grief experiences across different types of loss
        2. Provides supportive guidance for various emotional responses to grief
        3. Offers practical self-care strategies that would benefit most people grieving
        4. Suggests resources that are widely applicable and helpful
        
        Return the guide in JSON format with this structure:
        {
            "title": "A compassionate, thoughtful title for the guide",
            "introduction": "A detailed, empathetic overview that acknowledges the grief journey, validates difficult emotions, and offers hope for healing while respecting individual timelines",
            
            "weekly_routine": {
                "1": {
                    "hourly_schedule": {
                        "Morning": "Detailed suggestions for a gentle morning routine that supports emotional processing",
                        "Mid-morning": "Specific activities for this time period that balance reflection and daily tasks",
                        "Afternoon": "Structured but gentle afternoon activity suggestions that provide both support and distraction",
                        "Early evening": "Recommendations for emotionally supportive activities during this transition time",
                        "Evening": "Detailed evening ritual suggestions for emotional regulation and sleep preparation"
                    },
                    "key_focus": "A meaningful emotional or healing focus for this day"
                },
                "2": { similar detailed structure with variations },
                "3": { similar detailed structure with variations },
                "4": { similar detailed structure with variations },
                "5": { similar detailed structure with variations },
                "6": { similar detailed structure with variations },
                "7": { similar detailed structure with variations }
            },
            
            "self_care": {
                "physical_activity": "Detailed suggestions for gentle, grief-appropriate physical activities with specific examples",
                "nourishing_meals": "Specific meal suggestions that are both nourishing and practical for someone experiencing grief",
                "mindfulness_practices": "Detailed mindfulness exercises specifically designed for grief processing",
                "emotional_regulation": "Specific techniques for managing overwhelming emotions during grief",
                "sleep_support": "Detailed practices to support sleep during grief",
                "social_connection": "Thoughtful ways to maintain social connections while honoring grief"
            },
            
            "resources": {
                "support_groups": [
                    {
                        "name": "Name of widely available support group",
                        "url": "URL to support group",
                        "description": "Detailed description of how this group specifically helps with grief"
                    },
                    {
                        "name": "Name of another widely available support group",
                        "url": "URL to support group",
                        "description": "Detailed description of how this group specifically helps with grief"
                    },
                    {
                        "name": "Name of another widely available support group",
                        "url": "URL to support group",
                        "description": "Detailed description of how this group specifically helps with grief"
                    }
                ],
                "books": [
                    {
                        "title": "Title of widely respected grief book",
                        "author": "Author name",
                        "description": "Detailed description of how this book specifically helps with grief"
                    },
                    {
                        "title": "Title of another widely respected grief book",
                        "author": "Author name",
                        "description": "Detailed description of how this book specifically helps with grief"
                    },
                    {
                        "title": "Title of another widely respected grief book",
                        "author": "Author name",
                        "description": "Detailed description of how this book specifically helps with grief"
                    }
                ],
                "hotlines": [
                    {
                        "name": "Name of widely available crisis or support hotline",
                        "number": "Phone number",
                        "description": "Detailed description of when and how to use this service"
                    },
                    {
                        "name": "Name of another widely available crisis or support hotline",
                        "number": "Phone number",
                        "description": "Detailed description of when and how to use this service"
                    }
                ],
                "apps": [
                    {
                        "name": "Name of helpful grief support app",
                        "platform": "Available platforms",
                        "description": "Detailed description of how this app specifically helps with grief"
                    },
                    {
                        "name": "Name of another helpful grief support app",
                        "platform": "Available platforms",
                        "description": "Detailed description of how this app specifically helps with grief"
                    }
                ]
            }
        }
        
        Create completely original content that is compassionate, specific, and practical. Use a warm, supportive tone throughout.
        Focus on providing genuine support that would help anyone navigating grief, regardless of their specific circumstances.
        """
        
        # Get response from Groq with comprehensive system message
        response = client.invoke(
            [
                SystemMessage(content="""You are an expert in grief counseling and support with deep compassion for those experiencing loss.
                
                Your task is to create a comprehensive, supportive grief guide that would be helpful for anyone experiencing grief, regardless of their specific circumstances.
                
                Your guidance should be:
                1. Compassionate and validating of the grief experience
                2. Specific and actionable rather than vague platitudes
                3. Based on evidence-informed approaches to grief support
                4. Respectful of individual grief journeys and timelines
                5. Holistic, addressing emotional, physical, social, and spiritual dimensions
                
                Generate completely original content that feels personal and supportive. Use a warm, empathetic tone that conveys genuine care.
                
                All resources mentioned should be real, accessible, and widely available. Ensure book recommendations are actual published works, support groups are genuine organizations, and hotlines are real services."""),
                HumanMessage(content=prompt)
            ]
        )
        
        # Parse the response
        try:
            guide = json.loads(response.content)
            # Save current guide to session state for future reference
            if 'current_guide' not in st.session_state:
                st.session_state.current_guide = guide
            return guide
        except json.JSONDecodeError:
            # If the response is not valid JSON, try different extraction methods
            import re
            
            # Method 1: Try extracting JSON from code blocks - this pattern matches content between ```json and ``` 
            json_match = re.search(r'```(?:json)?\n(.*?)\n```', response.content, re.DOTALL)
            if json_match:
                try:
                    guide = json.loads(json_match.group(1))
                    # Save current guide to session state for future reference
                    if 'current_guide' not in st.session_state:
                        st.session_state.current_guide = guide
                    return guide
                except json.JSONDecodeError:
                    pass  # Continue to next extraction method if this fails
            
            # Method 2: Try looking for a JSON object directly in the text with relaxed pattern matching
            # Look for content between { and } that spans multiple lines 
            json_raw_match = re.search(r'(\{.+\})', response.content, re.DOTALL)
            if json_raw_match:
                try:
                    # Try to clean up the JSON by removing some common non-JSON compliant patterns
                    raw_json = json_raw_match.group(1)
                    # Replace non-standard quotes
                    raw_json = raw_json.replace("'", '"')
                    # Remove trailing commas before closing brackets
                    raw_json = re.sub(r',\s*([}\]])', r'\1', raw_json)
                    # Ensure all keys have double quotes
                    raw_json = re.sub(r'([{,]\s*)([a-zA-Z0-9_]+)(\s*:)', r'\1"\2"\3', raw_json)
                    
                    guide = json.loads(raw_json)
                    # Save current guide to session state for future reference
                    if 'current_guide' not in st.session_state:
                        st.session_state.current_guide = guide
                    return guide
                except json.JSONDecodeError:
                    pass  # Continue to next method if this fails
            
            # If all extraction methods fail, try with simplified prompt
            try:
                # Try with a more direct, simplified prompt
                simplified_prompt = """Create a brief, compassionate grief support guide in this exact JSON format:
                {
                    "title": "Support Guide for Your Grief Journey",
                    "introduction": "A paragraph offering compassion and validation for grief",
                    "weekly_routine": {
                        "1": {
                            "hourly_schedule": {
                                "Morning": "A morning suggestion",
                                "Afternoon": "An afternoon suggestion",
                                "Evening": "An evening suggestion"
                            },
                            "key_focus": "A focus for the day"
                        }
                    },
                    "self_care": {
                        "physical_activity": "A suggestion for physical self-care",
                        "emotional_support": "A suggestion for emotional self-care"
                    },
                    "resources": {
                        "support_groups": [{"name": "A support group name", "description": "Brief description"}],
                        "books": [{"title": "A helpful book", "author": "Author name", "description": "Brief description"}]
                    }
                }

Just respond with valid, properly formatted JSON."""
                
                # Try with simplified prompt
                second_response = client.invoke(
                    [
                        SystemMessage(content="You are a grief counselor creating a simple, helpful guide. Your response must be valid JSON and nothing else."),
                        HumanMessage(content=simplified_prompt)
                    ]
                )
                
                # Try to parse the second response with the same extraction methods
                try:
                    guide = json.loads(second_response.content)
                    # Save current guide to session state for future reference
                    if 'current_guide' not in st.session_state:
                        st.session_state.current_guide = guide
                    return guide
                except json.JSONDecodeError:
                    # Try code block extraction
                    json_match = re.search(r'```(?:json)?\n(.*?)\n```', second_response.content, re.DOTALL)
                    if json_match:
                        guide = json.loads(json_match.group(1))
                        # Save current guide to session state for future reference
                        if 'current_guide' not in st.session_state:
                            st.session_state.current_guide = guide
                        return guide
                    
                    # Try raw json extraction
                    json_raw_match = re.search(r'(\{.+\})', second_response.content, re.DOTALL)
                    if json_raw_match:
                        raw_json = json_raw_match.group(1)
                        raw_json = raw_json.replace("'", '"')
                        raw_json = re.sub(r',\s*([}\]])', r'\1', raw_json)
                        raw_json = re.sub(r'([{,]\s*)([a-zA-Z0-9_]+)(\s*:)', r'\1"\2"\3', raw_json)
                        
                        guide = json.loads(raw_json)
                        # Save current guide to session state for future reference
                        if 'current_guide' not in st.session_state:
                            st.session_state.current_guide = guide
                        return guide
                
            except Exception as e:
                # If all attempts fail, log error and return minimal guide
                st.error(f"All guide generation attempts failed: {str(e)}")
                
                # Absolute last resort - minimal guide with no fixed content except structure
                return {
                    "title": "Support for Your Grief Journey",
                    "introduction": "We're experiencing technical difficulties processing your full assessment. This temporary guide offers general support while our system recovers. Please consider trying again later for a fully personalized guide.",
                    "weekly_routine": {
                        "1": {"key_focus": "Gentle self-compassion during this difficult time"}
                    },
                    "self_care": {
                        "note": "Self-care is essential during grief. Consider what has helped you feel even slightly better in the past."
                    },
                    "resources": {
                        "note": "Please consider reaching out to local grief support services or a trusted healthcare provider for personalized guidance."
                    }
                }
    
    except Exception as e:
        # Absolute last resort if everything fails
        return {
            "title": "Support for Your Grief Journey",
            "introduction": "We're experiencing technical difficulties processing your full assessment. This temporary guide offers general support while our system recovers. Please consider trying again later for a fully personalized guide.",
            "weekly_routine": {
                "1": {"key_focus": "Gentle self-compassion during this difficult time"}
            },
            "self_care": {
                "note": "Self-care is essential during grief. Consider what has helped you feel even slightly better in the past."
            },
            "resources": {
                "note": "Please consider reaching out to local grief support services or a trusted healthcare provider for personalized guidance."
            }
        } 