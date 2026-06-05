import PropTypes from "prop-types";

function formatReceivedAt(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value || "";
  }

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

const PRIORITY_STYLES = {
  HIGH: {
    border: "border-l-4 border-red-500",
    badge: "bg-red-100 text-red-800",
  },
  MEDIUM: {
    border: "border-l-4 border-yellow-400",
    badge: "bg-yellow-100 text-yellow-800",
  },
  LOW: {
    border: "border-l-4 border-blue-500",
    badge: "bg-blue-100 text-blue-800",
  },
};

export default function NotificationCard({ notification, onDismiss }) {
  const priority = (notification?.priority || "LOW").toUpperCase();
  const styles = PRIORITY_STYLES[priority] || PRIORITY_STYLES.LOW;

  return (
    <article className={`${styles.border} rounded-xl bg-white p-5 shadow-sm`}>
      <div className="mb-3 flex items-start justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${styles.badge}`}>
            {priority}
          </span>
          <span className="rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-700">
            {notification?.category}
          </span>
        </div>
        <button
          type="button"
          onClick={() => onDismiss(notification?.id)}
          className="rounded-md bg-gray-100 px-3 py-1 text-xs font-medium text-gray-700 transition hover:bg-gray-200"
        >
          Dismiss
        </button>
      </div>

      <h3 className="mb-2 text-lg font-bold text-gray-900">{notification?.subject}</h3>
      <p className="mb-2 text-sm text-gray-700">{notification?.from}</p>
      <p className="mb-3 text-sm text-gray-600">{notification?.body}</p>
      <p className="mb-3 text-sm italic text-gray-700">{notification?.reason}</p>
      <p className="text-xs text-gray-500">{formatReceivedAt(notification?.received_at)}</p>
    </article>
  );
}

NotificationCard.propTypes = {
  notification: PropTypes.shape({
    id: PropTypes.string.isRequired,
    from: PropTypes.string.isRequired,
    subject: PropTypes.string.isRequired,
    body: PropTypes.string.isRequired,
    received_at: PropTypes.string.isRequired,
    important: PropTypes.bool,
    priority: PropTypes.string,
    category: PropTypes.string,
    reason: PropTypes.string,
  }).isRequired,
  onDismiss: PropTypes.func.isRequired,
};
