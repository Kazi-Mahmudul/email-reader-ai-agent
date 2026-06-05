import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import axios from "axios";

const DEFAULT_STATS = {
  total: 0,
  by_priority: { HIGH: 0, MEDIUM: 0, LOW: 0 },
  by_category: {},
};

export default function useNotifications() {
  const [notifications, setNotifications] = useState([]);
  const [stats, setStats] = useState(DEFAULT_STATS);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const isMountedRef = useRef(true);
  const apiBaseUrl = useMemo(
    () => import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
    []
  );

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [notificationsResponse, statsResponse] = await Promise.all([
        axios.get(`${apiBaseUrl}/api/notifications`),
        axios.get(`${apiBaseUrl}/api/notifications/stats`),
      ]);

      if (!isMountedRef.current) {
        return;
      }

      setNotifications(
        Array.isArray(notificationsResponse.data) ? notificationsResponse.data : []
      );
      setStats(
        statsResponse.data && typeof statsResponse.data === "object"
          ? statsResponse.data
          : DEFAULT_STATS
      );
      setError(null);
    } catch (err) {
      if (!isMountedRef.current) {
        return;
      }
      const message = axios.isAxiosError(err)
        ? err.message
        : "Failed to fetch notifications.";
      setError(message);
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  }, [apiBaseUrl]);

  const dismissNotification = useCallback(
    async (email_id) => {
      try {
        await axios.delete(`${apiBaseUrl}/api/notifications/${email_id}`);
        await refresh();
      } catch (err) {
        const message = axios.isAxiosError(err)
          ? err.message
          : "Failed to dismiss notification.";
        setError(message);
      }
    },
    [apiBaseUrl, refresh]
  );

  useEffect(() => {
    isMountedRef.current = true;
    refresh();

    const intervalId = setInterval(() => {
      refresh();
    }, 10000);

    return () => {
      isMountedRef.current = false;
      clearInterval(intervalId);
    };
  }, [refresh]);

  return {
    notifications,
    stats,
    loading,
    error,
    refresh,
    dismissNotification,
  };
}
