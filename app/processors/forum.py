# app/processors/forums.py
# from .base import BaseProcessor
# from utils.chunkers import resource_chunker
# from utils.moodle_helpers import clean_html_content, extract_file_text
# from typing import Dict
# class ForumProcessor:
#     async def process(self, course_id, content):
#         clean_text = strip_html(content["message"])
#         metadata = {
#             "author": content["author"],
#             "tags": content["tags"],
#             "type": "forum_post"
#         }
#         await index_chunks(course_id, [clean_text], metadata)