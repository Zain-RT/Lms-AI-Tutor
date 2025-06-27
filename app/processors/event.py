# from .base import BaseProcessor
# from utils.llama_helpers import create_document
# from utils.moodle_helpers import normalize_moodle_date

# class EventProcessor(BaseProcessor):
#     async def process(self, course_id: str, content: Dict):
#         start_time = normalize_moodle_date(content['timestart'])
#         end_time = normalize_moodle_date(content['timestart'] + content['timeduration'])
        
#         text = (
#             f"EVENT: {content['name']}\n"
#             f"Type: {content['eventtype']}\n"
#             f"Time: {start_time} to {end_time}\n"
#             f"Description: {content['description']}"
#         )
        
#         document = create_document(text, {
#             "type": "event",
#             "event_type": content["eventtype"],
#             "start_time": start_time.isoformat(),
#             "end_time": end_time.isoformat(),
#             "course_id": course_id
#         })
#         self.index_manager.add_documents(course_id, [document])