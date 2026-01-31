from datetime import datetime, timezone

from app.domain.models.subscription import TIER_LIMITS, SubscriptionStatus, SubscriptionTier
from app.services.subscription import Feature, FeatureAccessResult, SubscriptionInfo
from tests.api.helpers import TEST_USER_ID, build_client, mocked_dependencies


def test_get_subscription():
    internal = mocked_dependencies()
    client = build_client(internal)

    info = SubscriptionInfo(
        tier=SubscriptionTier.FREE,
        status=SubscriptionStatus.ACTIVE,
        is_active=True,
        limits=TIER_LIMITS[SubscriptionTier.FREE],
        usage={
            "statements_this_month": 2,
            "statements_total": 5,
            "ai_calls_this_month": 0,
            "ai_calls_total": 0,
        },
        stripe_customer_id=None,
        current_period_end=None,
        cancel_at_period_end=False,
    )
    internal.subscription_service.get_subscription_info.return_value = info

    response = client.get("/api/v1/subscription")

    assert response.status_code == 200
    data = response.json()
    assert data["tier"] == "free"
    assert data["status"] == "active"
    assert data["is_active"] is True
    assert data["limits"]["statements_per_month"] == 3
    assert data["limits"]["statements_total"] == 10
    assert data["limits"]["ai_categorisation"] is False
    assert data["usage"]["statements_this_month"] == 2
    assert data["usage"]["statements_total"] == 5
    internal.subscription_service.sync_from_stripe.assert_called_once_with(TEST_USER_ID)


def test_get_subscription_pro_tier():
    internal = mocked_dependencies()
    client = build_client(internal)

    info = SubscriptionInfo(
        tier=SubscriptionTier.PRO,
        status=SubscriptionStatus.ACTIVE,
        is_active=True,
        limits=TIER_LIMITS[SubscriptionTier.PRO],
        usage={
            "statements_this_month": 50,
            "statements_total": 200,
            "ai_calls_this_month": 100,
            "ai_calls_total": 500,
        },
        stripe_customer_id="cus_123",
        current_period_end=datetime(2024, 2, 15, tzinfo=timezone.utc),
        cancel_at_period_end=False,
    )
    internal.subscription_service.get_subscription_info.return_value = info

    response = client.get("/api/v1/subscription")

    assert response.status_code == 200
    data = response.json()
    assert data["tier"] == "pro"
    assert data["limits"]["statements_per_month"] is None
    assert data["limits"]["ai_categorisation"] is True
    assert data["limits"]["ai_rules"] is True
    assert data["usage"]["ai_calls_this_month"] == 100


def test_check_feature_access_allowed():
    internal = mocked_dependencies()
    client = build_client(internal)

    internal.subscription_service.check_feature_access.return_value = FeatureAccessResult(
        allowed=True,
        reason=None,
        limit=None,
        used=None,
    )

    response = client.get("/api/v1/subscription/check/statement_upload")

    assert response.status_code == 200
    data = response.json()
    assert data["allowed"] is True
    assert data["reason"] is None
    internal.subscription_service.check_feature_access.assert_called_once_with(TEST_USER_ID, Feature.STATEMENT_UPLOAD)


def test_check_feature_access_blocked():
    internal = mocked_dependencies()
    client = build_client(internal)

    internal.subscription_service.check_feature_access.return_value = FeatureAccessResult(
        allowed=False,
        reason="You've reached your monthly statement limit.",
        limit=3,
        used=3,
    )

    response = client.get("/api/v1/subscription/check/statement_upload")

    assert response.status_code == 200
    data = response.json()
    assert data["allowed"] is False
    assert "monthly" in data["reason"].lower()
    assert data["limit"] == 3
    assert data["used"] == 3


def test_check_feature_access_ai_feature():
    internal = mocked_dependencies()
    client = build_client(internal)

    internal.subscription_service.check_feature_access.return_value = FeatureAccessResult(
        allowed=False,
        reason="This feature requires a paid subscription.",
    )

    response = client.get("/api/v1/subscription/check/ai_categorisation")

    assert response.status_code == 200
    data = response.json()
    assert data["allowed"] is False
    internal.subscription_service.check_feature_access.assert_called_once_with(TEST_USER_ID, Feature.AI_CATEGORISATION)


