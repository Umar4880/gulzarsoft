import asyncio
import uuid
import logging
from typing import Optional
from dataclasses import dataclass
from typing import Any

from app.services.memory_service import MemoryService
from app.services.read_graph import GraphRunner


logger = logging.getLogger(__name__)

@dataclass(slots=True)
class ChatResult:
    conversation_id: uuid.UUID
    answer: str
    raw_state: dict[str, Any]
    approved: bool
    route_reason: str
    iteration_count: int


class ChatService:
    def __init__(
        self,
        graph_runner: Optional[GraphRunner] = None,
        memory_service: Optional[MemoryService] = None,
    ) -> None:
        self.graph_runner = graph_runner or GraphRunner()
        self.memory_service = memory_service or MemoryService()

    async def handle_message(
        self,
        user_id: str,
        user_query: str,
        conversation_id: Optional[uuid.UUID] = None,
    ) -> ChatResult:
        """
        Handle a chat message — unified for new and ongoing conversations.
        For new conversations, title generation runs CONCURRENTLY with agent.
        """
        
        # ─────────────────────────────────────────────────────────
        # Branch: Ongoing Conversation (sequential is fine)
        # ─────────────────────────────────────────────────────────
        print("======= in chat service ========")
        if conversation_id is not None:
            await self.memory_service.add_message(
                conversation_id=conversation_id,
                user_id=user_id,
                role="user",
                content=user_query,
            )
            
            state = await self.graph_runner.run(
                user_query=user_query,
                thread_id=str(conversation_id),
            )
            
            answer = self._extract_answer(state)
            await self.memory_service.add_message(
                conversation_id=conversation_id,
                user_id=user_id,
                role="ai",
                content=answer,
            )
            
            return ChatResult(
                conversation_id=conversation_id,
                answer=answer,
                raw_state=state,
                approved=bool(state.get("is_approved", False)),
                route_reason=str(state.get("route_reason", "")),
                iteration_count=int(state.get("iteration_count", 0) or 0),
            )
        
        # ─────────────────────────────────────────────────────────
        # Branch: New Conversation — TRUE CONCURRENCY
        # ─────────────────────────────────────────────────────────
        
        # Step 1: Create conversation immediately (fast DB operation)
        conv_id = await self._create_conversation_placeholder(
            user_id=user_id,
            user_query=user_query,
        )
        
        # Step 2: Run BOTH tasks CONCURRENTLY
        # Use asyncio.gather() to execute them at the same time
        title_task = self._generate_and_update_title(
            user_id=user_id,
            conversation_id=conv_id,
            query=user_query,
        )
        
        agent_task = self._run_agent_and_store_response(
            user_id=user_id,
            conversation_id=conv_id,
            user_query=user_query,
        )
        
        # Wait for BOTH to complete (but they run in parallel)
        # The total time = max(title_time, agent_time), not sum
        title, agent_result = await asyncio.gather(
            title_task,
            agent_task,
            return_exceptions=True  # Don't let title failure break agent
        )
        
        # If title generation failed, log it but continue
        if isinstance(title, Exception):
            logger.warning(
                "Title generation failed: %s", str(title)
            )
        
        # If agent failed, re-raise the exception
        if isinstance(agent_result, Exception):
            raise agent_result
        
        # Unpack agent result
        state, answer = agent_result
        
        return ChatResult(
            conversation_id=conv_id,
            answer=answer,
            raw_state=state,
            approved=bool(state.get("is_approved", False)),
            route_reason=str(state.get("route_reason", "")),
            iteration_count=int(state.get("iteration_count", 0) or 0),
        )

    # ─────────────────────────────────────────────────────────────
    # Concurrent Task Helpers
    # ─────────────────────────────────────────────────────────────
    
    async def _create_conversation_placeholder(
        self,
        user_id: str,
        user_query: str,
    ) -> uuid.UUID:
        """Create conversation with placeholder title (fast)."""
        conv, _ = await self.memory_service.start_conversation(
            user_id=user_id,
            first_message=user_query,
            title="..."  # placeholder
        )
        return conv.id

    async def _generate_and_update_title(
        self,
        user_id: str,
        conversation_id: uuid.UUID,
        query: str,
    ) -> str:
        """Generate title and update DB. Runs concurrently with agent."""
        title = await self.generate_title(query)
        await self.memory_service.update_title(
            user_id=user_id,
            conversation_id=conversation_id,
            title=title,
        )
        return title

    async def _run_agent_and_store_response(
        self,
        user_id: str,
        conversation_id: uuid.UUID,
        user_query: str,
    ) -> tuple[dict[str, Any], str]:
        """Run agent and store response. Runs concurrently with title."""
        # Run the agent
        state = await self.graph_runner.run(
            user_query=user_query,
            thread_id=str(conversation_id),
        )
        
        # Extract and store answer
        answer = self._extract_answer(state)
        await self.memory_service.add_message(
            conversation_id=conversation_id,
            user_id=user_id,
            role="ai",
            content=answer,
        )
        
        return state, answer

    async def generate_title(self, query: str) -> str:
        """Generate a short title from the first user query."""
        trimmed = " ".join(query.split())
        if not trimmed:
            return "New Chat"

        title = trimmed[:60].strip()
        if len(trimmed) > 60:
            title = f"{title.rstrip()}..."
        return title

    def _extract_answer(self, state: dict[str, Any]) -> str:
        if hasattr(state, "model_dump"):
            state = state.model_dump()

        if not isinstance(state, dict):
            return str(state)

        for key in ("report_draft", "draft_report", "final_answer", "answer"):
            value = state.get(key)
            if isinstance(value, str) and value.strip():
                return value

        messages = state.get("messages")
        if isinstance(messages, list) and messages:
            last = messages[-1]
            content = getattr(last, "content", None)
            if isinstance(content, str) and content.strip():
                return content

            if isinstance(last, dict):
                candidate = last.get("content")
                if isinstance(candidate, str) and candidate.strip():
                    return candidate

        return "I could not generate a final answer for this request."