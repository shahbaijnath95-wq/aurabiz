"""Master Database Models — Platform-level schema"""
import uuid
from sqlalchemy import Column, String, Boolean, Integer, Float, DateTime, Text, JSON
from sqlalchemy.sql import func
from database import Base


def gen_uuid():
    return str(uuid.uuid4())


# ─── Tenant Registry ───
class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String, primary_key=True, default=gen_uuid)
    slug = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    owner_name = Column(String(255))
    owner_email = Column(String(255), unique=True, nullable=False)
    owner_phone = Column(String(20))
    db_path = Column(String(500), nullable=False)
    status = Column(String(20), default="active")       # active | suspended | deleted | trial
    plan = Column(String(20), default="starter")         # starter | growth | enterprise
    trial_ends_at = Column(DateTime(timezone=True))
    max_products = Column(Integer, default=100)
    max_messages_per_month = Column(Integer, default=1000)
    messages_used_this_month = Column(Integer, default=0)
    preferred_language = Column(String(10), default="hi")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    suspended_at = Column(DateTime(timezone=True))
    suspend_reason = Column(Text)


# ─── Admin Users ───
class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(String, primary_key=True, default=gen_uuid)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(20), default="admin")       # super_admin | admin | viewer
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ─── AI Provider Config (Platform-level) ───
class AIProvider(Base):
    __tablename__ = "ai_providers"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String(100), nullable=False)
    provider_key = Column(String(50), unique=True, nullable=False)
    api_key = Column(Text, nullable=False)
    account_id = Column(String(255))
    model = Column(String(200))
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    rate_limit_rpm = Column(Integer, default=50)
    rate_limit_rpd = Column(Integer, default=1500)
    cost_per_1k_tokens = Column(Float, default=0.0)
    config = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ─── AI Usage Tracking ───
class AIUsageLog(Base):
    __tablename__ = "ai_usage_logs"

    id = Column(String, primary_key=True, default=gen_uuid)
    tenant_id = Column(String, nullable=False, index=True)
    provider_key = Column(String(50), nullable=False)
    model = Column(String(200))
    tokens_in = Column(Integer, default=0)
    tokens_out = Column(Integer, default=0)
    latency_ms = Column(Integer, default=0)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ─── Platform Analytics ───
class PlatformStats(Base):
    __tablename__ = "platform_stats"

    id = Column(String, primary_key=True, default=gen_uuid)
    date = Column(String(10), nullable=False)
    total_tenants = Column(Integer, default=0)
    active_tenants = Column(Integer, default=0)
    total_messages = Column(Integer, default=0)
    total_orders = Column(Integer, default=0)
    total_revenue = Column(Float, default=0.0)
    new_signups = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ─── Platform Invoices ───
class PlatformInvoice(Base):
    __tablename__ = "platform_invoices"

    id = Column(String, primary_key=True, default=gen_uuid)
    tenant_id = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="INR")
    status = Column(String(20), default="pending")
    plan = Column(String(20), nullable=False)
    billing_period = Column(String(10))
    payment_id = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    paid_at = Column(DateTime(timezone=True))


# ─── Desktop App Licenses (EXE activation) ───
class License(Base):
    """License key for the Windows desktop app (.exe)."""
    __tablename__ = "licenses"

    id = Column(String, primary_key=True, default=gen_uuid)
    license_key = Column(String(100), unique=True, nullable=False, index=True)
    tenant_id = Column(String, nullable=True, index=True)
    plan = Column(String(20), default="starter")         # starter | growth | enterprise
    status = Column(String(20), default="issued")        # issued | activated | expired | revoked
    machine_id = Column(String(255), nullable=True)      # customer PC fingerprint
    max_activations = Column(Integer, default=1)         # kitne PCs pe chal sakta hai
    activations_used = Column(Integer, default=0)
    owner_name = Column(String(255))
    owner_email = Column(String(255), nullable=False)
    owner_phone = Column(String(20))
    amount_paid = Column(Float, default=0.0)
    ai_tier = Column(String(20), default="free")         # free | paid
    paid_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_activated_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ─── Admin Audit Log ───
