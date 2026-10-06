/**
 * Browser Web Notifications API utility for AirAware.
 * Handles permission requests, notification dispatch, spam throttling, and fallback states.
 */

export const NOTIFY_COOLDOWN_MS = 60 * 60 * 1000; // 60 minutes between repeat alerts
export const NOTIFY_LAST_TIMESTAMP_KEY = "airaware-last-notified-time";
export const NOTIFY_LAST_PM25_KEY = "airaware-last-notified-pm25";

export type NotificationSupportStatus = "granted" | "denied" | "default" | "unsupported";

/** Check if Notification API is available in the current environment */
export function isNotificationSupported(): boolean {
  return (
    typeof window !== "undefined" &&
    typeof window.Notification !== "undefined" &&
    window.Notification !== null
  );
}

/** Get the current notification permission state */
export function getNotificationPermission(): NotificationSupportStatus {
  if (!isNotificationSupported()) {
    return "unsupported";
  }
  return Notification.permission;
}

/** Request notification permission from the user */
export async function requestNotificationPermission(): Promise<NotificationSupportStatus> {
  if (!isNotificationSupported()) {
    return "unsupported";
  }

  try {
    const permission = await Notification.requestPermission();
    return permission;
  } catch {
    return Notification.permission;
  }
}

export interface ThresholdNotificationOptions {
  currentPm25: number;
  threshold: number;
  locationName?: string;
  force?: boolean;
}

/**
 * Dispatch a native browser notification if current PM2.5 exceeds threshold.
 * Throttles notifications so the user isn't spammed on every 5-minute poll.
 */
export function sendThresholdNotification({
  currentPm25,
  threshold,
  locationName,
  force = false,
}: ThresholdNotificationOptions): boolean {
  if (!isNotificationSupported() || Notification.permission !== "granted") {
    return false;
  }

  if (currentPm25 <= threshold) {
    return false;
  }

  const now = Date.now();
  const lastTimeStr = window.sessionStorage.getItem(NOTIFY_LAST_TIMESTAMP_KEY);
  const lastPm25Str = window.sessionStorage.getItem(NOTIFY_LAST_PM25_KEY);

  const lastTime = lastTimeStr ? parseInt(lastTimeStr, 10) : 0;
  const lastPm25 = lastPm25Str ? parseFloat(lastPm25Str) : 0;

  // Unless forced, avoid re-notifying within cooldown window unless PM2.5 spiked significantly (+25 ug/m3)
  const isCooldownActive = now - lastTime < NOTIFY_COOLDOWN_MS;
  const hasSignificantSpike = currentPm25 - lastPm25 >= 25;

  if (!force && isCooldownActive && !hasSignificantSpike) {
    return false;
  }

  try {
    const excess = Math.max(0, Math.round((currentPm25 - threshold) * 10) / 10);
    const location = locationName ? ` in ${locationName}` : "";

    const options: NotificationOptions & { renotify?: boolean } = {
      body: `Live PM2.5${location} is ${currentPm25.toFixed(1)} µg/m³ (+${excess} µg/m³ above your ${threshold} µg/m³ limit).`,
      icon: "/notification-icon.png",
      badge: "/notification-icon.png",
      tag: "airaware-pm25-alert",
      renotify: true,
    };
    const notification = new Notification("AirAware · Air Quality Alert", options);

    notification.onclick = () => {
      window.focus();
      notification.close();
    };

    window.sessionStorage.setItem(NOTIFY_LAST_TIMESTAMP_KEY, now.toString());
    window.sessionStorage.setItem(NOTIFY_LAST_PM25_KEY, currentPm25.toString());

    return true;
  } catch {
    return false;
  }
}

/** Dispatch a test notification to verify that notifications are working */
export function sendTestNotification(): boolean {
  if (!isNotificationSupported() || Notification.permission !== "granted") {
    return false;
  }

  try {
    const notification = new Notification("AirAware · Notifications Active", {
      body: "You will receive desktop alerts here whenever live PM2.5 exceeds your chosen threshold.",
      icon: "/notification-icon.png",
      badge: "/notification-icon.png",
      tag: `airaware-test-alert-${Date.now()}`,
    });

    notification.onclick = () => {
      window.focus();
      notification.close();
    };

    return true;
  } catch {
    return false;
  }
}