def test_check_feature_access_unknown_feature():
    internal = mocked_dependencies()
    client = build_client(internal)

    response = client.get("/api/v1/subscription/check/unknown_feature")

    assert response.status_code == 400
    assert "Unknown feature" in response.json()["detail"]


def test_create_checkout_session():
    internal = mocked_dependencies()
    client = build_client(internal)

    internal.subscription_service.create_checkout_session.return_value = "https://checkout.stripe.com/xxx"

    response = client.post(
        "/api/v1/subscription/checkout",
        json={"tier": "basic"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["checkout_url"] == "https://checkout.stripe.com/xxx"
    internal.subscription_service.create_checkout_session.assert_called_once_with(TEST_USER_ID, SubscriptionTier.BASIC)


def test_create_checkout_session_pro_tier():
    internal = mocked_dependencies()
    client = build_client(internal)

    internal.subscription_service.create_checkout_session.return_value = "https://checkout.stripe.com/pro"

    response = client.post(
        "/api/v1/subscription/checkout",
        json={"tier": "pro"},
    )

    assert response.status_code == 200
    internal.subscription_service.create_checkout_session.assert_called_once_with(TEST_USER_ID, SubscriptionTier.PRO)


def test_create_checkout_session_free_tier_rejected():
    internal = mocked_dependencies()
    client = build_client(internal)

    response = client.post(
        "/api/v1/subscription/checkout",
        json={"tier": "free"},
    )

    assert response.status_code == 400
    assert "Cannot checkout for free tier" in response.json()["detail"]
    internal.subscription_service.create_checkout_session.assert_not_called()


def test_create_checkout_session_no_price_configured():
    internal = mocked_dependencies()
    client = build_client(internal)

    internal.subscription_service.create_checkout_session.side_effect = ValueError("No price configured for tier basic")

    response = client.post(
        "/api/v1/subscription/checkout",
        json={"tier": "basic"},
    )

    assert response.status_code == 400
    assert "No price configured" in response.json()["detail"]


def test_create_portal_session():
    internal = mocked_dependencies()
    client = build_client(internal)

    internal.subscription_service.create_portal_session.return_value = "https://billing.stripe.com/xxx"

    response = client.post("/api/v1/subscription/portal")

    assert response.status_code == 200
    data = response.json()
    assert data["portal_url"] == "https://billing.stripe.com/xxx"
    internal.subscription_service.create_portal_session.assert_called_once_with(TEST_USER_ID)


def test_create_portal_session_no_customer():
    internal = mocked_dependencies()
    client = build_client(internal)

    internal.subscription_service.create_portal_session.side_effect = ValueError(
        "No billing account found. Please subscribe first."
    )

    response = client.post("/api/v1/subscription/portal")

    assert response.status_code == 400
    assert "No billing account" in response.json()["detail"]


def test_webhook_missing_signature():
    internal = mocked_dependencies()
    client = build_client(internal)

    response = client.post(
        "/api/v1/subscription/webhook",
        content=b"{}",
    )

    assert response.status_code == 400
    assert "Missing Stripe-Signature" in response.json()["detail"]


def test_webhook_success():
    internal = mocked_dependencies()
    client = build_client(internal)

    response = client.post(
        "/api/v1/subscription/webhook",
        content=b'{"type": "checkout.session.completed"}',
        headers={"Stripe-Signature": "t=123,v1=abc"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    internal.subscription_service.handle_webhook_event.assert_called_once()


def test_webhook_invalid_signature():
    internal = mocked_dependencies()
    client = build_client(internal)

    internal.subscription_service.handle_webhook_event.side_effect = ValueError("Invalid signature")

    response = client.post(
        "/api/v1/subscription/webhook",
        content=b'{"type": "checkout.session.completed"}',
        headers={"Stripe-Signature": "invalid"},
    )

    assert response.status_code == 400
    assert "Invalid webhook" in response.json()["detail"]
