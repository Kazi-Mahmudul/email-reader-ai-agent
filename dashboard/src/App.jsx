import { useEffect, useMemo, useState } from "react";
import axios from "axios";

import FilterBar from "./components/FilterBar.jsx";
import NotificationCard from "./components/NotificationCard.jsx";
import StatsBar from "./components/StatsBar.jsx";
import useNotifications from "./hooks/useNotifications.js";

function formatRefreshTime(value) {
  if (!value) {
    return "Never";
  }
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
  }).format(value);
}

export default function App() {
  const {
    notifications,
    stats,
    loading,
    error,
    refresh,
    dismissNotification,
  } = useNotifications();
  const [filters, setFilters] = useState({ priority: "All", category: "All" });
  const [lastRefreshedAt, setLastRefreshedAt] = useState(null);
  const [triggerError, setTriggerError] = useState(null);
  const [triggering, setTriggering] = useState(false);

  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

  useEffect(() => {
    if (!loading) {
      setLastRefreshedAt(new Date());
    }
  }, [loading, notifications, stats]);

  const filteredNotifications = useMemo(() => {
    return notifications.filter((item) => {
      const matchesPriority =
        filters.priority === "All" || item.priority === filters.priority;
      const matchesCategory =
        filters.category === "All" || item.category === filters.category;
      return matchesPriority && matchesCategory;
    });
  }, [notifications, filters]);

  const handleTriggerPoll = async () => {
    setTriggering(true);
    setTriggerError(null);
    try {
      await axios.post(`${apiBaseUrl}/api/trigger-poll`);
      await refresh();
      setLastRefreshedAt(new Date());
    } catch (err) {
      const message = axios.isAxiosError(err)
        ? err.message
        : "Failed to trigger poll.";
      setTriggerError(message);
    } finally {
      setTriggering(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="bg-[#1a1a2e] px-4 py-5 text-white">
        <div className="mx-auto flex w-full max-w-7xl items-center justify-between">
          <h1 className="text-xl font-bold">AI Email Agent</h1>
          <div className="flex items-center gap-3">
            <p className="text-xs text-slate-200">
              Last refreshed: {formatRefreshTime(lastRefreshedAt)}
            </p>
            <button
              type="button"
              onClick={handleTriggerPoll}
              disabled={triggering}
              className="rounded-md bg-white px-3 py-1.5 text-sm font-semibold text-[#1a1a2e] transition hover:bg-slate-200 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {triggering ? "Triggering..." : "Trigger Poll"}
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-7xl space-y-4 px-4 py-6">
        <div className="rounded-xl bg-white p-4 shadow-sm">
          <StatsBar stats={loading ? null : stats} />
        </div>

        <div className="rounded-xl bg-white p-4 shadow-sm">
          <FilterBar filters={filters} onFilterChange={setFilters} />
        </div>

        {loading && (
          <div className="rounded-lg bg-white p-4 text-sm text-gray-700 shadow-sm">
            Checking inbox...
          </div>
        )}

        {error && (
          <div className="rounded-lg bg-white p-4 text-sm text-red-600 shadow-sm">
            {error}
          </div>
        )}

        {triggerError && (
          <div className="rounded-lg bg-white p-4 text-sm text-red-600 shadow-sm">
            {triggerError}
          </div>
        )}

        {!loading && filteredNotifications.length === 0 ? (
          <div className="rounded-lg bg-white p-6 text-center text-gray-600 shadow-sm">
            No important emails
          </div>
        ) : (
          <section className="grid grid-cols-1 gap-4 lg:grid-cols-3">
            {filteredNotifications.map((notification) => (
              <NotificationCard
                key={notification.id}
                notification={notification}
                onDismiss={dismissNotification}
              />
            ))}
          </section>
        )}
      </main>
    </div>
  );
}
