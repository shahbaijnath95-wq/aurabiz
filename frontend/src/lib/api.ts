import type {
  AuthResponse, User, Business,
  Product, ProductCreate,
  Customer, CustomerUpdate,
  Order, OrderUpdate,
  Transaction, TransactionCreate,
  Payment,
  LoyaltyProgram, LoyaltyTier, LoyaltyBalance, LoyaltyTransaction,
  Review, Survey,
  Team, TeamCreate, TeamMember, TeamMemberAdd,
  InventoryAlert,
  FollowUp, FollowUpCreate,
  Segment, SegmentCreate,
  ScheduledMessage, ScheduledMessageCreate,
  ExportJob,
  Webhook, WebhookLog, WebhookStats,
  Template, TemplateCreate,
  IntegrationStatus, IntegrationConnect,
  DashboardStats, RevenueForecast, ConversationStats,
  ChatMessage, Conversation,
  AuditLog, AuditCompliance,
  QRResponse, RevenueData,
  ExportStats, SegmentStats, ScheduledMessageStats, FollowUpStats, InventoryAlertStats,
  PaginationParams, StatusFilter,
} from "./types";

export const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000") + "/api/v1";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

function getBusinessId(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("business_id");
}

export async function request<T = unknown>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (options.body && typeof options.body === "string") {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });

  if (res.status === 401) {
    localStorage.removeItem("token");
    localStorage.removeItem("business_id");
    window.location.href = "/login";
    throw new Error("Unauthorized");
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Request fail ho gaya" }));
    throw new Error(err.detail || `Error: ${res.status}`);
  }

  const data = await res.json() as T;
  
  // Auto-unwrap: if response is { items: [...] } or { products: [...] } etc., return the array
  if (data && typeof data === "object" && !Array.isArray(data)) {
    const keys = Object.keys(data);
    if (keys.length === 1 && Array.isArray((data as Record<string, unknown>)[keys[0]])) {
      return (data as Record<string, unknown>)[keys[0]] as T;
    }
  }
  
  return data;
}

// ── Auth ──
export const auth = {
  login: async (email: string, password: string): Promise<AuthResponse> => {
    const body = new URLSearchParams();
    body.append("username", email);
    body.append("password", password);

    const headers: Record<string, string> = {
      "Content-Type": "application/x-www-form-urlencoded",
    };
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers,
      body,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Login fail ho gaya" }));
      throw new Error(err.detail || "Login fail ho gaya");
    }

    const data = await res.json() as AuthResponse;
    localStorage.setItem("token", data.access_token || data.accessToken || "");
    if (data.user) localStorage.setItem("user", JSON.stringify(data.user));
    return data;
  },

  register: async (data: { full_name: string; email: string; phone?: string; password: string }): Promise<AuthResponse> => {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Registration fail ho gaya" }));
      throw new Error(err.detail || "Registration fail ho gaya");
    }

    const result = await res.json() as AuthResponse;
    localStorage.setItem("token", result.access_token || result.accessToken || "");
    if (result.user) localStorage.setItem("user", JSON.stringify(result.user));
    return result;
  },

  me: (): Promise<User> => request<User>("/auth/me"),

  getBusiness: (): Promise<Business> => request<Business>("/auth/business"),

  createBusiness: (data: Partial<Business>): Promise<Business> =>
    request<Business>("/auth/business", { method: "POST", body: JSON.stringify(data) }),
};

// ── Transactions ──
export const transactions = {
  list: (businessId: string, params?: PaginationParams): Promise<Transaction[]> => {
    const q = params ? `?${new URLSearchParams(params as Record<string, string>).toString()}` : "";
    return request<Transaction[]>(`/transactions/${businessId}${q}`);
  },
  record: (data: TransactionCreate): Promise<Transaction> =>
    request<Transaction>("/transactions/record", { method: "POST", body: JSON.stringify(data) }),
  summary: (businessId: string): Promise<Record<string, number>> =>
    request<Record<string, number>>(`/transactions/summary/${businessId}`),
  bulk: (data: { transactions: TransactionCreate[] }): Promise<Transaction[]> =>
    request<Transaction[]>("/transactions/bulk", { method: "POST", body: JSON.stringify(data) }),
};

