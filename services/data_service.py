import json
import os
import datetime
import streamlit as st
import uuid

# Define the storage directory
DATA_DIR = "data"
ASSESSMENTS_DIR = os.path.join(DATA_DIR, "assessments")
GUIDES_DIR = os.path.join(DATA_DIR, "guides")

def initialize_storage():
    """Initialize the data storage directories"""
    os.makedirs(ASSESSMENTS_DIR, exist_ok=True)
    os.makedirs(GUIDES_DIR, exist_ok=True)

def save_assessment(user_id, responses, result=None):
    """Save assessment responses and results to file"""
    initialize_storage()
    
    # Generate unique assessment ID
    assessment_id = str(uuid.uuid4())
    
    # Create assessment data structure
    assessment_data = {
        "assessment_id": assessment_id,
        "user_id": user_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "responses": responses,
        "result": result
    }
    
    # Save to file
    file_path = os.path.join(ASSESSMENTS_DIR, f"{assessment_id}.json")
    with open(file_path, "w") as f:
        json.dump(assessment_data, f, indent=2)
    
    return assessment_id

def save_guide(assessment_id, guide_data):
    """Save a generated guide to file"""
    initialize_storage()
    
    # Create guide data structure
    guide_entry = {
        "guide_id": str(uuid.uuid4()),
        "assessment_id": assessment_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "guide_data": guide_data
    }
    
    # Save to file
    file_path = os.path.join(GUIDES_DIR, f"{assessment_id}_guide.json")
    with open(file_path, "w") as f:
        json.dump(guide_entry, f, indent=2)
    
    return guide_entry["guide_id"]

def get_assessment(assessment_id):
    """Retrieve an assessment by ID"""
    file_path = os.path.join(ASSESSMENTS_DIR, f"{assessment_id}.json")
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return None

def get_guide(assessment_id):
    """Retrieve a guide by assessment ID"""
    file_path = os.path.join(GUIDES_DIR, f"{assessment_id}_guide.json")
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return None

def get_user_assessments(user_id):
    """Get all assessments for a specific user"""
    if not os.path.exists(ASSESSMENTS_DIR):
        return []
    
    user_assessments = []
    for filename in os.listdir(ASSESSMENTS_DIR):
        if filename.endswith('.json'):
            file_path = os.path.join(ASSESSMENTS_DIR, filename)
            with open(file_path, 'r') as f:
                assessment = json.load(f)
                if assessment.get('user_id') == user_id:
                    user_assessments.append(assessment)
    
    # Sort by timestamp (newest first)
    user_assessments.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return user_assessments

def update_assessment_result(assessment_id, result):
    """Update the result for an existing assessment"""
    assessment = get_assessment(assessment_id)
    if not assessment:
        return False
    
    assessment['result'] = result
    
    file_path = os.path.join(ASSESSMENTS_DIR, f"{assessment_id}.json")
    with open(file_path, "w") as f:
        json.dump(assessment, f, indent=2)
    
    return True 