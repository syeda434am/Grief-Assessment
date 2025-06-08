from pydantic import BaseModel
from typing import List
from enum import Enum

class Relationship(str, Enum):
    PARENT = "Parent"
    CHILD = "Child"
    SIBLING = "Sibling"
    PARTNER = "Partner"
    FRIEND = "Friend"
    OTHER = "Other"

class CauseOfLoss(str, Enum):
    ILLNESS = "Illness"
    ACCIDENT = "Accident"
    SUICIDE = "Suicide"
    NATURAL = "Natural"
    MURDER = "Murder"
    OTHER = "Other"

class ToolTitle(str, Enum):
    STAY_CONNECTED = "Stay connected"
    WORK_THROUGH_EMOTIONS = "Work Through Emotions"
    FIND_STRENGTH = "Find Strength"
    MINDFULNESS = "Mindfulness"
    CHECK_IN = "Check In"
    GET_MOVING = "Get Moving"

class GriefContentRequest(BaseModel):
    user_thoughts: str
    relationship: Relationship
    cause_of_loss: CauseOfLoss
    tool_title: ToolTitle
    tool_description: str
    tool_name: str

class SongRecommendation(BaseModel):
    title: str
    url: str
    reason: str

class GriefContentResponse(BaseModel):
    motivation_cards: List[str]
    song_recommendation: SongRecommendation
    essay: dict