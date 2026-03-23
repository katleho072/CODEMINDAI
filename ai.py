from openai import AsyncOpenAI
from typing import List, Optional, Dict, Any
import json

from backend.app.core.config import settings
from backend.app.models.schemas import CodingRequest, ChatMessage, CodingResponse


class AIService:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL
        )

    async def generate_code_response(
            self,
            request: CodingRequest,
            context_snippets: List[str],
            conversation_history: List[ChatMessage] = None
    ) -> CodingResponse:
        """Generate a context-aware coding response"""

        # Build system prompt with context
        system_prompt = self._build_system_prompt(request, context_snippets)

        # Build conversation
        messages = [
            {"role": "system", "content": system_prompt}
        ]

        # Add conversation history if available
        if conversation_history:
            for msg in conversation_history[-6:]:  # Last 3 exchanges
                messages.append({"role": msg.role.value, "content": msg.content})

        # Add current request
        messages.append({"role": "user", "content": request.message})

        try:
            response = await self.client.chat.completions.create(
                model=settings.DEEPSEEK_MODEL,
                messages=messages,
                temperature=0.2,  # Lower temp for code generation
                max_tokens=2000,
                stream=False
            )

            content = response.choices[0].message.content

            # Parse the response for code blocks
            code_suggestions = self._extract_code_blocks(content)

            return CodingResponse(
                message=content,
                code_suggestions=code_suggestions,
                context_used=context_snippets[:2]  # Which snippets were used
            )

        except Exception as e:
            return CodingResponse(
                message=f"Error: {str(e)}",
                code_suggestions=[],
                explanation="Failed to generate response"
            )

    def _build_system_prompt(self, request: CodingRequest, context_snippets: List[str]) -> str:
        """Build a powerful system prompt with project context"""

        context_str = ""
        if context_snippets:
            context_str = "\n\n## PROJECT CONTEXT\n"
            for i, snippet in enumerate(context_snippets[:3]):  # Max 3 snippets
                context_str += f"\n--- Context {i + 1} ---\n{snippet}\n"

        language = request.language.value

        return f"""You are an expert {language} developer working directly on the user's codebase.

{context_str}

## YOUR ROLE
You are not just answering questions - you are an active participant in development:
1. UNDERSTAND the existing codebase structure and patterns
2. SUGGEST code that fits seamlessly with existing code
3. EXPLAIN why your suggestion works in this specific context
4. ANTICIPATE edge cases and provide robust solutions
5. When appropriate, show BOTH the code and how to integrate it

## RESPONSE FORMAT
1. Start with a brief understanding of the context
2. Provide code in Markdown code blocks with language specified
3. Explain key decisions and how it integrates with existing code
4. Mention any trade-offs or considerations

## IMPORTANT
- Reference specific files/functions from the context when relevant
- Match the existing code style and patterns
- Consider performance, security, and maintainability
- If suggesting refactoring, show before/after when helpful

Current task: {request.message}"""

    def _extract_code_blocks(self, content: str) -> List[str]:
        """Extract code blocks from markdown response"""
        import re
        code_blocks = re.findall(r'```(?:\w+)?\n(.*?)\n```', content, re.DOTALL)
        return [block.strip() for block in code_blocks if block.strip()]

    async def explain_code(self, code: str, language: str) -> str:
        """Generate explanation for given code"""
        response = await self.client.chat.completions.create(
            model=settings.DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": f"You are a senior {language} engineer explaining code to a colleague."},
                {"role": "user",
                 "content": f"Explain this {language} code:\n\n```{language}\n{code}\n```\n\nFocus on:\n1. What it does\n2. Key algorithms/patterns\n3. Potential issues\n4. How to improve it"}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        return response.choices[0].message.content