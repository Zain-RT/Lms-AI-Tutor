# app/processors/__init__.py
from .resource import ResourceProcessor
# from .forum import ForumProcessor
# from .event import EventProcessor
# from .announcement import AnnouncementProcessor

PROCESSORS = {
    "resource": ResourceProcessor
}

def get_processor(activity_type: str):
    return PROCESSORS.get(activity_type)