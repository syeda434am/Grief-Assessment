import logging

from datetime import datetime
from typing import Dict
from groq import Groq

from com.mhire.app.config.config import Config
from com.mhire.app.common.exceptions_utility import rethrow_as_http_exception
from com.mhire.app.common.json_handler import LLMJsonHandler
from com.mhire.app.services.schedule_builder.schedule_builder_schema import ScheduleRequest, DailySchedule

logger = logging.getLogger(__name__)

class ScheduleBuilder:
    MAX_RETRIES = 3

    def __init__(self):
        try:
            config = Config()
            self.client = Groq(api_key=config.groq_api_key)
            self.model = config.groq_api_model
            self.json_handler = LLMJsonHandler()
            
            if not self.client or not self.model:
                raise ValueError("Failed to initialize: Missing required components")
                
        except Exception as e:
            rethrow_as_http_exception(e)

    def _validate_schedule_structure(self, data: Dict) -> None:
        """Basic validation of schedule structure."""
        try:
            # Check each section has activities
            for section, activities in data.items():
                if section == 'date':
                    continue
                    
                if not isinstance(activities, list):
                    raise ValueError(f"Invalid activities format in {section}")
                    
                if len(activities) == 0:
                    raise ValueError(f"No activities found in {section}")

        except ValueError as e:
            rethrow_as_http_exception(e)
        except Exception as e:
            logger.error(f"Unexpected error in schedule validation: {str(e)}", exc_info=True)
            rethrow_as_http_exception(Exception("Invalid schedule structure"))

    async def generate_daily_schedule(self, request: ScheduleRequest) -> DailySchedule:
        """Generate a personalized daily schedule based on user's grief context."""
        try:
            system_prompt = """You are a compassionate grief counselor creating a SPECIFIC daily schedule in JSON format.
Your task is to return a valid JSON response with exactly 4-5 activities for each time period.

CRUCIAL REQUIREMENTS:
1. Generate EXACTLY 4-5 activities for EACH time period in the JSON output
2. Every activity must specify EXACTLY what to do - no vague suggestions
3. Activities must be personalized to their loss and emotional state

Create a detailed JSON schedule with:

1. PHYSICAL ACTIVITIES (1-2 per day):
   ❌ "Do some stretching" (too vague)
   ✅ "10-minute gentle yoga focusing on shoulder release"
   - Specify exact movements/duration/location
   - Located in afternoon section

2. MEALS (2-3 per day):
   ❌ "Have a nourishing breakfast" (too vague)
   ✅ "Prepare cinnamon-apple oatmeal with honey"
   - Specify exact foods and portions
   - Include comfort foods with meaning

3. GRIEF RITUALS (at least 1):
   ❌ "Write in journal" (too vague)
   ✅ "Write letter about favorite holiday memory together"
   - Include specific prompts/themes
   - Located in evening section

4. SUPPORTIVE ACTIVITIES:
   ❌ "Do something creative" (too vague)
   ✅ "Create photo memory collage with written captions"
   - Give step-by-step instructions
   - Specify materials/duration"""

            user_prompt = f"""Create a highly specific daily schedule as a JSON object for someone grieving their {request.relationship.value} lost to {request.cause_of_loss.value}.

Their current state: {request.user_thoughts}

CRUCIAL: Make every activity in the JSON response specific and actionable:

❌ "Choose breakfast foods" (too vague)
✅ "Make chamomile tea and honey oatmeal with berries"

❌ "Reflect on memories" (too vague)
✅ "Write about your favorite holiday with {request.relationship.value}"

❌ "Get some exercise" (too vague)
✅ "Walk 10 minutes in backyard listening to calm piano"

The JSON response must follow this exact format:
{{
    "date": "{datetime.now().strftime('%Y-%m-%d')}",

    "morning": [
        {{
            "time_frame": "7:00 AM - 7:30 AM",
            "activity": "Specific Activity Name",
            "description": "Detailed, step-by-step instructions"
        }},
        // 3-4 more morning activities with specific details
    ],
    
    "noon": [
        // MUST include 4-5 activities with appropriate spacing
    ],
    
    "afternoon": [
        // MUST include 4-5 activities with appropriate spacing
        // Include at least one physical activity here
    ],
    
    "evening": [
        // MUST include 4-5 activities with appropriate spacing
        // Include one grief ritual here
    ],
    
    "night": [
        // MUST include 4-5 activities with appropriate spacing
        // Focus on gentle wind-down activities
    ]
}}

Requirements for JSON output:
1. Each period MUST have EXACTLY 4-5 activities
2. Space activities 15-30 minutes apart
3. Include specific physical activity in afternoon
4. Include 2-3 detailed meals throughout day
5. Include specific grief ritual in evening
6. Make all instructions detailed and exact
7. Personalize to their loss and emotions"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=2000
            )

            if not response.choices or not response.choices[0].message.content:
                raise ValueError("Invalid response from language model")

            # Parse and validate JSON structure
            schedule_data = self.json_handler.parse_json(
                response.choices[0].message.content,
                max_retries=self.MAX_RETRIES
            )
            
            # Basic structure validation
            self._validate_schedule_structure(schedule_data)
            
            # Convert to DailySchedule model
            return self.json_handler.validate_model(schedule_data, DailySchedule)

        except ValueError as e:
            rethrow_as_http_exception(e)
        except Exception as e:
            logger.error(f"Error generating schedule: {str(e)}", exc_info=True)
            rethrow_as_http_exception(Exception("Failed to generate daily schedule"))
