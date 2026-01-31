from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock
from uuid import uuid4

import pytest

from app.domain.models.subscription import (
    TIER_LIMITS,
    Subscription,
    SubscriptionStatus,
    SubscriptionTier,
    SubscriptionUsage,
)
from app.domain.models.user import User
from app.ports.stripe import StripeClient
from app.services.subscription import (
    Feature,
    SubscriptionInfo,
    SubscriptionService,
)


class TestSubscriptionService:
    @pytest.fixture
    def user_id(self):
        return uuid4()

    @pytest.fixture
    def mock_subscription_repo(self):
        return Mock()

    @pytest.fixture
    def mock_usage_repo(self):
        return Mock()

    @pytest.fixture
    def mock_user_repo(self):
        return Mock()

    @pytest.fixture
    def mock_stripe_client(self):
        return Mock(spec=StripeClient)

    @pytest.fixture
    def service(self, mock_subscription_repo, mock_usage_repo, mock_user_repo, mock_stripe_client):
        return SubscriptionService(
            subscription_repository=mock_subscription_repo,
            subscription_usage_repository=mock_usage_repo,
            user_repository=mock_user_repo,
            stripe_client=mock_stripe_client,
        )

    @pytest.fixture
    def user(self, user_id):
        return User(
            id=user_id,
            email="test@example.com",
            name="Test User",
            oauth_provider="google",
            oauth_id="test-oauth-id",
        )

    @pytest.fixture
    def subscription(self, user_id):
        return Subscription(
            id=uuid4(),
            user_id=user_id,
            tier=SubscriptionTier.FREE,
            status=SubscriptionStatus.ACTIVE,
        )

    @pytest.fixture
    def usage(self, subscription):
        return SubscriptionUsage(
            id=uuid4(),
            subscription_id=subscription.id,
            statements_this_month=0,
            statements_total=0,
            ai_calls_this_month=0,
            ai_calls_total=0,
            current_period_start=datetime.now(timezone.utc),
        )


class TestGetOrCreateSubscription(TestSubscriptionService):
    def test_returns_existing_subscription(self, service, mock_subscription_repo, subscription, user_id):
        mock_subscription_repo.get_by_user_id.return_value = subscription

        result = service.get_or_create_subscription(user_id)

        assert result == subscription
        mock_subscription_repo.get_by_user_id.assert_called_once_with(user_id)
        mock_subscription_repo.create.assert_not_called()

    def test_creates_new_subscription_when_none_exists(self, service, mock_subscription_repo, mock_usage_repo, user_id):
        mock_subscription_repo.get_by_user_id.return_value = None
        mock_subscription_repo.create.return_value = Subscription(
            id=uuid4(),
            user_id=user_id,
            tier=SubscriptionTier.FREE,
            status=SubscriptionStatus.ACTIVE,
        )

        result = service.get_or_create_subscription(user_id)

        assert result.tier == SubscriptionTier.FREE
        assert result.status == SubscriptionStatus.ACTIVE
        mock_subscription_repo.create.assert_called_once()
        mock_usage_repo.create.assert_called_once()


class TestGetSubscriptionInfo(TestSubscriptionService):
    def test_returns_info_for_free_tier(
        self, service, mock_subscription_repo, mock_usage_repo, mock_user_repo, user, subscription, usage, user_id
    ):
        mock_user_repo.get_by_id.return_value = user
        mock_subscription_repo.get_by_user_id.return_value = subscription
        mock_usage_repo.get_by_subscription_id.return_value = usage

        result = service.get_subscription_info(user_id)

        assert isinstance(result, SubscriptionInfo)
        assert result.tier == SubscriptionTier.FREE
        assert result.status == SubscriptionStatus.ACTIVE
        assert result.is_active is True
        assert result.limits == TIER_LIMITS[SubscriptionTier.FREE]

    def test_respects_tier_override(
        self, service, mock_subscription_repo, mock_usage_repo, mock_user_repo, subscription, usage, user_id
    ):
        user_with_override = User(
            id=user_id,
            email="test@example.com",
            name="Test User",
            oauth_provider="google",
            oauth_id="test-oauth-id",
            tier_override="pro",
        )
        mock_user_repo.get_by_id.return_value = user_with_override
        mock_subscription_repo.get_by_user_id.return_value = subscription
        mock_usage_repo.get_by_subscription_id.return_value = usage

        result = service.get_subscription_info(user_id)

        assert result.tier == SubscriptionTier.PRO
        assert result.limits == TIER_LIMITS[SubscriptionTier.PRO]


