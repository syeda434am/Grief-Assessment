import os
import json
import streamlit as st
from datetime import datetime
from langchain_core.messages import SystemMessage, HumanMessage
from config.settings import get_groq_api_key
from services.guide_service import init_groq_client
import langchain_groq

class AIService:
    """Service class for AI-related functionality"""
    
    @staticmethod
    def get_groq_client():
        """Initialize the Groq client with API key"""
        api_key = get_groq_api_key()
        if not api_key:
            st.error("Groq API key not configured. Please set it in the .env file (GROQ_API_KEY=your_api_key)")
            return None
        
        try:
            return langchain_groq.ChatGroq(
                api_key=api_key,
                model_name="llama3-70b-8192"
            )
        except Exception as e:
            st.error(f"Error initializing Groq client: {str(e)}")
            return None
    
    @staticmethod
    def get_assessment_result(responses):
        """Process assessment responses and generate results using Groq"""
        client = AIService.get_groq_client()
        if not client:
            # Don't use fallback - force user to provide a valid API key
            st.error("Please provide a valid Groq API key to continue")
            return None
        
        try:
            # Convert responses dictionary to a format that can be processed
            formatted_responses = []
            for question_id, response_data in responses.items():
                if isinstance(response_data, dict):
                    # Add properly formatted response data
                    formatted_responses.append({
                        "question_id": question_id,
                        "question_text": response_data.get("question_text", "Unknown question"),
                        "response": response_data.get("response", "")
                    })
            
            # First, analyze emotions from responses
            emotion_analysis = AIService.analyze_emotions(responses)
            
            # Add emotion analysis to formatted responses
            if emotion_analysis:
                # Store emotion analysis in the responses
                responses["emotion_analysis"] = {
                    "question_id": "emotion_analysis",
                    "question_text": "AI Emotion Analysis",
                    "response": emotion_analysis
                }
                
                # Add it to formatted responses as well
                formatted_responses.append({
                    "question_id": "emotion_analysis",
                    "question_text": "AI Emotion Analysis",
                    "response": emotion_analysis
                })
            
            # Prepare assessment data for AI
            assessment_data = {
                "responses": formatted_responses,
                "timestamp": st.session_state.get("current_timestamp", "")
            }
            
            # Create a concise prompt for the AI
            prompt = AIService.create_assessment_prompt(assessment_data)
            
            # Get response from Groq
            messages = [
                SystemMessage(content="""You are an expert in grief assessment and counseling. Analyze the responses to provide an insightful assessment of the individual's grief state, including potential risk factors and recommendations.

IMPORTANT: Return your analysis as valid JSON with the following structure:
{
    "summary": "A comprehensive summary of the assessment results",
    "scores": {
        "grief_intensity": 7.5,
        "coping_ability": 4.2,
        "support_network": 3.8
    },
    "risk_factors": ["List of identified risk factors"],
    "recommendations": ["List of personalized recommendations"]
}

Use numeric values (not strings) for all scores. Do not add any explanatory text before or after the JSON."""),
                HumanMessage(content=prompt)
            ]
            
            response = client.invoke(messages)
            
            # Parse the response
            try:
                # Strip any potential markdown or extra characters
                content = response.content.strip()
                if content.startswith("```json"):
                    content = content.split("```json", 1)[1]
                if content.endswith("```"):
                    content = content.rsplit("```", 1)[0]
                
                content = content.strip()
                
                # Extract JSON object if embedded in text
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = content[start_idx:end_idx]
                    result = json.loads(json_str)
                    
                    # Add emotion analysis to result
                    if emotion_analysis:
                        result["emotion_analysis"] = emotion_analysis
                    return result
                else:
                    st.error("Could not extract valid JSON from the response")
                    return None
            except json.JSONDecodeError as e:
                st.error(f"Could not parse AI response as JSON: {str(e)}")
                return None
        
        except Exception as e:
            st.error(f"Error generating assessment result: {str(e)}")
            return None
    
    @staticmethod
    def analyze_emotions(responses):
        """
        Use AI to analyze emotions from grief story and other responses
        
        Args:
            responses (dict): The user's responses
            
        Returns:
            dict: Analyzed emotions and their intensities
        """
        client = AIService.get_groq_client()
        if not client:
            return None
        
        try:
            # Extract grief story which now comes from the "grief_story" field in the story view
            grief_story = ""
            if "grief_story" in responses:
                grief_story = responses["grief_story"].get("response", "")
            
            # Extract meaningful memories
            memories = ""
            if "meaningful_memories" in responses:
                memories = responses["meaningful_memories"].get("response", "")
            
            # Extract emotional triggers
            triggers = ""
            if "emotional_triggers" in responses:
                triggers = responses["emotional_triggers"].get("response", "")
            
            # Extract sleep changes
            sleep_changes = ""
            if "sleep_changes" in responses:
                sleep_changes = responses["sleep_changes"].get("response", "")
            
            # Extract grief impact
            grief_impact = ""
            if "grief_impact" in responses:
                grief_impact = responses["grief_impact"].get("response", "")
            
            # Build prompt for emotion analysis
            prompt = f"""
            Based on the following responses from someone experiencing grief, 
            identify the emotions they are experiencing and rate the intensity of each emotion on a scale of 1-10.
            
            Grief Story: {grief_story}
            
            Meaningful Memories: {memories}
            
            Emotional Triggers: {triggers}
            
            Sleep Changes: {sleep_changes}
            
            Grief Impact: {grief_impact}
            
            Please analyze the emotional content in these responses and provide:
            1. A list of emotions the person is experiencing
            2. The intensity of each emotion on a scale of 1-10
            3. Brief reasoning for each emotion identified
            
            Return the results as JSON with this structure:
            {{
                "emotions": [
                    {{
                        "name": "Emotion name",
                        "intensity": 7,
                        "reasoning": "Brief explanation of why this emotion was identified"
                    }},
                    ...
                ]
            }}
            
            Focus on these common grief emotions, but feel free to add others if strongly indicated:
            Sadness, Anger, Guilt, Regret, Anxiety, Shock, Numbness, Loneliness, Relief, Yearning, 
            Emptiness, Confusion, Overwhelm, Depression, Hope, Gratitude, Peace
            """
            
            # Get response from Groq
            messages = [
                SystemMessage(content="""You are an expert in grief psychology and emotion analysis. 
                Analyze text for emotional content related to grief and identify the emotions present 
                and their intensities. Be accurate, thoughtful, and compassionate in your analysis.
                RETURN ONLY VALID JSON with no explanatory text before or after."""),
                HumanMessage(content=prompt)
            ]
            
            response = client.invoke(messages)
            
            # Parse the response
            try:
                # Strip any potential markdown or extra characters
                content = response.content.strip()
                if content.startswith("```json"):
                    content = content.split("```json", 1)[1]
                if content.endswith("```"):
                    content = content.rsplit("```", 1)[0]
                
                content = content.strip()
                
                # Extract JSON object if embedded in text
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = content[start_idx:end_idx]
                    return json.loads(json_str)
                else:
                    return None
            except Exception:
                return None
        
        except Exception as e:
            st.error(f"Error analyzing emotions: {str(e)}")
            return None
    
    @staticmethod
    def create_assessment_prompt(assessment_data):
        """Create a prompt for the Groq API based on assessment data"""
        prompt = "Please analyze the following grief assessment responses and provide a structured evaluation as JSON:\n\n"
        
        # Add responses to prompt
        for i, response in enumerate(assessment_data["responses"]):
            prompt += f"Question {i+1}: {response['question_text']}\n"
            prompt += f"Response: {response['response']}\n\n"
        
        # Specify the desired output format
        prompt += """
Please provide a JSON response with the following structure:
{
    "summary": "A comprehensive summary of the assessment results",
    "scores": {
        "grief_intensity": "Score from 1-10",
        "coping_ability": "Score from 1-10",
        "support_network": "Score from 1-10"
    },
    "risk_factors": ["List of identified risk factors"],
    "recommendations": ["List of personalized recommendations"]
}

Only return valid JSON with no additional text or markdown before or after.
"""
        return prompt
    
    @staticmethod
    def generate_fallback_result():
        """Generate a fallback result when AI processing fails"""
        return {
            "summary": "We were unable to process your assessment with our AI system. Please consider reviewing your responses with a mental health professional.",
            "scores": {
                "grief_intensity": "N/A",
                "coping_ability": "N/A",
                "support_network": "N/A"
            },
            "risk_factors": [
                "Unable to determine risk factors"
            ],
            "recommendations": [
                "Speak with a mental health professional",
                "Consider joining a grief support group",
                "Practice self-care routines",
                "Maintain connections with supportive friends and family"
            ],
            "emotion_analysis": {
                "emotions": [
                    {"name": "Sadness", "intensity": 7, "reasoning": "Common emotion in grief"},
                    {"name": "Yearning", "intensity": 6, "reasoning": "Missing the deceased"},
                    {"name": "Anxiety", "intensity": 5, "reasoning": "Uncertainty in grief process"}
                ]
            }
        }

