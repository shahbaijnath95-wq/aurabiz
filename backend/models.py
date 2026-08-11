from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey,
    Enum as SAEnum, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum
import uuid


def generate_uuid():
    return str(uuid.uuid4())


class UserRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    STAFF = "staff"
    VIEWER = "viewer"
    SUPER_ADMIN = "super_admin"


class TransactionType(str, enum.Enum):
    SALE = "sale"
    REFUND = "refund"
    SUBSCRIPTION = "subscription"
    LOYALTY = "loyalty"
    OTHER = "other"


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class MessageDirection(str, enum.Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class MessageType(str, enum.Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    LOCATION = "location"
    STICKER = "sticker"
    TEMPLATE = "template"
    INTERACTIVE = "interactive"


class ConversationStatus(str, enum.Enum):
    OPEN = "open"
    WAITING = "waiting"
    CLOSED = "closed"
    ESCALATED = "escalated"


class SubscriptionTier(str, enum.Enum):
    STARTER = "starter"
    GROWTH = "growth"
    ENTERPRISE = "enterprise"


class LifecycleStage(str, enum.Enum):
    LEAD = "lead"
    PROSPECT = "prospect"
    ACTIVE = "active"
    RETENTION = "retention"
    LOYAL = "loyal"
    CHURNED = "churned"


class TemplateStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class WebhookEventType(str, enum.Enum):
    MESSAGE_RECEIVED = "message.received"
    MESSAGE_SENT = "message.sent"
    TRANSACTION_CREATED = "transaction.created"
    CUSTOMER_CREATED = "customer.created"
    ORDER_UPDATED = "order.updated"
    PAYMENT_RECEIVED = "payment.received"
    REVIEW_RECEIVED = "review.received"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=True, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="INR")
    payment_method = Column(String(50), nullable=True)
    payment_type = Column(String(50), nullable=True)
    status = Column(String(50), default="pending")  # pending, completed, failed
    reference = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    is_recurring = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    business = relationship("Business", back_populates="payments")
    customer = relationship("Customer", back_populates="payments")
    interactions = relationship("CustomerInteraction", back_populates="payment", cascade="all, delete-orphan")


class CustomerInteraction(Base):
    __tablename__ = "customer_interactions"

    id = Column(String, primary_key=True, default=generate_uuid)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False, index=True)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    payment_id = Column(String, ForeignKey("payments.id"), nullable=True, index=True)
    amount = Column(Float, default=0.0)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    type = Column(String(50), nullable=False)  # qr_payment, manual_payment, etc.

    customer = relationship("Customer", back_populates="interactions")
    business = relationship("Business", back_populates="interactions")
    payment = relationship("Payment", back_populates="interactions")


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), default=UserRole.OWNER)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    reset_token = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    businesses = relationship("Business", back_populates="user", cascade="all, delete-orphan")