class TestCheckFeatureAccess(TestSubscriptionService):
    def test_statement_upload_allowed_under_limit(
        self, service, mock_subscription_repo, mock_usage_repo, mock_user_repo, user, subscription, usage, user_id
    ):
        mock_user_repo.get_by_id.return_value = user
        mock_subscription_repo.get_by_user_id.return_value = subscription
        mock_usage_repo.get_by_subscription_id.return_value = usage

        result = service.check_feature_access(user_id, Feature.STATEMENT_UPLOAD)

        assert result.allowed is True
        assert result.reason is None

    def test_statement_upload_blocked_at_monthly_limit(
        self, service, mock_subscription_repo, mock_usage_repo, mock_user_repo, user, subscription, user_id
    ):
        usage_at_limit = SubscriptionUsage(
            id=uuid4(),
            subscription_id=subscription.id,
            statements_this_month=3,
            statements_total=3,
            current_period_start=datetime.now(timezone.utc),
        )
        mock_user_repo.get_by_id.return_value = user
        mock_subscription_repo.get_by_user_id.return_value = subscription
        mock_usage_repo.get_by_subscription_id.return_value = usage_at_limit

        result = service.check_feature_access(user_id, Feature.STATEMENT_UPLOAD)

        assert result.allowed is False
        assert "monthly" in result.reason.lower()
        assert result.limit == 3
        assert result.used == 3

    def test_statement_upload_blocked_at_total_limit(
        self, service, mock_subscription_repo, mock_usage_repo, mock_user_repo, user, subscription, user_id
    ):
        usage_at_total_limit = SubscriptionUsage(
            id=uuid4(),
            subscription_id=subscription.id,
            statements_this_month=1,
            statements_total=10,
            current_period_start=datetime.now(timezone.utc),
        )
        mock_user_repo.get_by_id.return_value = user
        mock_subscription_repo.get_by_user_id.return_value = subscription
        mock_usage_repo.get_by_subscription_id.return_value = usage_at_total_limit

        result = service.check_feature_access(user_id, Feature.STATEMENT_UPLOAD)

        assert result.allowed is False
        assert "total" in result.reason.lower()
        assert result.limit == 10
        assert result.used == 10

    def test_ai_feature_blocked_on_free_tier(
        self, service, mock_subscription_repo, mock_usage_repo, mock_user_repo, user, subscription, usage, user_id
    ):
        mock_user_repo.get_by_id.return_value = user
        mock_subscription_repo.get_by_user_id.return_value = subscription
        mock_usage_repo.get_by_subscription_id.return_value = usage

        result = service.check_feature_access(user_id, Feature.AI_CATEGORISATION)

        assert result.allowed is False
        assert "upgrade" in result.reason.lower()

    def test_ai_feature_allowed_on_basic_tier(
        self, service, mock_subscription_repo, mock_usage_repo, mock_user_repo, user, usage, user_id
    ):
        basic_subscription = Subscription(
            id=uuid4(),
            user_id=user_id,
            tier=SubscriptionTier.BASIC,
            status=SubscriptionStatus.ACTIVE,
        )
        mock_user_repo.get_by_id.return_value = user
        mock_subscription_repo.get_by_user_id.return_value = basic_subscription
        mock_usage_repo.get_by_subscription_id.return_value = usage

        result = service.check_feature_access(user_id, Feature.AI_CATEGORISATION)

        assert result.allowed is True

    def test_ai_rules_blocked_on_basic_tier(
        self, service, mock_subscription_repo, mock_usage_repo, mock_user_repo, user, usage, user_id
    ):
        basic_subscription = Subscription(
            id=uuid4(),
            user_id=user_id,
            tier=SubscriptionTier.BASIC,
            status=SubscriptionStatus.ACTIVE,
        )
        mock_user_repo.get_by_id.return_value = user
        mock_subscription_repo.get_by_user_id.return_value = basic_subscription
        mock_usage_repo.get_by_subscription_id.return_value = usage

        result = service.check_feature_access(user_id, Feature.AI_RULES)

        assert result.allowed is False

    def test_all_ai_features_allowed_on_pro_tier(
        self, service, mock_subscription_repo, mock_usage_repo, mock_user_repo, user, usage, user_id
    ):
        pro_subscription = Subscription(
            id=uuid4(),
            user_id=user_id,
            tier=SubscriptionTier.PRO,
            status=SubscriptionStatus.ACTIVE,
        )
        mock_user_repo.get_by_id.return_value = user
        mock_subscription_repo.get_by_user_id.return_value = pro_subscription
        mock_usage_repo.get_by_subscription_id.return_value = usage

        for feature in [Feature.AI_CATEGORISATION, Feature.AI_RULES, Feature.AI_PATTERNS, Feature.AI_INSIGHTS]:
            result = service.check_feature_access(user_id, feature)
            assert result.allowed is True


