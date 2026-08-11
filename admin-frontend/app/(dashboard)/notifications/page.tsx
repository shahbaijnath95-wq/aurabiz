"use client";
import { useEffect, useState } from "react";
import { masterAPI } from "@/lib/api";
import toast from "react-hot-toast";
import { Bell, Check, Settings as SettingsIcon } from "lucide-react";

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showSettings, setShowSettings] = useState(false);
  const [settings, setSettings] = useState<any>({
    email_enabled: true,
    slack_webhook: "",
    sms_enabled: false,
    alert_thresholds: {
      high_messages: 5000,
      failed_payments: 3,
      ban_alerts: true,
    },
  });

  const load = async () => {
    setLoading(true);
    try {
      const data = await masterAPI.getNotifications({ page: 1, unread_only: false });
      setNotifications(data.notifications || data.items || []);
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadSettings = async () => {
    try {
      const data = await masterAPI.getNotificationSettings();
      if (data && Object.keys(data).length > 0) setSettings(data);
    } catch (err: any) {
      // ignore if endpoint doesn't exist yet
    }
  };

  useEffect(() => { load(); loadSettings(); }, []);

  const handleMarkRead = async (id: string) => {
    try {
      await masterAPI.markNotificationRead(id);
      load();
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleSaveSettings = async () => {
    try {
      await masterAPI.updateNotificationSettings(settings);
      toast.success("Settings saved");
      setShowSettings(false);
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold inline-flex items-center gap-2">
          <Bell size={24} /> Notifications ({notifications.length})
        </h1>
        <button
          onClick={() => setShowSettings(!showSettings)}
          className="bg-gray-700 text-white px-3 py-2 rounded-lg text-sm inline-flex items-center gap-1"
        >
          <SettingsIcon size={14} /> Settings
        </button>
      </div>

      {showSettings && (
        <div className="bg-white rounded-xl shadow p-4 mb-4 space-y-3">
          <h3 className="font-bold">Notification Settings</h3>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={settings.email_enabled}
              onChange={(e) => setSettings({ ...settings, email_enabled: e.target.checked })}
            />
            Email notifications
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={settings.sms_enabled}
              onChange={(e) => setSettings({ ...settings, sms_enabled: e.target.checked })}
            />
            SMS notifications
          </label>
          <input
            type="text"
            placeholder="Slack Webhook URL"
            value={settings.slack_webhook || ""}
            onChange={(e) => setSettings({ ...settings, slack_webhook: e.target.value })}
            className="border rounded px-3 py-2 text-sm w-full"
          />
          <div className="border-t pt-3">
            <p className="text-sm font-medium mb-2">Alert Thresholds</p>
            <div className="grid grid-cols-2 gap-3">
              <label className="text-sm">
                High Messages/Day:
                <input
                  type="number"
                  value={settings.alert_thresholds?.high_messages || 5000}
                  onChange={(e) => setSettings({
                    ...settings,
                    alert_thresholds: { ...settings.alert_thresholds, high_messages: Number(e.target.value) },
                  })}
                  className="border rounded px-2 py-1 text-sm w-full"
                />
              </label>
              <label className="text-sm">
                Failed Payments:
                <input
                  type="number"
                  value={settings.alert_thresholds?.failed_payments || 3}
                  onChange={(e) => setSettings({
                    ...settings,
                    alert_thresholds: { ...settings.alert_thresholds, failed_payments: Number(e.target.value) },
                  })}
                  className="border rounded px-2 py-1 text-sm w-full"
                />
              </label>
            </div>
          </div>
          <button onClick={handleSaveSettings} className="bg-blue-600 text-white px-3 py-2 rounded-lg text-sm">
            Save Settings
          </button>
        </div>
      )}

      {loading ? (
        <div className="animate-pulse text-gray-400">Loading...</div>
      ) : notifications.length === 0 ? (
        <div className="text-gray-400 text-sm">No notifications found</div>
      ) : (
        <div className="space-y-2">
          {notifications.map((n) => (
            <div
              key={n.id}
              className={`bg-white rounded-xl shadow p-4 flex items-start gap-3 ${
                !n.read ? "border-l-4 border-blue-600" : ""
              }`}
            >
              <div className={`p-2 rounded-lg ${
                n.severity === "critical" ? "bg-red-100 text-red-600" :
                n.severity === "warning" ? "bg-yellow-100 text-yellow-600" :
                "bg-blue-100 text-blue-600"
              }`}>
                <Bell size={16} />
              </div>
              <div className="flex-1">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-medium text-sm">{n.title}</p>
                    <p className="text-xs text-gray-500">{n.message}</p>
                  </div>
                  <span className="text-xs text-gray-400">
                    {new Date(n.created_at).toLocaleString()}
                  </span>
                </div>
                {n.tenant_name && (
                  <p className="text-xs text-gray-400 mt-1">Tenant: {n.tenant_name}</p>
                )}
              </div>
              {!n.read && (
                <button
                  onClick={() => handleMarkRead(n.id)}
                  className="text-green-600 hover:underline text-xs inline-flex items-center gap-1"
                >
                  <Check size={12} /> Mark Read
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
