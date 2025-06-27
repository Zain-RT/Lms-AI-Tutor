from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from config import Config
from typing import List, Dict

def create_document(text: str, metadata: Dict) -> Document:
    """Create LlamaIndex document with metadata"""
    return Document(
        text=text,
        metadata=metadata,
        metadata_seperator="::",
        metadata_template="{key}: {value}"
    )

def chunk_document(document: Document) -> List[Document]:
    """Chunk document using LlamaIndex parser"""
    parser = SentenceSplitter(
        chunk_size=Config.CHUNK_SIZE,
        chunk_overlap=Config.CHUNK_OVERLAP,
        include_metadata=True
    )
    return parser.get_nodes_from_documents([document])