from typing import Dict, List, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
import hashlib
import json

from backend.app.models.schemas import CodebaseContext, FileUpload
from backend.app.services.parser import CodeParser


class CodebaseContextManager:
    def __init__(self):
        self.parser = CodeParser()
        self.contexts: Dict[str, CodebaseContext] = {}  # session_id -> context
        self.vector_stores: Dict[str, chromadb.Collection] = {}
        self._init_chromadb()

    def _init_chromadb(self):
        """Initialize ChromaDB for vector storage"""
        self.chroma_client = chromadb.Client(ChromaSettings(
            chroma_db_impl="duckdb+parquet",
            persist_directory="./.chromadb"
        ))

    def create_session(self, session_id: str) -> str:
        """Create a new context session"""
        self.contexts[session_id] = CodebaseContext(files=[])
        return session_id

    def add_files(self, session_id: str, files: List[FileUpload]) -> List[Dict]:
        """Add files to context and parse them"""
        if session_id not in self.contexts:
            self.create_session(session_id)

        context = self.contexts[session_id]
        results = []

        for file in files:
            # Auto-detect language if not provided
            if not file.language:
                file.language = self._detect_language(file.filename)

            # Parse file structure
            parsed = self.parser.parse_file(file.content, file.language.value)

            # Add to vector store for semantic search
            self._add_to_vector_store(session_id, file)

            context.files.append(file)

            results.append({
                'filename': file.filename,
                'language': file.language,
                'parsed': parsed,
                'size': len(file.content)
            })

        return results

    def _detect_language(self, filename: str) -> str:
        """Simple language detection by extension"""
        extensions = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.h': 'cpp',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            'kt': 'kotlin',
        }

        for ext, lang in extensions.items():
            if filename.endswith(ext):
                return lang
        return 'python'

    def _add_to_vector_store(self, session_id: str, file: FileUpload):
        """Add file content to vector database for semantic search"""
        try:
            collection_name = f"session_{session_id}"

            if collection_name not in self.vector_stores:
                self.vector_stores[collection_name] = self.chroma_client.create_collection(
                    name=collection_name,
                    metadata={"session_id": session_id}
                )

            collection = self.vector_stores[collection_name]

            # Split file into chunks for better search
            chunks = self._chunk_file(file.content, file.filename)

            for i, chunk in enumerate(chunks):
                chunk_id = f"{file.filename}_{i}"
                collection.add(
                    documents=[chunk['content']],
                    metadatas=[{
                        'filename': file.filename,
                        'chunk_index': i,
                        'language': file.language.value if file.language else 'unknown',
                        'path': file.path or file.filename
                    }],
                    ids=[chunk_id]
                )
        except Exception as e:
            print(f"Vector store error: {e}")
            # Continue without vector store

    def _chunk_file(self, content: str, filename: str, chunk_size: int = 1000) -> List[Dict]:
        """Split file into manageable chunks"""
        lines = content.split('\n')
        chunks = []
        current_chunk = []
        current_size = 0

        for line in lines:
            if current_size + len(line) > chunk_size and current_chunk:
                chunks.append({
                    'content': '\n'.join(current_chunk),
                    'line_start': len(chunks) * chunk_size
                })
                current_chunk = [line]
                current_size = len(line)
            else:
                current_chunk.append(line)
                current_size += len(line)

        if current_chunk:
            chunks.append({
                'content': '\n'.join(current_chunk),
                'line_start': len(chunks) * chunk_size
            })

        return chunks

    def get_relevant_context(self, session_id: str, query: str, top_k: int = 3) -> List[str]:
        """Get relevant code snippets for a query"""
        if session_id not in self.contexts or not self.contexts[session_id].files:
            return []

        context = []

        # Try vector search first
        try:
            collection_name = f"session_{session_id}"
            if collection_name in self.vector_stores:
                results = self.vector_stores[collection_name].query(
                    query_texts=[query],
                    n_results=top_k
                )

                for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
                    context.append(
                        f"File: {metadata['path']}\n"
                        f"```{metadata['language']}\n{doc}\n```"
                    )
        except:
            # Fallback: return first few files
            for file in self.contexts[session_id].files[:3]:
                preview = file.content[:500] + "..." if len(file.content) > 500 else file.content
                context.append(
                    f"File: {file.filename}\n"
                    f"```{file.language.value if file.language else 'text'}\n{preview}\n```"
                )

        return context

    def get_project_summary(self, session_id: str) -> Dict:
        """Generate a summary of the codebase"""
        if session_id not in self.contexts:
            return {}

        context = self.contexts[session_id]
        summary = {
            'file_count': len(context.files),
            'languages': {},
            'functions': 0,
            'classes': 0,
            'total_lines': 0
        }

        for file in context.files:
            lang = file.language.value if file.language else 'unknown'
            summary['languages'][lang] = summary['languages'].get(lang, 0) + 1

            # Parse for quick stats
            parsed = self.parser.parse_file(file.content, lang)
            summary['functions'] += len(parsed.get('functions', []))
            summary['classes'] += len(parsed.get('classes', []))
            summary['total_lines'] += parsed.get('line_count', 0)

        return summary