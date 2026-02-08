/**
 * Format number to compact display (e.g., 1.2k)
 * @param {number} num
 * @returns {string}
 */
export const formatNumber = (num) => {
  if (!num && num !== 0) return '0';
  return new Intl.NumberFormat('en-US', { notation: "compact", compactDisplay: "short" }).format(num);
};

/**
 * Truncate text to specified length with ellipsis
 * @param {string} text
 * @param {number} length
 * @returns {string}
 */
export const truncateText = (text, length) => {
  if (!text) return '';
  if (text.length <= length) return text;
  return text.substring(0, length) + '...';
};

/**
 * Format date string to localized string
 * @param {string} dateStr
 * @param {string} locale
 * @returns {string}
 */
export const formatDate = (dateStr, locale = 'zh-CN') => {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleDateString(locale, { month: 'short', day: 'numeric', year: 'numeric' });
};

/**
 * Get color for programming language
 * @param {string} language
 * @returns {string} Hex color code
 */
export const getLangColor = (language) => {
  const colors = {
    'JavaScript': '#f1e05a',
    'TypeScript': '#3178c6',
    'Python': '#3572a5',
    'Java': '#b07219',
    'Go': '#00add8',
    'Rust': '#dea584',
    'C++': '#f34b7d',
    'C': '#555555',
    'Ruby': '#701516',
    'PHP': '#4f5d95',
    'Swift': '#ffac45',
    'Kotlin': '#a97bff',
    'Dart': '#00b4ab',
    'Vue': '#41b883',
    'HTML': '#e34c26',
    'CSS': '#563d7c',
  };
  return colors[language] || '#8b949e';
};
