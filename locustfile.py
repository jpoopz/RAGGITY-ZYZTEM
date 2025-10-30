"""
Locust load testing file for RAGGITY ZYZTEM API.

Usage:
    # Install locust
    pip install locust
    
    # Run load test with web UI
    locust -f locustfile.py --host http://localhost:8000
    
    # Run headless load test
    locust -f locustfile.py --host http://localhost:8000 --users 10 --spawn-rate 2 --run-time 60s --headless
    
    # Then open: http://localhost:8089
"""

from locust import HttpUser, task, between
import random


class RaggityUser(HttpUser):
    """
    Simulates a user interacting with RAGGITY API.
    """
    
    # Wait 1-3 seconds between requests
    wait_time = between(1, 3)
    
    # Sample questions for testing
    questions = [
        "What is RAGGITY ZYZTEM?",
        "How do I start the API server?",
        "What vector stores are supported?",
        "Explain the CLO 3D integration",
        "What LLM providers can I use?",
        "How does the hybrid cloud mode work?",
        "What file formats are supported for ingestion?",
        "How do I configure the system?",
        "What are the main features?",
        "How do I run the UI?",
        "What is the purpose of the toast notification system?",
        "How do I switch between FAISS and ChromaDB?",
    ]
    
    @task(10)
    def query_endpoint(self):
        """
        Test /query endpoint (weight: 10)
        Most common operation
        """
        question = random.choice(self.questions)
        self.client.get("/query", params={"q": question, "k": 3}, name="/query")
    
    @task(2)
    def health_check(self):
        """
        Test /health endpoint (weight: 2)
        Lightweight monitoring calls
        """
        self.client.get("/health", name="/health")
    
    @task(1)
    def system_stats(self):
        """
        Test /system-stats endpoint (weight: 1)
        Moderate weight for monitoring
        """
        self.client.get("/system-stats", name="/system-stats")
    
    @task(1)
    def troubleshoot(self):
        """
        Test /troubleshoot endpoint (weight: 1)
        Diagnostic calls
        """
        self.client.get("/troubleshoot", name="/troubleshoot")
    
    def on_start(self):
        """Called when a simulated user starts"""
        # Could do authentication or setup here
        pass


class AdminUser(HttpUser):
    """
    Simulates admin operations (less frequent, heavier).
    """
    
    wait_time = between(5, 10)
    
    @task
    def system_stats(self):
        """Check system stats"""
        self.client.get("/system-stats")
    
    @task
    def troubleshoot(self):
        """Run troubleshooter"""
        self.client.get("/troubleshoot")


# Define user classes and their weights
# 90% normal users, 10% admin users
# Uncomment to use:
# from locust import HttpUser
# RaggityUser.weight = 9
# AdminUser.weight = 1