class TestIncrementUsage(TestSubscriptionService):
    def test_increment_statement_usage(self, service, mock_subscription_repo, mock_usage_repo, subscription, usage, user_id):
        mock_subscription_repo.get_by_user_id.return_value = subscription
        mock_usage_repo.get_by_subscription_id.return_value = usage

        service.increment_statement_usage(user_id, 1)

        assert usage.statements_this_month == 1
        assert usage.statements_total == 1
        mock_usage_repo.update.assert_called_once_with(usage)

    def test_increment_ai_usage(self, service, mock_subscription_repo, mock_usage_repo, subscription, usage, user_id):
        mock_subscription_repo.get_by_user_id.return_value = subscription
        mock_usage_repo.get_by_subscription_id.return_value = usage

        service.increment_ai_usage(user_id, 5)

        assert usage.ai_calls_this_month == 5
        assert usage.ai_calls_total == 5
        mock_usage_repo.update.assert_called_once_with(usage)


class TestMonthlyReset(TestSubscriptionService):
    def test_resets_monthly_counters_on_new_month(
        self, service, mock_subscription_repo, mock_usage_repo, mock_user_repo, user, subscription, user_id
    ):
        old_usage = SubscriptionUsage(
            id=uuid4(),
            subscription_id=subscription.id,
            statements_this_month=5,
            statements_total=10,
            ai_calls_this_month=20,
            ai_calls_total=50,
            current_period_start=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )
        mock_user_repo.get_by_id.return_value = user
        mock_subscription_repo.get_by_user_id.return_value = subscription
        mock_usage_repo.get_by_subscription_id.return_value = old_usage

        service.check_feature_access(user_id, Feature.STATEMENT_UPLOAD)

        assert old_usage.statements_this_month == 0
        assert old_usage.ai_calls_this_month == 0
        assert old_usage.statements_total == 10
        assert old_usage.ai_calls_total == 50
        mock_usage_repo.update.assert_called()


class TestStripeIntegration(TestSubscriptionService):
    def test_create_checkout_session(
        self, service, mock_subscription_repo, mock_user_repo, mock_stripe_client, user, subscription, user_id
    ):
        mock_user_repo.get_by_id.return_value = user
        mock_subscription_repo.get_by_user_id.return_value = subscription
        mock_stripe_client.get_price_id_for_tier.return_value = "price_basic"
        mock_stripe_client.create_customer.return_value = "cus_test123"
        mock_stripe_client.create_checkout_session.return_value = "https://checkout.stripe.com/xxx"

        result = service.create_checkout_session(user_id, SubscriptionTier.BASIC)

        assert result == "https://checkout.stripe.com/xxx"
        mock_stripe_client.create_customer.assert_called_once_with(
            email="test@example.com",
            name="Test User",
            user_id=str(user_id),
        )
        mock_stripe_client.create_checkout_session.assert_called_once()

    def test_create_checkout_session_existing_customer(
        self, service, mock_subscription_repo, mock_user_repo, mock_stripe_client, user, user_id
    ):
        subscription_with_customer = Subscription(
            id=uuid4(),
            user_id=user_id,
            tier=SubscriptionTier.FREE,
            status=SubscriptionStatus.ACTIVE,
            stripe_customer_id="cus_existing",
        )
        mock_user_repo.get_by_id.return_value = user
        mock_subscription_repo.get_by_user_id.return_value = subscription_with_customer
        mock_stripe_client.get_price_id_for_tier.return_value = "price_basic"
        mock_stripe_client.create_checkout_session.return_value = "https://checkout.stripe.com/xxx"

        result = service.create_checkout_session(user_id, SubscriptionTier.BASIC)

        assert result == "https://checkout.stripe.com/xxx"
        mock_stripe_client.create_customer.assert_not_called()

    def test_create_portal_session(self, service, mock_subscription_repo, mock_stripe_client, user_id):
        subscription_with_customer = Subscription(
            id=uuid4(),
            user_id=user_id,
            tier=SubscriptionTier.BASIC,
            status=SubscriptionStatus.ACTIVE,
            stripe_customer_id="cus_existing",
        )
        mock_subscription_repo.get_by_user_id.return_value = subscription_with_customer
        mock_stripe_client.create_portal_session.return_value = "https://billing.stripe.com/xxx"

        result = service.create_portal_session(user_id)

        assert result == "https://billing.stripe.com/xxx"
        mock_stripe_client.create_portal_session.assert_called_once_with("cus_existing")

    def test_create_portal_session_no_customer(self, service, mock_subscription_repo, subscription, user_id):
        mock_subscription_repo.get_by_user_id.return_value = subscription

        with pytest.raises(ValueError, match="No billing account"):
            service.create_portal_session(user_id)


