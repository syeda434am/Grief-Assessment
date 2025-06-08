from enum import Enum
from pydantic import BaseModel, ConfigDict
from typing import List, Dict
from datetime import datetime

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

class ScheduleRequest(BaseModel):
    user_thoughts: str
    relationship: Relationship
    cause_of_loss: CauseOfLoss

class Activity(BaseModel):
    time_frame: str
    activity: str
    description: str | None = None

class DailySchedule(BaseModel):
    date: str
    morning: List[Activity]
    noon: List[Activity]
    afternoon: List[Activity]
    evening: List[Activity]
    night: List[Activity]
    
    model_config = ConfigDict(from_attributes=True)