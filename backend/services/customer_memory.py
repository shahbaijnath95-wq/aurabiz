"""
Customer Memory Engine — Powerful Long-Term Memory
===================================================
Customer ki yaad-dasht — orders, preferences, visit history, total spent.
Kaam kare bina embedding ke (direct SQL queries), 2-3 din baad bhi yaad rakhe.

Memory Types:
  1. Order History   — kya kharida, kab, kitna
  2. Preferences     — language, payment type, delivery type
  3. Visit Pattern   — kitni baar aaya, last visit kab
  4. Total Spent     — lifetime value
  5. Favorite Items  — sabse zyada kharida
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from collections import Counter

from loguru import logger
from sqlalchemy import select, func, desc

from config import settings
from database import async_session
from models import (
    Customer, Order, Transaction, WhatsAppMessage, Conversation,
    Product, Payment
)


class CustomerMemory:
    """Per-customer structured memory using direct SQL (no embedding dependency)."""

    async def get_memory(self, business_id: str, customer_id: str = None, phone: str = None) -> Dict[str, Any]:
        """
        Customer ka complete memory context return karta hai.
        AI prompt me inject ke liye ready format.
        """
        async with async_session() as db:
            # Find customer
            customer = None
            if customer_id:
                result = await db.execute(select(Customer).where(Customer.id == customer_id))
                customer = result.scalar_one_or_none()
            elif phone:
                result = await db.execute(
                    select(Customer).where(
                        Customer.business_id == business_id,
                        Customer.phone_number == phone
                    )
                )
                customer = result.scalar_one_or_none()

            if not customer:
                return {"is_returning": False, "memory_text": ""}

            customer_id = customer.id

            # ── 1. Order History (last 10 orders) ──
            orders_result = await db.execute(
                select(Order)
                .where(Order.customer_id == customer_id, Order.business_id == business_id)
                .order_by(desc(Order.created_at))
                .limit(10)
            )
            orders = orders_result.scalars().all()

            # ── 2. Recent Transactions (payments) ──
            txn_result = await db.execute(
                select(Transaction)
                .where(Transaction.customer_id == customer_id, Transaction.business_id == business_id)
                .order_by(desc(Transaction.created_at))
                .limit(5)
            )
            transactions = txn_result.scalars().all()

            # ── 3. Total stats ──
            total_orders = len(orders)
            total_spent = sum(o.total_price for o in orders)
            avg_order = total_spent / total_orders if total_orders > 0 else 0

            # ── 4. Favorite products (most ordered) ──
            product_counter = Counter()
            for o in orders:
                product_counter[o.product_name] += o.quantity
            favorite_products = product_counter.most_common(3)

            # ── 5. Recent chat summary (last 5 conversations) ──
            conv_result = await db.execute(
                select(Conversation)
                .where(Conversation.customer_id == customer_id, Conversation.business_id == business_id)
                .order_by(desc(Conversation.updated_at))
                .limit(5)
            )
            conversations = conv_result.scalars().all()

            # ── 5b. WhatsApp message count + last message date ──
            msg_count_result = await db.execute(
                select(func.count(WhatsAppMessage.id))
                .where(WhatsAppMessage.customer_id == customer_id, WhatsAppMessage.business_id == business_id)
            )
            total_messages = msg_count_result.scalar() or 0

            last_msg_result = await db.execute(
                select(WhatsAppMessage.created_at)
                .where(WhatsAppMessage.customer_id == customer_id, WhatsAppMessage.business_id == business_id, WhatsAppMessage.direction == "inbound")
                .order_by(desc(WhatsAppMessage.created_at))
                .limit(1)
            )
            last_msg_dt = last_msg_result.scalar_one_or_none()

            # ── 6. Last visit (from messages OR orders, whichever recent) ──
            last_visit_dt = last_msg_dt
            if orders and orders[0].created_at:
                order_dt = orders[0].created_at
                if not last_visit_dt or (order_dt and order_dt > last_visit_dt):
                    last_visit_dt = order_dt
            last_visit_str = ""
            days_ago = None
            if last_visit_dt:
                now = datetime.now(timezone.utc)
                last_dt = last_visit_dt
                if last_dt.tzinfo is None:
                    last_dt = last_dt.replace(tzinfo=timezone.utc)
                delta = now - last_dt
                days_ago = delta.days
                if days_ago == 0:
                    last_visit_str = "aaj"
                elif days_ago == 1:
                    last_visit_str = "kal"
                elif days_ago < 7:
                    last_visit_str = f"{days_ago} din pehle"
                elif days_ago < 30:
                    last_visit_str = f"{days_ago // 7} hafte pehle"
                else:
                    last_visit_str = f"{days_ago // 30} mahine pehle"

            # ── 7. Payment preference ──
            payment_types = Counter()
            for t in transactions:
                if t.payment_method:
                    payment_types[t.payment_method] += 1
            preferred_payment = payment_types.most_common(1)[0][0] if payment_types else "unknown"

            # ── 8. Customer tier (spending + orders + messages) ──
            if total_spent >= 10000:
                tier = "VIP"
            elif total_spent >= 5000:
                tier = "Premium"
            elif total_orders >= 3 or total_messages >= 10:
                tier = "Regular"
            elif total_orders >= 1 or total_messages >= 3:
                tier = "Returning"
            else:
                tier = "New"

            # ── Is returning? (has any interaction) ──
            is_returning = total_orders > 0 or total_messages >= 3

            # ── Build memory text (for AI prompt) ──
            memory_lines = []
            memory_lines.append(f"Customer Tier: {tier}")
            memory_lines.append(f"Total Orders: {total_orders} | Total Spent: ₹{total_spent:.0f} | Avg Order: ₹{avg_order:.0f} | Messages: {total_messages}")

            if last_visit_str:
                memory_lines.append(f"Last Visit: {last_visit_str}")

            if favorite_products:
                fav_str = ", ".join([f"{name} ({qty}x)" for name, qty in favorite_products])
                memory_lines.append(f"Favorite Products: {fav_str}")

            if preferred_payment != "unknown":
                memory_lines.append(f"Preferred Payment: {preferred_payment}")

            if orders:
                recent_orders = orders[:3]
                recent_str = ", ".join([f"{o.product_name} (₹{o.total_price})" for o in recent_orders])
                memory_lines.append(f"Recent Orders: {recent_str}")

            # Language preference
            if customer.preferred_language:
                memory_lines.append(f"Preferred Language: {customer.preferred_language}")

            memory_text = "\n".join(memory_lines)

            return {
                "is_returning": is_returning,
                "customer_id": customer_id,
                "customer_name": customer.name or "Customer",
                "tier": tier,
                "total_orders": total_orders,
                "total_spent": total_spent,
                "avg_order": avg_order,
                "favorite_products": favorite_products,
                "preferred_payment": preferred_payment,
                "last_visit_days_ago": days_ago,
                "recent_orders": [
                    {"product": o.product_name, "price": o.total_price, "date": o.created_at.isoformat() if o.created_at else None}
                    for o in orders[:5]
                ],
                "lifecycle_stage": customer.lifecycle_stage.value if customer.lifecycle_stage else "lead",
                "memory_text": memory_text,
            }

    async def learn_from_chat(
        self,
        business_id: str,
        customer_id: str,
        message: str,
        response: str,
        db=None,
    ) -> None:
        """
        Chat se seekho — customer ki preferences update karo.
        Har chat ke baad automatically call karo.
        """
        close_db = False
        if db is None:
            db = async_session()
            close_db = True

        try:
            result = await db.execute(select(Customer).where(Customer.id == customer_id))
            customer = result.scalar_one_or_none()
            if not customer:
                return

            # Update last active
            customer.last_active = datetime.now(timezone.utc)

            # Detect language preference from message
            # Simple heuristic: check for Hindi/English dominance
            hindi_chars = sum(1 for c in message if '\u0900' <= c <= '\u097F')
            english_chars = sum(1 for c in message if c.isalpha() and c.isascii())
            if hindi_chars > english_chars:
                customer.preferred_language = "hi"
            elif english_chars > hindi_chars:
                customer.preferred_language = "en"

            await db.commit()
            logger.debug("[Memory] Updated customer {} preferences", customer_id[:8])

        except Exception as e:
            logger.debug("[Memory] learn_from_chat error: {}", e)
        finally:
            if close_db:
                await db.close()

    async def after_order_placed(
        self,
        business_id: str,
        customer_id: str,
        order_id: str,
        product_name: str,
        amount: float,
        db=None,
    ) -> None:
        """
        Order place hone ke baad memory update karo.
        Total orders, total spent, etc.
        """
        close_db = False
        if db is None:
            db = async_session()
            close_db = True

        try:
            result = await db.execute(select(Customer).where(Customer.id == customer_id))
            customer = result.scalar_one_or_none()
            if not customer:
                return

            customer.total_orders = (customer.total_orders or 0) + 1
            customer.total_spent = (customer.total_spent or 0) + amount
            customer.last_active = datetime.now(timezone.utc)

            # Update lifecycle stage
            if customer.total_orders >= 10:
                from models import LifecycleStage
                customer.lifecycle_stage = LifecycleStage.LOYAL
            elif customer.total_orders >= 3:
                from models import LifecycleStage
                customer.lifecycle_stage = LifecycleStage.REPEAT

            await db.commit()
            logger.debug("[Memory] Order recorded for customer {}: {} ₹{}", customer_id[:8], product_name, amount)

        except Exception as e:
            logger.debug("[Memory] after_order_placed error: {}", e)
        finally:
            if close_db:
                await db.close()


# ── Module-level instance ──
_customer_memory: Optional[CustomerMemory] = None


def get_customer_memory() -> CustomerMemory:
    global _customer_memory
    if _customer_memory is None:
        _customer_memory = CustomerMemory()
    return _customer_memory


def build_memory_prompt_section(memory: Dict[str, Any]) -> str:
    """
    Customer memory se AI prompt section banata hai.
    Inject this into the system prompt.
    """
    if not memory or not memory.get("is_returning"):
        return ""

    sections = []
    sections.append("\n" + "=" * 50)
    sections.append("CUSTOMER MEMORY (yaad rakho — is customer ka itihaas):")
    sections.append("=" * 50)
    sections.append(memory.get("memory_text", ""))
    sections.append("=" * 50)
    sections.append("INSTRUCTIONS: Upar diye gaye memory ka use karo personalized reply mein.")
    sections.append("Agar customer purana hai toh 'wapas aaya' khush se bolo.")
    sections.append("Agar pehli baar hai toh 'swagat' bolo.")
    sections.append("Favorite products yaad rakho — suggest karo agar relevant lage.")

    return "\n".join(sections)