class TestWebhookHandling(TestSubscriptionService):
    def test_handle_checkout_completed(self, service, mock_subscription_repo, mock_stripe_client, user_id):
        subscription = Subscription(
            id=uuid4(),
            user_id=user_id,
            tier=SubscriptionTier.FREE,
            status=SubscriptionStatus.ACTIVE,
            stripe_customer_id="cus_123",
        )
        mock_subscription_repo.get_by_stripe_customer_id.return_value = subscription

        mock_stripe_client.retrieve_subscription.return_value = {
            "id": "sub_123",
            "items": {"data": [{"price": {"id": "price_basic"}}]},
            "current_period_start": 1704067200,
            "current_period_end": 1706745600,
        }

        session_data = MagicMock()
        session_data.subscription = "sub_123"
        session_data.customer = "cus_123"
        session_data.metadata = {"tier": "basic"}

        service._handle_checkout_completed(session_data)

        assert subscription.tier == SubscriptionTier.BASIC
        assert subscription.status == SubscriptionStatus.ACTIVE
        assert subscription.stripe_subscription_id == "sub_123"
        mock_subscription_repo.update.assert_called_once()

    def test_handle_subscription_deleted(self, service, mock_subscription_repo, user_id):
        subscription = Subscription(
            id=uuid4(),
            user_id=user_id,
            tier=SubscriptionTier.BASIC,
            status=SubscriptionStatus.ACTIVE,
            stripe_subscription_id="sub_123",
        )
        mock_subscription_repo.get_by_stripe_subscription_id.return_value = subscription

        stripe_sub = MagicMock()
        stripe_sub.id = "sub_123"

        service._handle_subscription_deleted(stripe_sub)

        assert subscription.tier == SubscriptionTier.FREE
        assert subscription.status == SubscriptionStatus.CANCELLED
        assert subscription.stripe_subscription_id is None
        mock_subscription_repo.update.assert_called_once()

    def test_handle_payment_failed(self, service, mock_subscription_repo, user_id):
        subscription = Subscription(
            id=uuid4(),
            user_id=user_id,
            tier=SubscriptionTier.BASIC,
            status=SubscriptionStatus.ACTIVE,
            stripe_customer_id="cus_123",
        )
        mock_subscription_repo.get_by_stripe_customer_id.return_value = subscription

        invoice = MagicMock()
        invoice.customer = "cus_123"

        service._handle_payment_failed(invoice)

        assert subscription.status == SubscriptionStatus.PAST_DUE
        mock_subscription_repo.update.assert_called_once()

    def test_handle_webhook_event(self, service, mock_subscription_repo, mock_stripe_client, user_id):
        event = MagicMock()
        event.type = "checkout.session.completed"
        event.data.object.subscription = "sub_123"
        event.data.object.customer = "cus_123"
        event.data.object.metadata = {"tier": "basic"}

        mock_stripe_client.construct_webhook_event.return_value = event

        subscription = Subscription(
            id=uuid4(),
            user_id=user_id,
            tier=SubscriptionTier.FREE,
            status=SubscriptionStatus.ACTIVE,
            stripe_customer_id="cus_123",
        )
        mock_subscription_repo.get_by_stripe_customer_id.return_value = subscription
        mock_stripe_client.retrieve_subscription.return_value = {
            "id": "sub_123",
            "items": {"data": []},
        }

        service.handle_webhook_event(b"payload", "signature")

        mock_stripe_client.construct_webhook_event.assert_called_once_with(b"payload", "signature")
