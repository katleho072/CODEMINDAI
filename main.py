import os
import sys
import tempfile
import subprocess
from datetime import datetime
from typing import List, Optional, Dict, Any, Generator
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
import uvicorn

# Import our AI service
from backend_new. ai_service import ai_service



# Load environment variables
load_dotenv()

# In-memory storage (for development)
sessions = {}
code_analytics = {}


# ====================== LIFESPAN HANDLER ======================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler"""
    # Startup
    print("\n" + "=" * 60)
    print("🚀 DevMate AI Backend Server")
    print("=" * 60)
    print(f"📡 Server URL: http://localhost:8000")
    print(f"📚 API Docs: http://localhost:8000/docs")
    print(f"📖 ReDoc: http://localhost:8000/redoc")
    print("=" * 60)

    # AI Status
    status = ai_service.get_status()
    print(f"🤖 AI Provider: {status['provider'] or 'None (Mock Mode)'}")
    print(f"🔑 API Key: {'✅ Set and Valid' if status['enabled'] else '❌ Not configured'}")
    if status['enabled']:
        print(f"📦 Model: {status['model']}")
    print("=" * 60)

    # Create demo session
    sessions['demo'] = {
        'id': 'demo',
        'created_at': datetime.now().isoformat(),
        'files': [
            {
                'name': 'example.py',
                'language': 'python',
                'content': '''def hello_world():
    """A simple hello world function"""
    print("Hello from DevMate AI!")
    return "Hello, World!"

class Calculator:
    """Simple calculator class"""

    def add(self, a, b):
        """Add two numbers"""
        return a + b

    def multiply(self, a, b):
        """Multiply two numbers"""
        return a * b

    def factorial(self, n):
        """Calculate factorial recursively"""
        if n == 0:
            return 1
        return n * self.factorial(n-1)

# Usage example
if __name__ == "__main__":
    calc = Calculator()
    print(calc.add(5, 3))
    print(calc.factorial(5))''',
                'size': 450,
                'parsed': {
                    'imports': [],
                    'functions': [
                        {'name': 'hello_world', 'line': 1, 'signature': 'def hello_world():'},
                        {'name': 'add', 'line': 9, 'signature': 'def add(self, a, b):'},
                        {'name': 'multiply', 'line': 13, 'signature': 'def multiply(self, a, b):'},
                        {'name': 'factorial', 'line': 17, 'signature': 'def factorial(self, n):'}
                    ],
                    'classes': [
                        {'name': 'Calculator', 'line': 6, 'signature': 'class Calculator:'}
                    ],
                    'line_count': 28
                }
            }
        ]
    }

    # Initialize analytics
    code_analytics['demo'] = {
        'complexity': 2,
        'issues': [],
        'suggestions': ['Consider adding type hints', 'Add docstrings to all functions']
    }

    print("✅ Demo session created")
    print("=" * 60 + "\n")

    yield  # App runs here

    # Shutdown
    print("\n" + "=" * 60)
    print("👋 DevMate AI Server Shutting Down")
    print("=" * 60 + "\n")


# Initialize FastAPI app
app = FastAPI(
    title="DevMate AI",
    version="2.0.0",
    description="Your Intelligent Coding Assistant powered by DeepSeek AI",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ====================== UTILITY FUNCTIONS ======================

def detect_language(filename: str) -> str:
    """Detect programming language from filename extension"""
    extensions = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'javascript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.cpp': 'cpp',
        '.cc': 'cpp',
        '.cxx': 'cpp',
        '.h': 'c',
        '.hpp': 'cpp',
        '.c': 'c',
        '.go': 'go',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.kt': 'kotlin',
        '.kts': 'kotlin',
        '.swift': 'swift',
        '.php': 'php',
        '.html': 'html',
        '.htm': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.sass': 'sass',
        '.sql': 'sql',
        '.sh': 'bash',
        '.bash': 'bash',
        '.json': 'json',
        '.xml': 'xml',
        '.yml': 'yaml',
        '.yaml': 'yaml',
        '.md': 'markdown',
        '.txt': 'text',
        '.r': 'r',
        '.m': 'matlab',
        '.scala': 'scala',
        '.dart': 'dart',
        '.lua': 'lua',
        '.pl': 'perl',
        '.vim': 'vim'
    }

    filename_lower = filename.lower()
    for ext, lang in extensions.items():
        if filename_lower.endswith(ext):
            return lang
    return 'text'


