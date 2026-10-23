# Synthetic demo data. Replace with an authenticated order-system integration for real deployments.
ORDERS = {
    "ORD-1001": {"status": "Shipped", "estimated_delivery": "2026-10-25", "items": ["Wireless Headphones"], "customer": "Alex Morgan"},
    "ORD-1002": {"status": "Processing", "estimated_delivery": "2026-10-28", "items": ["Desk Lamp"], "customer": "Jordan Lee"},
    "ORD-1003": {"status": "Delivered", "estimated_delivery": "2026-10-20", "items": ["Water Bottle"], "customer": "Sam Taylor"},
}

def lookup_order(order_id: str):
    order = ORDERS.get(order_id.strip().upper())
    if not order:
        return {"found": False, "message": f"I couldn't find order {order_id}. Please verify the order ID."}
    return {"found": True, "order_id": order_id.upper(), **order}
