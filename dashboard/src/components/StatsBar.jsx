import PropTypes from "prop-types";

function getTopCategory(byCategory = {}) {
  const entries = Object.entries(byCategory);
  if (!entries.length) {
    return "N/A";
  }

  let top = entries[0];
  for (const entry of entries.slice(1)) {
    if (entry[1] > top[1]) {
      top = entry;
    }
  }
  return top[0];
}

export default function StatsBar({ stats }) {
  if (!stats) {
    return (
      <div className="rounded-lg bg-white p-3 text-sm text-gray-600 shadow-sm">
        Loading stats...
      </div>
    );
  }

  const high = stats.by_priority?.HIGH || 0;
  const medium = stats.by_priority?.MEDIUM || 0;
  const low = stats.by_priority?.LOW || 0;
  const topCategory = getTopCategory(stats.by_category);

  return (
    <div className="flex flex-wrap items-center gap-4 rounded-lg bg-white p-3 text-sm shadow-sm">
      <span className="font-semibold text-gray-800">Total: {stats.total || 0}</span>
      <span className="font-medium text-red-600">HIGH: {high}</span>
      <span className="font-medium text-amber-600">MEDIUM: {medium}</span>
      <span className="font-medium text-blue-600">LOW: {low}</span>
      <span className="text-gray-700">Top Category: {topCategory}</span>
    </div>
  );
}

StatsBar.propTypes = {
  stats: PropTypes.shape({
    total: PropTypes.number,
    by_priority: PropTypes.object,
    by_category: PropTypes.object,
  }),
};
