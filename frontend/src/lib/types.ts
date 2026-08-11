// ============================================================
// SHARED TYPES — Used across API and pages
// ============================================================

// ── Auth ──
export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  phone?: string;
}

export interface Business {
  id: string;
  user_id: string;
  name: string;
  type?: string;
  phone_number?: string;
  currency: string;
  timezone: string;
  locale?: string;
  subscription_tier: string;
  subscription_status: string;
  onboarding_completed: boolean;
}

export interface AuthResponse {
  access_token: string;
  accessToken?: string;
  user: User;
}

// ── Products / Inventory ──
export interface Product {
  id: string;
  name: string;
  description?: string;
  price: number;
  cost_price?: number;
  stock_quantity: number;
  min_stock?: number;
  category?: string;
  sku?: string;
  image_url?: string;
  is_active: boolean;
  business_id: string;
  created_at: string;
  updated_at: string;
}

export interface ProductCreate {
  name: string;
  description?: string;
  price: number;
  cost_price?: number;
  stock_quantity?: number;
  min_stock?: number;
  category?: string;
  sku?: string;
  image_url?: string;
}

// ── Customers ──
export interface Customer {
  id: string;
  name: string;
  phone: string;
  email?: string;
  total_spent: number;
  total_orders: number;
  loyalty_points?: number;
  segment?: string;
  tags?: string[];
  notes?: string;
  business_id: string;
  last_order_at?: string;
  created_at: string;
  updated_at: string;
}

export interface CustomerUpdate {
  name?: string;
  email?: string;
  phone?: string;
  notes?: string;
  tags?: string[];
}

// ── Orders ──
export interface Order {
  id: string;
  customer_id: string;
  customer_name?: string;
  customer_phone?: string;
  business_id: string;
  status: "pending" | "confirmed" | "processing" | "shipped" | "delivered" | "cancelled";
  total_amount: number;
  payment_status?: string;
  payment_method?: string;
  notes?: string;
  items?: OrderItem[];
  created_at: string;
  updated_at: string;
}

export interface OrderItem {
  product_id: string;
  product_name: string;
  quantity: number;
  price: number;
  total: number;
}

export interface OrderUpdate {
  status?: string;
  notes?: string;
}

// ── Transactions ──
export interface Transaction {
  id: string;
  business_id: string;
  type: "income" | "expense";
  amount: number;
  description: string;
  category?: string;
  reference_id?: string;
  date: string;
  created_at: string;
}

export interface TransactionCreate {
  business_id: string;
  type: "income" | "expense";
  amount: number;
  description: string;
  category?: string;
  date?: string;
}

// ── Payments ──
export interface Payment {
  id: string;
  business_id: string;
  customer_name?: string;
  customer_phone?: string;
  amount: number;
  status: "pending" | "completed" | "failed" | "refunded";
  payment_method?: string;
  reference_id?: string;
  created_at: string;
}

// ── Loyalty ──
export interface LoyaltyProgram {
  id: string;
  business_id: string;
  name: string;
  points_per_rupee: number;
  min_points_redeem: number;
  is_active: boolean;
  created_at: string;
}

export interface LoyaltyTier {
  id: string;
  business_id: string;
  name: string;
  min_points: number;
  discount_percent: number;
  benefits?: string;
}

export interface LoyaltyBalance {
  customer_id: string;
  points: number;
  tier: string;
  history?: LoyaltyTransaction[];
}

export interface LoyaltyTransaction {
  id: string;
  type: "earn" | "redeem" | "referral";
  points: number;
  description: string;
  created_at: string;
}

// ── Feedback ──
export interface Review {
  id: string;
  customer_name: string;
  rating: number;
  comment?: string;
  source: string;
  created_at: string;
}

export interface Survey {
  id: string;
  business_id: string;
  name: string;
  questions: SurveyQuestion[];
  is_active: boolean;
  created_at: string;
}

export interface SurveyQuestion {
  id: string;
  question: string;
  type: "rating" | "text" | "multiple_choice";
  options?: string[];
}

// ── Teams ──
export interface Team {
  id: string;
  business_id: string;
  name: string;
  description?: string;
  member_count?: number;
  members?: TeamMember[];
  created_at: string;
}

export interface TeamMember {
  id: string;
  user_id: string;
  user_name?: string;
  role: "owner" | "admin" | "staff";
  joined_at: string;
}

export interface TeamCreate {
  name: string;
  description?: string;
  business_id: string;
}

export interface TeamMemberAdd {
  user_id: string;
  role: string;
  team_id?: string;
}

// ── Inventory Alerts ──
export interface InventoryAlert {
  id: string;
  product_id: string;
  product_name?: string;
  business_id: string;
  alert_type: "low_stock" | "out_of_stock" | "expiring";
  threshold?: number;
  current_value?: number;
  status: "active" | "resolved" | "dismissed";
  created_at: string;
  resolved_at?: string;
}

// ── Follow-ups ──
export interface FollowUp {
  id: string;
  customer_id: string;
  customer_name?: string;
  business_id: string;
  followup_type: string;
  message: string;
  status: "pending" | "sent" | "completed" | "cancelled" | "failed";
  scheduled_for: string;
  completed_at?: string;
  created_at: string;
}

