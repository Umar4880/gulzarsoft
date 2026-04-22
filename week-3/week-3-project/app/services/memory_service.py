import uuid
import logging
from ..db.unit_of_work import UnitOfWork
from ..db.models import Conversation, Message

logger = logging.getLogger(__name__)


class MemoryService:

    def __init__(self):
        pass

    async def start_conversation(
        self,
        user_id: str,
        first_message: str,
        title: str,
    ) -> tuple[Conversation, Message]:

        async with UnitOfWork() as uow:
            conv = await uow.conversations.create(user_id=user_id, title=title)

            msg = await uow.messages.add_message(
                conversation_id=conv.id,
                user_id=user_id,
                role="user",
                content=first_message,
            )

            await uow.commit()

            return conv, msg

    async def add_message(
        self,
        conversation_id: uuid.UUID,
        user_id: str,
        role: str,
        content: str,
    ) -> Message:

        async with UnitOfWork() as uow:
            msg = await uow.messages.add_message(
                conversation_id=conversation_id,
                user_id=user_id,
                role=role,
                content=content,
            )
            await uow.commit()
            return msg

    async def get_history(
        self,
        conversation_id: uuid.UUID,
        user_id: str,
        limit: int = 20,
    ) -> list[Message]:

        async with UnitOfWork() as uow:
            return await uow.messages.get_history(
                conversation_id=conversation_id,
                user_id=user_id,
                limit=limit,
            )
        
    async def update_title(
        self,
        user_id: str,
        conversation_id: uuid.UUID,
        title: str,
    ) -> bool:
        async with UnitOfWork() as uow:
            updated = await uow.conversations.update_title(
                conversation_id=conversation_id,
                user_id=user_id,
                title=title,
            )
            if updated:
                await uow.commit()
            return updated