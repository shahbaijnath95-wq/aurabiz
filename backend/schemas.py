from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, Any
from datetime import datetime
from enum import Enum


def to_camel(string: str) -> str:
    parts = string.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:]) if len(parts) > 1 else string


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


# ── Auth ──
class UserCreate(CamelModel):
    email: str
    password: str
    full_name: str
    phone: Optional[str] = None


class UserLogin(CamelModel):
    email: str
    password: str


class UserResponse(CamelModel):
    id: str
    email: str
    full_name: str
    role: str
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None


class Token(CamelModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ── Business ──
class BusinessCreate(CamelModel):
    name: str
    type: Optional[str] = None
    phone_number: Optional[str] = None
    currency: str = "INR"
    timezone: str = "Asia/Kolkata"
    locale: str = "hi"
    brand_voice: Optional[str] = None


class BusinessUpdate(CamelModel):
    name: Optional[str] = None
    type: Optional[str] = None
    phone_number: Optional[str] = None
    currency: Optional[str] = None
    timezone: Optional[str] = None
    brand_voice: Optional[str] = None
    logo_url: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    subscription_tier: Optional[str] = None


class BusinessResponse(CamelModel):
    id: str
    user_id: str
    name: str
    type: Optional[str] = None
    phone_number: Optional[str] = None
    currency: str
    timezone: str
    locale: str
    brand_voice: Optional[str] = None
    subscription_tier: str
    subscription_status: str
    onboarding_completed: bool
    created_at: Optional[datetime] = None


# ── Customer ──
class CustomerCreate(CamelModel):
    business_id: str
    phone_number: str
    name: Optional[str] = None
    email: Optional[str] = None
    tags: list[str] = []
    preferred_language: str = "hi"
    is_wholesaler: bool = False


class CustomerUpdate(CamelModel):
    name: Optional[str] = None
    email: Optional[str] = None
    tags: Optional[list[str]] = None
    lifecycle_stage: Optional[str] = None
    notes: Optional[str] = None
    preferred_language: Optional[str] = None
    is_wholesaler: Optional[bool] = None


class CustomerResponse(CamelModel):
    id: str
    business_id: str
    phone_number: str
    name: Optional[str] = None
    email: Optional[str] = None
    tags: list[str] = []
    lifecycle_stage: str
    engagement_score: float
    preferred_language: str
    total_orders: int
    total_spent: float
    loyalty_points: int
    is_wholesaler: bool
    last_active: Optional[datetime] = None
    created_at: Optional[datetime] = None


class CustomerProfile(CamelModel):
    customer: CustomerResponse
    transactions: list["TransactionResponse"] = []
    recent_conversations: list[dict] = []
    sentiment_history: list[dict] = []
    insights: dict = {}


# ── Transaction ──
class TransactionCreate(CamelModel):
    business_id: str
    customer_id: Optional[str] = None
    amount: float
    currency: str = "INR"
    type: str = "sale"
    status: str = "completed"
    items: list[dict] = []
    payment_method: Optional[str] = None
    reference: Optional[str] = None
    notes: Optional[str] = None


class TransactionUpdate(CamelModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    payment_method: Optional[str] = None


class TransactionResponse(CamelModel):
    id: str
    business_id: str
    customer_id: Optional[str] = None
    amount: float
    currency: str
    type: str
    status: str
    items: list[dict] = []
    payment_method: Optional[str] = None
    reference: Optional[str] = None
    notes: Optional[str] = None
    is_recurring: bool
    created_at: Optional[datetime] = None


class TransactionSummary(CamelModel):
    total: float
    count: int
    average: float
    by_status: dict[str, int]
    by_type: dict[str, float]


# ── WhatsApp ──
class WhatsAppMessageSend(CamelModel):
    to: str
    message_type: str = "text"
    content: str
    template_name: Optional[str] = None
    template_vars: Optional[dict] = None
    media_id: Optional[str] = None
    phone_number_id: Optional[str] = None


class WhatsAppTemplateCreate(CamelModel):
    name: str
    category: str
    language: str = "hi"
    header: Optional[str] = None
    body: str
    footer: Optional[str] = None
    buttons: list[dict] = []
    variables: list[str] = []


class WhatsAppTemplateResponse(CamelModel):
    id: str
    business_id: str
    name: str
    category: str
    language: str
    status: str
    header: Optional[str] = None
    body: str
    footer: Optional[str] = None
    buttons: list[dict] = []
    variables: list[str] = []
    usage_count: int
    created_at: Optional[datetime] = None


class WhatsAppMessageResponse(CamelModel):
    id: str
    message_id: Optional[str] = None
    direction: str
    content: Optional[str] = None
    message_type: str
    status: str
    template_name: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None


class ConversationResponse(CamelModel):
    id: str
    customer_id: str
    customer_name: Optional[str] = None
    customer_phone: str
    status: str
    last_message_at: Optional[datetime] = None
    last_message_preview: Optional[str] = None
    messages_sent: int
    unread_count: int = 0


# ── Loyalty ──
class LoyaltyProgramCreate(CamelModel):
    name: str
    type: str = "points"
    points_per_currency: float = 1.0
    tier_thresholds: dict = {"bronze": 0, "silver": 1000, "gold": 5000, "platinum": 20000}
    reward_rules: list[dict] = []


class LoyaltyProgramResponse(CamelModel):
    id: str
    business_id: str
    name: str
    type: str
    points_per_currency: float
    tier_thresholds: dict
    reward_rules: list[dict]
    is_active: bool
    created_at: Optional[datetime] = None


class LoyaltyRedeem(CamelModel):
    customer_id: str
    points: int
    reward_id: Optional[str] = None


class LoyaltyEarn(CamelModel):
    customer_id: str
    amount: float
    transaction_id: Optional[str] = None


class LoyaltyBalanceResponse(CamelModel):
    customer_id: str
    balance: int
    tier: str
    points_expiring_soon: int = 0


class ReferralCreate(CamelModel):
    business_id: str
    reward_amount: int = 100
    referrer_reward: int = 100
    referred_reward: int = 50


class ReferralTrack(CamelModel):
    referral_code: str
    new_customer_phone: str
    new_customer_name: Optional[str] = None


# ── Product / Inventory ──
class ProductCreate(CamelModel):
    business_id: str
    name: str
    sku: Optional[str] = None
    price: float
    wholesale_price: Optional[float] = None
    cost_price: Optional[float] = None
    description: Optional[str] = None
    category: Optional[str] = None
    stock_quantity: int = 0
    unit: str = "piece"
    min_stock: int = 10
    image_url: Optional[str] = None
    item_type: Optional[str] = "product"
    duration_minutes: Optional[int] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    warranty: Optional[str] = None
    hsn_code: Optional[str] = None
    gst_rate: Optional[float] = 0.0
    tags: Optional[list[str]] = []
    specs: Optional[dict] = {}
    gallery: Optional[list[str]] = []


class ProductUpdate(CamelModel):
    name: Optional[str] = None
    price: Optional[float] = None
    wholesale_price: Optional[float] = None
    cost_price: Optional[float] = None
    description: Optional[str] = None
    category: Optional[str] = None
    stock_quantity: Optional[int] = None
    is_active: Optional[bool] = None
    image_url: Optional[str] = None
    min_stock: Optional[int] = None
    item_type: Optional[str] = None
    duration_minutes: Optional[int] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    warranty: Optional[str] = None
    hsn_code: Optional[str] = None
    gst_rate: Optional[float] = None
    tags: Optional[list[str]] = None
    specs: Optional[dict] = None
    gallery: Optional[list[str]] = None


class ProductResponse(CamelModel):
    id: str
    business_id: str
    name: str
    sku: Optional[str] = None
    price: float
    wholesale_price: Optional[float] = None
    cost_price: Optional[float] = None
    description: Optional[str] = None
    category: Optional[str] = None
    stock_quantity: int
    is_active: bool
    unit: str
    min_stock: int
    image_url: Optional[str] = None
    item_type: Optional[str] = "product"
    duration_minutes: Optional[int] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    warranty: Optional[str] = None
    hsn_code: Optional[str] = None
    gst_rate: Optional[float] = 0.0
    tags: list[str] = []
    specs: dict = {}
    gallery: list[str] = []
    created_at: Optional[datetime] = None


class StockUpdate(CamelModel):
    quantity: int
    operation: str = "set"  # set, add, subtract


class BulkStockUpdate(CamelModel):
    updates: list[dict]  # [{product_id, quantity, operation}]


# ── Invoice ──
class InvoiceCreate(CamelModel):
    business_id: str
    customer_id: Optional[str] = None
    items: list[dict] = []
    tax_rate: float = 0.0
    notes: Optional[str] = None
    due_days: int = 30


class InvoiceResponse(CamelModel):
    id: str
    business_id: str
    customer_id: Optional[str] = None
    number: str
    status: str
    subtotal: float
    tax: float
    total: float
    items: list[dict] = []
    due_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None


# ── Integration ──
class IntegrationConnect(CamelModel):
    business_id: str
    credentials: dict = {}
    config: dict = {}


class IntegrationResponse(CamelModel):
    id: str
    type: str
    status: str
    config: dict = {}
    last_synced_at: Optional[datetime] = None
    error_message: Optional[str] = None


# ── Webhook ──
class WebhookCreate(CamelModel):
    business_id: str
    url: str
    events: list[str] = []


class WebhookResponse(CamelModel):
    id: str
    business_id: str
    url: str
    events: list[str] = []
    is_active: bool
    failure_count: int
    created_at: Optional[datetime] = None


class WebhookDeliveryLogResponse(CamelModel):
    id: str
    event_type: str
    url: str
    status: str
    status_code: Optional[int] = None
    attempts: int
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    delivered_at: Optional[str] = None


class WebhookStatsResponse(CamelModel):
    total_webhooks: int
    active_webhooks: int
    delivery_7d: dict = {}


# ── Catalog ──
class CatalogSearchRequest(CamelModel):
    business_id: str
    query: str
    category: Optional[str] = None
    limit: int = 10


class CatalogProductResponse(CamelModel):
    id: str
    name: str
    price: float
    description: Optional[str] = None
    category: Optional[str] = None
    stock_quantity: int
    image_url: Optional[str] = None
    brand: Optional[str] = None


class CatalogResponse(CamelModel):
    products: list[dict] = []
    total: int
    page: int
    per_page: int


# ── Payment Link ──
class PaymentLinkCreate(CamelModel):
    business_id: str
    amount: float
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    description: Optional[str] = None
    upi_id: Optional[str] = None


class PaymentLinkResponse(CamelModel):
    payment_id: str
    upi_link: str
    qr_code: Optional[str] = None
    amount: float
    status: str


# ── Conversation Analytics ──
class ConversationStatsResponse(CamelModel):
    total_messages: int = 0
    inbound_messages: int = 0
    outbound_messages: int = 0
    unique_customers: int = 0
    active_conversations: int = 0
    avg_response_time_minutes: Optional[float] = None
    sentiment_distribution: dict = {}
    intent_distribution: dict = {}
    hourly_trend: list = []
    daily_trend: list = []


# ── Language ──
class LanguageDetectRequest(CamelModel):
    text: str


class LanguageDetectResponse(CamelModel):
    detected_language: str
    confidence: float
    language_name: str


# ── Admin ──
class AdminUserRoleUpdate(CamelModel):
    role: str


class AdminSubscriptionUpdate(CamelModel):
    tier: str
    status: Optional[str] = None


class NotificationSend(CamelModel):
    user_id: str
    title: str
    message: str
    channel: str = "whatsapp"


class BroadcastNotification(CamelModel):
    title: str
    message: str
    channel: str = "whatsapp"
    target_tier: Optional[str] = None


class APIKeyCreate(CamelModel):
    name: str
    permissions: list[str] = []


class APIKeyResponse(CamelModel):
    id: str
    name: str
    key_prefix: str
    permissions: list[str] = []
    is_active: bool
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


# ── Analytics ──
class DashboardResponse(CamelModel):
    stat_cards: dict
    revenue_chart: list[dict] = []
    customer_metrics: dict = {}
    top_products: list[dict] = []
    revenue_forecast: list[dict] = []
    customer_segments: dict = {}
    recent_transactions: list[dict] = []
    activity_feed: list[dict] = []
    ai_insights: list[str] = []


class RevenueForecastResponse(CamelModel):
    date: str
    predicted: float
    lower: float
    upper: float


# ── Feedback ──
class NPSSurveySend(CamelModel):
    business_id: str
    customer_id: str
    template_id: Optional[str] = None


class SurveyCreate(CamelModel):
    business_id: str
    name: str
    questions: list[dict] = []


class ReviewRespond(CamelModel):
    response: str
    tone: str = "professional"


# ── Audit ──
class AuditLogResponse(CamelModel):
    id: str
    business_id: str
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    changes: dict = {}
    ip_address: Optional[str] = None
    timestamp: Optional[datetime] = None


# ── Scheduled Message ──
class ScheduledMessageCreate(CamelModel):
    business_id: str
    customer_id: Optional[str] = None
    content: str
    message_type: str = "text"
    template_name: Optional[str] = None
    template_vars: dict = {}
    scheduled_for: datetime


class ScheduledMessageResponse(CamelModel):
    id: str
    business_id: str
    customer_id: Optional[str] = None
    content: str
    status: str
    scheduled_for: datetime
    sent_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


# ── Generic ──
class PaginationParams(CamelModel):
    page: int = 1
    limit: int = 20
    search: Optional[str] = None
    sort_by: Optional[str] = None
    sort_order: str = "desc"


class PaginatedResponse(CamelModel):
    items: list[Any] = []
    total: int
    page: int
    limit: int
    pages: int


class ErrorResponse(CamelModel):
    detail: str
    code: Optional[str] = None


class SuccessResponse(CamelModel):
    message: str
    data: Optional[Any] = None


# ── Coupon ──
class CouponCreate(CamelModel):
    business_id: str
    code: str
    discount_type: str = "percent"  # percent or flat
    discount_value: float = 0.0
    min_order: float = 0.0
    max_uses: int = 100
    expires_at: Optional[datetime] = None


class CouponResponse(CamelModel):
    id: str
    business_id: str
    code: str
    discount_type: str
    discount_value: float
    min_order: float
    max_uses: int
    used_count: int
    is_active: bool
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


# ── Cart ──
class CartItemCreate(CamelModel):
    business_id: str
    customer_id: str
    product_id: str
    quantity: int = 1


class CartItemResponse(CamelModel):
    id: str
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    total_price: float


# ── Feedback ──
class FeedbackCreate(CamelModel):
    business_id: str
    customer_id: Optional[str] = None
    order_id: Optional[str] = None
    rating: int = 5
    comment: Optional[str] = None


class FeedbackResponse(CamelModel):
    id: str
    business_id: str
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    rating: int
    comment: Optional[str] = None
    created_at: Optional[datetime] = None


# ── Order ──
class OrderCreate(CamelModel):
    business_id: str
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    product_id: Optional[str] = None
    product_name: str
    quantity: int = 1
    unit_price: float = 0.0
    total_price: float = 0.0
    discount_amount: float = 0.0
    coupon_code: Optional[str] = None
    delivery_type: str = "pickup"
    delivery_address: Optional[str] = None
    delivery_fee: float = 0.0
    notes: Optional[str] = None


class OrderUpdate(CamelModel):
    status: Optional[str] = None
    notes: Optional[str] = None


class OrderResponse(CamelModel):
    id: str
    business_id: str
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    product_name: str
    quantity: int
    unit_price: float
    total_price: float
    discount_amount: float
    coupon_code: Optional[str] = None
    delivery_type: str
    delivery_address: Optional[str] = None
    delivery_fee: float
    status: str
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ── Broadcast ──
class BroadcastCreate(CamelModel):
    business_id: str
    message: str


class BroadcastResponse(CamelModel):
    id: str
    business_id: str
    message: str
    target_count: int
    sent_count: int
    failed_count: int
    status: str
    created_at: Optional[datetime] = None


# ── Team ──
class TeamCreate(CamelModel):
    business_id: str
    name: str
    description: Optional[str] = None


class TeamUpdate(CamelModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class TeamMemberAdd(CamelModel):
    user_id: str
    role: str = "staff"
    permissions: list[str] = []


class TeamMemberUpdate(CamelModel):
    role: Optional[str] = None
    permissions: Optional[list[str]] = None
    is_active: Optional[bool] = None


class TeamMemberResponse(CamelModel):
    id: str
    team_id: str
    user_id: str
    role: str
    permissions: list[str] = []
    is_active: bool
    joined_at: Optional[datetime] = None


class TeamResponse(CamelModel):
    id: str
    business_id: str
    name: str
    description: Optional[str] = None
    is_active: bool
    member_count: int = 0
    created_at: Optional[datetime] = None


# ── Inventory Alerts ──
class InventoryAlertCreate(CamelModel):
    business_id: str
    product_id: Optional[str] = None
    alert_type: str = "low_stock"
    threshold: int = 5
    message: Optional[str] = None
    notified_channels: list[str] = ["dashboard"]


class InventoryAlertUpdate(CamelModel):
    threshold: Optional[int] = None
    is_resolved: Optional[bool] = None
    notified_channels: Optional[list[str]] = None


class InventoryAlertResponse(CamelModel):
    id: str
    business_id: str
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    alert_type: str
    threshold: int
    current_stock: int
    message: Optional[str] = None
    is_resolved: bool
    notified_channels: list[str] = []
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


# ── Follow-Ups ──
class FollowUpCreate(CamelModel):
    business_id: str
    customer_id: Optional[str] = None
    trigger_type: str = "custom"
    trigger_reference_id: Optional[str] = None
    message_template: str
    delay_hours: int = 24


class FollowUpUpdate(CamelModel):
    message_template: Optional[str] = None
    delay_hours: Optional[int] = None
    status: Optional[str] = None
    scheduled_for: Optional[datetime] = None


class FollowUpResponse(CamelModel):
    id: str
    business_id: str
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    trigger_type: str
    trigger_reference_id: Optional[str] = None
    message_template: str
    delay_hours: int
    status: str
    scheduled_for: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None


# ── Segments ──
class SegmentRule(CamelModel):
    field: str  # total_spent, total_orders, last_order_days, tags, lifecycle_stage, etc.
    op: str  # eq, neq, gte, lte, gt, lt, in, not_in, contains
    value: Any


class SegmentCreate(CamelModel):
    business_id: str
    name: str
    description: Optional[str] = None
    rules: list[SegmentRule] = []
    rule_operator: str = "and"
    is_dynamic: bool = True


class SegmentUpdate(CamelModel):
    name: Optional[str] = None
    description: Optional[str] = None
    rules: Optional[list[SegmentRule]] = None
    rule_operator: Optional[str] = None
    is_dynamic: Optional[bool] = None


class SegmentResponse(CamelModel):
    id: str
    business_id: str
    name: str
    description: Optional[str] = None
    rules: list[dict] = []
    rule_operator: str
    is_dynamic: bool
    customer_count: int
    last_refreshed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class CustomerSegmentAssign(CamelModel):
    customer_ids: list[str]


# ── Scheduled Messages ──
class ScheduledMessageUpdate(CamelModel):
    content: Optional[str] = None
    message_type: Optional[str] = None
    scheduled_for: Optional[datetime] = None
    status: Optional[str] = None


# ── Export ──
class ExportRequest(CamelModel):
    business_id: str
    export_type: str  # customers, transactions, orders, products, analytics
    format: str = "csv"
    filters: dict = {}


class ExportResponse(CamelModel):
    id: str
    business_id: str
    export_type: str
    format: str
    status: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    row_count: Optional[int] = None
    error_message: Optional[str] = None
    requested_by: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ExportStatsResponse(CamelModel):
    total_jobs: int
    completed: int
    processing: int
    failed: int