class AdminAuditLog(Base):
    __tablename__ = "admin_audit_log"

    id = Column(String, primary_key=True, default=gen_uuid)
    admin_user_id = Column(String)
    action = Column(String(100), nullable=False)
    target_tenant_id = Column(String)
    details = Column(JSON)
    ip_address = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ─── Feature Flags ───
class FeatureFlag(Base):
    __tablename__ = "feature_flags"

    id = Column(String, primary_key=True, default=gen_uuid)
    flag_name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    enabled = Column(Boolean, default=False)
    target_tenant_ids = Column(JSON)  # null = all tenants, list = specific tenants
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ─── API Keys ───
class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    key_hash = Column(String(255), nullable=False)
    key_preview = Column(String(20))
    permissions = Column(JSON, default=list)  # ["read"], ["read","write"], ["read","write","admin"]
    rate_limit = Column(Integer, default=100)
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ─── Support Tickets ───
class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(String, primary_key=True, default=gen_uuid)
    tenant_id = Column(String, nullable=False, index=True)
    subject = Column(String(500), nullable=False)
    description = Column(Text)
    status = Column(String(20), default="open")  # open | in_progress | resolved | closed
    priority = Column(String(20), default="medium")  # low | medium | high | critical
    assigned_to = Column(String)
    internal_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class SupportMessage(Base):
    __tablename__ = "support_messages"

    id = Column(String, primary_key=True, default=gen_uuid)
    ticket_id = Column(String, nullable=False, index=True)
    message = Column(Text, nullable=False)
    from_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ─── Notifications ───
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=gen_uuid)
    title = Column(String(255), nullable=False)
    message = Column(Text)
    severity = Column(String(20), default="info")  # info | warning | critical
    tenant_id = Column(String)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class NotificationSetting(Base):
    __tablename__ = "notification_settings"

    id = Column(String, primary_key=True, default=gen_uuid)
    email_enabled = Column(Boolean, default=True)
    slack_webhook = Column(String(500))
    sms_enabled = Column(Boolean, default=False)
    alert_thresholds = Column(JSON, default=dict)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ─── Platform Webhooks ───
class PlatformWebhook(Base):
    __tablename__ = "platform_webhooks"

    id = Column(String, primary_key=True, default=gen_uuid)
    url = Column(String(500), nullable=False)
    events = Column(JSON, default=list)
    secret = Column(String(255))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class WebhookDeliveryLog(Base):
    __tablename__ = "webhook_delivery_logs"

    id = Column(String, primary_key=True, default=gen_uuid)
    webhook_id = Column(String, nullable=False, index=True)
    event = Column(String(100))
    payload = Column(JSON)
    status_code = Column(Integer)
    response_body = Column(Text)
    error = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ─── Backups ───
class Backup(Base):
    __tablename__ = "backups"

    id = Column(String, primary_key=True, default=gen_uuid)
    tenant_id = Column(String)  # null = all tenants
    tenant_name = Column(String(255))
    size_bytes = Column(Integer, default=0)
    type = Column(String(20), default="manual")  # manual | auto
    file_path = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ─── Resellers ───
class Reseller(Base):
    __tablename__ = "resellers"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    commission_rate = Column(Integer, default=30)  # percentage
    is_active = Column(Boolean, default=True)
    tenants_count = Column(Integer, default=0)
    total_commission = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ResellerPayout(Base):
    __tablename__ = "reseller_payouts"

    id = Column(String, primary_key=True, default=gen_uuid)
    reseller_id = Column(String, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    status = Column(String(20), default="pending")  # pending | paid | cancelled
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    paid_at = Column(DateTime(timezone=True))


# ─── White-Label Config ───
class WhiteLabelConfig(Base):
    __tablename__ = "white_label_configs"

    id = Column(String, primary_key=True, default=gen_uuid)
    tenant_id = Column(String, nullable=False, index=True)
    logo_url = Column(String(500))
    primary_color = Column(String(20), default="#3B82F6")
    domain = Column(String(255))
    remove_branding = Column(Boolean, default=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ─── Integrations ───
class Integration(Base):
    __tablename__ = "integrations"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String(100), nullable=False)
    category = Column(String(50))  # payments | crm | ecommerce | communication | analytics
    description = Column(Text)
    enabled = Column(Boolean, default=False)
    price = Column(Integer, default=0)  # monthly price in INR (0 = free)
    config = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
