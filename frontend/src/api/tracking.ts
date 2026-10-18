/**
 * Anonymous view counting for the organiser's statistics page.
 * Sends one small beacon per section view; nothing identifies the visitor.
 * Respects "Do Not Track" and "Global Privacy Control".
 */
type PrivacyNavigator = Navigator & { globalPrivacyControl?: boolean };

function trackingAllowed(): boolean {
  const nav = navigator as PrivacyNavigator;
  return nav.doNotTrack !== "1" && nav.globalPrivacyControl !== true;
}

export function trackView(slug: string, section: string): void {
  if (!trackingAllowed()) return;

  const url = `/api/tournaments/${encodeURIComponent(slug)}/track/`;
  const body = JSON.stringify({ section });

  try {
    if (navigator.sendBeacon) {
      const sent = navigator.sendBeacon(url, new Blob([body], { type: "application/json" }));
      if (sent) return;
    }
    void fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
      keepalive: true,
      credentials: "omit",
    });
  } catch {
    // Statistics must never break the page
  }
}