class Business(Base):
    __tablename__ = "businesses"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(100), nullable=True)
    phone_number = Column(String(20), nullable=True)
    whatsapp_phone_id = Column(String(100), nullable=True)
    currency = Column(String(10), default="INR")
    timezone = Column(String(50), default="Asia/Kolkata")
    locale = Column(String(10), default="hi")
    preferred_language = Column(String(10), default="mr")
    brand_voice = Column(Text, nullable=True)
    subscription_tier = Column(SAEnum(SubscriptionTier), default=SubscriptionTier.STARTER)
    subscription_status = Column(String(50), default="active")
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    onboarding_completed = Column(Boolean, default=False)
    onboarded_at = Column(DateTime(timezone=True), nullable=True)
    default_delay_ms = Column(Integer, default=3000)
    max_products = Column(Integer, default=100)
    custom_fields = Column(JSON, default=dict)
    logo_url = Column(String(500), nullable=True)
    address = Column(Text, nullable=True)
    website = Column(String(500), nullable=True)
    email = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="businesses")
    customers = relationship("Customer", back_populates="business", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="business", cascade="all, delete-orphan")
    whatsapp_messages = relationship("WhatsAppMessage", back_populates="business", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="business", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="business", cascade="all, delete-orphan")
    integrations = relationship("Integration", back_populates="business", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="business", cascade="all, delete-orphan")
    webhook_subscriptions = relationship("WebhookSubscription", back_populates="business", cascade="all, delete-orphan")
    scheduled_messages = relationship("ScheduledMessage", back_populates="business", cascade="all, delete-orphan")
    conversation_contexts = relationship("ConversationContext", back_populates="business", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="business", cascade="all, delete-orphan")
    loyalty_programs = relationship("LoyaltyProgram", back_populates="business", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="business", cascade="all, delete-orphan")
    whatsapp_templates = relationship("WhatsAppTemplate", back_populates="business", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="business", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="business", cascade="all, delete-orphan")
    interactions = relationship("CustomerInteraction", back_populates="business", cascade="all, delete-orphan")
    coupons = relationship("Coupon", back_populates="business", cascade="all, delete-orphan")
    cart_items = relationship("CartItem", back_populates="business", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="business", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="business", cascade="all, delete-orphan")
    broadcasts = relationship("Broadcast", back_populates="business", cascade="all, delete-orphan")
    settings = relationship("BusinessSettings", back_populates="business", cascade="all, delete-orphan")
    teams = relationship("Team", back_populates="business", cascade="all, delete-orphan")
    inventory_alerts = relationship("InventoryAlert", back_populates="business", cascade="all, delete-orphan")
    follow_ups = relationship("FollowUp", back_populates="business", cascade="all, delete-orphan")
    segments = relationship("Segment", back_populates="business", cascade="all, delete-orphan")
    export_jobs = relationship("ExportJob", back_populates="business", cascade="all, delete-orphan")
    knowledge_documents = relationship("KnowledgeDocument", back_populates="business", cascade="all, delete-orphan")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    phone_number = Column(String(20), nullable=False, index=True)
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    tags = Column(JSON, default=list)
    lifecycle_stage = Column(SAEnum(LifecycleStage), default=LifecycleStage.LEAD)
    engagement_score = Column(Float, default=0.0)
    preferred_language = Column(String(10), default="hi")
    total_orders = Column(Integer, default=0)
    total_spent = Column(Float, default=0.0)
    loyalty_points = Column(Integer, default=0)
    last_active = Column(DateTime(timezone=True), nullable=True)
    is_wholesaler = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    business = relationship("Business", back_populates="customers")
    transactions = relationship("Transaction", back_populates="customer", cascade="all, delete-orphan")
    whatsapp_messages = relationship("WhatsAppMessage", back_populates="customer", cascade="all, delete-orphan")
    loyalty_points_records = relationship("LoyaltyPoints", back_populates="customer", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="customer", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="customer", cascade="all, delete-orphan")
    conversation_contexts = relationship("ConversationContext", back_populates="customer", cascade="all, delete-orphan")
    scheduled_messages = relationship("ScheduledMessage", back_populates="customer", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="customer", cascade="all, delete-orphan")
    interactions = relationship("CustomerInteraction", back_populates="customer", cascade="all, delete-orphan")
    cart_items = relationship("CartItem", back_populates="customer", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="customer", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="customer", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_customers_business_phone", "business_id", "phone_number", unique=True),
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=True, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="INR")
    type = Column(SAEnum(TransactionType), default=TransactionType.SALE)
    status = Column(SAEnum(TransactionStatus), default=TransactionStatus.PENDING)
    items = Column(JSON, default=list)
    payment_method = Column(String(50), nullable=True)
    reference = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    is_recurring = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    business = relationship("Business", back_populates="transactions")
    customer = relationship("Customer", back_populates="transactions")


class LoyaltyPoints(Base):
    __tablename__ = "loyalty_points"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False, index=True)
    points = Column(Integer, nullable=False)
    balance = Column(Integer, nullable=False)
    type = Column(String(50), nullable=False)  # earn, redeem, expire, adjust
    reference_id = Column(String, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    customer = relationship("Customer", back_populates="loyalty_points_records")


class LoyaltyProgram(Base):
    __tablename__ = "loyalty_programs"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), default="points")  # points, cashback, tier
    points_per_currency = Column(Float, default=1.0)
    tier_thresholds = Column(JSON, default={"bronze": 0, "silver": 1000, "gold": 5000, "platinum": 20000})
    reward_rules = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    business = relationship("Business", back_populates="loyalty_programs")


