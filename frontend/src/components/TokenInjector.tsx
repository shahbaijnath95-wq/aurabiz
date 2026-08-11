"use client";

import { useEffect } from "react";

/**
 * Desktop app se token URL query me aata hai (?token=XXX).
 * Isko localStorage me store karta hai — baaki frontend normal chalega.
 */
export default function TokenInjector() {
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");
    if (token) {
      localStorage.setItem("token", token);
      // URL se token param hatao (clean URL)
      const url = new URL(window.location.href);
      url.searchParams.delete("token");
      window.history.replaceState({}, "", url.toString());
      // Page reload karo taaki auth context fresh ho
      window.location.reload();
    }
  }, []);

  return null;
}
