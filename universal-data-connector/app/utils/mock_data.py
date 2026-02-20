"""Mock data generators for testing and development."""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def generate_customers(count: int = 50) -> List[Dict[str, Any]]:
    """
    Generate mock customer data.
    
    Args:
        count: Number of customers to generate
        
    Returns:
        List of customer dictionaries
    """
    customers = []
    statuses = ["active", "inactive"]
    
    for i in range(1, count + 1):
        customer = {
            "customer_id": i,
            "name": f"Customer {i}",
            "email": f"user{i}@example.com",
            "created_at": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
            "status": random.choice(statuses)
        }
        customers.append(customer)
    
    logger.info(f"Generated {count} mock customers")
    return customers


def generate_support_tickets(count: int = 100) -> List[Dict[str, Any]]:
    """
    Generate mock support ticket data.
    
    Args:
        count: Number of tickets to generate
        
    Returns:
        List of support ticket dictionaries
    """
    tickets = []
    statuses = ["open", "closed"]
    priorities = ["low", "medium", "high"]
    
    for i in range(1, count + 1):
        ticket = {
            "ticket_id": i,
            "customer_id": random.randint(1, 50),
            "subject": f"Issue {i}",
            "priority": random.choice(priorities),
            "created_at": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
            "status": random.choice(statuses)
        }
        tickets.append(ticket)
    
    logger.info(f"Generated {count} mock support tickets")
    return tickets


def generate_analytics(days: int = 30, metrics: List[str] = None) -> List[Dict[str, Any]]:
    """
    Generate mock analytics data.
    
    Args:
        days: Number of days of data to generate
        metrics: List of metric names to generate
        
    Returns:
        List of analytics dictionaries
    """
    if metrics is None:
        metrics = ["daily_active_users", "signups", "conversion_rate"]
    
    analytics = []
    base_date = datetime.now() - timedelta(days=days)
    
    for day in range(days):
        current_date = (base_date + timedelta(days=day)).strftime("%Y-%m-%d")
        
        for metric in metrics:
            if metric == "daily_active_users":
                value = random.randint(100, 1000)
            elif metric == "signups":
                value = random.randint(10, 100)
            elif metric == "conversion_rate":
                value = round(random.uniform(0.01, 0.10), 4)
            else:
                value = random.randint(1, 100)
            
            analytics.append({
                "metric": metric,
                "date": current_date,
                "value": value
            })
    
    logger.info(f"Generated {len(analytics)} mock analytics records")
    return analytics


def save_mock_data(output_dir: str = "data"):
    """
    Generate and save all mock data to JSON files.
    
    Args:
        output_dir: Directory to save the JSON files
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Generate and save customers
    customers = generate_customers(50)
    with open(output_path / "customers.json", "w") as f:
        json.dump(customers, f, indent=2)
    logger.info(f"Saved customers to {output_path / 'customers.json'}")
    
    # Generate and save support tickets
    tickets = generate_support_tickets(100)
    with open(output_path / "support_tickets.json", "w") as f:
        json.dump(tickets, f, indent=2)
    logger.info(f"Saved support tickets to {output_path / 'support_tickets.json'}")
    
    # Generate and save analytics
    analytics = generate_analytics(30)
    with open(output_path / "analytics.json", "w") as f:
        json.dump(analytics, f, indent=2)
    logger.info(f"Saved analytics to {output_path / 'analytics.json'}")
    
    logger.info("All mock data generated and saved successfully")


if __name__ == "__main__":
    # Configure logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    save_mock_data()
