from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import WhatsAppTemplate


DEFAULT_TEMPLATES = [
    {
        "name": "order_confirmation",
        "category": "UTILITY",
        "language": "hi",
        "body": "Aapka order confirm ho gaya! 🎉 Order ID: {{order_id}} | Amount: ₹{{amount}} | Delivery: {{delivery_date}}",
        "variables": ["order_id", "amount", "delivery_date"],
    },
    {
        "name": "payment_reminder",
        "category": "UTILITY",
        "language": "hi",
        "body": "Namaste {{customer_name}}! ₹{{amount}} ka payment pending hai. UPI se pay karein: {{upi_link}}",
        "variables": ["customer_name", "amount", "upi_link"],
    },
    {
        "name": "feedback_request",
        "category": "MARKETING",
        "language": "hi",
        "body": "{{customer_name}}, kaisa raha aapka experience? ⭐ {{feedback_link}}",
        "variables": ["customer_name", "feedback_link"],
    },
    {
        "name": "appointment_reminder",
        "category": "UTILITY",
        "language": "hi",
        "body": "{{customer_name}}, aapka appointment {{date}} ko {{time}} bhai hai. Confirm karein!",
        "variables": ["customer_name", "date", "time"],
    },
    {
        "name": "welcome_message",
        "category": "MARKETING",
        "language": "hi",
        "body": "{{customer_name}} ji, {{business_name}} mein aapka swagat hai! 🙏 Hum kaise help kar sakte hain?",
        "variables": ["customer_name", "business_name"],
    },
    {
        "name": "delivery_update",
        "category": "UTILITY",
        "language": "hi",
        "body": "{{customer_name}}, aapka order {{status}} hai. Track karein: {{tracking_link}}",
        "variables": ["customer_name", "status", "tracking_link"],
    },
    {
        "name": "promotion",
        "category": "MARKETING",
        "language": "hi",
        "body": "{{customer_name}}! 🎉 Special offer: {{offer_details}}. Abhi order karein: {{order_link}}",
        "variables": ["customer_name", "offer_details", "order_link"],
    },
    {
        "name": "payment_confirmation",
        "category": "UTILITY",
        "language": "hi",
        "body": "Payment received! ₹{{amount}} - {{customer_name}} ka order confirmed. ✅",
        "variables": ["amount", "customer_name"],
    },
    {
        "name": "out_of_stock",
        "category": "UTILITY",
        "language": "hi",
        "body": "{{customer_name}}, {{product_name}} abhi out of stock hai. Restock hone pe batayenge!",
        "variables": ["customer_name", "product_name"],
    },
    {
        "name": "thank_you",
        "category": "UTILITY",
        "language": "hi",
        "body": "{{customer_name}}, aapka order deliver ho gaya! Kaisa laga product? Reply mein batayein 🙏",
        "variables": ["customer_name"],
    },
]


class TemplateManager:
    def __init__(self, db: AsyncSession = None):
        self.db = db

    async def get_templates(self, business_id: str) -> list:
        if not self.db:
            return DEFAULT_TEMPLATES
        result = await self.db.execute(
            select(WhatsAppTemplate).where(WhatsAppTemplate.business_id == business_id)
        )
        templates = result.scalars().all()
        if not templates:
            return await self._seed_default_templates(business_id)
        return templates

    async def _seed_default_templates(self, business_id: str) -> list:
        for tpl in DEFAULT_TEMPLATES:
            template = WhatsAppTemplate(
                business_id=business_id,
                name=tpl["name"],
                category=tpl["category"],
                language=tpl["language"],
                body=tpl["body"],
                variables=tpl.get("variables", []),
                status="approved",
            )
            self.db.add(template)
        await self.db.flush()
        result = await self.db.execute(
            select(WhatsAppTemplate).where(WhatsAppTemplate.business_id == business_id)
        )
        return result.scalars().all()

    async def create_template(self, business_id: str, template_data: dict) -> WhatsAppTemplate:
        template = WhatsAppTemplate(business_id=business_id, **template_data)
        self.db.add(template)
        await self.db.flush()
        return template

    async def update_template(self, template_id: str, data: dict) -> Optional[WhatsAppTemplate]:
        result = await self.db.execute(select(WhatsAppTemplate).where(WhatsAppTemplate.id == template_id))
        template = result.scalar_one_or_none()
        if not template:
            return None
        for key, value in data.items():
            if hasattr(template, key):
                setattr(template, key, value)
        await self.db.flush()
        return template

    async def delete_template(self, template_id: str) -> bool:
        result = await self.db.execute(select(WhatsAppTemplate).where(WhatsAppTemplate.id == template_id))
        template = result.scalar_one_or_none()
        if template:
            await self.db.delete(template)
            await self.db.flush()
            return True
        return False

    async def preview_template(self, template_id: str, variables: dict = None) -> str:
        result = await self.db.execute(select(WhatsAppTemplate).where(WhatsAppTemplate.id == template_id))
        template = result.scalar_one_or_none()
        if not template:
            return "Template nahi mili"
        text = template.body
        if variables:
            for key, value in variables.items():
                text = text.replace(f"{{{{{key}}}}}", str(value))
        return text

    async def get_categories(self) -> list[str]:
        return ["AUTHENTICATION", "UTILITY", "MARKETING"]

    async def send_test(self, template_id: str, phone_number: str) -> dict:
        return {"status": "sent", "phone": phone_number, "template_id": template_id}

    async def apply_variables(self, template_text: str, variables: dict) -> str:
        text = template_text
        for key, value in variables.items():
            text = text.replace(f"{{{{{key}}}}}", str(value))
        return text

    async def get_template_analytics(self, template_id: str) -> dict:
        return {"template_id": template_id, "sent": 0, "delivered": 0, "read": 0}