export interface FollowUpCreate {
  customer_id: string;
  message: string;
  followup_type?: string;
  scheduled_for?: string;
  business_id: string;
}

// ── Segments ──
export interface Segment {
  id: string;
  business_id: string;
  name: string;
  description?: string;
  segment_type: "dynamic" | "manual";
  rules?: SegmentRule[];
  customer_count?: number;
  created_at: string;
}

export interface SegmentRule {
  field: string;
  operator: string;
  value: string;
}

export interface SegmentCreate {
  name: string;
  description?: string;
  segment_type?: string;
  rules?: string;
  business_id: string;
}

// ── Scheduled Messages ──
export interface ScheduledMessage {
  id: string;
  business_id: string;
  customer_id?: string;
  customer_name?: string;
  content: string;
  message_type: string;
  status: "pending" | "sent" | "failed" | "cancelled";
  scheduled_for: string;
  sent_at?: string;
  created_at: string;
}

export interface ScheduledMessageCreate {
  content: string;
  customer_id?: string;
  message_type?: string;
  scheduled_for: string;
  business_id: string;
}

// ── Exports ──
export interface ExportJob {
  id: string;
  business_id: string;
  export_type: string;
  format: string;
  status: "pending" | "processing" | "completed" | "failed";
  row_count?: number;
  file_size?: number;
  download_url?: string;
  created_at: string;
  completed_at?: string;
}

// ── Webhooks ──
export interface Webhook {
  id: string;
  business_id: string;
  url: string;
  events: string[];
  is_active: boolean;
  created_at: string;
}

export interface WebhookLog {
  id: string;
  webhook_id: string;
  status: "success" | "failed" | "pending";
  event_type?: string;
  request_body?: string;
  response_body?: string;
  status_code?: number;
  duration_ms?: number;
  url?: string;
  error_message?: string;
  created_at: string;
}

export interface WebhookStats {
  total: number;
  active: number;
  total_deliveries: number;
  success_rate: number;
}

// ── Templates ──
export interface Template {
  id: string;
  name: string;
  category: string;
  body: string;
  created_at: string;
}

export interface TemplateCreate {
  name: string;
  category: string;
  body: string;
}

// ── Integrations ──
export interface IntegrationStatus {
  type: string;
  status: "connected" | "disconnected";
  connected_at?: string;
}

export interface IntegrationConnect {
  business_id: string;
  credentials: Record<string, string>;
  config?: Record<string, unknown>;
}

// ── Analytics ──
export interface DashboardStats {
  revenue: { value: number; change: number };
  messages: { value: number; change: number };
  customers: { value: number; change: number };
  orders: { value: number; change: number };
  revenue_chart?: { date: string; revenue: number }[];
  top_products?: { name: string; sales: number; quantity?: number }[];
}

export interface RevenueForecast {
  forecasted_revenue: number;
  growth_rate: number;
  peak_day: string;
  avg_daily: number;
  daily_data?: { date: string; revenue: number }[];
}

export interface ConversationStats {
  total_conversations: number;
  avg_response_time: string;
  messages_today: number;
  active_customers: number;
}

// ── Chat ──
export interface ChatMessage {
  id: string;
  conversation_id: string;
  sender: "customer" | "bot" | "agent";
  message: string;
  message_type: string;
  created_at: string;
}

export interface Conversation {
  id: string;
  customer_id: string;
  customer_name?: string;
  customer_phone?: string;
  channel?: string;
  last_message?: string;
  last_direction?: string;
  last_message_at?: string;
  unread_count?: number;
  status: string;
}

// ── Audit ──
export interface AuditLog {
  id: string;
  business_id: string;
  action: string;
  entity_type: string;
  entity_id?: string;
  details?: string;
  user_id?: string;
  created_at: string;
}

// ── Generic API params ──
export interface PaginationParams {
  page?: number;
  limit?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}

export interface DateRangeParams {
  start_date?: string;
  end_date?: string;
}

export interface StatusFilter {
  status?: string;
}

// ── QR / UPI ──
export interface QRResponse {
  qr_url?: string;
  qr_code?: string;
  upi_link: string;
  payment_id: string;
}

// ── Revenue ──
export interface RevenueData {
  forecasted_revenue?: number;
  total?: number;
  growth_rate?: number;
  growth?: number;
  peak_day?: string;
  avg_daily?: number;
  average?: number;
  daily_data?: { date: string; revenue: number }[];
}

// ── Audit Stats ──
export interface AuditCompliance {
  total_actions: number;
  unique_users: number;
  entity_breakdown: Record<string, number>;
  risk_events: number;
}

// ── Export Stats ──
export interface ExportStats {
  total_exports: number;
  pending: number;
  completed: number;
  failed: number;
}

// ── Segment Stats ──
export interface SegmentStats {
  total_segments: number;
  total_customers: number;
  auto_segments: number;
}

// ── Scheduled Message Stats ──
export interface ScheduledMessageStats {
  total: number;
  pending: number;
  sent: number;
  failed: number;
}

// ── FollowUp Stats ──
export interface FollowUpStats {
  total: number;
  pending: number;
  sent: number;
  completed: number;
  cancelled: number;
  failed: number;
}

// ── Inventory Alert Stats ──
export interface InventoryAlertStats {
  total: number;
  active: number;
  resolved: number;
  dismissed: number;
}
