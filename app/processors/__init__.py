# app/processors/__init__.py
from .resource import ResourceProcessor
# from .forum import ForumProcessor
# from .event import EventProcessor
# from .announcement import AnnouncementProcessor

PROCESSORS = {
    "resource": ResourceProcessor,
    # "forum": ForumProcessor,
    # "event": EventProcessor,
    # "announcement": AnnouncementProcessor,
}

def get_processor(activity_type: str):
    return PROCESSORS.get(activity_type)