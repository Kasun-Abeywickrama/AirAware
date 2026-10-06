import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  getNotificationPermission,
  isNotificationSupported,
  requestNotificationPermission,
  sendTestNotification,
  sendThresholdNotification,
} from "./notifications";

class MockNotification {
  static permission: NotificationPermission = "default";
  static requestPermission = vi.fn().mockResolvedValue("granted");
  title: string;
  options: NotificationOptions;
  onclick: (() => void) | null = null;
  close = vi.fn();

  constructor(title: string, options: NotificationOptions = {}) {
    this.title = title;
    this.options = options;
  }
}

describe("notifications utility", () => {
  let originalNotification: typeof Notification | undefined;

  beforeEach(() => {
    window.sessionStorage.clear();
    originalNotification = window.Notification;
    MockNotification.permission = "default";
    MockNotification.requestPermission = vi.fn().mockResolvedValue("granted");
    window.Notification = MockNotification as unknown as typeof Notification;
  });

  afterEach(() => {
    window.Notification = originalNotification as typeof Notification;
    vi.restoreAllMocks();
  });

  it("checks if notifications are supported", () => {
    expect(isNotificationSupported()).toBe(true);
  });

  it("handles unsupported environment gracefully", () => {
    // @ts-expect-error intentionally simulate unsupported environment
    delete window.Notification;
    expect(isNotificationSupported()).toBe(false);
    expect(getNotificationPermission()).toBe("unsupported");
  });

  it("returns current permission", () => {
    MockNotification.permission = "granted";
    expect(getNotificationPermission()).toBe("granted");
  });

  it("requests permission from browser", async () => {
    const res = await requestNotificationPermission();
    expect(res).toBe("granted");
    expect(MockNotification.requestPermission).toHaveBeenCalled();
  });

  it("does not send threshold notification when permission is not granted", () => {
    MockNotification.permission = "denied";

    const sent = sendThresholdNotification({ currentPm25: 80, threshold: 50 });
    expect(sent).toBe(false);
  });

  it("does not send threshold notification when current PM2.5 is below or equal to threshold", () => {
    MockNotification.permission = "granted";

    const sent = sendThresholdNotification({ currentPm25: 45, threshold: 50 });
    expect(sent).toBe(false);
  });

  it("sends notification when PM2.5 exceeds threshold and permission is granted", () => {
    MockNotification.permission = "granted";
    const spyConstructor = vi.fn();

    class CustomMockNotification extends MockNotification {
      constructor(title: string, options: NotificationOptions = {}) {
        super(title, options);
        spyConstructor(title, options);
      }
    }
    window.Notification = CustomMockNotification as unknown as typeof Notification;

    const sent = sendThresholdNotification({
      currentPm25: 89.3,
      threshold: 55,
      locationName: "Anand Lok",
    });

    expect(sent).toBe(true);
    expect(spyConstructor).toHaveBeenCalledWith(
      "AirAware · Air Quality Alert",
      expect.objectContaining({
        body: expect.stringContaining("89.3 µg/m³"),
        tag: "airaware-pm25-alert",
      })
    );
  });

  it("throttles repeated notifications within cooldown window", () => {
    MockNotification.permission = "granted";

    // First alert succeeds
    const first = sendThresholdNotification({ currentPm25: 80, threshold: 50 });
    expect(first).toBe(true);

    // Second immediate alert with same PM2.5 is throttled
    const second = sendThresholdNotification({ currentPm25: 81, threshold: 50 });
    expect(second).toBe(false);

    // Forced alert bypasses cooldown
    const forced = sendThresholdNotification({ currentPm25: 81, threshold: 50, force: true });
    expect(forced).toBe(true);
  });

  it("sends test notification when permission is granted", () => {
    MockNotification.permission = "granted";
    const spyConstructor = vi.fn();

    class CustomMockNotification extends MockNotification {
      constructor(title: string, options: NotificationOptions = {}) {
        super(title, options);
        spyConstructor(title, options);
      }
    }
    window.Notification = CustomMockNotification as unknown as typeof Notification;

    const sent = sendTestNotification();
    expect(sent).toBe(true);
    expect(spyConstructor).toHaveBeenCalledWith(
      "AirAware · Notifications Active",
      expect.objectContaining({
        tag: expect.stringContaining("airaware-test-alert"),
      })
    );
  });
});
