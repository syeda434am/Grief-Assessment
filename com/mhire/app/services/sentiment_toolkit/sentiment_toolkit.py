import logging

from typing import Dict, Any
from groq import Groq

from com.mhire.app.config.config import Config
from com.mhire.app.common.json_handler import LLMJsonHandler
from com.mhire.app.common.exceptions_utility import rethrow_as_http_exception
from com.mhire.app.services.sentiment_toolkit.sentiment_toolkit_schema import UserInput, ToolsResponse, Emotion

logger = logging.getLogger(__name__)

class SentimentToolkit:
    """
    A toolkit for analyzing grief-related sentiment and providing personalized support tools.
    Handles sentiment analysis and tool recommendations with proper error handling and JSON validation.
    """

    MAX_RETRIES = 3
    ALLOWED_EMOTIONS = set(emotion.value for emotion in Emotion)

    def __init__(self):
        """Initialize the SentimentToolkit with required configurations."""
        try:
            config = Config()
            if not config.groq_api_key or not config.groq_api_model:
                raise ValueError("Missing required configuration: GROQ_API_KEY or GROQ_MODEL_NAME")
                
            self.client = Groq(api_key=config.groq_api_key)
            self.model = config.groq_api_model
            self.json_handler = LLMJsonHandler()
            
        except Exception as e:
            logger.error(f"Failed to initialize SentimentToolkit: {str(e)}")
            rethrow_as_http_exception(e)

    async def _analyze_sentiment(self, user_thoughts: str) -> str:
        """Analyze the sentiment of user's grief-related thoughts."""
        try:
            sentiment_prompt = f"""
            Analyze the sentiment in this grief-related thought. 
            Return ONLY ONE emotional keyword from this exact list: {', '.join(sorted(self.ALLOWED_EMOTIONS))}
            
            Thought: "{user_thoughts}"
            
            CRUCIAL REQUIREMENTS:
            1. Return ONLY the emotion word, no other text
            2. ONLY use emotions from the provided list
            3. Choose the most relevant emotion for grief counseling
            """

            sentiment_response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": sentiment_prompt}],
                response_format={"type": "text"}
            )

            if not sentiment_response.choices or not sentiment_response.choices[0].message.content:
                raise ValueError("Invalid sentiment analysis response")

            # Clean and validate emotion
            mood = sentiment_response.choices[0].message.content.strip()
            if mood not in self.ALLOWED_EMOTIONS:
                raise ValueError(f"Invalid emotion: {mood}")

            return mood

        except Exception as e:
            logger.error(f"Error in sentiment analysis: {str(e)}")
            rethrow_as_http_exception(e)

    async def analyze_grief(self, request: UserInput) -> Dict[str, Any]:
        """
        Analyze grief input and provide personalized tool recommendations.
        
        Args:
            request: UserInput model containing user's grief context
            
        Returns:
            Dict containing mood analysis and personalized tool recommendations
            
        Raises:
            HTTPException: For any errors in processing or invalid responses
        """
        try:
            # First, analyze sentiment
            mood = await self._analyze_sentiment(request.user_thoughts)            # Generate tools based on input and mood
            tools_prompt = f"""
            Based on:
            - User thoughts: {request.user_thoughts}
            - Relationship: {request.relationship}
            - Cause of loss: {request.cause_of_loss}
            - Current mood: {mood}

             You are a compassionate mental health assistant designed to support individuals experiencing grief. You will be provided with six fixed categories related to grief management. For each category:

Write a gentle, supportive description explaining the purpose of the category and how it helps with grief.

Suggest two tool names or activity titles under each category.

Each tool should have a clear, and supportive title (Between 4 to 5 words).

The titles should be practical, actionable, and relevant to the category.

Descriptions should be written in a kind, hopeful tone.

Avoid medical jargon — keep the language accessible and empathetic.
Focus on emotional support, mindfulness, physical well-being, and personal reflection.:
Generate a JSON response with this exact structure for grief support tools.

            {{
              "1. Stay Connected": {{
                "description": "one line description here",
                "tools": ["tool1 name", "tool2 name"]
              }},
              "2. Work Through Emotions": {{
                "description": "Clear, single-line purpose statement",
                "tools": ["Specific tool 1", "Specific tool 2"]
              }},
              "3. Find Strength": {{
                "description": "Clear, single-line purpose statement",
                "tools": ["Specific tool 1", "Specific tool 2"]
              }},
              "4. Mindfulness": {{
                "description": "Clear, single-line purpose statement",
                "tools": ["Specific tool 1", "Specific tool 2"]
              }},
              "5. Check In": {{
                "description": "Clear, single-line purpose statement",
                "tools": ["Specific tool 1", "Specific tool 2"]
              }},
              "6. Get Moving": {{
                "description": "Clear, single-line purpose statement",
                "tools": ["Specific tool 1", "Specific tool 2"]
              }}
            }}            Make the descriptions concise and tool names specific to grief support.
            Return only the JSON object, no other text."""

            tools_response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": tools_prompt}],
                response_format={"type": "json_object"}
            )

            if not tools_response.choices or not tools_response.choices[0].message.content:
                raise ValueError("Invalid tools generation response")

            # Process and validate response
            content = tools_response.choices[0].message.content
            titles = self.json_handler.parse_json(content, max_retries=self.MAX_RETRIES)

            # Construct and validate final response
            result = {
                "mood": mood,
                "titles": titles
            }
            
            # Validate with model but return dictionary instead of model object
            validated_model = self.json_handler.validate_model(result, ToolsResponse)
            return validated_model.model_dump()  # For Pydantic v2
            # If using Pydantic v1, use: return validated_model.dict()

        except Exception as e:
            logger.error(f"Error in analyze_grief: {str(e)}", exc_info=True)
            rethrow_as_http_exception(e)