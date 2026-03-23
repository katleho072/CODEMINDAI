import tree_sitter
from tree_sitter import Language, Parser
from typing import Dict, List, Any
import os


class CodeParser:
    def __init__(self):
        self.parsers = {}
        self._load_languages()

    def _load_languages(self):
        # Initialize parsers for different languages
        try:
            # You'll need to build language libraries first
            # For now, we'll use a simple regex-based parser
            pass
        except:
            print("Tree-sitter languages not loaded, using fallback parser")

    def parse_file(self, content: str, language: str) -> Dict[str, Any]:
        """Extract structure from code file"""
        if language == "python":
            return self._parse_python(content)
        elif language in ["javascript", "typescript"]:
            return self._parse_javascript(content)
        else:
            return self._parse_generic(content)

    def _parse_python(self, content: str) -> Dict[str, Any]:
        """Simple Python parser (weekend version)"""
        imports = []
        functions = []
        classes = []

        lines = content.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()

            # Find imports
            if line.startswith(('import ', 'from ')):
                imports.append({
                    'line': i + 1,
                    'content': line,
                    'type': 'import'
                })

            # Find function definitions
            elif line.startswith('def '):
                func_name = line[4:].split('(')[0].strip()
                functions.append({
                    'name': func_name,
                    'line': i + 1,
                    'signature': line
                })

            # Find class definitions
            elif line.startswith('class '):
                class_name = line[6:].split('(')[0].split(':')[0].strip()
                classes.append({
                    'name': class_name,
                    'line': i + 1,
                    'signature': line
                })

        return {
            'imports': imports,
            'functions': functions,
            'classes': classes,
            'line_count': len(lines)
        }

    def _parse_javascript(self, content: str) -> Dict[str, Any]:
        """Simple JavaScript parser"""
        imports = []
        functions = []
        classes = []

        lines = content.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()

            # Find imports
            if line.startswith(('import ', 'require(', 'from ')):
                imports.append({
                    'line': i + 1,
                    'content': line,
                    'type': 'import'
                })

            # Find function definitions
            elif line.startswith('function ') or 'function(' in line:
                # Simple extraction
                if line.startswith('function '):
                    func_name = line[9:].split('(')[0].strip()
                else:
                    func_name = 'anonymous'
                functions.append({
                    'name': func_name,
                    'line': i + 1,
                    'signature': line[:100]  # First 100 chars
                })

            # Find arrow functions
            elif '=>' in line and ('const ' in line or 'let ' in line or 'var ' in line):
                func_name = line.split('=')[0].strip()
                functions.append({
                    'name': func_name,
                    'line': i + 1,
                    'signature': line[:100]
                })

            # Find class definitions
            elif line.startswith('class '):
                class_name = line[6:].split(' ')[0].split('{')[0].strip()
                classes.append({
                    'name': class_name,
                    'line': i + 1,
                    'signature': line
                })

        return {
            'imports': imports,
            'functions': functions,
            'classes': classes,
            'line_count': len(lines)
        }

    def _parse_generic(self, content: str) -> Dict[str, Any]:
        """Generic parser for other languages"""
        return {
            'line_count': len(content.split('\n')),
            'char_count': len(content)
        }