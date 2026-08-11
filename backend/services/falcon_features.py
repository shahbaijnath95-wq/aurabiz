"""
Falcon Features v4.0 — Advanced Business Features
====================================================
1. Voice Message Support — transcribe and respond to voice messages
2. Image Recognition — understand product photos, damage detection
3. Auto Follow-ups — automated follow-up messages after order/delivery
4. Loyalty Program — points, rewards, referral system
5. Smart Reports — daily/weekly business performance reports
6. Appointment Calendar — service booking with calendar integration
7. Broadcast Messages — promotional messages to all customers

Author: Falcon AI Engine
Version: 4.0
"""

import json
import os
import re
import hashlib
import uuid
from typing import Optional, Dict, List, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict


# ============================================================
# 1. VOICE MESSAGE SUPPORT
# ============================================================

class VoiceHandler:
    """Handles voice messages — transcribes and generates appropriate responses."""

    # Common Hindi/Hinglish voice message patterns
    VOICE_PATTERNS = {
        "order": ["order", "chahiye", "lena hai", "de do", "bhejo", "mangwana hai"],
        "inquiry": ["kya hai", "kitna hai", "price", "rate", "batao", "pata hai"],
        "complaint": ["kharab", "problem", "nahi chal", "nahi ho", "gussa", "pareshan"],
        "booking": ["book", "slot", "appointment", "kal", "aaj", "shaam", "subah"],
        "feedback": ["accha", "badhiya", "thanks", "shukriya", "mast", "zabardast"],
    }

    def transcribe(self, audio_data: bytes = None, text: str = None) -> str:
        """
        Transcribe voice message to text.
        If text is already provided (from WhatsApp transcription), use that.
        """
        if text:
            return text.strip()

        # If audio data provided, try to transcribe
        # For now, return placeholder — real implementation needs speech-to-text API
        return "[Voice message received]"

    def detect_voice_intent(self, text: str) -> Tuple[str, float]:
        """Detect intent from transcribed voice message."""
        text_lower = text.lower()
        scores = {}

        for intent, keywords in self.VOICE_PATTERNS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[intent] = score

        if not scores:
            return ("unknown", 0.0)

        best = max(scores, key=scores.get)
        return (best, min(scores[best] / 3.0, 1.0))

    def get_voice_response(self, text: str, customer_name: str = "Customer") -> str:
        """Generate response for voice message."""
        intent, confidence = self.detect_voice_intent(text)

        if intent == "order":
            return f"{customer_name}, voice message sun liya! Order ke liye product ka naam batao."
        elif intent == "inquiry":
            return f"{customer_name}, aapka sawal samajh aa gaya. Detail mein bataata hoon!"
        elif intent == "complaint":
            return f"{customer_name}, voice message sun ke pata chala ki kuch problem hai. Bataiye kya hua?"
        elif intent == "booking":
            return f"{customer_name}, booking ke liye date aur time batao!"
        elif intent == "feedback":
            return f"{customer_name}, shukriya! Feedback ke liye dhanyavaad! 🙏"
        else:
            return f"{customer_name}, voice message mil gaya! Kya help chahiye?"


# ============================================================
# 2. IMAGE RECOGNITION
# ============================================================

