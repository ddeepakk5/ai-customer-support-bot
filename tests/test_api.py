"""
Test script for API endpoints
Run from project root: python tests/test_api.py
"""

import requests
import json
from typing import Dict, Any
import time

API_BASE_URL = "http://localhost:8000/api/v1"


class APITester:
    def __init__(self):
        self.session_id = None
        self.customer_id = None
        self.results = []

    def print_result(self, test_name: str, success: bool, message: str = ""):
        """Print test result"""
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"\n{status}: {test_name}")
        if message:
            print(f"   {message}")
        self.results.append({"test": test_name, "success": success})

    def test_health(self):
        """Test health endpoint"""
        try:
            response = requests.get(f"http://localhost:8000/health", timeout=5)
            self.print_result("Health Check", response.status_code == 200)
        except Exception as e:
            self.print_result("Health Check", False, str(e))

    def test_create_session(self):
        """Test session creation"""
        try:
            import uuid

            self.customer_id = f"test-customer-{uuid.uuid4().hex[:8]}"
            response = requests.post(
                f"{API_BASE_URL}/sessions",
                params={
                    "customer_id": self.customer_id,
                    "topic": "billing",
                },
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                self.session_id = data["session_id"]
                self.print_result(
                    "Create Session",
                    True,
                    f"Session ID: {self.session_id}",
                )
            else:
                self.print_result("Create Session", False, f"Status: {response.status_code}")
        except Exception as e:
            self.print_result("Create Session", False, str(e))

    def test_get_session(self):
        """Test get session"""
        if not self.session_id:
            self.print_result("Get Session", False, "No session ID")
            return

        try:
            response = requests.get(
                f"{API_BASE_URL}/sessions/{self.session_id}",
                timeout=10,
            )
            self.print_result("Get Session", response.status_code == 200)
        except Exception as e:
            self.print_result("Get Session", False, str(e))

    def test_chat(self):
        """Test chat endpoint"""
        if not self.session_id or not self.customer_id:
            self.print_result("Chat", False, "No session or customer ID")
            return

        try:
            test_messages = [
                "How do I reset my password?",
                "What is your refund policy?",
                "I need to delete my account",
                "Can I upgrade my plan?",
            ]

            for msg in test_messages:
                response = requests.post(
                    f"{API_BASE_URL}/chat",
                    json={
                        "session_id": self.session_id,
                        "customer_id": self.customer_id,
                        "message": msg,
                    },
                    timeout=30,
                )

                if response.status_code == 200:
                    data = response.json()
                    confidence = data.get("confidence_score", 0)
                    response_type = data.get("response_type", "unknown")
                    self.print_result(
                        f'Chat: "{msg[:30]}..."',
                        True,
                        f"Type: {response_type}, Confidence: {confidence:.1%}",
                    )
                else:
                    self.print_result(
                        f'Chat: "{msg[:30]}..."',
                        False,
                        f"Status: {response.status_code}",
                    )

                time.sleep(1)  # Rate limiting

        except Exception as e:
            self.print_result("Chat", False, str(e))

    def test_get_messages(self):
        """Test get session messages"""
        if not self.session_id:
            self.print_result("Get Messages", False, "No session ID")
            return

        try:
            response = requests.get(
                f"{API_BASE_URL}/sessions/{self.session_id}/messages",
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                self.print_result(
                    "Get Messages",
                    True,
                    f"Retrieved {len(data)} messages",
                )
            else:
                self.print_result("Get Messages", False, f"Status: {response.status_code}")

        except Exception as e:
            self.print_result("Get Messages", False, str(e))

    def test_get_faqs(self):
        """Test get all FAQs"""
        try:
            response = requests.get(
                f"{API_BASE_URL}/faqs",
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                self.print_result(
                    "Get FAQs",
                    True,
                    f"Retrieved {len(data)} FAQs",
                )
            else:
                self.print_result("Get FAQs", False, f"Status: {response.status_code}")

        except Exception as e:
            self.print_result("Get FAQs", False, str(e))

    def test_search_faqs(self):
        """Test FAQ search"""
        try:
            response = requests.get(
                f"{API_BASE_URL}/faqs/search",
                params={"query": "password reset", "limit": 5},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                self.print_result(
                    "Search FAQs",
                    True,
                    f"Found {len(data)} matching FAQs",
                )
            else:
                self.print_result("Search FAQs", False, f"Status: {response.status_code}")

        except Exception as e:
            self.print_result("Search FAQs", False, str(e))

    def test_summarize(self):
        """Test conversation summarization"""
        if not self.session_id:
            self.print_result("Summarize", False, "No session ID")
            return

        try:
            response = requests.post(
                f"{API_BASE_URL}/conversations/{self.session_id}/summarize",
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                summary = data.get("summary", "")
                self.print_result(
                    "Summarize",
                    True,
                    f"Summary length: {len(summary)} chars",
                )
            else:
                self.print_result("Summarize", False, f"Status: {response.status_code}")

        except Exception as e:
            self.print_result("Summarize", False, str(e))

    def test_suggest_actions(self):
        """Test next action suggestions"""
        if not self.session_id:
            self.print_result("Suggest Actions", False, "No session ID")
            return

        try:
            response = requests.post(
                f"{API_BASE_URL}/conversations/{self.session_id}/suggest-actions",
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                actions = data.get("suggested_actions", [])
                self.print_result(
                    "Suggest Actions",
                    True,
                    f"Generated {len(actions)} suggestions",
                )
            else:
                self.print_result("Suggest Actions", False, f"Status: {response.status_code}")

        except Exception as e:
            self.print_result("Suggest Actions", False, str(e))

    def test_metrics(self):
        """Test metrics endpoint"""
        try:
            response = requests.get(
                f"{API_BASE_URL}/admin/metrics",
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                self.print_result(
                    "Get Metrics",
                    True,
                    f"Sessions: {data.get('total_sessions')}, "
                    f"Messages: {data.get('total_messages')}, "
                    f"FAQs: {data.get('total_faqs')}",
                )
            else:
                self.print_result("Get Metrics", False, f"Status: {response.status_code}")

        except Exception as e:
            self.print_result("Get Metrics", False, str(e))

    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "=" * 60)
        print("AI CUSTOMER SUPPORT BOT - API TEST SUITE")
        print("=" * 60)

        print("\n[1/11] Testing Health Check...")
        self.test_health()

        print("\n[2/11] Testing Session Creation...")
        self.test_create_session()

        print("\n[3/11] Testing Get Session...")
        self.test_get_session()

        print("\n[4/11] Testing Chat Messages...")
        self.test_chat()

        print("\n[5/11] Testing Get Messages...")
        self.test_get_messages()

        print("\n[6/11] Testing Get FAQs...")
        self.test_get_faqs()

        print("\n[7/11] Testing Search FAQs...")
        self.test_search_faqs()

        print("\n[8/11] Testing Conversation Summarization...")
        self.test_summarize()

        print("\n[9/11] Testing Suggest Actions...")
        self.test_suggest_actions()

        print("\n[10/11] Testing Metrics...")
        self.test_metrics()

        # Print summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)

        passed = sum(1 for r in self.results if r["success"])
        total = len(self.results)

        print(f"\nTotal Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")

        print("\n" + "=" * 60)


if __name__ == "__main__":
    tester = APITester()
    tester.run_all_tests()