# Provide the function interfaces for compatibility
def init_groq_client():
    """For compatibility with existing code"""
    return AIService.get_groq_client()

def get_assessment_result(responses):
    """For compatibility with existing code"""
    return AIService.get_assessment_result(responses)

def create_assessment_prompt(assessment_data):
    """For compatibility with existing code"""
    return AIService.create_assessment_prompt(assessment_data)

def generate_fallback_result():
    """For compatibility with existing code"""
    return AIService.generate_fallback_result()

# Add the get_emotion_scores function
def get_emotion_scores(responses):
    """
    Analyze responses to identify and score emotions using Groq AI
    
    Args:
        responses (dict): User's responses from the assessment
        
    Returns:
        dict: Dictionary mapping emotions to intensity scores (0-10)
    """
    # Initialize Groq client
    client = init_groq_client()
    if not client:
        # If client initialization fails, return None
        return None
    
    try:
        # Extract key information for emotion analysis
        grief_story = responses.get("grief_story", {}).get("response", "")
        current_feelings = responses.get("current_feelings", {}).get("response", "")
        cause_of_death = responses.get("cause_of_death", {}).get("response", "")
        relationship = responses.get("relationship", {}).get("response", "")
        time_since_loss = responses.get("time_since_loss", {}).get("response", "")
        
        # Get all other response values that might contain emotional content
        emotional_content = ""
        for key, value in responses.items():
            if key not in ["grief_story", "current_feelings", "cause_of_death", "relationship", "time_since_loss"]:
                if isinstance(value, dict) and "response" in value:
                    response_text = value.get("response", "")
                    if isinstance(response_text, str) and len(response_text) > 0:
                        emotional_content += f"{response_text} "
        
        # Create combined text for analysis
        analysis_text = f"""
        Grief Story: {grief_story}
        Current Feelings: {current_feelings}
        Cause of Death: {cause_of_death}
        Relationship to Deceased: {relationship}
        Time Since Loss: {time_since_loss}
        Additional Content: {emotional_content}
        """
        
        # Define the fixed list of grief emotions to analyze
        grief_emotions = [
            "Sadness", "Yearning/Missing", "Guilt", "Anger", "Denial", 
            "Anxiety", "Loneliness", "Depression", "Numbness", "Shock", 
            "Regret", "Despair", "Resentment", "Acceptance", "Hope"
        ]
        
        # Create prompt for emotion analysis
        prompt = f"""
        Based on the following grief assessment responses, analyze the emotional state and identify the intensity of different emotions present.
        
        {analysis_text}
        
        Please analyze and score ONLY the following emotions on a scale of 1-10:
        {", ".join(grief_emotions)}
        
        For each emotion, provide a score that reflects how strongly that emotion is present in the person's grief experience.
        A score of 1 means minimal presence, while 10 indicates overwhelming intensity.
        
        Return your analysis ONLY as a valid JSON object with emotion names as keys and intensity scores (1-10) as values.
        For example: {{"Sadness": 8.2, "Anger": 5.7, "Guilt": 7.1, "Yearning/Missing": 9.3}}
        
        Even if an emotion seems absent, include it with a very low score (1-2) rather than omitting it.
        IMPORTANT: Return ONLY a valid JSON object - no explanatory text before or after.
        """
        
        # Get response from Groq
        response = client.invoke(
            [
                SystemMessage(content="""You are an expert emotion analyst specializing in grief psychology.
                Your task is to analyze grief narratives and identify the intensity of different emotions present.
                
                IMPORTANT INSTRUCTIONS:
                1. Return ONLY a valid JSON object with emotion names as keys and numeric scores (0-10) as values
                2. Do not include any explanations, markdown formatting, or text outside the JSON object
                3. Base your analysis solely on the text provided
                4. Include ALL emotions in the list provided, even if they have very low scores
                5. Make sure your response is properly formatted JSON with double quotes around keys
                """),
                HumanMessage(content=prompt)
            ]
        )
        
        # Clean and parse the response
        response_content = response.content.strip()
        
        # Remove any markdown code blocks or extra text
        import re
        response_content = re.sub(r'```json\s*|\s*```', '', response_content).strip()
        
        # Find where the JSON object starts and ends
        start_idx = response_content.find('{')
        end_idx = response_content.rfind('}') + 1
        
        if start_idx >= 0 and end_idx > start_idx:
            json_str = response_content[start_idx:end_idx]
            emotion_scores = json.loads(json_str)
            
            # Ensure all grief emotions are included with at least a minimal score
            for emotion in grief_emotions:
                found = False
                # Check for exact or partial matches
                for key in list(emotion_scores.keys()):
                    if emotion.lower() in key.lower() or key.lower() in emotion.lower():
                        # If found with similar name, standardize the key
                        if key != emotion:
                            emotion_scores[emotion] = emotion_scores.pop(key)
                        found = True
                        break
                
                # If not found at all, add with minimal score
                if not found:
                    emotion_scores[emotion] = 1.0
            
            return emotion_scores
        else:
            # If no valid JSON found, return None
            return None
            
    except Exception as e:
        if st.session_state.get("debug_mode", False):
            st.error(f"Error in emotion scoring: {str(e)}")
        return None 