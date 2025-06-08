import os
import json
import logging
import re
from typing import Dict, Any

from groq import Groq
from tavily import TavilyClient

from com.mhire.app.config.config import Config
from com.mhire.app.common.exceptions_utility import rethrow_as_http_exception
from com.mhire.app.common.json_handler import LLMJsonHandler
from com.mhire.app.services.personalized_content.personalized_content_schema import GriefContentRequest, Relationship, CauseOfLoss

logger = logging.getLogger(__name__)

class PersonalizedContent:
    MAX_RETRIES = 3
    
    def __init__(self):
        try:
            config = Config()
            self.client = Groq(api_key=config.groq_api_key)
            self.model = config.groq_api_model
            self.tavily_client = TavilyClient(api_key=config.tavily_api_key)
            self.json_handler = LLMJsonHandler()
            
            # Validate all required components
            if not self.client or not self.model or not self.tavily_client:
                raise ValueError("Failed to initialize: Missing required configuration")
                
        except Exception as e:                
            rethrow_as_http_exception(e)

    def _count_words(self, text: str) -> int:
        """Count words in a text string."""
        return len(text.split())
    
    def _get_total_essay_words(self, essay_data: dict) -> int:
        """Calculate total words in all essay sections."""
        return sum(self._count_words(section) for section in essay_data.values())

    async def _get_song_suggestion(self, user_thoughts: str, relationship: Relationship, cause_of_loss: CauseOfLoss) -> Dict:
        """Get a song suggestion from the LLM based on the grief context."""
        try:
            # Step 1: Have LLM suggest a personalized song based on user's grief context
            system_prompt = (
                "You are a grief counselor and music therapist specialized in modern music (2010-latest). "
                "Suggest a modern, uplifting song or music that directly relates to this person's specific grief situation. "
                "The song or music should resonate with their emotions while offering hope. "
                "The song or music should be from 2010 or later to ensure it's modern and relatable. "
                "Return ONLY a JSON object. Use only double quotes for JSON strings. "
                "Never use single quotes or unescaped quotes in values."
            )
            
            user_prompt = f"""Based on this grief context, suggest a healing and uplifting song or music:
User's Thoughts: {user_thoughts}
Relationship to deceased: {relationship}
Cause of Loss: {cause_of_loss}

Consider:
1. Their specific relationship ({relationship}) - choose a song or music that relates to this bond
2. Their expressed thoughts and emotions
3. The nature of their loss ({cause_of_loss})
4. Must be a modern song or music (2010-latest) with high production quality
5. Should have themes of love, memory, healing, and finding strength
6. Must be uplifting while respecting the depth of their grief

Respond ONLY with a JSON object in this format:
{{
    "title": "Song  or music title",
    "artist": "Artist name",
    "why_relevant": "Detailed explanation of why this specific song or music matches their situation"
}}"""

            for attempt in range(self.MAX_RETRIES):
                try:
                    completion = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        response_format={"type": "json_object"},
                        temperature=0.7
                    )
                    response = completion.choices[0].message.content
                    initial_song = self.json_handler.parse_json(response, max_retries=self.MAX_RETRIES)
                    
                    if isinstance(initial_song, dict) and all(k in initial_song for k in ('title', 'artist', 'why_relevant')):
                        break
                except Exception as e:
                    logger.warning(f"Initial song suggestion attempt {attempt + 1} failed: {str(e)}")
                    if attempt == self.MAX_RETRIES - 1:
                        rethrow_as_http_exception(e)
            else:
                logger.error("Failed to get initial song suggestion")
                rethrow_as_http_exception(Exception("Could not generate initial song suggestion"))

            # Step 2: Search for official music video versions of the suggested song
            search_query = f"{initial_song['title']} {initial_song['artist']} official music video youtube"
            search_results = self.tavily_client.search(
                query=search_query,
                search_depth="advanced",
                max_results=5  # Get exactly 5 versions to choose from
            )

            # Step 3: Process YouTube results
            youtube_candidates = []
            seen_urls = set()
            
            for result in search_results.get('results', []):
                url = result.get('url', '')
                if 'youtube.com/watch?v=' in url and url not in seen_urls:
                    # Normalize URL format to www.youtube.com
                    normalized_url = url.replace('m.youtube.com', 'www.youtube.com')
                    if not normalized_url.startswith('https://www.'):
                        normalized_url = normalized_url.replace('https://', 'https://www.')
                    
                    seen_urls.add(normalized_url)
                    youtube_candidates.append({
                        "title": result.get('title', ''),
                        "url": normalized_url,
                        "description": result.get('description', '')
                    })

            if not youtube_candidates:
                logger.error("No YouTube results found for suggested song")
                rethrow_as_http_exception(Exception("Could not find any video versions of the suggested song"))

            # Step 4: Have LLM choose the best version for their situation
            selection_prompt = f"""Based on this grief context:
User's Thoughts: {user_thoughts}
Relationship to deceased: {relationship}
Cause of Loss: {cause_of_loss}

I initially recommended {initial_song['title']} by {initial_song['artist']} because:
{initial_song['why_relevant']}

Here are available YouTube versions. Select the most appropriate one that will be healing for them:
{json.dumps(youtube_candidates, indent=2)}

Consider:
1. Video quality and production value
2. Official vs unofficial versions
3. Whether it has visuals that support the healing message
4. Audio clarity and quality

Respond ONLY with a JSON object in this format:
{{
    "selected_index": 0,  # Index of the chosen video (0-4)
    "reason": "1 very short line of why this specific version will be most healing for them"
}}"""

            for attempt in range(self.MAX_RETRIES):
                try:
                    completion = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": selection_prompt}
                        ],
                        response_format={"type": "json_object"},
                        temperature=0.7
                    )
                    response = completion.choices[0].message.content
                    selection_data = self.json_handler.parse_json(response, max_retries=self.MAX_RETRIES)
                    
                    if selection_data and isinstance(selection_data, dict) and 'selected_index' in selection_data:
                        index = int(selection_data['selected_index'])
                        if 0 <= index < len(youtube_candidates):
                            selected_video = youtube_candidates[index]
                            return {
                                'title': initial_song['title'],
                                'url': selected_video['url'],
                                'reason': f"{initial_song['why_relevant']} {selection_data.get('reason', '')}"
                            }
                except Exception as e:
                    logger.warning(f"Video selection attempt {attempt + 1} failed: {str(e)}")
                    if attempt == self.MAX_RETRIES - 1:
                        rethrow_as_http_exception(e)

            # If all attempts fail
            logger.error("Failed to select appropriate video version")
            rethrow_as_http_exception(Exception("Could not select the most appropriate song video"))
            
        except Exception as e:
            rethrow_as_http_exception(e)

    async def generate_personalized_content(self, request: GriefContentRequest) -> dict:
        """Generate personalized grief content based on user input."""
        try:
            # Step 1: Get song suggestion
            song_suggestion = await self._get_song_suggestion(
                user_thoughts=request.user_thoughts,
                relationship=request.relationship.value,
                cause_of_loss=request.cause_of_loss.value
            )

            # Step 2: Generate content with structured JSON response
            system_prompt = f"""Create personalized grief guidance based on:

Context:
- User's Thoughts: {request.user_thoughts}
- Relationship: {request.relationship.value}
- Cause of Loss: {request.cause_of_loss.value}
- Tool Selected: {request.tool_title.value}
- Tool Description: {request.tool_description}

Return ONLY a JSON object with this structure and EXACT word counts:
{{
    "motivation_cards": [
        "First message - one actionable, comforting sentence with no quotes",
        "Second message - one actionable, comforting sentence with no quotes",
        "Third message - one actionable, comforting sentence with no quotes"
    ],
    "essay": {{
        "quote": "Quote and author in format: Quote text - Author Name (EXACTLY 10-15 words)",
        "welcome_to_grief_works": "How grief work begins - personalized to them (EXACTLY 130 words)",
        "grief_is_hard_work": "Challenges of grieving specific to their loss (EXACTLY 100 words)",
        "about_your_grief": "Personalize guidance to their situation (EXACTLY 130 words)",
        "heal_and_grow": "Actionable steps forward with a ritual to calm the soul (EXACTLY 125 words)"
    }}
}}

Total essay word count MUST be EXACTLY between 490-530 words (sum of quote: 15, welcome_to_grief_works: 130, grief_is_hard_work: 100, about_your_grief: 130, heal_and_grow: 125 = 500 words).
Do NOT generate fewer or more words per section or in total. Use meaningful content to reach exact counts, avoiding fluff.
Other Requirements:
1. Never use quotes inside any value
2. Each section must directly relate to their situation
3. Use compassionate, understanding tone
4. Make content actionable while acknowledging pain
5. Each motivation card must be a complete sentence"""

            for attempt in range(self.MAX_RETRIES):
                try:
                    completion = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": system_prompt}
                        ],
                        response_format={"type": "json_object"},
                        temperature=0.7
                    )

                    response = completion.choices[0].message.content.strip()
                    logger.debug(f"Content generation response: {response}")
                    
                    content_data = self.json_handler.parse_json(response, max_retries=self.MAX_RETRIES)

                    # Basic structure validation
                    if not isinstance(content_data, dict):
                        logger.error("Content response is not a valid JSON object")
                        if attempt == self.MAX_RETRIES - 1:
                            rethrow_as_http_exception(Exception("Invalid response format"))
                        continue
                    
                    if 'motivation_cards' not in content_data or 'essay' not in content_data:
                        logger.error("Content response missing required fields")
                        if attempt == self.MAX_RETRIES - 1:
                            rethrow_as_http_exception(Exception("Response missing required fields: motivation_cards, essay"))
                        continue
                    
                    cards = content_data.get('motivation_cards', [])
                    essay_data = content_data.get('essay', {})
                    
                    # Basic validation of motivation cards
                    valid_cards = []
                    for card in cards[:3]:  # Take up to 3 cards
                        if isinstance(card, str) and card.strip():
                            valid_cards.append(card.strip())
                    
                    if not valid_cards:
                        if attempt == self.MAX_RETRIES - 1:
                            rethrow_as_http_exception(Exception("No valid motivation cards found in response"))
                        continue
                    
                    # Basic validation of essay sections
                    required_essay_sections = [
                        'quote',
                        'welcome_to_grief_works',
                        'grief_is_hard_work',
                        'about_your_grief',
                        'heal_and_grow'
                    ]
                    
                    valid_essay = True
                    for section in required_essay_sections:
                        if section not in essay_data or not isinstance(essay_data[section], str) or not essay_data[section].strip():
                            valid_essay = False
                            break
                    
                    if not valid_essay:
                        if attempt == self.MAX_RETRIES - 1:
                            rethrow_as_http_exception(Exception("Essay is missing required sections"))
                        continue                    # Log word counts for monitoring
                    for section, content in essay_data.items():
                        word_count = self._count_words(content)
                        logger.info(f"Section {section} word count: {word_count}")

                    # Calculate total words for logging purposes
                    total_words = self._get_total_essay_words(essay_data)
                    if total_words < 490 or total_words > 510:
                        logger.warning(f"Essay total word count {total_words} outside target range (490-510)")

                    # If we get here, return the content
                    return {
                        "motivation_cards": valid_cards,
                        "song_recommendation": song_suggestion,
                        "essay": {
                            "quote": essay_data['quote'],
                            "welcome_to_grief_works": essay_data['welcome_to_grief_works'],
                            "grief_is_hard_work": essay_data['grief_is_hard_work'],
                            "about_your_grief": essay_data['about_your_grief'],
                            "heal_and_grow": essay_data['heal_and_grow']
                        }
                    }

                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                    if attempt == self.MAX_RETRIES - 1:
                        logger.error("Failed to generate content after all retries", exc_info=True)
                        rethrow_as_http_exception(e)
            
        except Exception as e:
            logger.error(f"Error generating personalized content: {str(e)}", exc_info=True)
            rethrow_as_http_exception(e)