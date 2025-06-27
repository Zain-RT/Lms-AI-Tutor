# from .base import BaseProcessor
# from utils.llama_helpers import create_document

# class ForumProcessor(BaseProcessor):
#     async def process(self, course_id: str, content: Dict):
#         text = f"FORUM POST by {content['author']}\n\n{content['message']}"
#         document = create_document(text, {
#             "type": "forum",
#             "author": content["author"],
#             "post_date": content["created"],
#             "course_id": course_id
#         })
#         self.index_manager.add_documents(course_id, [document])