# app/processors/event.py
from .base import BaseProcessor
from services import IndexManager
from utils.moodle_helpers import normalize_moodle_date
from typing import Dict
from models import CourseDocument

class EventProcessor(BaseProcessor):
    async def process(self, course_id: str, content: Dict):
        """Process calendar events and deadlines"""
        try:
            # Format event information
            start_time = normalize_moodle_date(content['timestart'])
            end_time = normalize_moodle_date(content['timestart'] + content['timeduration'])
            
            event_text = (
                f"Calendar Event: {content['name']}\n"
                f"Type: {content['eventtype']}\n"
                f"Time: {start_time} to {end_time}\n"
                f"Description: {content['description']}"
            )
            
            # Create document with metadata
            document = self._create_document(
                text=event_text,
                course_id=course_id,
                metadata={
                    "type": "event",
                    "event_type": content['eventtype'],
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat()
                }
            )
            
            IndexManager().add_documents([document])
            
        except KeyError as e:
            raise ValueError(f"Missing required event field: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Event processing failed: {str(e)}")