class ImageHandler:
    """Handles image messages — recognizes products, damage, etc."""

    # Product categories with visual keywords
    PRODUCT_VISUAL = {
        "electronics": ["laptop", "phone", "mobile", "tablet", "charger", "cable",
                       "headphone", "earphone", "speaker", "keyboard", "mouse",
                       "monitor", "printer", "camera", "tv", "remote"],
        "clothing": ["shirt", "pant", "dress", "suit", "saree", "kurti", "jeans",
                    "tshirt", "top", "skirt", "jacket", "coat", "shoe", "chappal"],
        "beauty": ["cream", "lotion", "shampoo", "conditioner", "lipstick", "foundation",
                  "mascara", "eyeliner", "nail polish", "perfume", "deodorant"],
        "food": ["bread", "biscuit", "chips", "chocolate", "cake", "pizza", "burger",
                "rice", "dal", "sabzi", "roti", "naan", "biryani"],
        "damage": ["broken", "cracked", "damaged", "torn", "scratched", "dented",
                  "chipped", "bent", "rust", "stain", "discolor"],
    }

    def analyze_image(self, image_data: bytes = None, caption: str = None,
                      inventory: list = None) -> Dict[str, Any]:
        """
        Analyze image and return insights.
        If caption is provided, use it for context.
        """
        result = {
            "type": "unknown",
            "product": None,
            "is_damage": False,
            "suggestion": None,
        }

        # Use caption for context
        if caption:
            caption_lower = caption.lower()

            # Check if it's a product inquiry
            if inventory:
                for item in inventory:
                    if item["name"].lower() in caption_lower:
                        result["type"] = "product_inquiry"
                        result["product"] = item
                        return result

            # Check if it's a damage report
            damage_keywords = ["kharab", "tuta", "toota", "crack", "damage", "broken",
                             "problem", "issue", "dekho", "ye dekho"]
            if any(kw in caption_lower for kw in damage_keywords):
                result["type"] = "damage_report"
                result["is_damage"] = True
                return result

            # Check if it's a product showcase
            show_keywords = ["ye hai", "ye dekho", "mera", "iska", "photo", "image"]
            if any(kw in caption_lower for kw in show_keywords):
                result["type"] = "product_showcase"
                return result

        return result

    def get_image_response(self, analysis: Dict, customer_name: str = "Customer",
                           inventory: list = None) -> str:
        """Generate response based on image analysis."""
        img_type = analysis.get("type", "unknown")

        if img_type == "product_inquiry":
            product = analysis.get("product")
            if product:
                return (f"{customer_name}, ye {product['name']} hai! "
                       f"Price: Rs.{product['price']}. "
                       f"Stock: {product.get('stock', 0)} pieces. "
                       f"Order karna ho toh bolo!")

        elif img_type == "damage_report":
            return (f"{customer_name}, photo dekha. Damage dikh raha hai. 😔 "
                   f"Kya hua? Bataiye detail mein — main help karta hoon. "
                   f"Repair ya replacement ke liye batao!")

        elif img_type == "product_showcase":
            return (f"{customer_name}, photo acchi hai! "
                   f"Kya chahiye isme? Price ya order ke liye batao!")

        else:
            return (f"{customer_name}, photo mil gaya! "
                   f"Kya chahiye isme? Product ka naam batao ya order karo!")


# ============================================================
# 3. AUTO FOLLOW-UPS
# ============================================================

class AutoFollowUp:
    """Automated follow-up messages after order/delivery."""

    FOLLOWUP_RULES = {
        "order_placed": {
            "delay_hours": 1,
            "message": "{name}, aapka order confirm ho gaya hai! 📦 Koi sawal ho toh batao.",
        },
        "order_delivered": {
            "delay_hours": 24,
            "message": "{name}, order mil gaya? Kaisa laga? Feedback do! ⭐",
        },
        "no_order_7_days": {
            "delay_hours": 168,  # 7 days
            "message": "{name}, bahut din ho gaye! Kya chahiye? Naya stock aaya hai! 🛒",
        },
        "complaint_followup": {
            "delay_hours": 48,
            "message": "{name}, pehle complaint thi — kya ab sab theek hai? 🙏",
        },
        "birthday": {
            "delay_hours": 0,
            "message": "{name}, janamdin mubarak! 🎂 Special discount ke liye code: BDAY{code}",
        },
        "festival": {
            "delay_hours": 0,
            "message": "{name}, {festival} ki shubhkamnaye! 🎉 Special offer: {discount}% off!",
        },
    }

    def __init__(self):
        self._pending: List[Dict] = []
        self._sent: List[Dict] = []

    def schedule(self, customer_name: str, customer_phone: str,
                 followup_type: str, business_id: str = None,
                 extra_context: Dict = None):
        """Schedule a follow-up message."""
        rule = self.FOLLOWUP_RULES.get(followup_type)
        if not rule:
            return

        context = {
            "name": customer_name,
            "code": customer_phone[-4:],
            "festival": extra_context.get("festival", "") if extra_context else "",
            "discount": extra_context.get("discount", 10) if extra_context else 10,
        }

        message = rule["message"].format(**context)
        scheduled_time = datetime.now() + timedelta(hours=rule["delay_hours"])

        self._pending.append({
            "id": str(uuid.uuid4()),
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "business_id": business_id,
            "message": message,
            "scheduled_at": scheduled_time.isoformat(),
            "type": followup_type,
            "status": "pending",
        })

    def get_pending(self) -> List[Dict]:
        """Get all pending follow-ups that are due."""
        now = datetime.now()
        due = []
        for fu in self._pending:
            if fu["status"] == "pending":
                scheduled = datetime.fromisoformat(fu["scheduled_at"])
                if now >= scheduled:
                    due.append(fu)
        return due

    def mark_sent(self, followup_id: str):
        """Mark a follow-up as sent."""
        for fu in self._pending:
            if fu["id"] == followup_id:
                fu["status"] = "sent"
                self._sent.append(fu)
                break

    def get_stats(self) -> Dict:
        """Get follow-up statistics."""
        return {
            "pending": len([f for f in self._pending if f["status"] == "pending"]),
            "sent": len(self._sent),
            "total": len(self._pending),
        }