def parse_code_simple(content: str, language: str) -> Dict[str, Any]:
    """Simple code parser without external dependencies"""
    lines = content.split('\n')
    non_empty_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]

    if language == 'python':
        imports = [l.strip() for l in lines if l.strip().startswith(('import ', 'from '))]
        functions = []
        classes = []

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('def '):
                func_name = stripped[4:].split('(')[0].strip()
                functions.append({
                    'name': func_name,
                    'line': i + 1,
                    'signature': stripped
                })
            elif stripped.startswith('class '):
                class_name = stripped[6:].split('(')[0].split(':')[0].strip()
                classes.append({
                    'name': class_name,
                    'line': i + 1,
                    'signature': stripped
                })

    elif language in ['javascript', 'typescript']:
        imports = [l.strip() for l in lines if 'import ' in l or 'require(' in l]
        functions = []
        classes = []

        for i, line in enumerate(lines):
            stripped = line.strip()
            if 'function ' in stripped:
                try:
                    func_name = stripped.split('function ')[1].split('(')[0].strip()
                    functions.append({
                        'name': func_name,
                        'line': i + 1,
                        'signature': stripped
                    })
                except:
                    pass
            if 'class ' in stripped:
                try:
                    class_name = stripped.split('class ')[1].split(' ')[0].split('{')[0].strip()
                    classes.append({
                        'name': class_name,
                        'line': i + 1,
                        'signature': stripped
                    })
                except:
                    pass
    else:
        imports = []
        functions = []
        classes = []

    return {
        'imports': imports,
        'functions': functions,
        'classes': classes,
        'line_count': len(lines),
        'non_empty_lines': len(non_empty_lines),
        'char_count': len(content),
        'comment_count': len([l for l in lines if l.strip().startswith(('#', '//', '/*', '*'))])
    }