class WhatsAppMessage(Base):
    __tablename__ = "whatsapp_messages"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=True, index=True)
    session_id = Column(String(255), nullable=True, index=True)
    message_id = Column(String(255), nullable=True, unique=True)
    direction = Column(SAEnum(MessageDirection), nullable=False)
    content = Column(Text, nullable=True)
    message_type = Column(SAEnum(MessageType), default=MessageType.TEXT)
    status = Column(String(50), default="sent")  # sent, delivered, read, failed
    media_id = Column(String(255), nullable=True)
    media_url = Column(String(500), nullable=True)
    template_name = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    business = relationship("Business", back_populates="whatsapp_messages")
    customer = relationship("Customer", back_populates="whatsapp_messages")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=True, index=True)
    session_id = Column(String(255), nullable=True, index=True)
    status = Column(SAEnum(ConversationStatus), default=ConversationStatus.OPEN)
    last_message_at = Column(DateTime(timezone=True), server_default=func.now())
    last_message_preview = Column(Text, nullable=True)
    messages_sent = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    business = relationship("Business", back_populates="conversations")
    customer = relationship("Customer", back_populates="conversations")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String, nullable=True)
    changes = Column(JSON, default=dict)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    business = relationship("Business", back_populates="audit_logs")


class Integration(Base):
    __tablename__ = "integrations"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    type = Column(String(50), nullable=False)  # google_business, instagram, razorpay, phonepe, tally
    status = Column(String(50), default="disconnected")  # connected, disconnected, error
    config = Column(JSON, default=dict)
    credentials = Column(JSON, default=dict)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    business = relationship("Business", back_populates="integrations")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=True, index=True)
    number = Column(String(50), nullable=False, unique=True)
    status = Column(String(50), default="draft")  # draft, sent, paid, overdue, cancelled
    subtotal = Column(Float, default=0.0)
    tax = Column(Float, default=0.0)
    total = Column(Float, nullable=False)
    items = Column(JSON, default=list)
    due_at = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    business = relationship("Business", back_populates="invoices")
    customer = relationship("Customer", back_populates="invoices")


class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    sku = Column(String(100), nullable=True)
    price = Column(Float, nullable=False)
    wholesale_price = Column(Float, nullable=True)
    cost_price = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    stock_quantity = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    image_url = Column(String(500), nullable=True)
    unit = Column(String(20), default="piece")
    min_stock = Column(Integer, default=10)
    item_type = Column(String(20), default="product")  # "product" or "service"
    duration_minutes = Column(Integer, nullable=True)
    # Advanced fields
    brand = Column(String(150), nullable=True)
    model = Column(String(150), nullable=True)
    warranty = Column(String(100), nullable=True)  # e.g. "1 year", "6 months", "No warranty"
    hsn_code = Column(String(20), nullable=True)  # HSN for GST
    gst_rate = Column(Float, default=0.0)  # GST percentage
    tags = Column(JSON, default=list)  # ["gaming", "wireless", "bestseller"]
    specs = Column(JSON, default=dict)  # {"weight": "200g", "color": "Black", "warranty": "1 year"}
    gallery = Column(JSON, default=list)  # multiple image URLs
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    business = relationship("Business", back_populates="products")


class KnowledgeDocument(Base):
    """
    Knowledge Base (RAG) documents — business-specific knowledge jo bot seekhta hai.
    Sources: uploaded files (PDF/Word/Excel/TXT), manual text/FAQ, ya auto-ingested inventory.
    Actual chunks + embeddings vector store (Qdrant) me hote hain;
    yeh table sirf metadata + full content (for re-index) rakhta hai.
    """
    __tablename__ = "knowledge_documents"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)           # full text (re-index ke liye)
    doc_type = Column(String(30), default="manual")  # file | manual | inventory
    source = Column(String(500), nullable=True)      # filename | "manual" | "inventory"
    file_path = Column(String(500), nullable=True)   # saved file path (for file docs)
    chunk_count = Column(Integer, default=0)
    mime_type = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    business = relationship("Business", back_populates="knowledge_documents")


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True)
    key_prefix = Column(String(10), nullable=False)
    permissions = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    business = relationship("Business", back_populates="api_keys")


class WebhookSubscription(Base):
    __tablename__ = "webhook_subscriptions"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    url = Column(String(500), nullable=False)
    events = Column(JSON, default=list)
    secret = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    failure_count = Column(Integer, default=0)
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    business = relationship("Business", back_populates="webhook_subscriptions")


class ScheduledMessage(Base):
    __tablename__ = "scheduled_messages"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=True, index=True)
    content = Column(Text, nullable=False)
    message_type = Column(String(50), default="text")
    template_name = Column(String(255), nullable=True)
    template_vars = Column(JSON, default=dict)
    scheduled_for = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(50), default="pending")  # pending, sent, failed, cancelled
    sent_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    business = relationship("Business", back_populates="scheduled_messages")
    customer = relationship("Customer", back_populates="scheduled_messages")


class ConversationContext(Base):
    __tablename__ = "conversation_contexts"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False, index=True)
    context_data = Column(JSON, default=dict)
    model_used = Column(String(100), nullable=True)
    confidence_score = Column(Float, default=0.0)
    last_interaction_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    business = relationship("Business", back_populates="conversation_contexts")
    customer = relationship("Customer", back_populates="conversation_contexts")


class WhatsAppTemplate(Base):
    __tablename__ = "whatsapp_templates"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    language = Column(String(10), default="hi")
    status = Column(SAEnum(TemplateStatus), default=TemplateStatus.DRAFT)
    header = Column(Text, nullable=True)
    body = Column(Text, nullable=False)
    footer = Column(Text, nullable=True)
    buttons = Column(JSON, default=list)
    variables = Column(JSON, default=list)
    meta_template_id = Column(String(255), nullable=True)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    business = relationship("Business", back_populates="whatsapp_templates")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=True, index=True)
    service_id = Column(String, ForeignKey("products.id"), nullable=True)
    service_name = Column(String(255), nullable=False)
    customer_name = Column(String(255), nullable=True)
    customer_phone = Column(String(20), nullable=True)
    booking_date = Column(String(20), nullable=False)  # YYYY-MM-DD
    booking_time = Column(String(10), nullable=False)   # HH:MM
    duration_minutes = Column(Integer, default=30)
    status = Column(String(20), default="pending")  # pending, confirmed, completed, cancelled
    notes = Column(Text, nullable=True)
    price = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    business = relationship("Business", back_populates="bookings")


class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    code = Column(String(50), nullable=False, index=True)
    discount_type = Column(String(20), default="percent")  # percent or flat
    discount_value = Column(Float, default=0.0)
    min_order = Column(Float, default=0.0)
    max_uses = Column(Integer, default=100)
    used_count = Column(Integer, default=0)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    business = relationship("Business", back_populates="coupons")


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False, index=True)
    product_id = Column(String, ForeignKey("products.id"), nullable=False, index=True)
    quantity = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    business = relationship("Business", back_populates="cart_items")
    customer = relationship("Customer", back_populates="cart_items")
    product = relationship("Product")


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=True, index=True)
    order_id = Column(String, nullable=True)
    rating = Column(Integer, default=5)  # 1-5
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    business = relationship("Business", back_populates="feedbacks")
    customer = relationship("Customer", back_populates="feedbacks")


class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=True, index=True)
    customer_name = Column(String(255), nullable=True)
    customer_phone = Column(String(20), nullable=True)
    product_id = Column(String, ForeignKey("products.id"), nullable=True)
    product_name = Column(String(255), nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, default=0.0)
    total_price = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    coupon_code = Column(String(50), nullable=True)
    delivery_type = Column(String(20), default="pickup")  # pickup or delivery
    delivery_address = Column(Text, nullable=True)
    delivery_fee = Column(Float, default=0.0)
    status = Column(String(30), default="pending")  # pending, confirmed, preparing, shipped, delivered, cancelled
    payment_status = Column(String(30), default="pending")  # pending, completed, cancelled
    payment_id = Column(String, ForeignKey("payments.id"), nullable=True, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    business = relationship("Business", back_populates="orders")
    customer = relationship("Customer", back_populates="orders")
    payment = relationship("Payment", foreign_keys=[payment_id])


class Broadcast(Base):
    __tablename__ = "broadcasts"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    message = Column(Text, nullable=False)
    target_count = Column(Integer, default=0)
    sent_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    status = Column(String(20), default="pending")  # pending, sending, sent, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    business = relationship("Business", back_populates="broadcasts")


class BusinessSettings(Base):
    __tablename__ = "business_settings"
    __table_args__ = (UniqueConstraint("business_id", "section", name="uq_business_section"),)

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    section = Column(String(50), nullable=False)  # invoice, ai, payments, profile, business_hours
    data = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    business = relationship("Business", back_populates="settings")


class WebhookDeliveryLog(Base):
    __tablename__ = "webhook_delivery_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    webhook_id = Column(String, ForeignKey("webhook_subscriptions.id"), nullable=False, index=True)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    payload = Column(JSON, default=dict)
    status_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    status = Column(String(20), default="pending")  # pending, delivered, failed, retrying
    attempts = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    error_message = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    delivered_at = Column(DateTime(timezone=True), nullable=True)

    webhook = relationship("WebhookSubscription")


class Team(Base):
    __tablename__ = "teams"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    business = relationship("Business", back_populates="teams")
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")


class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(String, primary_key=True, default=generate_uuid)
    team_id = Column(String, ForeignKey("teams.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String(20), default="staff")  # owner, admin, staff, viewer
    permissions = Column(JSON, default=list)  # ["orders.read", "inventory.write", ...]
    is_active = Column(Boolean, default=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    team = relationship("Team", back_populates="members")
    user = relationship("User")


class InventoryAlert(Base):
    __tablename__ = "inventory_alerts"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    product_id = Column(String, ForeignKey("products.id"), nullable=True, index=True)
    alert_type = Column(String(50), nullable=False)  # low_stock, out_of_stock, reorder
    threshold = Column(Integer, default=5)
    current_stock = Column(Integer, default=0)
    message = Column(Text, nullable=True)
    is_resolved = Column(Boolean, default=False)
    notified_channels = Column(JSON, default=list)  # ["whatsapp", "email", "dashboard"]
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    business = relationship("Business", back_populates="inventory_alerts")
    product = relationship("Product")


class FollowUp(Base):
    __tablename__ = "follow_ups"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=True, index=True)
    trigger_type = Column(String(50), nullable=False)  # order_completed, appointment, review, custom
    trigger_reference_id = Column(String, nullable=True)  # order_id, booking_id, etc.
    message_template = Column(Text, nullable=False)
    delay_hours = Column(Integer, default=24)
    status = Column(String(20), default="pending")  # pending, sent, failed, cancelled
    scheduled_for = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    business = relationship("Business", back_populates="follow_ups")
    customer = relationship("Customer")


class Segment(Base):
    __tablename__ = "segments"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    rules = Column(JSON, default=list)  # [{"field": "total_spent", "op": "gte", "value": 5000}, ...]
    rule_operator = Column(String(5), default="and")  # "and" or "or"
    is_dynamic = Column(Boolean, default=True)  # auto-refresh vs static
    customer_count = Column(Integer, default=0)
    last_refreshed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    business = relationship("Business", back_populates="segments")
    customers = relationship("CustomerSegment", back_populates="segment", cascade="all, delete-orphan")


class CustomerSegment(Base):
    __tablename__ = "customer_segments"

    id = Column(String, primary_key=True, default=generate_uuid)
    segment_id = Column(String, ForeignKey("segments.id"), nullable=False, index=True)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False, index=True)
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    segment = relationship("Segment", back_populates="customers")
    customer = relationship("Customer")


class ExportJob(Base):
    __tablename__ = "export_jobs"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    export_type = Column(String(50), nullable=False)  # customers, transactions, orders, products, analytics
    format = Column(String(10), default="csv")  # csv, json
    filters = Column(JSON, default=dict)
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    row_count = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    requested_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    business = relationship("Business", back_populates="export_jobs")
