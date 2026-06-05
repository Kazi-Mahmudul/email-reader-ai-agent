import PropTypes from "prop-types";

const CATEGORY_OPTIONS = [
  "All",
  "PAYMENT_ISSUE",
  "SERVER_DOWN",
  "CLIENT_COMPLAINT",
  "SPAM",
  "NEWSLETTER",
  "MEETING_REQUEST",
  "GENERAL_INQUIRY",
  "CLASSIFICATION_ERROR",
];

const PRIORITY_OPTIONS = ["All", "HIGH", "MEDIUM", "LOW"];

export default function FilterBar({ onFilterChange, filters }) {
  const handlePriorityChange = (event) => {
    onFilterChange({ ...filters, priority: event.target.value });
  };

  const handleCategoryChange = (event) => {
    onFilterChange({ ...filters, category: event.target.value });
  };

  return (
    <div className="flex items-center gap-3 rounded-lg bg-white p-3 shadow-sm">
      <label className="flex items-center gap-2 text-sm text-gray-700">
        <span>Priority</span>
        <select
          value={filters.priority}
          onChange={handlePriorityChange}
          className="rounded-md border border-gray-300 px-2 py-1 text-sm"
        >
          {PRIORITY_OPTIONS.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>

      <label className="flex items-center gap-2 text-sm text-gray-700">
        <span>Category</span>
        <select
          value={filters.category}
          onChange={handleCategoryChange}
          className="rounded-md border border-gray-300 px-2 py-1 text-sm"
        >
          {CATEGORY_OPTIONS.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}

FilterBar.propTypes = {
  onFilterChange: PropTypes.func.isRequired,
  filters: PropTypes.shape({
    priority: PropTypes.string.isRequired,
    category: PropTypes.string.isRequired,
  }).isRequired,
};
