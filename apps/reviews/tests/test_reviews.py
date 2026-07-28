"""Reviews API + service tests."""

from __future__ import annotations

import pytest

from apps.core.exceptions import ConflictError, ValidationError
from apps.reviews.services import review_service

pytestmark = pytest.mark.django_db


class TestReviewService:
    def test_create_review(self, user, user_factory):
        from tests.factories import ProductFactory

        product = ProductFactory()
        review = review_service.create(
            product=product, user=user, rating=5, title="Great", comment="Loved it"
        )
        assert review.rating == 5
        assert review.is_approved is False  # moderation-ready

    def test_one_review_per_user_per_product(self, user):
        from tests.factories import ProductFactory

        product = ProductFactory()
        review_service.create(product=product, user=user, rating=4)
        with pytest.raises(ConflictError):
            review_service.create(product=product, user=user, rating=3)

    def test_rating_bounds(self, user):
        from tests.factories import ProductFactory

        product = ProductFactory()
        with pytest.raises(ValidationError):
            review_service.create(product=product, user=user, rating=0)
        with pytest.raises(ValidationError):
            review_service.create(product=product, user=user, rating=6)

    def test_average_rating_excludes_unapproved(self, user):
        from tests.factories import ProductFactory

        product = ProductFactory()
        r1 = review_service.create(product=product, user=user, rating=5)
        from apps.accounts.models import User

        other = User.objects.create_user(email="other@example.com", password="Str0ngP@ss!")
        review_service.create(product=product, user=other, rating=3)
        review_service.approve(r1)
        avg = review_service.average_rating(product)
        assert avg == 5.0  # only the approved one counts


class TestReviewAPI:
    def test_create_review_authed(self, authed_client, user):
        from tests.factories import ProductFactory

        product = ProductFactory()
        resp = authed_client.post(
            f"/api/v1/products/{product.id}/reviews/",
            {"product": product.id, "rating": 5, "title": "Good"},
            format="json",
        )
        assert resp.status_code == 201

    def test_list_approved_only(self, api_client, user):
        from tests.factories import ProductFactory

        product = ProductFactory()
        review_service.create(product=product, user=user, rating=4, title="Pending")
        resp = api_client.get(f"/api/v1/products/{product.id}/reviews/")
        assert resp.status_code == 200
        # unapproved review should not appear
        assert resp.json()["data"] == []
