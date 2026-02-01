import json
from typing import Callable, Iterator

from fastapi import APIRouter, Depends, FastAPI
from starlette.responses import StreamingResponse

from app.api.routes.auth import require_current_user
from app.api.routes.feature_gate import require_feature
from app.api.schemas import ChatMessageRequest
from app.core.dependencies import InternalDependencies
from app.domain.models.user import User
from app.services.subscription import Feature


def register_chat_routes(
    app: FastAPI,
    provide_dependencies: Callable[[], Iterator[InternalDependencies]],
):
    router = APIRouter(prefix="/chat", tags=["chat"])

    @router.post("/message")
    async def send_message(
        request: ChatMessageRequest,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        require_feature(internal.subscription_service, current_user.id, Feature.AI_INSIGHTS)
        internal.subscription_service.increment_ai_usage(current_user.id)

        history = [{"role": msg.role, "content": msg.content} for msg in request.history]

        async def generate():
            try:
                async for chunk in internal.chat_service.process_message(
                    user_id=current_user.id,
                    message=request.message,
                    history=history,
                ):
                    yield f"data: {json.dumps(chunk)}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    app.include_router(router, prefix="/api/v1")
