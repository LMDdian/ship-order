"""
简单测试：订单列表 GET /api/orders/，仅 is_completed=true 时返回已完成订单且结构正确。
"""
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model

from .models import Order

User = get_user_model()


class OrderListIsCompletedTest(TestCase):
    """GET /api/orders/?is_completed=true 仅返回当前用户已完成订单，且含 completed_time 等字段"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
        )
        self.other_user = User.objects.create_user(
            username="other",
            password="otherpass123",
        )

    def test_is_completed_true_returns_only_completed_orders(self):
        now = timezone.now()
        completed = Order.objects.create(
            user=self.user,
            tracking_number="TN001",
            is_completed=True,
            completed_time=now,
        )
        Order.objects.create(
            user=self.user,
            tracking_number="TN002",
            is_completed=False,
        )
        Order.objects.create(
            user=self.other_user,
            tracking_number="TN003",
            is_completed=True,
            completed_time=now,
        )

        self.client.force_authenticate(user=self.user)
        resp = self.client.get("/api/orders/", {"is_completed": "true"})

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        results = data if isinstance(data, list) else data.get("results", data)
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 1)
        item = results[0]
        self.assertEqual(item["id"], completed.id)
        self.assertEqual(item["tracking_number"], "TN001")
        self.assertTrue(item["is_completed"])
        self.assertIn("completed_time", item)
        self.assertIn("tracking_number", item)
        self.assertIn("card_image_url", item)
        self.assertIn("card_line1", item)
        self.assertIn("card_line2", item)

    def test_is_completed_true_empty_when_no_completed(self):
        Order.objects.create(
            user=self.user,
            tracking_number="TN001",
            is_completed=False,
        )
        self.client.force_authenticate(user=self.user)
        resp = self.client.get("/api/orders/", {"is_completed": "true"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        results = data if isinstance(data, list) else data.get("results", data)
        self.assertEqual(len(results), 0)
