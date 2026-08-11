from typing import Callable, Optional
from dataclasses import dataclass, field
import json


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict = field(default_factory=dict)
    handler: Callable = None


@dataclass
class ToolResult:
    success: bool
    data: any = None
    error: str = None


class ToolExecutor:
    def __init__(self, tools: dict[str, Callable] = None):
        self.tools = tools or {}
        self._schemas = {}

    async def execute(self, tool_name: str, params: dict) -> ToolResult:
        if tool_name not in self.tools:
            return ToolResult(success=False, error=f"Tool '{tool_name}' nahi mila")
        try:
            handler = self.tools[tool_name]
            if callable(handler):
                result = await handler(**params) if hasattr(handler, '__call__') else handler(**params)
                return ToolResult(success=True, data=result)
            return ToolResult(success=False, error="Tool callable nahi hai")
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def list_tools(self) -> list[Tool]:
        tools = []
        for name, handler in self.tools.items():
            tools.append(Tool(
                name=name,
                description=self._schemas.get(name, {}).get("description", f"Tool: {name}"),
                parameters=self._schemas.get(name, {}).get("parameters", {}),
            ))
        return tools

    async def register_tool(self, tool: Tool) -> None:
        self.tools[tool.name] = tool.handler
        self._schemas[tool.name] = {
            "description": tool.description,
            "parameters": tool.parameters,
        }

    async def validate_params(self, tool_name: str, params: dict) -> bool:
        if tool_name not in self._schemas:
            return False
        schema = self._schemas[tool_name].get("parameters", {})
        required = schema.get("required", [])
        return all(r in params for r in required)

    async def get_tool_schema(self, tool_name: str) -> dict:
        return self._schemas.get(tool_name, {})


async def check_inventory(product_name: str = None, **kwargs) -> dict:
    return {"available": True, "product": product_name, "quantity": 50}


async def get_price(product_name: str = None, **kwargs) -> dict:
    return {"product": product_name, "price": 999, "currency": "INR"}


async def update_price(product_name: str = None, new_price: float = 0, **kwargs) -> dict:
    return {"product": product_name, "updated_price": new_price, "status": "updated"}


async def process_refund(transaction_id: str = None, amount: float = 0, **kwargs) -> dict:
    return {"transaction_id": transaction_id, "amount": amount, "status": "refund_initiated"}


async def generate_bill(customer_id: str = None, items: list = None, **kwargs) -> dict:
    total = sum(item.get("price", 0) * item.get("quantity", 1) for item in (items or []))
    return {"customer_id": customer_id, "items": items, "total": total, "bill_id": "BILL-001"}


async def send_payment_link(phone: str = None, amount: float = 0, **kwargs) -> dict:
    return {"phone": phone, "amount": amount, "link": f"https://upi://pay?amount={amount}"}


async def get_balance(business_id: str = None, **kwargs) -> dict:
    return {"business_id": business_id, "balance": 45000, "currency": "INR"}


async def create_estimate(customer_id: str = None, items: list = None, **kwargs) -> dict:
    total = sum(item.get("price", 0) * item.get("quantity", 1) for item in (items or []))
    return {"customer_id": customer_id, "items": items, "total": total, "estimate_id": "EST-001"}


async def search_products(query: str = None, business_id: str = None, **kwargs) -> dict:
    return {"query": query, "results": [], "count": 0}


async def update_stock(product_id: str = None, quantity: int = 0, operation: str = "set", **kwargs) -> dict:
    return {"product_id": product_id, "quantity": quantity, "operation": operation, "status": "updated"}


async def get_customer_history(customer_id: str = None, **kwargs) -> dict:
    return {"customer_id": customer_id, "transactions": [], "total_orders": 0}


async def schedule_followup(customer_id: str = None, message: str = None, delay_hours: int = 24, **kwargs) -> dict:
    return {"customer_id": customer_id, "message": message, "scheduled": True, "delay_hours": delay_hours}


async def send_broadcast(business_id: str = None, message: str = None, segment: str = "all", **kwargs) -> dict:
    return {"business_id": business_id, "message": message, "segment": segment, "sent_count": 0}


async def generate_report(business_id: str = None, report_type: str = "sales", **kwargs) -> dict:
    return {"business_id": business_id, "report_type": report_type, "status": "generated"}


async def search_knowledge(query: str = None, business_id: str = None, **kwargs) -> dict:
    return {"query": query, "results": [], "count": 0}


DEFAULT_TOOLS = {
    "check_inventory": check_inventory,
    "get_price": get_price,
    "update_price": update_price,
    "process_refund": process_refund,
    "generate_bill": generate_bill,
    "send_payment_link": send_payment_link,
    "get_balance": get_balance,
    "create_estimate": create_estimate,
    "search_products": search_products,
    "update_stock": update_stock,
    "get_customer_history": get_customer_history,
    "schedule_followup": schedule_followup,
    "send_broadcast": send_broadcast,
    "generate_report": generate_report,
    "search_knowledge": search_knowledge,
}
