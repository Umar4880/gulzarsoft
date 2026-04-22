from fastapi import APIRouter, HTTPException

from app.models.requests.chat_request import ChatRequest
from app.services.service_factory import build_chat_service


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
async def chat(request: ChatRequest) -> dict:
	service = build_chat_service()

	try:
		result = await service.handle_message(
			user_id=request.user_id,
			user_query=request.query,
			conversation_id=request.conversation_id,
		)
	except Exception as exc:
		raise HTTPException(status_code=500, detail=str(exc)) from exc

	return {
		"conversation_id": str(result.conversation_id),
		"answer": result.answer,
		"approved": result.approved,
		"route_reason": result.route_reason,
		"iteration_count": result.iteration_count,
		"raw_state": result.raw_state,
	}