def calculate_complexity(content: str, language: str = 'python') -> int:
    """Calculate simple code complexity score"""
    lines = content.split('\n')
    complexity = 0

    # Keywords that add complexity
    complexity_keywords = {
        'python': ['if ', 'elif ', 'for ', 'while ', 'def ', 'class ', 'try:', 'except ', 'with ', 'lambda'],
        'javascript': ['if ', 'else ', 'for ', 'while ', 'function ', 'class ', 'try', 'catch', '=>'],
        'java': ['if ', 'else ', 'for ', 'while ', 'switch', 'case', 'try', 'catch'],
        'cpp': ['if ', 'else ', 'for ', 'while ', 'switch', 'case', 'try', 'catch']
    }

    keywords = complexity_keywords.get(language, complexity_keywords['python'])

    for line in lines:
        line_lower = line.lower().strip()
        for keyword in keywords:
            if keyword in line_lower:
                complexity += 1

        # Logical operators add complexity
        complexity += line_lower.count(' and ')
        complexity += line_lower.count(' or ')
        complexity += line_lower.count('&&')
        complexity += line_lower.count('||')

    # Normalize to 1-10 scale
    return max(1, min(10, complexity // 3))


# ====================== API ENDPOINTS ======================

@app.get("/")
async def root():
    """Root endpoint with API information"""
    ai_status = ai_service.get_status()

    return {
        "app": "DevMate AI",
        "version": "2.0.0",
        "status": "running",
        "ai": {
            "enabled": ai_status['enabled'],
            "provider": ai_status['provider'],
            "model": ai_status['model']
        },
        "features": [
            "💬 Code Chat with Context",
            "📁 File Upload & Analysis",
            "▶️ Code Execution (Python)",
            "🔍 Code Review & Quality Analysis",
            "📝 Documentation Generation",
            "🧪 Test Generation",
            "♻️ Code Refactoring",
            "⚡ Performance Optimization",
            "🔄 Language Conversion"
        ],
        "endpoints": {
            "health": "GET /health",
            "upload": "POST /api/upload",
            "chat": "POST /api/chat",
            "execute": "POST /api/execute",
            "analyze": "POST /api/analyze",
            "review": "POST /api/review",
            "document": "POST /api/document",
            "tests": "POST /api/tests",
            "refactor": "POST /api/refactor",
            "optimize": "POST /api/optimize",
            "convert": "POST /api/convert",
            "sessions": "GET /api/sessions",
            "ai_status": "GET /api/ai/status"
        },
        "documentation": {
            "swagger": "GET /docs",
            "redoc": "GET /redoc"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    ai_status = ai_service.get_status()

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "ai_enabled": ai_status['enabled'],
        "ai_provider": ai_status['provider'],
        "sessions_count": len(sessions),
        "uptime": "running",
        "features_available": [
            "chat",
            "upload",
            "execute",
            "analyze",
            "review",
            "document",
            "tests",
            "refactor",
            "optimize"
        ]
    }


@app.get("/api/ai/status")
async def ai_status():
    """Get detailed AI service status"""
    status = ai_service.get_status()
    return {
        "ai_service": status,
        "recommendations": [
            "DeepSeek API provides excellent code generation" if status[
                'enabled'] else "Enable DeepSeek AI for intelligent code assistance",
            "Visit https://platform.deepseek.com/ to get started" if not status[
                'enabled'] else "AI is ready to help with your coding tasks"
        ]
    }


@app.post("/api/upload")
async def upload_files(
        files: List[UploadFile] = File(...),
        session_id: Optional[str] = Form("default")
):
    """
    Upload code files for analysis

    - **files**: One or more code files
    - **session_id**: Session identifier (optional)
    """

    if session_id not in sessions:
        sessions[session_id] = {
            'id': session_id,
            'created_at': datetime.now().isoformat(),
            'files': []
        }

    uploaded = []
    total_lines = 0
    total_complexity = 0

    for file in files:
        try:
            # Read file content
            content_bytes = await file.read()
            content = content_bytes.decode('utf-8')
            filename = file.filename
            language = detect_language(filename)

            # Parse code
            parsed = parse_code_simple(content, language)

            # Calculate complexity
            complexity = calculate_complexity(content, language)
            total_complexity += complexity
            total_lines += parsed['line_count']

            # Store file data
            file_data = {
                'name': filename,
                'language': language,
                'content': content,
                'size': len(content),
                'parsed': parsed,
                'complexity': complexity,
                'uploaded_at': datetime.now().isoformat()
            }

            sessions[session_id]['files'].append(file_data)

            uploaded.append({
                'filename': filename,
                'language': language,
                'size': len(content),
                'lines': parsed['line_count'],
                'functions': len(parsed['functions']),
                'classes': len(parsed['classes']),
                'complexity': complexity,
                'success': True
            })

        except Exception as e:
            uploaded.append({
                'filename': file.filename,
                'error': str(e),
                'success': False
            })

    return {
        'success': True,
        'session_id': session_id,
        'uploaded': uploaded,
        'summary': {
            'total_files': len(sessions[session_id]['files']),
            'total_lines': total_lines,
            'total_complexity': total_complexity,
            'languages': list(set(f['language'] for f in sessions[session_id]['files']))
        }
    }


@app.post("/api/chat")
async def chat(
        message: str = Form(...),
        session_id: Optional[str] = Form("default"),
        language: str = Form("python"),
        include_context: bool = Form(True)
):
    """
    Chat with AI coding assistant

    - **message**: Your question or code request
    - **session_id**: Session ID for context (optional)
    - **language**: Programming language (default: python)
    - **include_context**: Include session files as context
    """

    # Build context from session files
    context = ""
    if include_context and session_id in sessions:
        session_files = sessions[session_id]['files']
        if session_files:
            context = f"## Project Context ({len(session_files)} files)\n\n"
            for file in session_files[:3]:  # Include first 3 files
                preview_length = 300
                preview = file['content'][:preview_length]
                if len(file['content']) > preview_length:
                    preview += "...\n[truncated]"

                context += f"### File: {file['name']} ({file['language']})\n"
                context += f"```{file['language']}\n{preview}\n```\n\n"

    # Generate AI response
    response = await ai_service.generate_response(message, context, language)

    return {
        'response': response,
        'session_id': session_id,
        'ai_enabled': ai_service.has_ai,
        'has_context': bool(context),
        'language': language,
        'timestamp': datetime.now().isoformat()
    }


@app.post("/api/execute")
async def execute_code(
        code: str = Form(...),
        language: str = Form("python"),
        timeout: int = Form(10)
):
    """
    Execute code in a safe environment

    - **code**: Code to execute
    - **language**: Programming language (currently only Python supported)
    - **timeout**: Execution timeout in seconds
    """

    if language != 'python':
        raise HTTPException(
            status_code=400,
            detail=f"Code execution currently only supports Python. Requested: {language}"
        )

    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            # Execute with timeout
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=timeout
            )

            return {
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode,
                'success': result.returncode == 0,
                'execution_time': f"< {timeout}s"
            }

        except subprocess.TimeoutExpired:
            return {
                'stdout': '',
                'stderr': f'⏱️ Execution timed out after {timeout} seconds',
                'returncode': -1,
                'success': False,
                'execution_time': f'{timeout}s (timeout)'
            }
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file)
            except:
                pass

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")


@app.post("/api/analyze")
async def analyze_code(
        session_id: str = Form(...),
        file_index: int = Form(0),
        ai_analysis: bool = Form(True)
):
    """
    Analyze code for complexity, issues, and suggestions

    - **session_id**: Session identifier
    - **file_index**: Index of file to analyze
    - **ai_analysis**: Include AI-powered analysis
    """

    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    if not session['files']:
        raise HTTPException(status_code=400, detail="No files in session")

    if file_index >= len(session['files']):
        raise HTTPException(status_code=400,
                            detail=f"File index {file_index} out of range (max: {len(session['files']) - 1})")

    file_data = session['files'][file_index]
    content = file_data['content']
    language = file_data['language']
    parsed = file_data['parsed']

    # Basic analysis
    analysis = {
        'filename': file_data['name'],
        'language': language,
        'size': len(content),
        'lines': {
            'total': parsed['line_count'],
            'non_empty': parsed['non_empty_lines'],
            'comments': parsed['comment_count']
        },
        'complexity': file_data.get('complexity', 1),
        'structure': {
            'functions': len(parsed['functions']),
            'classes': len(parsed['classes']),
            'imports': len(parsed['imports'])
        },
        'issues': [],
        'suggestions': [],
        'metrics': {}
    }

    # Code quality checks
    lines = content.split('\n')

    # Check for long lines
    long_lines = [i + 1 for i, line in enumerate(lines) if len(line) > 100]
    if long_lines:
        analysis['issues'].append({
            'type': 'style',
            'severity': 'low',
            'message': f'Found {len(long_lines)} lines longer than 100 characters',
            'lines': long_lines[:5],  # Show first 5
            'suggestion': 'Break long lines for better readability'
        })

    # Check for TODO/FIXME
    todos = []
    for i, line in enumerate(lines):
        if any(marker in line.upper() for marker in ['TODO', 'FIXME', 'HACK', 'XXX']):
            todos.append({'line': i + 1, 'content': line.strip()})

    if todos:
        analysis['issues'].append({
            'type': 'todo',
            'severity': 'info',
            'message': f'Found {len(todos)} TODO/FIXME comments',
            'details': todos[:3]  # Show first 3
        })

    # Calculate metrics
    analysis['metrics'] = {
        'comment_ratio': round(parsed['comment_count'] / max(1, parsed['line_count']), 2),
        'code_ratio': round(parsed['non_empty_lines'] / max(1, parsed['line_count']), 2),
        'avg_line_length': round(len(content) / max(1, parsed['line_count']), 1),
        'function_density': round(len(parsed['functions']) / max(1, parsed['line_count'] / 50), 2)
    }

    # AI analysis if enabled and requested
    if ai_analysis and ai_service.has_ai and len(content) < 2000:
        try:
            ai_prompt = f"""Analyze this {language} code and provide:
1. Top 2-3 potential issues or bugs
2. Top 2-3 improvement suggestions
3. Security concerns (if any)
4. Performance considerations

Code:
```{language}
{content[:1500]}
```

Format your response clearly with sections."""

            ai_response = await ai_service.generate_response(ai_prompt, "", language)
            analysis['ai_insights'] = ai_response

        except Exception as e:
            analysis['ai_insights'] = f"AI analysis unavailable: {str(e)}"

    # Store analysis
    if session_id not in code_analytics:
        code_analytics[session_id] = {}
    code_analytics[session_id][file_data['name']] = analysis

    return analysis


@app.post("/api/review")
async def code_review(
        code: str = Form(...),
        language: str = Form("python"),
        focus: str = Form("all")
):
    """
    Comprehensive code review

    - **code**: Code to review
    - **language**: Programming language
    - **focus**: Review focus (all, security, performance, style)
    """

    if not ai_service.has_ai:
        return {
            'review': "⚠️ AI not enabled. Please configure DeepSeek API for code reviews.",
            'rating': 'N/A',
            'suggestions': ["Enable AI for detailed code reviews"]
        }

    try:
        focus_descriptions = {
            'all': 'comprehensive review covering all aspects',
            'security': 'security vulnerabilities and best practices',
            'performance': 'performance optimization opportunities',
            'style': 'code style and readability'
        }

        prompt = f"""Perform a {focus_descriptions.get(focus, 'comprehensive')} code review for this {language} code.

Code to review:
```{language}
{code}
```

Provide a structured review with:
1. **Overall Assessment**: Brief summary and rating (Excellent/Good/Fair/Needs Improvement)
2. **Strengths**: What's done well (2-3 points)
3. **Issues Found**: Critical problems (if any)
4. **Suggestions**: Specific improvements (3-5 actionable items)
5. **Best Practices**: Recommendations for this type of code

Be professional, constructive, and specific."""

        review = await ai_service.generate_response(prompt, "", language)

        return {
            'review': review,
            'language': language,
            'focus': focus,
            'code_length': len(code),
            'lines': len(code.split('\n')),
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Review failed: {str(e)}")


@app.post("/api/document")
async def generate_documentation(
        code: str = Form(...),
        language: str = Form("python"),
        style: str = Form("detailed")
):
    """
    Generate code documentation

    - **code**: Code to document
    - **language**: Programming language
    - **style**: Documentation style (brief, detailed, api)
    """

    if not ai_service.has_ai:
        return {
            'documentation': f"# Documentation\n\n⚠️ AI not enabled\n\nCode: {len(code)} characters\nLanguage: {language}",
            'style': style
        }

    try:
        style_instructions = {
            'brief': 'concise documentation with key points',
            'detailed': 'comprehensive documentation with examples',
            'api': 'API reference style documentation'
        }

        prompt = f"""Generate {style_instructions.get(style, 'detailed')} documentation for this {language} code.

Code:
```{language}
{code}
```

Include:
1. **Overview**: What this code does
2. **Components**: Document all functions/classes/methods
3. **Parameters**: Input parameters and types
4. **Returns**: Return values and types
5. **Examples**: Usage examples
6. **Notes**: Important considerations or edge cases

Format in clean Markdown."""

        documentation = await ai_service.generate_response(prompt, "", language)

        return {
            'documentation': documentation,
            'language': language,
            'style': style,
            'generated_at': datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Documentation generation failed: {str(e)}")


@app.post("/api/tests")
async def generate_tests(
        code: str = Form(...),
        language: str = Form("python"),
        framework: str = Form("pytest")
):
    """
    Generate test cases

    - **code**: Code to test
    - **language**: Programming language
    - **framework**: Testing framework (pytest, unittest, jest, etc.)
    """

    if not ai_service.has_ai:
        return {
            'tests': f"# Test Cases\n\n⚠️ AI not enabled\n\nFramework: {framework}\nLanguage: {language}",
            'framework': framework
        }

    try:
        prompt = f"""Generate comprehensive {framework} test cases for this {language} code.

Code to test:
```{language}
{code}
```

Create tests including:
1. **Unit tests** for all functions/methods
2. **Edge cases** (empty inputs, boundaries, etc.)
3. **Error cases** (invalid inputs, exceptions)
4. **Happy path** tests
5. **Setup/teardown** if needed

Make tests clear, well-documented, and runnable."""

        tests = await ai_service.generate_response(prompt, "", language)

        return {
            'tests': tests,
            'language': language,
            'framework': framework,
            'generated_at': datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test generation failed: {str(e)}")


@app.post("/api/refactor")
async def refactor_code(
        code: str = Form(...),
        language: str = Form("python"),
        goal: str = Form("readability")
):
    """
    Refactor code

    - **code**: Code to refactor
    - **language**: Programming language
    - **goal**: Refactoring goal (readability, performance, maintainability)
    """

    if not ai_service.has_ai:
        return {
            'original': code,
            'refactored': f"# Refactored Code\n\n⚠️ AI not enabled\n\nGoal: {goal}",
            'changes': []
        }

    try:
        goal_descriptions = {
            'readability': 'improve code readability and clarity',
            'performance': 'optimize for better performance',
            'maintainability': 'enhance maintainability and structure'
        }

        prompt = f"""Refactor this {language} code to {goal_descriptions.get(goal, 'improve it')}.

Original code:
```{language}
{code}
```

Provide:
1. **Refactored code**: Clean, improved version
2. **Changes made**: List of specific changes
3. **Explanation**: Why each change improves the code
4. **Trade-offs**: Any considerations or compromises

Maintain the same functionality."""

        response = await ai_service.generate_response(prompt, "", language)

        return {
            'original': code,
            'refactored': response,
            'goal': goal,
            'language': language,
            'generated_at': datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Refactoring failed: {str(e)}")


@app.post("/api/optimize")
async def optimize_code(
        code: str = Form(...),
        language: str = Form("python"),
        metric: str = Form("performance")
):
    """
    Optimize code

    - **code**: Code to optimize
    - **language**: Programming language
    - **metric**: Optimization target (performance, memory, both)
    """

    if not ai_service.has_ai:
        return {
            'original': code,
            'optimized': f"# Optimized Code\n\n⚠️ AI not enabled\n\nMetric: {metric}",
            'improvements': []
        }

    try:
        prompt = f"""Optimize this {language} code for {metric}.

Code to optimize:
```{language}
{code}
```

Provide:
1. **Optimized code**: Performance-improved version
2. **Optimizations applied**: Specific techniques used
3. **Expected improvements**: Estimated performance gains
4. **Benchmarking**: How to measure improvements
5. **Trade-offs**: Any downsides or compromises

Focus on practical, production-ready optimizations."""

        response = await ai_service.generate_response(prompt, "", language)

        return {
            'original': code,
            'optimized': response,
            'metric': metric,
            'language': language,
            'generated_at': datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@app.post("/api/convert")
async def convert_code(
        code: str = Form(...),
        from_language: str = Form("python"),
        to_language: str = Form("javascript")
):
    """
    Convert code between languages

    - **code**: Code to convert
    - **from_language**: Source language
    - **to_language**: Target language
    """

    if not ai_service.has_ai:
        return {
            'original': code,
            'converted': f"# Converted Code\n\n⚠️ AI not enabled\n\nFrom: {from_language} to {to_language}",
            'notes': []
        }

    try:
        prompt = f"""Convert this {from_language} code to {to_language}.

Original {from_language} code:
```{from_language}
{code}
```

Provide:
1. **Converted code**: Equivalent {to_language} code
2. **Explanation**: Key differences in approach
3. **Idioms**: Language-specific best practices applied
4. **Limitations**: Any features that don't translate directly
5. **Testing notes**: How to verify the conversion

Maintain the same functionality and logic."""

        converted = await ai_service.generate_response(prompt, "", from_language)

        return {
            'original': code,
            'converted': converted,
            'from_language': from_language,
            'to_language': to_language,
            'generated_at': datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")


@app.get("/api/sessions")
async def get_sessions():
    """List all sessions"""
    result = []
    for session_id, data in sessions.items():
        files = data['files']

        result.append({
            'id': session_id,
            'created_at': data['created_at'],
            'file_count': len(files),
            'languages': list(set(f['language'] for f in files)),
            'total_lines': sum(f['parsed']['line_count'] for f in files),
            'total_complexity': sum(f.get('complexity', 0) for f in files),
            'functions': sum(len(f['parsed']['functions']) for f in files),
            'classes': sum(len(f['parsed']['classes']) for f in files)
        })

    return {'sessions': result, 'count': len(result)}


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get detailed session information"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    session = sessions[session_id]

    return {
        'session_id': session_id,
        'created_at': session['created_at'],
        'files': [
            {
                'name': f['name'],
                'language': f['language'],
                'size': f['size'],
                'lines': f['parsed']['line_count'],
                'complexity': f.get('complexity', 1),
                'functions': len(f['parsed']['functions']),
                'classes': len(f['parsed']['classes']),
                'uploaded_at': f.get('uploaded_at', 'N/A')
            }
            for f in session['files']
        ],
        'summary': {
            'total_files': len(session['files']),
            'total_lines': sum(f['parsed']['line_count'] for f in session['files']),
            'languages': list(set(f['language'] for f in session['files']))
        }
    }


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    if session_id == 'demo':
        raise HTTPException(status_code=400, detail="Cannot delete demo session")

    del sessions[session_id]
    if session_id in code_analytics:
        del code_analytics[session_id]

    return {'message': f"Session '{session_id}' deleted successfully"}


@app.get("/api/analytics/{session_id}")
async def get_analytics(session_id: str):
    """Get code analytics for a session"""
    if session_id not in code_analytics:
        raise HTTPException(status_code=404, detail=f"No analytics found for session '{session_id}'")

    return {
        'session_id': session_id,
        'analytics': code_analytics[session_id],
        'generated_at': datetime.now().isoformat()
    }


# ====================== MAIN ======================

if __name__ == "__main__":
    # Check if .env exists, create if not
    if not os.path.exists(".env"):
        print("\n📝 Creating .env file...")
        with open(".env", "w") as f:
            f.write("""# DevMate AI Configuration
# Get your API key from: https://platform.deepseek.com/

DEEPSEEK_API_KEY=your_key_here

# Optional: Enable debug mode
DEBUG=True
""")
        print("✅ Created .env file")
        print("⚠️  Please add your DeepSeek API key to the .env file")
        print("   Get one at: https://platform.deepseek.com/")
        print()

    # Run server
    print("Starting server...\n")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )