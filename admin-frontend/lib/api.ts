const MASTER_API = process.env.NEXT_PUBLIC_MASTER_API_URL || "http://localhost:8010";

interface RequestOptions {
  method?: string;
  body?: any;
  headers?: Record<string, string>;
}

class MasterAPI {
  private token: string | null = null;

  constructor() {
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("admin_token");
    }
  }

  setToken(token: string) {
    this.token = token;
    if (typeof window !== "undefined") {
      localStorage.setItem("admin_token", token);
    }
  }

  clearToken() {
    this.token = null;
    if (typeof window !== "undefined") {
      localStorage.removeItem("admin_token");
    }
  }

  async request(path: string, options: RequestOptions = {}) {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...options.headers,
    };
    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }

    const res = await fetch(`${MASTER_API}${path}`, {
      method: options.method || "GET",
      headers,
      body: options.body ? JSON.stringify(options.body) : undefined,
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || `Request failed: ${res.status}`);
    }
    return data;
  }

  // ─── Auth ─────────────────────────────────────────────────
  async login(email: string, password: string) {
    const data = await this.request("/admin/login", {
      method: "POST",
      body: { email, password },
    });
    this.setToken(data.token);
    return data;
  }

  logout() {
    this.clearToken();
  }

  async getMe() {
    return this.request("/admin/me");
  }

  // ─── Tenants ─────────────────────────────────────────────
  async getTenants(params?: { status?: string; plan?: string; search?: string; page?: number; limit?: number }) {
    const qs = new URLSearchParams();
    if (params?.status) qs.set("status", params.status);
    if (params?.plan) qs.set("plan", params.plan);
    if (params?.search) qs.set("search", params.search);
    if (params?.page) qs.set("page", String(params.page));
    if (params?.limit) qs.set("limit", String(params.limit));
    return this.request(`/admin/tenants?${qs.toString()}`);
  }

  async getTenant(id: string) {
    return this.request(`/admin/tenants/${id}`);
  }

  async createTenant(data: { name: string; owner_name: string; owner_email: string; plan?: string; owner_phone?: string }) {
    return this.request("/admin/tenants", { method: "POST", body: data });
  }

  async updateTenant(id: string, data: Partial<{ name: string; owner_name: string; owner_email: string; owner_phone: string; status: string; plan: string }>) {
    return this.request(`/admin/tenants/${id}`, { method: "PUT", body: data });
  }

  async deleteTenant(id: string) {
    return this.request(`/admin/tenants/${id}`, { method: "DELETE" });
  }

  async suspendTenant(id: string, reason: string) {
    return this.request(`/admin/tenants/${id}/suspend`, { method: "POST", body: { reason } });
  }

  async reactivateTenant(id: string) {
    return this.request(`/admin/tenants/${id}/reactivate`, { method: "POST" });
  }

  async updateTenantPlan(tenantId: string, plan: string) {
    return this.request(`/admin/tenants/${tenantId}/plan`, { method: "PUT", body: { plan } });
  }

  async getTenantData(tenantId: string, table: string, page?: number) {
    const qs = page ? `?page=${page}&limit=50` : "?limit=50";
    return this.request(`/admin/tenants/${tenantId}/data/${table}${qs}`);
  }

  async impersonateTenant(tenantId: string) {
    return this.request(`/admin/tenants/${tenantId}/impersonate`, { method: "POST" });
  }

  // ─── AI Providers ─────────────────────────────────────────
  async getAIProviders() {
    return this.request("/admin/ai-providers");
  }

  async createAIProvider(data: any) {
    return this.request("/admin/ai-providers", { method: "POST", body: data });
  }

  async updateAIProvider(id: string, data: any) {
    return this.request(`/admin/ai-providers/${id}`, { method: "PUT", body: data });
  }

  async deleteAIProvider(id: string) {
    return this.request(`/admin/ai-providers/${id}`, { method: "DELETE" });
  }

  async testAIProvider(id: string) {
    return this.request(`/admin/ai-providers/${id}/test`, { method: "POST" });
  }

  async getAIUsage(params?: { tenant_id?: string; provider_key?: string; days?: number }) {
    const qs = new URLSearchParams();
    if (params?.tenant_id) qs.set("tenant_id", params.tenant_id);
    if (params?.provider_key) qs.set("provider_key", params.provider_key);
    if (params?.days) qs.set("days", String(params.days));
    return this.request(`/admin/ai-usage?${qs.toString()}`);
  }

  // ─── Analytics ────────────────────────────────────────────
  async getAnalyticsOverview() {
    return this.request("/admin/analytics/overview");
  }

  async getDailyStats(days: number = 30) {
    return this.request(`/admin/analytics/daily?days=${days}`);
  }

  async getGrowthStats() {
    return this.request("/admin/analytics/growth");
  }

  async getTopTenants(limit: number = 10) {
    return this.request(`/admin/analytics/top-tenants?limit=${limit}`);
  }

  async aggregateStats() {
    return this.request("/admin/analytics/aggregate", { method: "POST" });
  }

  // ─── Billing ─────────────────────────────────────────────
  async getInvoices(params?: { status?: string; tenant_id?: string; page?: number }) {
    const qs = new URLSearchParams();
    if (params?.status) qs.set("status", params.status);
    if (params?.tenant_id) qs.set("tenant_id", params.tenant_id);
    if (params?.page) qs.set("page", String(params.page));
    return this.request(`/admin/billing/invoices?${qs.toString()}`);
  }

  async createInvoice(data: { tenant_id: string; amount: number; plan: string; billing_period?: string }) {
    return this.request("/admin/billing/invoices", { method: "POST", body: data });
  }

  async updateInvoice(id: string, data: { status: string; payment_id?: string }) {
    return this.request(`/admin/billing/invoices/${id}`, { method: "PUT", body: data });
  }

  async getRevenue() {
    return this.request("/admin/billing/revenue");
  }

  async generateMonthlyInvoices() {
    return this.request("/admin/billing/generate-monthly", { method: "POST" });
  }

  // ─── Audit Log ────────────────────────────────────────────
  async getAuditLogs(params?: { admin_user_id?: string; action?: string; page?: number; limit?: number; start_date?: string; end_date?: string }) {
    const qs = new URLSearchParams();
    if (params?.admin_user_id) qs.set("admin_user_id", params.admin_user_id);
    if (params?.action) qs.set("action", params.action);
    if (params?.page) qs.set("page", String(params.page));
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.start_date) qs.set("start_date", params.start_date);
    if (params?.end_date) qs.set("end_date", params.end_date);
    return this.request(`/admin/audit-logs?${qs.toString()}`);
  }

  async exportAuditLogs(params?: { start_date?: string; end_date?: string }) {
    const qs = new URLSearchParams();
    if (params?.start_date) qs.set("start_date", params.start_date);
    if (params?.end_date) qs.set("end_date", params.end_date);
    return this.request(`/admin/audit-logs/export?${qs.toString()}`);
  }

  // ─── Feature Flags ────────────────────────────────────────
  async getFeatureFlags() {
    return this.request("/admin/feature-flags");
  }

  async createFeatureFlag(data: { flag_name: string; description: string; enabled: boolean }) {
    return this.request("/admin/feature-flags", { method: "POST", body: data });
  }

  async updateFeatureFlag(id: string, data: { enabled?: boolean; description?: string; target_tenant_ids?: string[] }) {
    return this.request(`/admin/feature-flags/${id}`, { method: "PUT", body: data });
  }

  async deleteFeatureFlag(id: string) {
    return this.request(`/admin/feature-flags/${id}`, { method: "DELETE" });
  }

  // ─── Team Management ──────────────────────────────────────
  async getTeamMembers() {
    return this.request("/admin/team");
  }

  async createTeamMember(data: { email: string; name: string; role: string; password: string }) {
    return this.request("/admin/team", { method: "POST", body: data });
  }

  async updateTeamMember(id: string, data: { name?: string; role?: string; is_active?: boolean }) {
    return this.request(`/admin/team/${id}`, { method: "PUT", body: data });
  }

  async deleteTeamMember(id: string) {
    return this.request(`/admin/team/${id}`, { method: "DELETE" });
  }

  // ─── API Keys ────────────────────────────────────────────
  async getAPIKeys() {
    return this.request("/admin/api-keys");
  }

  async createAPIKey(data: { name: string; permissions: string[]; rate_limit?: number }) {
    return this.request("/admin/api-keys", { method: "POST", body: data });
  }

  async revokeAPIKey(id: string) {
    return this.request(`/admin/api-keys/${id}`, { method: "DELETE" });
  }

  // ─── WhatsApp Monitor ─────────────────────────────────────
  async getWhatsAppStatus() {
    return this.request("/admin/whatsapp/status");
  }

  async forceReconnectBot(tenantId: string) {
    return this.request(`/admin/whatsapp/${tenantId}/reconnect`, { method: "POST" });
  }

  async disconnectBot(tenantId: string) {
    return this.request(`/admin/whatsapp/${tenantId}/disconnect`, { method: "POST" });
  }

  // ─── Support Tickets ─────────────────────────────────────
  async getSupportTickets(params?: { status?: string; priority?: string; page?: number }) {
    const qs = new URLSearchParams();
    if (params?.status) qs.set("status", params.status);
    if (params?.priority) qs.set("priority", params.priority);
    if (params?.page) qs.set("page", String(params.page));
    return this.request(`/admin/support/tickets?${qs.toString()}`);
  }

  async getSupportTicket(id: string) {
    return this.request(`/admin/support/tickets/${id}`);
  }

  async updateSupportTicket(id: string, data: { status?: string; priority?: string; assigned_to?: string; internal_notes?: string }) {
    return this.request(`/admin/support/tickets/${id}`, { method: "PUT", body: data });
  }

  async replySupportTicket(id: string, message: string) {
    return this.request(`/admin/support/tickets/${id}/reply`, { method: "POST", body: { message } });
  }

  // ─── Notifications ────────────────────────────────────────
  async getNotifications(params?: { page?: number; unread_only?: boolean }) {
    const qs = new URLSearchParams();
    if (params?.page) qs.set("page", String(params.page));
    if (params?.unread_only) qs.set("unread_only", "true");
    return this.request(`/admin/notifications?${qs.toString()}`);
  }

  async markNotificationRead(id: string) {
    return this.request(`/admin/notifications/${id}/read`, { method: "POST" });
  }

  async getNotificationSettings() {
    return this.request("/admin/notifications/settings");
  }

  async updateNotificationSettings(data: { email_enabled: boolean; slack_webhook?: string; sms_enabled: boolean; alert_thresholds: any }) {
    return this.request("/admin/notifications/settings", { method: "PUT", body: data });
  }

  // ─── Webhooks ─────────────────────────────────────────────
  async getPlatformWebhooks() {
    return this.request("/admin/webhooks");
  }

  async createPlatformWebhook(data: { url: string; events: string[]; secret: string }) {
    return this.request("/admin/webhooks", { method: "POST", body: data });
  }

  async updatePlatformWebhook(id: string, data: { url?: string; events?: string[]; active?: boolean }) {
    return this.request(`/admin/webhooks/${id}`, { method: "PUT", body: data });
  }

  async deletePlatformWebhook(id: string) {
    return this.request(`/admin/webhooks/${id}`, { method: "DELETE" });
  }

  async getWebhookDeliveryLogs(webhookId: string) {
    return this.request(`/admin/webhooks/${webhookId}/logs`);
  }

  // ─── Backups ──────────────────────────────────────────────
  async getBackups() {
    return this.request("/admin/backups");
  }

  async createBackup(tenantId?: string) {
    return this.request("/admin/backups", { method: "POST", body: { tenant_id: tenantId } });
  }

  async restoreBackup(backupId: string) {
    return this.request(`/admin/backups/${backupId}/restore`, { method: "POST" });
  }

  async downloadBackup(backupId: string) {
    return this.request(`/admin/backups/${backupId}/download`);
  }

  async deleteBackup(backupId: string) {
    return this.request(`/admin/backups/${backupId}`, { method: "DELETE" });
  }

  // ─── System Health ────────────────────────────────────────
  async getSystemHealth() {
    return this.request("/admin/system/health");
  }

  async getServiceStatus(service: string) {
    return this.request(`/admin/system/health/${service}`);
  }

  // ─── Resellers ────────────────────────────────────────────
  async getResellers() {
    return this.request("/admin/resellers");
  }

  async createReseller(data: { name: string; email: string; commission_rate: number }) {
    return this.request("/admin/resellers", { method: "POST", body: data });
  }

  async updateReseller(id: string, data: { name?: string; email?: string; commission_rate?: number; is_active?: boolean }) {
    return this.request(`/admin/resellers/${id}`, { method: "PUT", body: data });
  }

  async getResellerPayouts(resellerId: string) {
    return this.request(`/admin/resellers/${resellerId}/payouts`);
  }

  // ─── White-Label ──────────────────────────────────────────
  async getWhiteLabelConfigs() {
    return this.request("/admin/white-label");
  }

  async updateWhiteLabelConfig(tenantId: string, data: { logo_url?: string; primary_color?: string; domain?: string; remove_branding: boolean }) {
    return this.request(`/admin/white-label/${tenantId}`, { method: "PUT", body: data });
  }

  // ─── Integrations ─────────────────────────────────────────
  async getIntegrations() {
    return this.request("/admin/integrations");
  }

  async toggleIntegration(id: string, enabled: boolean) {
    return this.request(`/admin/integrations/${id}`, { method: "PUT", body: { enabled } });
  }

  // ─── Licenses (Desktop App) ───
  async getLicenses() {
    return this.request("/api/license/admin/licenses");
  }

  async getLicenseStats() {
    return this.request("/api/license/admin/licenses/stats");
  }

  async revokeLicense(licenseKey: string) {
    return this.request(`/api/license/admin/licenses/${licenseKey}/revoke`, { method: "POST" });
  }
}

export const masterAPI = new MasterAPI();
