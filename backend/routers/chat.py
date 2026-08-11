"""
Direct Chat API - WhatsApp API ke bina kaam karta hai.
QR code scan → web chat → AI response.
Customer data auto-capture hota hai.
Ab FREE AI models use karta hai (OpenRouter).
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime, timezone
import uuid
import urllib.request
from loguru import logger
import re as re_mod
import json as json_mod

from database import get_db
from models import Customer, Conversation, WhatsAppMessage, User, Booking, Order, Coupon, Transaction, Business, Payment
from services.free_ai import get_ai_reply_free, get_fallback_reply, falcon_reply
from services.inventory_manager import InventoryManager
from services.order_manager import OrderManager
from services.language_service import detect_language
from services.catalog_service import CatalogService
from services.knowledge_base import get_knowledge_base
from services.memory_manager import get_memory_manager
from auth import get_current_user, verify_business_access

BOT_URL = "http://127.0.0.1:8001"

router = APIRouter(prefix="/api/v1")


class ChatRequest(BaseModel):
    message: str
    business_id: str
    session_id: str
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    business_name: Optional[str] = "aapka business"
    business_type: Optional[str] = "general"
    message_type: Optional[str] = "text"  # text, voice, image
    image_url: Optional[str] = None
    voice_text: Optional[str] = None  # Transcribed voice text


class ChatAudioRequest(BaseModel):
    audio_base64: str
    business_id: str
    session_id: str
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    business_name: Optional[str] = "aapka business"


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    customer_id: Optional[str] = None


def get_ai_reply_with_inventory(message: str, business_id: str, customer_name: str = None, inventory_context: list = None) -> str:
    """Fallback reply - jab AI fail ho. Inventory data use karta hai."""
    msg = message.lower().strip()
    name = customer_name or "aap"

    # Agar inventory mein products hain toh unhe check karo
    if inventory_context:
        for p in inventory_context:
            if any(word in msg for word in p["name"].lower().split()):
                if p["stock"] > 0:
                    return f"{name}, {p['name']} hamare paas hai! 🎉\n💰 Price: ₹{p['price']}\n📦 Stock: {p['stock']} {p['unit']} bache hain\n\nOrder karna ho toh batao!"
                else:
                    return f"{name}, {p['name']} abhi out of stock hai 😔\nKoi aur product dekhna ho toh batao!"

    if any(w in msg for w in ["hi", "hello", "hey", "namaste", "namaskar", "hii"]):
        return f"Namaste {name}! Main aapki kya madad kar sakta hoon?"
    if any(w in msg for w in ["price", "pricing", "rate", "kitna", "cost", "dam"]):
        return f"{name}, hamari pricing affordable hai! Starter Rs999, Growth Rs2499."
    if any(w in msg for w in ["order", "delivery", "ship"]):
        return f"{name}, order track karne ke liye order number batao."
    if any(w in msg for w in ["pay", "payment", "paise", "bill", "upi"]):
        return f"{name}, payment ke liye UPI: business@upi"
    if any(w in msg for w in ["service", "kya karte", "offer"]):
        return f"{name}, ham AI WhatsApp assistant, analytics, payments provide karte hain."
    if any(w in msg for w in ["complaint", "problem", "issue"]):
        return f"{name}, afsoos hai! Complaint note ho gayi."
    if any(w in msg for w in ["thanks", "shukriya", "thank"]):
        return f"Khushi hui {name}!"
    if any(w in msg for w in ["bye", "alvida", "tata"]):
        return f"Bye {name}!"
    return f"{name}, message mil gaya! Pricing, order, ya payment pooch sakte ho."


@router.post("/chat/audio", response_model=ChatResponse)
async def handle_audio_chat(req: ChatAudioRequest, db: AsyncSession = Depends(get_db)):
    """Handles WhatsApp voice notes. Transcribes using Groq Whisper, then passes to handle_chat."""
    # Check if voice orders are enabled for this business
    try:
        from routers.settings import get_setting
        ai_settings = await get_setting(db, req.business_id, "ai")
        if ai_settings and not ai_settings.get("voice_orders_enabled", False):
            return ChatResponse(
                reply="Maaf kijiye, abhi voice messages (audio) allowed nahi hain. Kripya type karke message bhejiye. 🙏",
                session_id=req.session_id,
            )
    except Exception as e:
        logger.error(f"Failed to check voice_orders_enabled setting: {e}")

    # Transcribe audio
    from services.voice_service import transcribe_audio
    transcribed_text = await transcribe_audio(req.audio_base64)
    
    logger.info(f"[VOICE TRANSCRIBED] {req.customer_phone}: {transcribed_text}")
    
    # Check if transcription failed gracefully
    if "Kripya type karke" in transcribed_text:
        return ChatResponse(
            reply=transcribed_text,
            session_id=req.session_id,
        )

    # Proceed as normal chat request
    chat_req = ChatRequest(
        message=transcribed_text,
        business_id=req.business_id,
        session_id=req.session_id,
        customer_name=req.customer_name,
        customer_phone=req.customer_phone,
        business_name=req.business_name,
        message_type="voice",
        voice_text=transcribed_text
    )
    
    return await handle_chat(chat_req, db)


@router.post("/chat", response_model=ChatResponse)
async def handle_chat(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Direct chat - QR scan ya web link se. FREE AI use karta hai."""

    # 1. Find or create customer
    customer = None
    customer_identifier = req.customer_phone or f"session_{req.session_id}"
    result = await db.execute(
        select(Customer).where(
            Customer.phone_number == customer_identifier,
            Customer.business_id == req.business_id
        )
    )
    customer = result.scalar_one_or_none()

    if not customer:
        customer = Customer(
            id=str(uuid.uuid4()),
            business_id=req.business_id,
            name=req.customer_name or "Web Customer",
            phone_number=customer_identifier,
        )
        db.add(customer)
        await db.flush()

    # 2. Save customer message
    customer_msg = WhatsAppMessage(
        id=str(uuid.uuid4()),
        business_id=req.business_id,
        customer_id=customer.id,
        session_id=req.session_id,
        direction="inbound",
        content=req.message,
        message_type="text",
        status="received",
    )
    db.add(customer_msg)
    await db.flush()

    # 3. Fetch conversation history (last 10 messages) - AI ko context milega
    history_messages = []
    try:
        past_result = await db.execute(
            select(WhatsAppMessage).where(
                WhatsAppMessage.business_id == req.business_id,
                WhatsAppMessage.customer_id == customer.id,
            ).order_by(desc(WhatsAppMessage.created_at)).limit(11)  # 11 because we just saved current msg
        )
        past_msgs = list(reversed(past_result.scalars().all()))

        # Exclude the current message (last one we just saved) to avoid duplication
        for m in past_msgs[:-1]:
            role = "user" if m.direction == "inbound" else "assistant"
            history_messages.append({"role": role, "content": m.content or ""})
    except Exception as e:
        logger.error("History fetch error: {}", e)

    # 3b. Search inventory for matching products - AI ko real stock data milega
    inventory_context = []
    products = []
    try:
        im = InventoryManager(db)

        # Check if message is just a quantity BEFORE product search
        qty_only_match = re_mod.match(r'^(\d+)\s*(pc|piece|pieces|pcs|unit|units|sets?|bottle|bottles|box|boxes|pack|packs)?$', req.message.strip().lower())
        is_pure_qty = qty_only_match and not any(w in req.message.lower() for w in ["road", "street", "lane", "nagar", "colony", "area", "city", "pin", "flat", "house"])

        # Single-word affirmative/negative responses — skip inventory search, let AI handle with context
        affirmative_words = {"ha", "haan", "han", "ji", "ok", "theek", "acha", "accha", "sahi", "bilkul", "zaroor", "sure", "yes", "yup", "yeah", "nahi", "nahin", "no", "na"}
        is_single_word_response = req.message.strip().lower() in affirmative_words

        if is_single_word_response:
            products = []
            services = []
        elif not is_pure_qty:
            products = await im.search_products(req.business_id, req.message, limit=5)
        else:
            # For quantity-only messages, force history-based product lookup
            products = []

        # If message contains date/time but no products found, load services
        # Try to find the service from conversation history first
        from services.free_ai import extract_date_time
        date_val, time_val = extract_date_time(req.message)
        if date_val and time_val and not products:
            # Search history for most recently mentioned service name
            from models import Product as ProductModel
            history_svc = None

            # First get all services for this business
            all_svcs_result = await db.execute(
                select(ProductModel).where(
                    ProductModel.business_id == req.business_id,
                    ProductModel.is_active == True,
                    ProductModel.item_type == "service",
                )
            )
            all_services = list(all_svcs_result.scalars().all())

            # Search history messages for service mentions (by name or by keywords)
            for m in reversed(past_msgs[:-1]):
                if m.direction != "inbound":
                    continue
                hist_text = (m.content or "").lower()
                # Try exact name match first
                for svc in all_services:
                    if svc.name.lower() in hist_text:
                        history_svc = svc
                        break
                # If no exact match, try word-by-word match (e.g. "computer" matches "Laptop Repair" via category/description)
                if not history_svc:
                    for svc in all_services:
                        svc_words = svc.name.lower().split()
                        if any(w in hist_text for w in svc_words if len(w) > 3):
                            history_svc = svc
                            break
                if history_svc:
                    break

            if history_svc:
                products = [history_svc]
            else:
                # No history match - load first 5 services
                products = all_services[:5]

        # If message is just a quantity (e.g. "1 pc", "2 pieces"), load products from history
        qty_match = re_mod.match(r'^(\d+)\s*(pc|piece|pieces|pcs|unit|units|sets?|bottle|bottles|box|boxes|pack|packs)?$', req.message.strip().lower())
        is_address = any(w in req.message.lower() for w in ["road", "street", "lane", "nagar", "colony", "area", "city", "pin", "flat", "house", "apartment", "floor"])
        is_delivery = req.message.strip().lower() in ["delivery", "deliver", "pickup", "pick", "1", "2"]
        is_order_word = any(w in req.message.lower() for w in ["order", "buy", "kharid", "lena hai", "chahiye", "purchase"])

        # Check if message mentions a specific brand/product name that's NOT in inventory
        # If so, don't load from history — customer wants something different
        from models import Product as ProductModel
        all_prod_names = []
        try:
            all_p_result = await db.execute(
                select(ProductModel).where(
                    ProductModel.business_id == req.business_id,
                    ProductModel.is_active == True,
                    ProductModel.item_type != "service",
                )
            )
            all_prod_names = [p.name.lower() for p in all_p_result.scalars().all()]
        except:
            pass

        # Extract meaningful words from message (exclude stop words)
        stop_words = {"mein", "mujhe", "mujha", "muje", "ko", "ka", "ki", "ke", "hai", "chahiye",
                      "karna", "karo", "batao", "do", "ye", "wo", "aur", "ya", "se", "pe", "me",
                      "aap", "main", "hum", "apna", "apne", "iska", "uska", "kya", "kab", "kaise",
                      "nahi", "ho", "raha", "hain", "bhi", "abhi", "kal", "aaj", "wala", "wali",
                      "order", "buy", "purchase", "book"}
        msg_lower = req.message.lower().strip()
        msg_words = [w for w in msg_lower.split() if w not in stop_words and len(w) > 2]

        # Check if any message word looks like a product/brand but doesn't match inventory
        has_unmatched_brand = False
        if msg_words and is_order_word:
            for word in msg_words:
                # If word exists in any product name, it's a match — no problem
                if any(word in pname for pname in all_prod_names):
                    has_unmatched_brand = False
                    break
                # If word looks like a brand/product name (not a common word), flag it
                if len(word) > 2 and word not in ["koi", "sirf", "bas", "jaldi", "abhi"]:
                    has_unmatched_brand = True
                    # Don't break yet — check remaining words too

        if (qty_match or is_address or is_delivery or (is_order_word and not has_unmatched_brand)) and not products:
            from models import Product as ProductModel
            history_prod = None
            # Get all products for this business
            all_prods_result = await db.execute(
                select(ProductModel).where(
                    ProductModel.business_id == req.business_id,
                    ProductModel.is_active == True,
                    ProductModel.item_type != "service",
                )
            )
            all_products = list(all_prods_result.scalars().all())

            hist_msgs = past_msgs[:-1] if len(past_msgs) > 1 else past_msgs
            for m in reversed(hist_msgs):
                if m.direction != "inbound":
                    continue
                hist_text = (m.content or "").lower().replace(" ", "")
                # Exact name match
                for prod in all_products:
                    prod_name = prod.name.lower().replace(" ", "")
                    if prod_name in hist_text:
                        history_prod = prod
                        break
                # Word-by-word match
                if not history_prod:
                    for prod in all_products:
                        prod_words = prod.name.lower().split()
                        hist_lower = (m.content or "").lower()
                        if any(w in hist_lower for w in prod_words if len(w) > 3):
                            history_prod = prod
                            break
                if history_prod:
                    break
            if history_prod:
                products = [history_prod]

        for p in products:
            inventory_context.append({
                "id": p.id,
                "name": p.name,
                "price": p.price,
                "stock": p.stock_quantity,
                "unit": p.unit or "piece",
                "category": p.category or "General",
                "sku": p.sku or "",
                "item_type": p.item_type or "product",
                "duration_minutes": p.duration_minutes or 30,
                "image_url": getattr(p, "image_url", None) or None,
            })
    except Exception as e:
        import traceback
        logger.error("Inventory search error: {}", e)
        traceback.print_exc()

    # 3c. Fetch recent orders for this customer - order status + repeat order
    order_context = []
    try:
        if customer:
            order_result = await db.execute(
                select(Order).where(
                    Order.business_id == req.business_id,
                    Order.customer_id == customer.id,
                ).order_by(desc(Order.created_at)).limit(5)
            )
            for o in order_result.scalars().all():
                order_context.append({
                    "product_name": o.product_name,
                    "quantity": o.quantity,
                    "unit_price": o.unit_price,
                    "total_price": o.total_price,
                    "status": o.status,
                    "delivery_type": o.delivery_type,
                    "created_at": str(o.created_at) if o.created_at else None,
                })
    except Exception as e:
        logger.error("Order fetch error: {}", e)

    # 3d. Fetch available coupons - coupon inquiry
    coupon_context = []
    try:
        coupon_result = await db.execute(
            select(Coupon).where(
                Coupon.business_id == req.business_id,
                Coupon.is_active == True,
            )
        )
        for c in coupon_result.scalars().all():
            coupon_context.append({
                "code": c.code,
                "discount_type": c.discount_type,
                "discount_value": c.discount_value,
                "min_order": c.min_order,
            })
    except Exception as e:
        logger.error("Coupon fetch error: {}", e)

    # 3d. Fetch business name and preferred language from DB
    biz_name = req.business_name or "aapka business"
    biz_language = "hi"  # Default Hindi
    try:
        biz_result = await db.execute(select(Business).where(Business.id == req.business_id))
        biz = biz_result.scalar_one_or_none()
        if biz:
            biz_name = biz.name or biz_name
            biz_language = getattr(biz, "preferred_language", None) or "hi"
    except:
        pass

    # 3e. Load payment settings (UPI ID)
    payment_context = None
    try:
        import os as _os
        settings_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "data", "business_settings.json")
        if _os.path.exists(settings_path):
            with open(settings_path) as _f:
                all_settings = json_mod.loads(_f.read())
                upi_id = all_settings.get("invoice", {}).get("upi_id", "")
                if upi_id and upi_id.strip():
                    payment_context = {"upi_id": upi_id.strip()}
    except:
        pass

    # 3f. Detect customer language for localized responses
    detected_lang = detect_language(req.message)

    # 3g. Load catalog context for product-specific queries
    catalog_context = []
    try:
        catalog_svc = CatalogService(db)
        # Search catalog if message mentions products/categories
        catalog_keywords = ["product", "catalog", "menu", "price list", "dikhao", "show", "available",
                           "stock", "item", "samam", "samaan", "cheez", "kya hai", "kya hai"]
        if any(w in req.message.lower() for w in catalog_keywords):
            catalog_products = await catalog_svc.search_products(req.business_id, req.message, limit=5)
            catalog_context = catalog_products
    except Exception as e:
        logger.debug("Catalog context error: {}", e)

    # 3c. Voice/Image preprocessing — enrich message with context
    reply_text = None
    if req.message_type == "voice" and req.voice_text:
        try:
            from services.falcon_features import get_features
            features = get_features()
            voice_reply = features.process_voice(text=req.voice_text, customer_name=req.customer_name or "Customer")
            # Use voice reply as the AI response, but still save to DB below
            reply_text = voice_reply
        except Exception:
            pass  # Fall through to normal AI

    if req.message_type == "image" and req.image_url:
        try:
            from services.falcon_features import get_features
            features = get_features()
            image_reply = features.process_image(caption=req.message, customer_name=req.customer_name or "Customer", inventory=inventory_context)
            reply_text = image_reply
        except Exception:
            pass  # Fall through to normal AI

    # 4. Get AI reply - FREE AI with conversation history + inventory + order + coupon context
    # Extract last quantity from outbound messages for pickup/delivery flow
    last_qty = None
    try:
        for m in reversed(past_msgs):
            if m.direction == "outbound" and m.content:
                qty_extract = re.search(r'Quantity:\s*(\d+)', m.content)
                if qty_extract:
                    last_qty = int(qty_extract.group(1))
                    break
    except:
        pass

    # Skip AI if reply already set (voice/image preprocessing)
    if not reply_text:
        # ── Plan enforcement: check message quota ──
        try:
            from services.billing_service import BillingService
            bs = BillingService(db=db)
            quota = await bs.check_message_quota(req.business_id)
            if not quota.get("unlimited") and quota.get("remaining", 0) <= 0:
                reply_text = (
                    f"⚠️ Aapka monthly message quota khatam ho gaya hai!\n"
                    f"Plan: {quota.get('tier', 'starter').title()} ({quota.get('limit', 0)} messages)\n"
                    f"Used: {quota.get('used', 0)}\n\n"
                    f"Upgrade karein: Admin panel se Growth/Enterprise plan select karein."
                )
                logger.info("[CHAT] Quota exceeded for business {}", req.business_id[:8])
        except Exception as e:
            logger.debug("[CHAT] Quota check skipped: {}", e)
        # Fetch AI provider settings from DB
        ai_provider_settings = None
        try:
            from routers.settings import get_setting
            ai_provider_settings = await get_setting(db, req.business_id, "ai")
        except Exception:
            pass

        # -- Knowledge Base (RAG): relevant chunks from business docs/FAQ/inventory --
        knowledge_context = None
        try:
            from services.knowledge_base import get_knowledge_base
            kb = get_knowledge_base(db=db)
            knowledge_context = await kb.get_context(req.business_id, req.message, top_k=4)
        except Exception as e:
            logger.debug("[CHAT] knowledge fetch skipped: {}", e)

        # 4a. If ALL matched products are out of stock, skip AI (it gets confused) and use fallback
        all_out_of_stock = inventory_context and all(p["stock"] == 0 for p in inventory_context)
        if all_out_of_stock:
            reply_text = falcon_reply(req.message, req.customer_name or "Customer", inventory_context, order_context, coupon_context, last_qty=last_qty, payment_context=payment_context, session_id=req.session_id, customer_id=customer.id if customer else None, business_name=biz_name, knowledge_context=knowledge_context, language=detected_lang)
        else:
            try:
                # -- Customer long-term memory: facts + recent similar interactions --
                customer_memory = None
                try:
                    if customer:
                        from services.memory_manager import get_memory_manager
                        mm = get_memory_manager()
                        customer_memory = await mm.get_context(customer.id, req.business_id, req.message)
                        if not (customer_memory.get("facts") or customer_memory.get("recent_similar")):
                            customer_memory = None  # don't send empty memory
                except Exception as e:
                    logger.debug("[CHAT] memory fetch skipped: {}", e)

                from services.free_ai import get_ai_reply_free
                reply_text = await get_ai_reply_free(
                    message=req.message,
                    business_name=biz_name,
                    business_type=req.business_type or "general",
                    customer_name=req.customer_name or "Customer",
                    business_id=req.business_id,
                    customer_id=customer.id if customer else None,
                    conversation_history=history_messages,
                    inventory_context=inventory_context if inventory_context else None,
                    last_qty=last_qty,
                    payment_context=payment_context,
                    knowledge_context=knowledge_context,
                    customer_memory=customer_memory,
                    ai_provider_settings=ai_provider_settings,
                    language=detected_lang,
                )
                logger.debug("[CHAT] AI reply OK: {} chars", len(reply_text))

                # 4b. Hallucination check: verify AI reply against actual inventory
                from models import Product as ProductModel
                all_prods_list = []
                try:
                    all_prod_result = await db.execute(
                        select(ProductModel).where(
                            ProductModel.business_id == req.business_id,
                            ProductModel.is_active == True,
                        )
                    )
                    all_prods_list = list(all_prod_result.scalars().all())
                except:
                    pass
                hallucinated = False
                if all_prods_list:
                    reply_lower = reply_text.lower()
                    all_inv_text = " ".join(p.name.lower() for p in all_prods_list)
                    hallucination_words = ["speaker", "headphone", "earphone", "charger", "adapter",
                                           "monitor", "printer", "scanner", "tablet", "iphone",
                                           "smartphone", "washing machine", "refrigerator", "fridge",
                                           "tv", "television", "camera", "hard drive", "bluetooth"]
                    for hw in hallucination_words:
                        if hw in reply_lower and hw not in all_inv_text:
                            hallucinated = True
                            break
                    if not hallucinated:
                        for prod in all_prods_list:
                            pname = prod.name.lower()
                            if pname in reply_lower:
                                price_matches = re_mod.findall(r'(?:rs|₹)\s*[.:,\s]*(\d[\d,]*\.?\d*)', reply_lower)
                                for pm in price_matches:
                                    mentioned = float(pm.replace(',', ''))
                                    if abs(mentioned - float(prod.price)) > 10:
                                        hallucinated = True
                                        break
                                if hallucinated:
                                    break
                if hallucinated:
                    reply_text = falcon_reply(req.message, req.customer_name or "Customer", inventory_context or None, order_context, coupon_context, last_qty=last_qty, payment_context=payment_context, session_id=req.session_id, customer_id=customer.id if customer else None, business_name=biz_name, language=detected_lang, knowledge_context=knowledge_context)
            except Exception as e:
                logger.warning("[CHAT] Free AI failed: {}, using fallback rules", e)
                import traceback; traceback.print_exc()
                reply_text = falcon_reply(req.message, req.customer_name or "Customer", inventory_context, order_context, coupon_context, last_qty=last_qty, payment_context=payment_context, session_id=req.session_id, customer_id=customer.id if customer else None, business_name=biz_name, language=detected_lang, knowledge_context=knowledge_context)

    # 4c. Self-learning: save API response to Falcon trainer
    try:
        from services.falcon_trainer import get_trainer
        from services.falcon_engine import IntentClassifier, EntityExtractor
        trainer = get_trainer()
        ic = IntentClassifier()
        intent, confidence = ic.classify(req.message.lower())
        ee = EntityExtractor()
        entities = ee.extract(req.message, inventory_context)
        product_name = entities.get("product", {}).get("name") if entities.get("product") else None
        trainer.learn(
            query=req.message,
            response=reply_text,
            intent=intent,
            entities=entities,
            product_name=product_name,
            customer_name=req.customer_name or "Customer",
            business_name=biz_name,
            confidence=confidence,
            language=detected_lang,
        )
    except Exception:
        pass  # Learning failure should never break chat

    # 5. Save bot reply
    bot_msg = WhatsAppMessage(
        id=str(uuid.uuid4()),
        business_id=req.business_id,
        customer_id=customer.id if customer else None,
        session_id=req.session_id,
        direction="outbound",
        content=reply_text,
        message_type="text",
        status="sent",
    )
    db.add(bot_msg)

    # 6. Update or create conversation
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.business_id == req.business_id,
            Conversation.session_id == req.session_id,
        )
    )
    conversation = conv_result.scalars().first()
    if not conversation and (customer or req.session_id):
        conversation = Conversation(
            id=str(uuid.uuid4()),
            business_id=req.business_id,
            customer_id=customer.id,
            session_id=req.session_id,
            last_message_preview=reply_text[:200],
            messages_sent=1,
        )
        db.add(conversation)
    elif conversation:
        conversation.last_message_preview = reply_text[:200]
        conversation.messages_sent = (conversation.messages_sent or 0) + 1
        conversation.last_message_at = datetime.now(timezone.utc).replace(tzinfo=None)

    # 7. Update customer last_active
    if customer:
        customer.last_active = datetime.now(timezone.utc).replace(tzinfo=None)

    # 7a. Store interaction in long-term memory (fire-and-forget, errors don't break chat)
    if customer:
        try:
            mm = get_memory_manager()
            await mm.add_interaction(customer.id, req.business_id, req.message, reply_text)
        except Exception as e:
            logger.debug("[CHAT] memory store skipped: {}",e)

    # 7a2. Update structured customer memory (preferences, language, etc.)
    if customer:
        try:
            from services.customer_memory import get_customer_memory
            cm = get_customer_memory()
            await cm.learn_from_chat(req.business_id, customer.id, req.message, reply_text, db)
        except Exception as e:
            logger.debug("[CHAT] customer_memory learn skipped: {}", e)

    # 7b. Save booking if AI confirmed one
    # Match both exact Falcon format AND natural language AI booking confirmations
    booking_confirmed = (
        reply_text.startswith("✅ Booking confirmed")
        or ("book" in reply_text.lower() and ("confirm" in reply_text.lower() or "kar diya" in reply_text.lower() or "ho gaya" in reply_text.lower()))
        or ("appointment" in reply_text.lower() and ("confirm" in reply_text.lower() or "book kar" in reply_text.lower()))
    )
    if booking_confirmed:
        try:
            from services.free_ai import extract_date_time
            date_val, time_val = extract_date_time(req.message)
            svc_name = ""
            svc_price = 0
            # Try exact format first (Falcon engine responses)
            for line in reply_text.split("\n"):
                if "Service:" in line:
                    svc_name = line.split("Service:")[-1].strip()
                if "Price:" in line or "💰" in line:
                    price_match = re_mod.search(r'₹([\d,.]+)', line)
                    if price_match:
                        svc_price = float(price_match.group(1).replace(",", ""))
            # Fallback: find service name from inventory context
            if not svc_name and inventory_context:
                # Try matching service names in the reply text
                for p in inventory_context:
                    if p.get("item_type") == "service" and p["name"].lower() in reply_text.lower():
                        svc_name = p["name"]
                        svc_price = p["price"]
                        break
                # Try matching service names in the customer message
                if not svc_name:
                    for p in inventory_context:
                        if p.get("item_type") == "service":
                            words = [w for w in p["name"].lower().split() if len(w) > 2]
                            if any(w in req.message.lower() for w in words):
                                svc_name = p["name"]
                                svc_price = p["price"]
                                break
            if not date_val:
                date_val = datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d")
            if not time_val:
                time_val = datetime.now(timezone.utc).replace(tzinfo=None).strftime("%H:%M")
            if svc_name:
                booking = Booking(
                    id=f"BOOK-{uuid.uuid4().hex[:8].upper()}",
                    business_id=req.business_id,
                    customer_id=customer.id if customer else None,
                    service_name=svc_name,
                    customer_name=req.customer_name or "Customer",
                    customer_phone=req.customer_phone or "",
                    booking_date=date_val,
                    booking_time=time_val,
                    duration_minutes=30,
                    price=svc_price,
                    status="confirmed",
                )
                db.add(booking)
                logger.info("[BOOKING SAVED] {} for {} on {} {}", svc_name, req.customer_name, date_val, time_val)
        except Exception as e:
            logger.error("Booking save error: {}", e)

    # 7c. Save order if AI confirmed one
    order_confirmed = (
        reply_text.startswith("✅ Order confirmed")
        or reply_text.startswith("✅ Pickup order confirmed")
        or reply_text.startswith("✅ Delivery order confirmed")
        or ("order" in reply_text.lower() and ("confirm" in reply_text.lower() or "ho gaya" in reply_text.lower() or "kar diya" in reply_text.lower()))
    )
    if order_confirmed:
        try:
            prod_name = ""
            prod_qty = 1
            prod_total = 0
            delivery_type = "pickup"
            # Try exact format first (Falcon engine responses)
            for line in reply_text.split("\n"):
                if "Product:" in line or "📦 Product:" in line:
                    prod_name = line.split("Product:")[-1].strip()
                if "Quantity:" in line or "🔢 Quantity:" in line:
                    qty_match = re_mod.search(r'(\d+)', line)
                    if qty_match:
                        prod_qty = int(qty_match.group(1))
                if "Total:" in line or "💰 Total:" in line:
                    price_match = re_mod.search(r'₹([\d,.]+)', line)
                    if price_match:
                        prod_total = float(price_match.group(1).replace(",", ""))
                if "Delivery" in line:
                    delivery_type = "delivery"
                if "Pickup" in line or "pickup" in line:
                    delivery_type = "pickup"
            # Fallback: find product name from inventory context or customer message
            if not prod_name and inventory_context:
                for p in inventory_context:
                    if p.get("item_type") != "service" and p["name"].lower() in reply_text.lower():
                        prod_name = p["name"]
                        if prod_total == 0:
                            prod_total = p["price"]
                        break
                if not prod_name:
                    for p in inventory_context:
                        if p.get("item_type") != "service":
                            words = [w for w in p["name"].lower().split() if len(w) > 2]
                            if any(w in req.message.lower() for w in words):
                                prod_name = p["name"]
                                if prod_total == 0:
                                    prod_total = p["price"]
                                break
            # Find product_id from inventory
            prod_id = None
            if prod_name:
                from models import Product as ProductModel
                try:
                    p_result = await db.execute(
                        select(ProductModel).where(
                            ProductModel.business_id == req.business_id,
                            ProductModel.name.ilike(f"%{prod_name}%"),
                        )
                    )
                    prod_obj = p_result.scalar_one_or_none()
                    if prod_obj:
                        prod_id = prod_obj.id
                        if prod_total == 0:
                            prod_total = prod_obj.price * prod_qty
                except:
                    pass
            if prod_name:
                order = Order(
                    id=str(uuid.uuid4()),
                    business_id=req.business_id,
                    customer_id=customer.id if customer else None,
                    customer_name=req.customer_name or "Customer",
                    customer_phone=req.customer_phone or "",
                    product_id=prod_id,
                    product_name=prod_name,
                    quantity=prod_qty,
                    unit_price=prod_total / prod_qty if prod_qty > 0 else 0,
                    total_price=prod_total,
                    delivery_type=delivery_type,
                    status="confirmed" if "Pickup" in reply_text else "pending",
                )
                db.add(order)

                # Also create a Transaction record for analytics/financial tracking
                txn = Transaction(
                    id=str(uuid.uuid4()),
                    business_id=req.business_id,
                    customer_id=customer.id if customer else None,
                    amount=prod_total,
                    type="sale",
                    status="completed" if "Pickup" in reply_text else "pending",
                    payment_method="cash",
                    reference=order.id,
                    notes=f"Chat order: {prod_name} x{prod_qty}",
                )
                db.add(txn)
                logger.info("[ORDER SAVED] {} x{} = {} ({})", prod_name, prod_qty, prod_total, delivery_type)

                # Update customer memory (order history, total spent, tier)
                if customer:
                    try:
                        from services.customer_memory import get_customer_memory
                        cm = get_customer_memory()
                        await cm.after_order_placed(
                            business_id=req.business_id,
                            customer_id=customer.id,
                            order_id=order.id,
                            product_name=prod_name,
                            amount=prod_total,
                            db=db,
                        )
                    except Exception as e:
                        logger.debug("[CHAT] customer_memory order update skipped: {}", e)

                # Loyalty points (DB-backed — survives restart) + follow-up scheduling
                try:
                    from services.loyalty_manager import LoyaltyManager
                    if customer:
                        lm = LoyaltyManager(db)
                        await lm.earn_points(customer.id, prod_total, transaction_id=txn.id)
                    from services.falcon_features import get_features
                    features = get_features()
                    features.schedule_followup(
                        customer_name=req.customer_name or "Customer",
                        customer_phone=req.customer_phone or "",
                        followup_type="order_placed",
                        business_id=req.business_id,
                    )
                    features.reports.record_order(prod_name, prod_total, req.customer_name or "Customer")
                except Exception:
                    pass  # Feature failure should never break order

        except Exception as e:
            logger.error("Order save error: {}", e)

    await db.commit()

    return ChatResponse(
        reply=reply_text,
        session_id=req.session_id,
        customer_id=customer.id if customer else None,
    )


