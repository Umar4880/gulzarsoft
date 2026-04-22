import uuid
import logging

from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.db.repositories.base import BaseRepository
from app.db.models import Conversation, Message

logger = logging.getLogger(__name__)

class MessageRepository(BaseRepository):

    async def add_message(self, 
        conversation_id: uuid.UUID, 
        user_id: str, role: str, 
        content: str) -> Message:

        try:
            eligible_user = await self._s.execute(
                select(Conversation.id).where(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user_id
                )
            )

            if not eligible_user.scalar_one_or_none():
                logger.error("MessageRepository | converation not found | user_id=%s | conversation_id=%s", user_id, conversation_id)
                return PermissionError(f"Conversation_id {conversation_id} not found or does not belong to the user {user_id}")

            msg = Message(
                conversation_id = conversation_id, 
                role = role, 
                content = content
                )
            
            self._s.add(msg)
            await self._s.flush()

            logger.debug(
                "MessageRepository | saved | role=%s | conversation_id=%s | tokens_in=%s | tokens_out=%s",
                role,
                conversation_id,

            )
            return msg

        except PermissionError:
            raise
    
    async def get_history(
        self,
        conversation_id: uuid.UUID,
        user_id: str,                   
        limit: int = 20,             
    ) -> list[Message]:
        
        try:
            # Verify ownership first
            conv_check = await self._session.execute(
                select(Conversation.id).where(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user_id,
                )
            )
            if not conv_check.scalar_one_or_none():
                raise PermissionError(
                    f"Conversation {conversation_id} not found or does not belong to user {user_id}"
                )

            subq = (
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.desc())
                .limit(limit)
                .subquery()
            )

            result = await self._session.execute(
                select(Message)
                .select_from(subq)
                .order_by(subq.c.created_at.asc())
            )
            return list(result.scalars().all())

        except PermissionError:
            raise

        except SQLAlchemyError:
            logger.exception(
                "MessageRepository | get_history failed | conversation_id=%s",
                conversation_id,
            )
            raise


