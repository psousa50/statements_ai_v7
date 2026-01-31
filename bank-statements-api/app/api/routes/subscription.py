from typing import Callable, Iterator

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Request, status

from app.api.routes.auth import require_current_user
from app.api.schemas import (
    CheckoutRequest,
    CheckoutResponse,
    FeatureAccessResponse,
    PortalResponse,
    SubscriptionLimitsResponse,
    SubscriptionResponse,
    SubscriptionUsageResponse,
)
from app.core.config import settings
from app.core.dependencies import InternalDependencies
from app.domain.models.subscription import SubscriptionTier
from app.domain.models.user import User
from app.logging.utils import log_exception
from app.services.subscription import Feature


def register_subscription_routes(
    app: FastAPI,
    provide_dependencies: Callable[[], Iterator[InternalDependencies]],
):
    router = APIRouter(prefix="/subscription", tags=["subscription"])

    @router.get("", response_model=SubscriptionResponse)
    async def get_subscription(
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        try:
            internal.subscription_service.sync_from_stripe(current_user.id)
            info = internal.subscription_service.get_subscription_info(current_user.id)

            return SubscriptionResponse(
                tier=info.tier,
                status=info.status,
                is_active=info.is_active,
                limits=SubscriptionLimitsResponse(
                    statements_per_month=info.limits.get("statements_per_month"),
                    statements_total=info.limits.get("statements_total"),
                    ai_categorisation=info.limits.get("ai_categorisation", False),
                    ai_rules=info.limits.get("ai_rules", False),
                    ai_patterns=info.limits.get("ai_patterns", False),
                    ai_insights=info.limits.get("ai_insights", False),
                ),
                usage=SubscriptionUsageResponse(
                    statements_this_month=info.usage.get("statements_this_month", 0),
                    statements_total=info.usage.get("statements_total", 0),
                    ai_calls_this_month=info.usage.get("ai_calls_this_month", 0),
                    ai_calls_total=info.usage.get("ai_calls_total", 0),
                ),
                current_period_end=info.current_period_end,
                cancel_at_period_end=info.cancel_at_period_end,
            )
        except Exception as e:
            log_exception("Error getting subscription: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error getting subscription: {str(e)}",
            )

    @router.get("/check/{feature}", response_model=FeatureAccessResponse)
    async def check_feature_access(
        feature: str,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        try:
            feature_enum = Feature(feature)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown feature: {feature}",
            )

        result = internal.subscription_service.check_feature_access(current_user.id, feature_enum)
        return FeatureAccessResponse(
            allowed=result.allowed,
            reason=result.reason,
            limit=result.limit,
            used=result.used,
        )

    @router.post("/checkout", response_model=CheckoutResponse)
    async def create_checkout_session(
        checkout_request: CheckoutRequest,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        if checkout_request.tier == SubscriptionTier.FREE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot checkout for free tier",
            )

        try:
            checkout_url = internal.subscription_service.create_checkout_session(current_user.id, checkout_request.tier)
            return CheckoutResponse(checkout_url=checkout_url)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except Exception as e:
            log_exception("Error creating checkout session: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating checkout session: {str(e)}",
            )

    @router.post("/portal", response_model=PortalResponse)
    async def create_portal_session(
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        try:
            portal_url = internal.subscription_service.create_portal_session(current_user.id)
            return PortalResponse(portal_url=portal_url)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except Exception as e:
            log_exception("Error creating portal session: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating portal session: {str(e)}",
            )

    @router.post("/webhook", status_code=status.HTTP_200_OK)
    async def handle_webhook(
        request: Request,
        stripe_signature: str = Header(None, alias="Stripe-Signature"),
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        if not stripe_signature:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing Stripe-Signature header",
            )

        try:
            payload = await request.body()
            internal.subscription_service.handle_webhook_event(payload, stripe_signature)
            return {"status": "success"}
        except ValueError as e:
            log_exception("Webhook signature verification failed: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid webhook: {str(e)}",
            )
        except Exception as e:
            log_exception("Error processing webhook: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing webhook: {str(e)}",
            )

    app.include_router(router, prefix=settings.API_V1_STR)