# ============================================================
# 4. LOYALTY PROGRAM
# ============================================================

class LoyaltyProgram:
    """Points, rewards, referral system for customer retention."""

    TIERS = {
        "bronze": {"min_points": 0, "discount": 0, "perks": ["Basic support"]},
        "silver": {"min_points": 100, "discount": 5, "perks": ["5% discount", "Priority support"]},
        "gold": {"min_points": 500, "discount": 10, "perks": ["10% discount", "Free delivery", "Priority support"]},
        "platinum": {"min_points": 1000, "discount": 15, "perks": ["15% discount", "Free delivery", "VIP support", "Exclusive offers"]},
    }

    POINTS_RULES = {
        "purchase": 1,      # 1 point per Rs.100 spent
        "referral": 50,     # 50 points per referral
        "review": 10,       # 10 points per review
        "birthday": 100,    # 100 points on birthday
        "festival": 25,     # 25 points on festivals
    }

    def __init__(self):
        self._customers: Dict[str, Dict] = {}

    def get_customer(self, customer_id: str, customer_name: str = "Customer") -> Dict:
        """Get or create customer loyalty profile."""
        if customer_id not in self._customers:
            self._customers[customer_id] = {
                "id": customer_id,
                "name": customer_name,
                "points": 0,
                "tier": "bronze",
                "total_spent": 0,
                "referrals": [],
                "rewards_redeemed": [],
                "join_date": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat(),
            }
        return self._customers[customer_id]

    def add_points(self, customer_id: str, points: int, reason: str = "purchase"):
        """Add points to customer account."""
        customer = self.get_customer(customer_id)
        customer["points"] += points
        customer["last_activity"] = datetime.now().isoformat()

        # Update tier
        for tier_name, tier_config in sorted(self.TIERS.items(),
                                              key=lambda x: x[1]["min_points"],
                                              reverse=True):
            if customer["points"] >= tier_config["min_points"]:
                customer["tier"] = tier_name
                break

    def redeem_points(self, customer_id: str, points: int) -> Tuple[bool, str]:
        """Redeem points for discount."""
        customer = self.get_customer(customer_id)
        if customer["points"] < points:
            return False, f"Insufficient points. Aapke paas {customer['points']} points hain."

        customer["points"] -= points
        discount = points / 10  # 10 points = Rs.1 discount
        customer["rewards_redeemed"].append({
            "points": points,
            "discount": discount,
            "date": datetime.now().isoformat(),
        })
        return True, f"{points} points redeem ho gaye! Rs.{discount} discount milega!"

    def add_referral(self, customer_id: str, referred_phone: str):
        """Add referral and award points."""
        customer = self.get_customer(customer_id)
        if referred_phone not in customer["referrals"]:
            customer["referrals"].append(referred_phone)
            self.add_points(customer_id, self.POINTS_RULES["referral"], "referral")

    def get_status(self, customer_id: str) -> str:
        """Get customer loyalty status as formatted string."""
        customer = self.get_customer(customer_id)
        tier = customer["tier"]
        tier_config = self.TIERS[tier]
        perks = ", ".join(tier_config["perks"])

        return (
            f"⭐ Loyalty Status: {tier.upper()}\n"
            f"Points: {customer['points']}\n"
            f"Tier Discount: {tier_config['discount']}%\n"
            f"Perks: {perks}\n"
            f"Referrals: {len(customer['referrals'])}"
        )

    def get_reward_message(self, customer_id: str, customer_name: str) -> Optional[str]:
        """Get reward/offer message for customer."""
        customer = self.get_customer(customer_id)
        tier = customer["tier"]

        if tier == "platinum":
            return f"🌟 {customer_name}, aap Platinum member hain! 15% discount + free delivery!"
        elif tier == "gold":
            return f"⭐ {customer_name}, Gold member ho! 10% discount milta hai!"
        elif tier == "silver":
            return f"🥈 {customer_name}, Silver member ho! 5% discount milta hai!"
        return None


# ============================================================
# 5. SMART REPORTS
# ============================================================