// ── Customers ──
export const customers = {
  create: (data: CustomerCreate): Promise<Customer> =>
    request<Customer>("/customers", { method: "POST", body: JSON.stringify(data) }),
  list: (businessId: string, params?: PaginationParams): Promise<Customer[]> => {
    const q = params ? `?${new URLSearchParams(params as Record<string, string>).toString()}` : "";
    return request<Customer[]>(`/customers/${businessId}${q}`);
  },
  getProfile: (id: string): Promise<Customer> => request<Customer>(`/customers/${id}/profile`),
  update: (id: string, data: CustomerUpdate): Promise<Customer> =>
    request<Customer>(`/customers/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  segment: (data: { customer_id: string; segment: string }): Promise<Customer> =>
    request<Customer>("/customers/segment", { method: "POST", body: JSON.stringify(data) }),
  getSegments: (businessId: string): Promise<Segment[]> =>
    request<Segment[]>(`/customers/segments/${businessId}`),
  search: (businessId: string, q: string): Promise<Customer[]> =>
    request<Customer[]>(`/customers/search/${businessId}?q=${encodeURIComponent(q)}`),
  importCsv: (businessId: string, csvData: string): Promise<{ imported: number }> =>
    request<{ imported: number }>(`/customers/import?business_id=${businessId}`, {
      method: "POST",
      body: JSON.stringify({ csv_data: csvData }),
    }),
  exportCsv: (businessId: string): Promise<Customer[]> =>
    request<Customer[]>(`/customers/export?business_id=${businessId}`),
};

// ── Analytics ──
export const analytics = {
  dashboard: (businessId: string, period?: string): Promise<DashboardStats> =>
    request<DashboardStats>(`/analytics/dashboard/${businessId}?period=${period || "7d"}`),
  revenue: (businessId: string): Promise<RevenueForecast> =>
    request<RevenueForecast>(`/analytics/revenue/${businessId}`),
  transactions: (businessId: string): Promise<Transaction[]> =>
    request<Transaction[]>(`/analytics/transactions/${businessId}`),
  customers: (businessId: string): Promise<Customer[]> =>
    request<Customer[]>(`/analytics/customers/${businessId}`),
  insights: (businessId: string): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>(`/analytics/insights/${businessId}`),
  activity: (businessId: string): Promise<{ text: string; time: string; type: string }[]> =>
    request<{ text: string; time: string; type: string }[]>(`/analytics/activity/${businessId}`),
  refresh: (businessId: string): Promise<{ message: string }> =>
    request<{ message: string }>(`/analytics/refresh/${businessId}`, { method: "POST" }),
};

// ── Loyalty ──
export const loyalty = {
  programs: (businessId: string): Promise<LoyaltyProgram[]> =>
    request<LoyaltyProgram[]>(`/loyalty/programs?business_id=${businessId}`),
  createProgram: (data: Partial<LoyaltyProgram>): Promise<LoyaltyProgram> =>
    request<LoyaltyProgram>("/loyalty/programs", { method: "POST", body: JSON.stringify(data) }),
  tiers: (businessId: string): Promise<LoyaltyTier[]> =>
    request<LoyaltyTier[]>(`/loyalty/tiers/${businessId}`),
  createTier: (data: Partial<LoyaltyTier>): Promise<LoyaltyTier> =>
    request<LoyaltyTier>("/loyalty/tiers", { method: "POST", body: JSON.stringify(data) }),
  analytics: (businessId: string): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>(`/loyalty/analytics/${businessId}`),
  balance: (customerId: string): Promise<LoyaltyBalance> =>
    request<LoyaltyBalance>(`/loyalty/balance/${customerId}`),
  earn: (data: { customer_id: string; points: number; description?: string }): Promise<LoyaltyTransaction> =>
    request<LoyaltyTransaction>("/loyalty/earn", { method: "POST", body: JSON.stringify(data) }),
  redeem: (data: { customer_id: string; points: number; description?: string }): Promise<LoyaltyTransaction> =>
    request<LoyaltyTransaction>("/loyalty/redeem", { method: "POST", body: JSON.stringify(data) }),
  history: (customerId: string): Promise<LoyaltyTransaction[]> =>
    request<LoyaltyTransaction[]>(`/loyalty/history/${customerId}`),
  referrals: (data: { referrer_id: string; referred_id: string }): Promise<LoyaltyTransaction> =>
    request<LoyaltyTransaction>("/loyalty/referrals", { method: "POST", body: JSON.stringify(data) }),
};

// ── Inventory ──
export const inventory = {
  list: (businessId: string): Promise<Product[]> =>
    request<Product[]>(`/inventory/${businessId}`),
  add: (data: ProductCreate): Promise<Product> =>
    request<Product>("/inventory/products", { method: "POST", body: JSON.stringify(data) }),
  update: (id: string, data: Partial<ProductCreate>): Promise<Product> =>
    request<Product>(`/inventory/products/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  delete: (id: string): Promise<{ message: string }> =>
    request<{ message: string }>(`/inventory/products/${id}`, { method: "DELETE" }),
  updateStock: (id: string, data: { quantity: number; operation?: string }): Promise<Product> =>
    request<Product>(`/inventory/products/${id}/stock`, { method: "PUT", body: JSON.stringify(data) }),
  lowStock: (businessId: string): Promise<Product[]> =>
    request<Product[]>(`/inventory/low-stock/${businessId}`),
  analytics: (businessId: string): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>(`/inventory/analytics/${businessId}`),
};

// ── Feedback ──
export const feedback = {
  nps: (businessId: string): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>(`/feedback/nps/${businessId}`),
  sendNps: (data: { business_id: string; customer_id: string; score: number }): Promise<{ message: string }> =>
    request<{ message: string }>("/feedback/nps/send", { method: "POST", body: JSON.stringify(data) }),
  reviews: (businessId: string): Promise<Review[]> =>
    request<Review[]>(`/feedback/reviews/${businessId}`),
  monitorReviews: (businessId: string): Promise<{ message: string }> =>
    request<{ message: string }>(`/feedback/reviews/monitor/${businessId}`, { method: "POST" }),
  surveys: (businessId: string): Promise<Survey[]> =>
    request<Survey[]>(`/feedback/surveys/${businessId}`),
  createSurvey: (data: Partial<Survey>): Promise<Survey> =>
    request<Survey>("/feedback/surveys", { method: "POST", body: JSON.stringify(data) }),
};

// ── Revenue ──
export const revenue = {
  forecast: (businessId: string, days?: number): Promise<RevenueData> =>
    request<RevenueData>(`/revenue/forecast/${businessId}?days=${days || 30}`),
  patterns: (businessId: string): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>(`/revenue/patterns/${businessId}`),
  alerts: (businessId: string): Promise<Record<string, unknown>[]> =>
    request<Record<string, unknown>[]>(`/revenue/alerts/${businessId}`),
  whatIf: (businessId: string, params?: Record<string, string>): Promise<Record<string, unknown>> => {
    const q = params ? `?${new URLSearchParams(params).toString()}` : "";
    return request<Record<string, unknown>>(`/revenue/what-if/${businessId}${q}`);
  },
};

// ── Admin ──
export const admin = {
  users: (params?: PaginationParams): Promise<User[]> => {
    const q = params ? `?${new URLSearchParams(params as Record<string, string>).toString()}` : "";
    return request<User[]>(`/admin/users${q}`);
  },
  getUser: (id: string): Promise<User> => request<User>(`/admin/users/${id}`),
  updateRole: (id: string, role: string): Promise<User> =>
    request<User>(`/admin/users/${id}/role`, { method: "PUT", body: JSON.stringify({ role }) }),
  billingOverview: (): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>("/admin/billing/overview"),
  getSubscription: (userId: string): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>(`/admin/billing/subscription/${userId}`),
  updateSubscription: (userId: string, data: Record<string, unknown>): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>(`/admin/billing/subscription/${userId}`, { method: "PUT", body: JSON.stringify(data) }),
  integrationsOverview: (): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>("/admin/integrations/overview"),
  apiKeys: (): Promise<Record<string, unknown>[]> =>
    request<Record<string, unknown>[]>("/admin/api-keys"),
  createApiKey: (data: { name: string; permissions?: string[] }): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>("/admin/api-keys", { method: "POST", body: JSON.stringify(data) }),
  revokeApiKey: (id: string): Promise<{ message: string }> =>
    request<{ message: string }>(`/admin/api-keys/${id}`, { method: "DELETE" }),
  systemStatus: (): Promise<{ status: string }> =>
    request<{ status: string }>("/health"),
  payments: (businessId: string): Promise<Payment[]> =>
    request<Payment[]>(`/admin/payments?business_id=${businessId}`),
  generateQR: (amount: string, customerName: string, customerEmail: string, customerPhone: string, businessId?: string): Promise<QRResponse> =>
    request<QRResponse>(`/admin/qr/generate?amount=${amount}&customer_name=${encodeURIComponent(customerName)}&customer_email=${encodeURIComponent(customerEmail)}&customer_phone=${encodeURIComponent(customerPhone)}${businessId ? `&business_id=${businessId}` : ""}`, { method: "POST" }),
  updatePaymentStatus: (id: string, status: string): Promise<Payment> =>
    request<Payment>(`/admin/payments/${id}/status`, { method: "POST", body: JSON.stringify({ status }) }),
};

// ── Integrations ──
export const integrations = {
  status: (businessId: string): Promise<{ integrations: IntegrationStatus[] }> =>
    request<{ integrations: IntegrationStatus[] }>(`/integrations/status/${businessId}`),
  connectGoogleBusiness: (data: IntegrationConnect): Promise<{ message: string }> =>
    request<{ message: string }>("/integrations/connect/google-business", { method: "POST", body: JSON.stringify(data) }),
  connectInstagram: (data: IntegrationConnect): Promise<{ message: string }> =>
    request<{ message: string }>("/integrations/connect/instagram", { method: "POST", body: JSON.stringify(data) }),
  connectRazorpay: (data: IntegrationConnect): Promise<{ message: string }> =>
    request<{ message: string }>("/integrations/connect/razorpay", { method: "POST", body: JSON.stringify(data) }),
  connectPhonepe: (data: IntegrationConnect): Promise<{ message: string }> =>
    request<{ message: string }>("/integrations/connect/phonepe", { method: "POST", body: JSON.stringify(data) }),
  connectTally: (data: IntegrationConnect): Promise<{ message: string }> =>
    request<{ message: string }>("/integrations/connect/tally", { method: "POST", body: JSON.stringify(data) }),
  disconnect: (type: string, businessId: string): Promise<{ message: string }> =>
    request<{ message: string }>(`/integrations/disconnect/${type}?business_id=${businessId}`, { method: "POST" }),
  reviews: (businessId: string): Promise<Review[]> =>
    request<Review[]>(`/integrations/reviews/${businessId}`),
  replyReview: (reviewId: string, data: { reply: string }): Promise<{ message: string }> =>
    request<{ message: string }>(`/integrations/google-business/reply/${reviewId}`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  instagramMessages: (businessId: string): Promise<ChatMessage[]> =>
    request<ChatMessage[]>(`/integrations/instagram/messages/${businessId}`),
  razorpayCreateLink: (data: { amount: number; description?: string; customer_name?: string }): Promise<{ payment_link: string }> =>
    request<{ payment_link: string }>("/integrations/razorpay/create-payment-link", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  razorpayStatus: (id: string): Promise<Payment> =>
    request<Payment>(`/integrations/razorpay/transaction/${id}`),
  phonepeCreate: (data: { amount: number; merchant_transaction_id?: string }): Promise<{ payment_url: string }> =>
    request<{ payment_url: string }>("/integrations/phonepe/create-payment", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  phonepeStatus: (id: string): Promise<Payment> =>
    request<Payment>(`/integrations/phonepe/status/${id}`),
};

// ── Webhooks ──
export const webhooks = {
  list: (businessId: string): Promise<Webhook[]> =>
    request<Webhook[]>(`/webhooks/?business_id=${businessId}`),
  register: (data: { business_id: string; url: string; events: string[] }): Promise<Webhook> =>
    request<Webhook>("/webhooks/register", { method: "POST", body: JSON.stringify(data) }),
  delete: (id: string): Promise<{ message: string }> =>
    request<{ message: string }>(`/webhooks/${id}`, { method: "DELETE" }),
  test: (id: string): Promise<{ message: string }> =>
    request<{ message: string }>(`/webhooks/${id}/test`, { method: "POST" }),
  logs: (id: string): Promise<WebhookLog[]> =>
    request<WebhookLog[]>(`/webhooks/${id}/logs`),
  retry: (id: string): Promise<{ message: string }> =>
    request<{ message: string }>(`/webhooks/${id}/retry`, { method: "POST" }),
  stats: (businessId: string): Promise<WebhookStats> =>
    request<WebhookStats>(`/webhooks/stats/${businessId}`),
};

// ── Catalog ──
export const catalog = {
  list: (businessId: string): Promise<Product[]> =>
    request<Product[]>(`/catalog/${businessId}`),
  search: (businessId: string, query: string): Promise<Product[]> =>
    request<Product[]>(`/catalog/${businessId}/search?q=${encodeURIComponent(query)}`),
  categories: (businessId: string): Promise<string[]> =>
    request<string[]>(`/catalog/${businessId}/categories`),
  recommendations: (businessId: string, productId: string): Promise<Product[]> =>
    request<Product[]>(`/catalog/${businessId}/recommendations?product_id=${productId}`),
  whatsapp: (businessId: string): Promise<Product[]> =>
    request<Product[]>(`/catalog/${businessId}/whatsapp`),
};

// ── Payments ──
export const payments = {
  list: (businessId: string): Promise<Payment[]> =>
    request<Payment[]>(`/payments/${businessId}`),
  createLink: (businessId: string, data: { amount: number; description?: string; customer_name?: string; customer_phone?: string }): Promise<{ link: string }> =>
    request<{ link: string }>(`/payments/${businessId}/link`, { method: "POST", body: JSON.stringify(data) }),
  whatsappLink: (businessId: string, data: { amount: number; description?: string; customer_name?: string; customer_phone?: string }): Promise<{ link: string }> =>
    request<{ link: string }>(`/payments/${businessId}/link/whatsapp`, { method: "POST", body: JSON.stringify(data) }),
  updateStatus: (paymentId: string, status: string): Promise<Payment> =>
    request<Payment>(`/payments/${paymentId}/status`, { method: "PUT", body: JSON.stringify({ status }) }),
  stats: (businessId: string): Promise<Record<string, number>> =>
    request<Record<string, number>>(`/payments/${businessId}/stats`),
};

// ── Conversation Analytics ──
export const conversationAnalytics = {
  stats: (businessId: string): Promise<ConversationStats> =>
    request<ConversationStats>(`/analytics/conversations/${businessId}`),
  sentiment: (businessId: string): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>(`/analytics/conversations/${businessId}/sentiment`),
  engagement: (businessId: string): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>(`/analytics/conversations/${businessId}/engagement`),
  intents: (businessId: string): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>(`/analytics/conversations/${businessId}/intents`),
  detectLanguage: (text: string): Promise<{ language: string; confidence: number }> =>
    request<{ language: string; confidence: number }>("/analytics/language/detect", { method: "POST", body: JSON.stringify({ text }) }),
};

// ── Templates ──
export const templates = {
  list: (): Promise<Template[]> => request<Template[]>("/whatsapp/templates"),
  create: (data: TemplateCreate): Promise<Template> =>
    request<Template>("/whatsapp/templates", { method: "POST", body: JSON.stringify(data) }),
  delete: (id: string): Promise<{ message: string }> =>
    request<{ message: string }>(`/whatsapp/templates/${id}`, { method: "DELETE" }),
  categories: (): Promise<string[]> => request<string[]>("/whatsapp/templates/categories"),
};

// ── Audit ──
export const audit = {
  logs: (businessId: string, params?: PaginationParams & StatusFilter): Promise<AuditLog[]> => {
    const q = params ? `?${new URLSearchParams(params as Record<string, string>).toString()}` : "";
    return request<AuditLog[]>(`/audit/${businessId}${q}`);
  },
  compliance: (businessId: string, period?: string): Promise<AuditCompliance> =>
    request<AuditCompliance>(`/audit/compliance/${businessId}?period=${period || "30d"}`),
};

// ── Orders ──
export const orders = {
  list: (businessId: string, status?: string): Promise<Order[]> =>
    request<Order[]>(`/orders/${businessId}${status ? `?status=${status}` : ""}`),
  stats: (businessId: string): Promise<Record<string, number>> =>
    request<Record<string, number>>(`/orders/${businessId}/stats`),
  update: (orderId: string, data: OrderUpdate): Promise<Order> =>
    request<Order>(`/orders/${orderId}`, { method: "PUT", body: JSON.stringify(data) }),
  invoice: (orderId: string): string => `${API_BASE}/orders/${orderId}/invoice`,
  paymentLink: (orderId: string): string => `${API_BASE}/orders/${orderId}/payment-link`,
};

// ── Chat (Baileys / Web Chat) ──
export const chat = {
  send: (data: { message: string; business_id: string; session_id: string; customer_name?: string; customer_phone?: string }): Promise<ChatMessage> =>
    request<ChatMessage>("/chat", { method: "POST", body: JSON.stringify(data) }),
  sessions: (businessId: string): Promise<Record<string, unknown>[]> =>
    request<Record<string, unknown>[]>(`/chat/sessions/${businessId}`),
  qr: (businessId: string): Promise<{ qr: string }> =>
    request<{ qr: string }>(`/chat/qr/${businessId}`),
  conversations: (businessId: string): Promise<Conversation[]> =>
    request<Conversation[]>(`/chat/conversations/${businessId}`),
  messages: (conversationId: string): Promise<ChatMessage[]> =>
    request<ChatMessage[]>(`/chat/messages/${conversationId}`),
  reply: (data: { conversation_id: string; message: string; business_id: string }): Promise<ChatMessage> =>
    request<ChatMessage>("/chat/reply", { method: "POST", body: JSON.stringify(data) }),
  buy: (data: { product_id: string; quantity: number; business_id: string; customer_phone: string; customer_name?: string }): Promise<{ order_id: string; total: number }> =>
    request<{ order_id: string; total: number }>("/chat/buy", { method: "POST", body: JSON.stringify(data) }),
  confirmPayment: (payment_id: string): Promise<{ message: string }> =>
    request<{ message: string }>("/chat/confirm-payment", { method: "POST", body: JSON.stringify({ payment_id }) }),
  cancelOrder: (payment_id: string): Promise<{ message: string }> =>
    request<{ message: string }>("/chat/cancel-order", { method: "POST", body: JSON.stringify({ payment_id }) }),
  orderStatus: (orderId: string): Promise<Order> =>
    request<Order>(`/chat/order/${orderId}`),
  clearMessages: (conversationId: string): Promise<{ message: string }> =>
    request<{ message: string }>(`/chat/messages/${conversationId}`, { method: "DELETE" }),
  deleteConversation: (conversationId: string): Promise<{ message: string }> =>
    request<{ message: string }>(`/chat/conversation/${conversationId}`, { method: "DELETE" }),
};

// ── Teams ──
export const teams = {
  list: (businessId: string): Promise<Team[]> =>
    request<Team[]>(`/teams/${businessId}`),
  create: (data: TeamCreate): Promise<Team> =>
    request<Team>("/teams", { method: "POST", body: JSON.stringify(data) }),
  get: (teamId: string): Promise<Team> =>
    request<Team>(`/teams/detail/${teamId}`),
  update: (teamId: string, data: Partial<TeamCreate>): Promise<Team> =>
    request<Team>(`/teams/${teamId}`, { method: "PUT", body: JSON.stringify(data) }),
  delete: (teamId: string): Promise<{ message: string }> =>
    request<{ message: string }>(`/teams/${teamId}`, { method: "DELETE" }),
  addMember: (teamId: string, data: TeamMemberAdd): Promise<TeamMember> =>
    request<TeamMember>(`/teams/${teamId}/members`, { method: "POST", body: JSON.stringify(data) }),
  removeMember: (teamId: string, memberId: string): Promise<{ message: string }> =>
    request<{ message: string }>(`/teams/${teamId}/members/${memberId}`, { method: "DELETE" }),
  updateMember: (teamId: string, memberId: string, data: Partial<TeamMemberAdd>): Promise<TeamMember> =>
    request<TeamMember>(`/teams/${teamId}/members/${memberId}`, { method: "PUT", body: JSON.stringify(data) }),
  myPermissions: (teamId: string): Promise<Record<string, boolean>> =>
    request<Record<string, boolean>>(`/teams/${teamId}/my-permissions`),
};

// ── Inventory Alerts ──
export const inventoryAlerts = {
  list: (businessId: string, status?: string): Promise<InventoryAlert[]> =>
    request<InventoryAlert[]>(`/inventory-alerts/${businessId}${status ? `?status=${status}` : ""}`),
  create: (data: Partial<InventoryAlert>): Promise<InventoryAlert> =>
    request<InventoryAlert>("/inventory-alerts", { method: "POST", body: JSON.stringify(data) }),
  get: (alertId: string): Promise<InventoryAlert> =>
    request<InventoryAlert>(`/inventory-alerts/detail/${alertId}`),
  update: (alertId: string, data: Partial<InventoryAlert>): Promise<InventoryAlert> =>
    request<InventoryAlert>(`/inventory-alerts/${alertId}`, { method: "PUT", body: JSON.stringify(data) }),
  resolve: (alertId: string): Promise<InventoryAlert> =>
    request<InventoryAlert>(`/inventory-alerts/${alertId}/resolve`, { method: "POST" }),
  checkStock: (businessId: string): Promise<{ checked: number; alerts: number }> =>
    request<{ checked: number; alerts: number }>(`/inventory-alerts/check/${businessId}`, { method: "POST" }),
  stats: (businessId: string): Promise<InventoryAlertStats> =>
    request<InventoryAlertStats>(`/inventory-alerts/stats/${businessId}`),
};

// ── Follow-ups ──
export const followups = {
  list: (businessId: string, status?: string): Promise<FollowUp[]> =>
    request<FollowUp[]>(`/followups/${businessId}${status ? `?status=${status}` : ""}`),
  create: (data: FollowUpCreate): Promise<FollowUp> =>
    request<FollowUp>("/followups", { method: "POST", body: JSON.stringify(data) }),
  get: (followupId: string): Promise<FollowUp> =>
    request<FollowUp>(`/followups/detail/${followupId}`),
  update: (followupId: string, data: Partial<FollowUpCreate>): Promise<FollowUp> =>
    request<FollowUp>(`/followups/${followupId}`, { method: "PUT", body: JSON.stringify(data) }),
  complete: (followupId: string): Promise<FollowUp> =>
    request<FollowUp>(`/followups/${followupId}/complete`, { method: "POST" }),
  cancel: (followupId: string): Promise<FollowUp> =>
    request<FollowUp>(`/followups/${followupId}/cancel`, { method: "POST" }),
  stats: (businessId: string): Promise<FollowUpStats> =>
    request<FollowUpStats>(`/followups/stats/${businessId}`),
};

// ── Segments ──
export const segments = {
  list: (businessId: string): Promise<Segment[]> =>
    request<Segment[]>(`/segments/${businessId}`),
  create: (data: SegmentCreate): Promise<Segment> =>
    request<Segment>("/segments", { method: "POST", body: JSON.stringify(data) }),
  get: (segmentId: string): Promise<Segment> =>
    request<Segment>(`/segments/detail/${segmentId}`),
  update: (segmentId: string, data: Partial<SegmentCreate>): Promise<Segment> =>
    request<Segment>(`/segments/${segmentId}`, { method: "PUT", body: JSON.stringify(data) }),
  delete: (segmentId: string): Promise<{ message: string }> =>
    request<{ message: string }>(`/segments/${segmentId}`, { method: "DELETE" }),
  assignCustomer: (segmentId: string, data: { customer_id: string }): Promise<{ message: string }> =>
    request<{ message: string }>(`/segments/${segmentId}/assign`, { method: "POST", body: JSON.stringify(data) }),
  removeCustomer: (segmentId: string, customerId: string): Promise<{ message: string }> =>
    request<{ message: string }>(`/segments/${segmentId}/remove/${customerId}`, { method: "DELETE" }),
  refresh: (segmentId: string): Promise<{ message: string; count: number }> =>
    request<{ message: string; count: number }>(`/segments/${segmentId}/refresh`, { method: "POST" }),
  auto: (businessId: string): Promise<{ message: string; created: number }> =>
    request<{ message: string; created: number }>(`/segments/auto/${businessId}`, { method: "POST" }),
  stats: (businessId: string): Promise<SegmentStats> =>
    request<SegmentStats>(`/segments/stats/${businessId}`),
};

// ── Scheduled Messages ──
export const scheduledMessages = {
  list: (businessId: string, status?: string): Promise<ScheduledMessage[]> =>
    request<ScheduledMessage[]>(`/scheduled-messages/${businessId}${status ? `?status=${status}` : ""}`),
  create: (data: ScheduledMessageCreate): Promise<ScheduledMessage> =>
    request<ScheduledMessage>("/scheduled-messages", { method: "POST", body: JSON.stringify(data) }),
  get: (messageId: string): Promise<ScheduledMessage> =>
    request<ScheduledMessage>(`/scheduled-messages/detail/${messageId}`),
  update: (messageId: string, data: Partial<ScheduledMessageCreate>): Promise<ScheduledMessage> =>
    request<ScheduledMessage>(`/scheduled-messages/${messageId}`, { method: "PUT", body: JSON.stringify(data) }),
  cancel: (messageId: string): Promise<ScheduledMessage> =>
    request<ScheduledMessage>(`/scheduled-messages/${messageId}/cancel`, { method: "POST" }),
  delete: (messageId: string): Promise<{ message: string }> =>
    request<{ message: string }>(`/scheduled-messages/${messageId}`, { method: "DELETE" }),
  pending: (businessId: string): Promise<ScheduledMessage[]> =>
    request<ScheduledMessage[]>(`/scheduled-messages/pending/${businessId}`),
  stats: (businessId: string): Promise<ScheduledMessageStats> =>
    request<ScheduledMessageStats>(`/scheduled-messages/stats/${businessId}`),
};

// ── Exports ──
export const exportsApi = {
  list: (businessId: string): Promise<ExportJob[]> =>
    request<ExportJob[]>(`/exports/${businessId}`),
  create: (data: { business_id: string; export_type: string; format: string }): Promise<ExportJob> =>
    request<ExportJob>("/exports", { method: "POST", body: JSON.stringify(data) }),
  get: (exportId: string): Promise<ExportJob> =>
    request<ExportJob>(`/exports/detail/${exportId}`),
  download: (exportId: string): string => `${API_BASE}/exports/download/${exportId}`,
  delete: (exportId: string): Promise<{ message: string }> =>
    request<{ message: string }>(`/exports/${exportId}`, { method: "DELETE" }),
  stats: (businessId: string): Promise<ExportStats> =>
    request<ExportStats>(`/exports/stats/${businessId}`),
};

// ── Monitoring ──
export const monitoring = {
  metrics: (): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>("/metrics"),
  healthDetailed: (): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>("/health/detailed"),
};

// ── Settings ──
export const settings = {
  get: (): Promise<Record<string, unknown>> => {
    const bizId = getBusinessId();
    return request<Record<string, unknown>>(`/settings${bizId ? `?business_id=${bizId}` : ""}`);
  },
  update: (section: string, data: unknown): Promise<{ message: string }> =>
    request<{ message: string }>(`/settings/${section}`, { method: "PUT", body: JSON.stringify(data) }),
};
