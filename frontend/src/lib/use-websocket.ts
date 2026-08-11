"use client";

import { useEffect, useRef, useState, useCallback } from "react";

interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

export function useWebSocket(businessId?: string) {
  const ws = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    if (typeof window === "undefined") return;

    const params = new URLSearchParams();
    if (businessId) params.set("business_id", businessId);
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    if (token) params.set("token", token);

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
    const wsProtocol = apiUrl.startsWith("https") ? "wss" : "ws";
    const wsHost = apiUrl.replace(/^https?:\/\//, "");

    // Build URL with business_id only (token sent via subprotocol)
    const url = `${wsProtocol}://${wsHost}/ws?business_id=${businessId || ""}`;

    try {
      // Pass token as subprotocol (not in query string — more secure)
      const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
      const protocols = token ? [`auth.${token}`] : [];
      ws.current = new WebSocket(url, protocols);

      ws.current.onopen = () => {
        setIsConnected(true);
        console.log("WebSocket connected");
      };

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLastMessage(data);
        } catch {}
      };

      ws.current.onclose = () => {
        setIsConnected(false);
        // Reconnect after 3 seconds
        reconnectTimeout.current = setTimeout(() => {
          connect();
        }, 3000);
      };

      ws.current.onerror = () => {
        setIsConnected(false);
      };
    } catch (error) {
      console.error("WebSocket connection failed:", error);
    }
  }, [businessId]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [connect]);

  const send = useCallback((message: any) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    }
  }, []);

  return { isConnected, lastMessage, send };
}