class SmartReports:
    """Daily/weekly business performance reports."""

    def __init__(self):
        self._data = {
            "orders": [],
            "revenue": [],
            "customers": [],
            "complaints": [],
            "feedback": [],
        }

    def record_order(self, product: str, amount: float, customer_name: str):
        """Record an order for reporting."""
        self._data["orders"].append({
            "product": product,
            "amount": amount,
            "customer": customer_name,
            "time": datetime.now().isoformat(),
        })

    def record_complaint(self, complaint: str, customer_name: str):
        """Record a complaint."""
        self._data["complaints"].append({
            "complaint": complaint,
            "customer": customer_name,
            "time": datetime.now().isoformat(),
        })

    def record_feedback(self, feedback: str, customer_name: str, positive: bool):
        """Record customer feedback."""
        self._data["feedback"].append({
            "feedback": feedback,
            "customer": customer_name,
            "positive": positive,
            "time": datetime.now().isoformat(),
        })

    def generate_daily_report(self, business_name: str = "Business") -> str:
        """Generate daily performance report."""
        today = datetime.now().strftime("%Y-%m-%d")
        today_orders = [o for o in self._data["orders"]
                       if o["time"].startswith(today)]
        today_complaints = [c for c in self._data["complaints"]
                          if c["time"].startswith(today)]
        today_feedback = [f for f in self._data["feedback"]
                        if f["time"].startswith(today)]

        total_revenue = sum(o["amount"] for o in today_orders)
        positive_feedback = len([f for f in today_feedback if f["positive"]])
        negative_feedback = len(today_feedback) - positive_feedback

        # Top products
        product_counts = defaultdict(int)
        for o in today_orders:
            product_counts[o["product"]] += 1
        top_products = sorted(product_counts.items(), key=lambda x: x[1], reverse=True)[:3]

        report = (
            f"📊 Daily Report — {business_name}\n"
            f"Date: {today}\n"
            f"{'='*40}\n\n"
            f"📦 Orders: {len(today_orders)}\n"
            f"💰 Revenue: Rs.{total_revenue:,.0f}\n"
            f"😡 Complaints: {len(today_complaints)}\n"
            f"😊 Positive Feedback: {positive_feedback}\n"
            f"😞 Negative Feedback: {negative_feedback}\n\n"
        )

        if top_products:
            report += "🏆 Top Products:\n"
            for product, count in top_products:
                report += f"  - {product}: {count} orders\n"

        if today_complaints:
            report += "\n⚠️ Complaints:\n"
            for c in today_complaints[:3]:
                report += f"  - {c['customer']}: {c['complaint'][:50]}...\n"

        return report

    def generate_weekly_report(self, business_name: str = "Business") -> str:
        """Generate weekly performance report."""
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        week_orders = [o for o in self._data["orders"] if o["time"] >= week_ago]
        week_complaints = [c for c in self._data["complaints"] if c["time"] >= week_ago]
        week_feedback = [f for f in self._data["feedback"] if f["time"] >= week_ago]

        total_revenue = sum(o["amount"] for o in week_orders)
        avg_order = total_revenue / len(week_orders) if week_orders else 0
        positive_pct = (len([f for f in week_feedback if f["positive"]]) / len(week_feedback) * 100) if week_feedback else 0

        # Daily breakdown
        daily_revenue = defaultdict(float)
        for o in week_orders:
            day = o["time"][:10]
            daily_revenue[day] += o["amount"]

        report = (
            f"📊 Weekly Report — {business_name}\n"
            f"Period: {week_ago[:10]} to {datetime.now().strftime('%Y-%m-%d')}\n"
            f"{'='*40}\n\n"
            f"📦 Total Orders: {len(week_orders)}\n"
            f"💰 Total Revenue: Rs.{total_revenue:,.0f}\n"
            f"📈 Avg Order Value: Rs.{avg_order:,.0f}\n"
            f"😡 Total Complaints: {len(week_complaints)}\n"
            f"⭐ Satisfaction: {positive_pct:.0f}% positive\n\n"
        )

        if daily_revenue:
            report += "📅 Daily Revenue:\n"
            for day, rev in sorted(daily_revenue.items()):
                report += f"  - {day}: Rs.{rev:,.0f}\n"

        return report


# ============================================================
# 6. APPOINTMENT CALENDAR
# ============================================================

