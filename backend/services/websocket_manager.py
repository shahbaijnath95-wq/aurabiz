from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set
import json
import asyncio
from datetime import datetime


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.user_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, business_id: str = None, user_id: int = None):
        """Accept and store a new WebSocket connection."""
        await websocket.accept()

        if business_id:
            if business_id not in self.active_connections:
                self.active_connections[business_id] = []
            self.active_connections[business_id].append(websocket)

        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(websocket)

    def disconnect(self, websocket: WebSocket, business_id: str = None, user_id: int = None):
        """Remove a WebSocket connection."""
        if business_id and business_id in self.active_connections:
            if websocket in self.active_connections[business_id]:
                self.active_connections[business_id].remove(websocket)
            if not self.active_connections[business_id]:
                del self.active_connections[business_id]

        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

    async def send_to_business(self, business_id: str, message: dict):
        """Send message to all connections for a business."""
        if business_id in self.active_connections:
            dead = []
            for connection in self.active_connections[business_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    dead.append(connection)
            for d in dead:
                self.active_connections[business_id].remove(d)

    async def send_to_user(self, user_id: int, message: dict):
        """Send message to all connections for a user."""
        if user_id in self.user_connections:
            dead = []
            for connection in self.user_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    dead.append(connection)
            for d in dead:
                self.user_connections[user_id].discard(d)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        for business_id in list(self.active_connections.keys()):
            await self.send_to_business(business_id, message)

    async def notify_new_message(self, business_id: str, customer_name: str, message: str, phone: str):
        """Notify about a new incoming message."""
        await self.send_to_business(business_id, {
            "type": "new_message",
            "customer_name": customer_name,
            "message": message,
            "phone": phone,
            "timestamp": datetime.utcnow().isoformat(),
        })

    async def notify_new_order(self, business_id: str, order_id: str, amount: float, customer_name: str):
        """Notify about a new order."""
        await self.send_to_business(business_id, {
            "type": "new_order",
            "order_id": order_id,
            "amount": amount,
            "customer_name": customer_name,
            "timestamp": datetime.utcnow().isoformat(),
        })

    async def notify_low_stock(self, business_id: str, product_name: str, stock: int):
        """Notify about low stock."""
        await self.send_to_business(business_id, {
            "type": "low_stock",
            "product_name": product_name,
            "stock": stock,
            "timestamp": datetime.utcnow().isoformat(),
        })

    async def notify_stats_update(self, business_id: str, stats: dict):
        """Notify about stats update."""
        await self.send_to_business(business_id, {
            "type": "stats_update",
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat(),
        })


# Singleton manager
ws_manager = ConnectionManager()