@router.get("/chat/sessions/{business_id}")
async def get_chat_sessions(business_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Business ke saare chat sessions dikhao."""
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    result = await db.execute(
        select(Conversation).where(
            Conversation.business_id == business_id,
        ).order_by(desc(Conversation.updated_at)).limit(50)
    )
    sessions = result.scalars().all()

    return {
        "sessions": [
            {
                "id": s.id,
                "customer_id": s.customer_id,
                "last_message": s.last_message_preview,
                "status": s.status.value if s.status else "open",
                "created_at": str(s.created_at) if s.created_at else None,
                "updated_at": str(s.updated_at) if s.updated_at else None,
            }
            for s in sessions
        ]
    }


@router.get("/chat/qr/{business_id}")
async def generate_qr_data(business_id: str):
    """QR code ke liye data return karo."""
    # Web chat UI lives on the frontend (port 3001), not OmniRoute (3000)
    chat_url = f"http://localhost:3001/chat?business={business_id}"
    return {
        "business_id": business_id,
        "chat_url": chat_url,
        "instructions": "Is URL ka QR code banao ya seedha link share karo.",
    }


class ReplyRequest(BaseModel):
    conversation_id: str
    message: str
    business_id: str


@router.post("/chat/reply")
async def admin_reply(req: ReplyRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Admin manually reply bhejta hai customer ko — WhatsApp pe bhi bhejta hai."""
    if not await verify_business_access(current_user, req.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")

    # Fetch conversation to get customer_id
    conv_result = await db.execute(select(Conversation).where(Conversation.id == req.conversation_id))
    conversation = conv_result.scalar_one_or_none()

    # Get customer phone number for WhatsApp delivery
    phone_number = None
    if conversation and conversation.customer_id:
        cust_result = await db.execute(select(Customer).where(Customer.id == conversation.customer_id))
        customer = cust_result.scalar_one_or_none()
        if customer:
            phone_number = customer.phone_number

    # Save outbound message to DB
    bot_msg = WhatsAppMessage(
        id=str(uuid.uuid4()),
        business_id=req.business_id,
        customer_id=conversation.customer_id if conversation else None,
        session_id=req.session_id if hasattr(req, 'session_id') else None,
        direction="outbound",
        content=req.message,
        message_type="text",
        status="pending",
    )
    db.add(bot_msg)

    if conversation:
        conversation.last_message_preview = req.message[:200]
        conversation.last_message_at = datetime.now(timezone.utc).replace(tzinfo=None)
        conversation.messages_sent = (conversation.messages_sent or 0) + 1

    await db.commit()

    # Actually send via WhatsApp bot
    if phone_number:
        try:
            send_data = json_mod.dumps({"phone": phone_number, "message": req.message}).encode()
            send_req = urllib.request.Request(
                f"{BOT_URL}/send",
                data=send_data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(send_req, timeout=10)
            bot_msg.status = "sent"
            await db.commit()
            logger.info("[ADMIN REPLY] Sent to {}: {}...", phone_number, req.message[:50])
        except Exception as e:
            bot_msg.status = "failed"
            await db.commit()
            logger.error("[ADMIN REPLY] Failed to send to {}: {}", phone_number, e)
    else:
        logger.info("[ADMIN REPLY] No phone number — saved to DB only")

    return {"status": "sent", "message_id": bot_msg.id}


@router.get("/chat/conversations/{business_id}")
async def get_all_conversations(business_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Business ke saare conversations - admin inbox ke liye."""
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.business_id == business_id,
        ).order_by(desc(Conversation.last_message_at)).limit(50)
    )
    conversations = conv_result.scalars().all()

    items = []
    for conv in conversations:
        cust_result = await db.execute(select(Customer).where(Customer.id == conv.customer_id))
        customer = cust_result.scalar_one_or_none()

        msg_result = await db.execute(
            select(WhatsAppMessage).where(
                WhatsAppMessage.customer_id == conv.customer_id,
                WhatsAppMessage.business_id == business_id,
            ).order_by(desc(WhatsAppMessage.created_at)).limit(1)
        )
        last_msg = msg_result.scalar_one_or_none()

        items.append({
            "id": conv.id,
            "customer_id": conv.customer_id,
            "customer_name": customer.name if customer else "Unknown",
            "customer_phone": customer.phone_number if customer else "",
            "channel": "whatsapp",
            "status": conv.status.value if conv.status else "open",
            "last_message": last_msg.content if last_msg else (conv.last_message_preview or ""),
            "last_direction": last_msg.direction if last_msg else "",
            "last_message_at": str(conv.last_message_at) if conv.last_message_at else None,
        })

    return {"conversations": items}


@router.get("/chat/messages/{conversation_id}")
async def get_conversation_messages(conversation_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Ek conversation ke saare messages - admin inbox ke liye."""

    # Conversation se customer_id nikalo
    conv_result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conversation = conv_result.scalar_one_or_none()
    if not conversation:
        return {"messages": []}
    if not await verify_business_access(current_user, conversation.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(
        select(WhatsAppMessage).where(
            WhatsAppMessage.customer_id == conversation.customer_id,
            WhatsAppMessage.business_id == conversation.business_id,
        ).order_by(WhatsAppMessage.created_at.asc()).limit(100)
    )
    messages = result.scalars().all()

    return {
        "messages": [
            {
                "id": m.id,
                "direction": m.direction,
                "content": m.content,
                "message_type": m.message_type.value if m.message_type else "text",
                "timestamp": str(m.created_at) if m.created_at else None,
            }
            for m in messages
        ],
    }


@router.delete("/chat/messages/{conversation_id}")
async def clear_conversation_messages(conversation_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Conversation ke saare messages delete kar do."""
    conv_result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conversation = conv_result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation nahi mili")
    if not await verify_business_access(current_user, conversation.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")

    msg_result = await db.execute(
        select(WhatsAppMessage).where(
            WhatsAppMessage.customer_id == conversation.customer_id,
            WhatsAppMessage.business_id == conversation.business_id,
        )
    )
    messages = msg_result.scalars().all()
    count = len(messages)
    for msg in messages:
        await db.delete(msg)

    conversation.last_message_preview = None
    conversation.messages_sent = 0
    await db.commit()

    return {"status": "cleared", "deleted_count": count}


@router.delete("/chat/conversation/{conversation_id}")
async def delete_conversation(conversation_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Poora conversation delete kar do — messages + conversation record."""
    conv_result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conversation = conv_result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation nahi mili")
    if not await verify_business_access(current_user, conversation.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")

    msg_result = await db.execute(
        select(WhatsAppMessage).where(
            WhatsAppMessage.customer_id == conversation.customer_id,
            WhatsAppMessage.business_id == conversation.business_id,
        )
    )
    messages = msg_result.scalars().all()
    for msg in messages:
        await db.delete(msg)

    await db.delete(conversation)
    await db.commit()

    return {"status": "deleted"}


# ─────────────────────────────────────────────────────
# ORDER / BUY FLOW - Customer bole "buy karna hai"
# ─────────────────────────────────────────────────────

class BuyRequest(BaseModel):
    product_id: str
    quantity: int = 1
    business_id: str
    customer_phone: str
    customer_name: Optional[str] = "Customer"
    delivery_address: Optional[str] = None


@router.post("/chat/buy")
async def buy_product(req: BuyRequest, db: AsyncSession = Depends(get_db)):
    """Customer product buy karta hai - order + payment link generate hota hai."""

    # 1. Customer dhundho
    cust_result = await db.execute(
        select(Customer).where(
            Customer.phone_number == req.customer_phone,
            Customer.business_id == req.business_id,
        )
    )
    customer = cust_result.scalar_one_or_none()
    if not customer:
        return {"error": "Customer nahi mila - pehle chat karo usse"}

    # 2. Order banao - SAFE version (retry + atomic stock)
    order_mgr = OrderManager(db)
    order = await order_mgr.create_order_safe(
        business_id=req.business_id,
        customer_id=customer.id,
        product_id=req.product_id,
        quantity=req.quantity,
        delivery_address=req.delivery_address,
    )

    if "error" in order:
        return order

    # 3. Confirmation message bhejo customer ko
    confirmation_msg = (
        f"🎉 Order confirm ho gaya!\n\n"
        f"📦 Product: {order['product_name']}\n"
        f"🔢 Quantity: {order['quantity']}\n"
        f"💰 Total: ₹{order['total_amount']}\n\n"
        f"💳 Payment karo is link pe:\n{order['upi_link']}\n\n"
        f"Payment ke baad order process ho jayega!"
    )

    # 4. Message save karo
    bot_msg = WhatsAppMessage(
        id=str(uuid.uuid4()),
        business_id=req.business_id,
        customer_id=customer.id,
        direction="outbound",
        content=confirmation_msg,
        message_type="text",
        status="sent",
    )
    db.add(bot_msg)

    # 5. Conversation update karo
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.business_id == req.business_id,
            Conversation.customer_id == customer.id,
        )
    )
    conversation = conv_result.scalars().first()
    if conversation:
        conversation.last_message_preview = confirmation_msg[:200]
        conversation.last_message_at = datetime.now(timezone.utc).replace(tzinfo=None)
        conversation.messages_sent = (conversation.messages_sent or 0) + 1

    await db.commit()

    return {
        "status": "order_created",
        "order_id": order["order_id"],
        "product_name": order["product_name"],
        "quantity": order["quantity"],
        "total_amount": order["total_amount"],
        "upi_link": order["upi_link"],
        "stock_remaining": order["stock_remaining"],
        "confirmation_message": confirmation_msg,
    }


class ConfirmPaymentRequest(BaseModel):
    payment_id: str


@router.post("/chat/confirm-payment")
async def confirm_payment(req: ConfirmPaymentRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Payment confirm karo - authenticated users only."""
    pay_result = await db.execute(select(Payment).where(Payment.id == req.payment_id))
    payment = pay_result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment nahi mila")
    if not await verify_business_access(current_user, payment.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    order_mgr = OrderManager(db)
    result = await order_mgr.confirm_payment(req.payment_id)
    return result


@router.get("/chat/order/{order_id}")
async def get_order(order_id: str, db: AsyncSession = Depends(get_db)):
    """Order status check karo."""
    order_mgr = OrderManager(db)
    return await order_mgr.get_order_status(order_id)


@router.post("/chat/cancel-order")
async def cancel_order(data: ConfirmPaymentRequest, db: AsyncSession = Depends(get_db)):
    """Order cancel karo - stock wapas aa jayega."""
    order_mgr = OrderManager(db)
    return await order_mgr.cancel_order(data.payment_id)


# ─────────────────────────────────────────────────────
# BOOKING FLOW - Service book karna hai
# ─────────────────────────────────────────────────────

class BookServiceRequest(BaseModel):
    service_id: str
    business_id: str
    customer_phone: str
    customer_name: Optional[str] = "Customer"
    booking_date: str
    booking_time: str
    duration_minutes: int = 30
    notes: Optional[str] = None
    price: float = 0


@router.post("/chat/book")
async def book_service(req: BookServiceRequest, db: AsyncSession = Depends(get_db)):
    """Service booking create karo."""
    booking_id = f"BOOK-{uuid.uuid4().hex[:8].upper()}"

    # Resolve the real service name from the product catalog instead of
    # storing the raw service_id as the display name.
    from models import Product as ProductModel
    service_name = req.service_id
    try:
        prod = await db.execute(
            select(ProductModel).where(
                ProductModel.id == req.service_id,
                ProductModel.business_id == req.business_id,
            )
        )
        product = prod.scalar_one_or_none()
        if product:
            service_name = product.name
    except Exception:
        pass  # Fall back to service_id if lookup fails

    booking = Booking(
        id=booking_id,
        business_id=req.business_id,
        service_id=req.service_id,
        service_name=service_name,
        customer_name=req.customer_name,
        customer_phone=req.customer_phone,
        booking_date=req.booking_date,
        booking_time=req.booking_time,
        duration_minutes=req.duration_minutes,
        notes=req.notes,
        price=req.price,
    )
    db.add(booking)
    await db.commit()

    return {
        "status": "booked",
        "booking_id": booking_id,
        "service": service_name,
        "date": req.booking_date,
        "time": req.booking_time,
        "duration": f"{req.duration_minutes} min",
        "price": req.price,
    }


# ─── FALCON SELF-LEARNING FEEDBACK ─────────────────────────

class FeedbackRequest(BaseModel):
    query: str
    intent: Optional[str] = ""
    positive: bool = True


@router.post("/chat/feedback")
async def falcon_feedback(req: FeedbackRequest):
    """Falcon ko feedback do — reply accha tha ya bura."""
    try:
        from services.falcon_trainer import get_trainer
        trainer = get_trainer()
        trainer.feedback(req.query, req.intent, req.positive)
        stats = trainer.get_stats()
        return {"status": "ok", "message": "Feedback recorded!", "stats": stats}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/chat/falcon-stats")
async def falcon_stats():
    """Falcon training statistics dekho."""
    try:
        from services.falcon_trainer import get_trainer
        trainer = get_trainer()
        return trainer.get_stats()
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ─── FALCON FEATURES ENDPOINTS ─────────────────────────────

@router.get("/chat/loyalty/{customer_id}")
async def get_loyalty_status(customer_id: str, customer_name: str = "Customer"):
    """Customer ka loyalty status dekho."""
    try:
        from services.falcon_features import get_features
        features = get_features()
        return {"status": "ok", "loyalty": features.get_loyalty_status(customer_id, customer_name)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/chat/appointments/available/{date}")
async def get_available_slots(date: str):
    """Available appointment slots dekho."""
    try:
        from services.falcon_features import get_features
        features = get_features()
        slots = features.get_available_slots(date)
        return {"status": "ok", "date": date, "available_slots": slots}
    except Exception as e:
        return {"status": "error", "message": str(e)}


class BookAppointmentRequest(BaseModel):
    customer_name: str
    customer_phone: str
    service: str
    date: str
    time: str
    price: float = 0
    duration: int = 30


@router.post("/chat/appointments/book")
async def book_appointment(req: BookAppointmentRequest):
    """Appointment book karo."""
    try:
        from services.falcon_features import get_features
        features = get_features()
        result = features.book_appointment(
            req.customer_name, req.customer_phone, req.service,
            req.date, req.time, req.price, req.duration
        )
        if "error" in result:
            return result
        return {
            "status": "booked",
            "appointment": result,
            "message": features.calendar.get_appointment_message(result),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/chat/reports/daily")
async def daily_report(business_name: str = "Business"):
    """Daily business report generate karo."""
    try:
        from services.falcon_features import get_features
        features = get_features()
        report = features.generate_report(business_name, "daily")
        return {"status": "ok", "report": report}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/chat/reports/weekly")
async def weekly_report(business_name: str = "Business"):
    """Weekly business report generate karo."""
    try:
        from services.falcon_features import get_features
        features = get_features()
        report = features.generate_report(business_name, "weekly")
        return {"status": "ok", "report": report}
    except Exception as e:
        return {"status": "error", "message": str(e)}


class BroadcastRequest(BaseModel):
    name: str
    message: str
    target_customers: list
    business_id: Optional[str] = None


@router.post("/chat/broadcast")
async def create_broadcast(req: BroadcastRequest):
    """Broadcast campaign create karo."""
    try:
        from services.falcon_features import get_features
        features = get_features()
        campaign = features.create_broadcast(
            req.name, req.message, req.target_customers, req.business_id
        )
        return {"status": "created", "campaign": campaign}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/chat/promotional/{offer_type}")
async def get_promotional_message(offer_type: str, discount: int = 10):
    """Promotional message generate karo."""
    try:
        from services.falcon_features import get_features
        features = get_features()
        message = features.get_promotional_message(offer_type, discount)
        return {"status": "ok", "message": message}
    except Exception as e:
        return {"status": "error", "message": str(e)}