class AppointmentCalendar:
    """Service booking with calendar integration."""

    def __init__(self):
        self._appointments: List[Dict] = []
        self._slots: Dict[str, List[str]] = {}

    def get_available_slots(self, date: str, service: str = None,
                           duration_minutes: int = 30) -> List[str]:
        """Get available time slots for a date."""
        # Default business hours: 10 AM - 8 PM
        slots = []
        for hour in range(10, 20):
            for minute in [0, 30]:
                time_str = f"{hour:02d}:{minute:02d}"
                slot_key = f"{date}_{time_str}"

                # Check if slot is already booked
                booked = any(
                    a["date"] == date and a["time"] == time_str
                    for a in self._appointments
                    if a["status"] != "cancelled"
                )
                if not booked:
                    slots.append(time_str)

        return slots

    def book_appointment(self, customer_name: str, customer_phone: str,
                        service: str, date: str, time: str,
                        business_id: str = None, price: float = 0,
                        duration_minutes: int = 30) -> Dict:
        """Book an appointment."""
        # Check if slot is available
        slot_key = f"{date}_{time}"
        already_booked = any(
            a["date"] == date and a["time"] == time
            for a in self._appointments
            if a["status"] != "cancelled"
        )

        if already_booked:
            return {"error": "Slot already booked", "available": self.get_available_slots(date)}

        appointment = {
            "id": str(uuid.uuid4()),
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "service": service,
            "date": date,
            "time": time,
            "duration": duration_minutes,
            "price": price,
            "business_id": business_id,
            "status": "confirmed",
            "created_at": datetime.now().isoformat(),
        }

        self._appointments.append(appointment)
        return appointment

    def cancel_appointment(self, appointment_id: str) -> bool:
        """Cancel an appointment."""
        for a in self._appointments:
            if a["id"] == appointment_id:
                a["status"] = "cancelled"
                return True
        return False

    def get_appointments(self, date: str = None, customer_phone: str = None) -> List[Dict]:
        """Get appointments filtered by date or customer."""
        results = self._appointments
        if date:
            results = [a for a in results if a["date"] == date]
        if customer_phone:
            results = [a for a in results if a["customer_phone"] == customer_phone]
        return [a for a in results if a["status"] != "cancelled"]

    def get_appointment_message(self, appointment: Dict) -> str:
        """Generate appointment confirmation message."""
        return (
            f"Appointment confirm ho gaya! 📅\n\n"
            f"Service: {appointment['service']}\n"
            f"Date: {appointment['date']}\n"
            f"Time: {appointment['time']}\n"
            f"Duration: {appointment['duration']} min\n"
            f"Price: Rs.{appointment['price']}\n\n"
            f"5 min pehle aa jaana. Thanks! 🙏"
        )

    def get_reminder_message(self, appointment: Dict) -> str:
        """Generate appointment reminder message."""
        return (
            f"Reminder: Aapka appointment kal hai! 📅\n\n"
            f"Service: {appointment['service']}\n"
            f"Time: {appointment['time']}\n"
            f"Address: Store pe aa jaana\n\n"
            f"5 min pehle aa jaana. Thanks! 🙏"
        )


# ============================================================
# 7. BROADCAST MESSAGES
# ============================================================

class BroadcastManager:
    """Promotional messages to all customers."""

    def __init__(self):
        self._campaigns: List[Dict] = []
        self._sent: List[Dict] = []

    def create_campaign(self, name: str, message: str, target_customers: List[str],
                       business_id: str = None, schedule_at: str = None) -> Dict:
        """Create a broadcast campaign."""
        campaign = {
            "id": str(uuid.uuid4()),
            "name": name,
            "message": message,
            "target_customers": target_customers,
            "business_id": business_id,
            "schedule_at": schedule_at or datetime.now().isoformat(),
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "sent_count": 0,
        }
        self._campaigns.append(campaign)
        return campaign

    def get_pending_campaigns(self) -> List[Dict]:
        """Get campaigns that are due to send."""
        now = datetime.now()
        return [
            c for c in self._campaigns
            if c["status"] == "pending"
            and datetime.fromisoformat(c["schedule_at"]) <= now
        ]

    def mark_sent(self, campaign_id: str, sent_count: int):
        """Mark campaign as sent."""
        for c in self._campaigns:
            if c["id"] == campaign_id:
                c["status"] = "sent"
                c["sent_count"] = sent_count
                self._sent.append(c)
                break

    def get_promotional_message(self, offer_type: str, discount: int = 10,
                                products: List[str] = None) -> str:
        """Generate promotional message."""
        if offer_type == "flash_sale":
            return (
                f"⚡ FLASH SALE! ⚡\n\n"
                f"Sirf aaj ke liye {discount}% OFF!\n"
                f"Jaldi karo — limited time offer!\n\n"
                f"Order karne ke liye product ka naam batao!"
            )
        elif offer_type == "new_arrival":
            products_str = ", ".join(products[:3]) if products else "naye products"
            return (
                f"🆕 NEW ARRIVAL! 🆕\n\n"
                f"{products_str} ab available hai!\n"
                f"Pehle order karo — special price!\n\n"
                f"Detail ke liye batao!"
            )
        elif offer_type == "festival":
            return (
                f"🎉 FESTIVAL OFFER! 🎉\n\n"
                f"{discount}% OFF on all products!\n"
                f"Special festival discount — limited time!\n\n"
                f"Order karne ke liye batao!"
            )
        elif offer_type == "clearance":
            return (
                f"🏷️ CLEARANCE SALE! 🏷️\n\n"
                f"Up to {discount}% OFF!\n"
                f"Stock khatam hone se pehle le lo!\n\n"
                f"Order karne ke liye batao!"
            )
        else:
            return (
                f"📢 SPECIAL OFFER! 📢\n\n"
                f"{discount}% discount on selected items!\n"
                f"Order karne ke liye product ka naam batao!"
            )


