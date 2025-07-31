#!/usr/bin/env python3
"""
API Analytics Dashboard for KBI Labs
Shows API usage, popular endpoints, and revenue metrics
"""
import requests
import json
from datetime import datetime, timedelta

API_UMBRELLA_ADMIN = "http://localhost:3001"

def get_api_metrics():
    """Fetch API metrics from API Umbrella"""
    # This would connect to API Umbrella's analytics
    metrics = {
        "total_calls_today": 4521,
        "unique_api_keys": 23,
        "most_popular_endpoint": "/api/v1/digital-gap/companies",
        "revenue_mtd": 4483,
        "top_users": [
            {"email": "digitalagency@example.com", "calls": 823, "tier": "professional"},
            {"email": "webdesign@example.com", "calls": 445, "tier": "basic"}
        ]
    }
    return metrics

def display_dashboard():
    metrics = get_api_metrics()
    print("🎯 KBI Labs API Dashboard")
    print("=" * 50)
    print(f"📊 Total API Calls Today: {metrics['total_calls_today']:,}")
    print(f"🔑 Active API Keys: {metrics['unique_api_keys']}")
    print(f"💰 Revenue This Month: ${metrics['revenue_mtd']:,}")
    print(f"🔥 Most Popular: {metrics['most_popular_endpoint']}")
    print("\n👥 Top Users:")
    for user in metrics['top_users']:
        print(f"  • {user['email']} ({user['tier']}): {user['calls']} calls")

if __name__ == "__main__":
    display_dashboard()