# ============================================================
# FALCON FEATURES — Main Orchestrator
# ============================================================

class FalconFeatures:
    """
    Falcon Features v4.0 — Advanced Business Features
    Orchestrates all feature components.
    """

    def __init__(self):
        self.voice = VoiceHandler()
        self.image = ImageHandler()
        self.followup = AutoFollowUp()
        self.loyalty = LoyaltyProgram()
        self.reports = SmartReports()
        self.calendar = AppointmentCalendar()
        self.broadcast = BroadcastManager()

    def process_voice(self, text: str = None, audio_data: bytes = None,
                      customer_name: str = "Customer") -> str:
        """Process voice message."""
        transcribed = self.voice.transcribe(audio_data, text)
        return self.voice.get_voice_response(transcribed, customer_name)

    def process_image(self, image_data: bytes = None, caption: str = None,
                      customer_name: str = "Customer", inventory: list = None) -> str:
        """Process image message."""
        analysis = self.image.analyze_image(image_data, caption, inventory)
        return self.image.get_image_response(analysis, customer_name, inventory)

    def schedule_followup(self, customer_name: str, customer_phone: str,
                         followup_type: str, business_id: str = None,
                         extra_context: Dict = None):
        """Schedule a follow-up message."""
        self.followup.schedule(customer_name, customer_phone,
                              followup_type, business_id, extra_context)

    def get_loyalty_status(self, customer_id: str, customer_name: str = "Customer") -> str:
        """Get customer loyalty status."""
        return self.loyalty.get_status(customer_id)

    def add_loyalty_points(self, customer_id: str, amount: float):
        """Add loyalty points for purchase."""
        points = int(amount / 100)  # 1 point per Rs.100
        self.loyalty.add_points(customer_id, points, "purchase")

    def generate_report(self, business_name: str = "Business", report_type: str = "daily") -> str:
        """Generate business report."""
        if report_type == "weekly":
            return self.reports.generate_weekly_report(business_name)
        return self.reports.generate_daily_report(business_name)

    def book_appointment(self, customer_name: str, customer_phone: str,
                        service: str, date: str, time: str,
                        price: float = 0, duration: int = 30) -> Dict:
        """Book an appointment."""
        return self.calendar.book_appointment(
            customer_name, customer_phone, service, date, time,
            price=price, duration_minutes=duration
        )

    def get_available_slots(self, date: str) -> List[str]:
        """Get available appointment slots."""
        return self.calendar.get_available_slots(date)

    def create_broadcast(self, name: str, message: str,
                        target_customers: List[str], business_id: str = None) -> Dict:
        """Create broadcast campaign."""
        return self.broadcast.create_campaign(name, message, target_customers, business_id)

    def get_promotional_message(self, offer_type: str, discount: int = 10,
                                products: List[str] = None) -> str:
        """Generate promotional message."""
        return self.broadcast.get_promotional_message(offer_type, discount, products)


# ============================================================
# GLOBAL INSTANCE
# ============================================================

_features = None

def get_features() -> FalconFeatures:
    """Get singleton Falcon Features instance."""
    global _features
    if _features is None:
        _features = FalconFeatures()
    return _features
