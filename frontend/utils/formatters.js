/**
 * Utility functions for formatting data in the frontend
 */

/**
 * Format currency values
 * @param {number|string} value - The value to format
 * @param {Object} options - Formatting options
 * @param {string} options.currency - Currency code (default: 'USD')
 * @param {string} options.locale - Locale code (default: 'en-US')
 * @param {boolean} options.compact - Use compact notation for large numbers
 * @returns {string} Formatted currency string
 */
export const formatCurrency = (value, options = {}) => {
  const {
    currency = 'USD',
    locale = 'en-US',
    compact = false
  } = options;

  const numericValue = typeof value === 'string' ? parseFloat(value) : value;
  
  if (isNaN(numericValue)) {
    return '$0.00';
  }

  const formatOptions = {
    style: 'currency',
    currency: currency,
  };

  // Use compact notation for large numbers
  if (compact && Math.abs(numericValue) >= 1000000) {
    formatOptions.notation = 'compact';
    formatOptions.compactDisplay = 'short';
  }

  try {
    return new Intl.NumberFormat(locale, formatOptions).format(numericValue);
  } catch (error) {
    console.warn('Error formatting currency:', error);
    return `$${numericValue.toLocaleString()}`;
  }
};

/**
 * Format percentage values
 * @param {number|string} value - The value to format (0-1 range or 0-100 if asPercent is true)
 * @param {Object} options - Formatting options
 * @param {number} options.decimals - Number of decimal places (default: 1)
 * @param {string} options.locale - Locale code (default: 'en-US')
 * @param {boolean} options.asPercent - Whether input is already in percent form (default: false)
 * @returns {string} Formatted percentage string
 */
export const formatPercentage = (value, options = {}) => {
  const {
    decimals = 1,
    locale = 'en-US',
    asPercent = false
  } = options;

  const numericValue = typeof value === 'string' ? parseFloat(value) : value;
  
  if (isNaN(numericValue)) {
    return '0%';
  }

  // Convert to percentage if value is in 0-1 range
  const percentValue = asPercent ? numericValue : numericValue * 100;

  const formatOptions = {
    style: 'percent',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  };

  try {
    // Note: Intl.NumberFormat expects percentage values in 0-1 range
    const valueForFormatter = asPercent ? numericValue / 100 : numericValue;
    return new Intl.NumberFormat(locale, formatOptions).format(valueForFormatter);
  } catch (error) {
    console.warn('Error formatting percentage:', error);
    return `${percentValue.toFixed(decimals)}%`;
  }
};

/**
 * Format date values
 * @param {string|Date} value - The date to format
 * @param {Object} options - Formatting options
 * @param {string} options.style - Format style ('short', 'medium', 'long', 'full', 'relative')
 * @param {string} options.locale - Locale code (default: 'en-US')
 * @param {boolean} options.includeTime - Whether to include time (default: false)
 * @returns {string} Formatted date string
 */
export const formatDate = (value, options = {}) => {
  const {
    style = 'medium',
    locale = 'en-US',
    includeTime = false
  } = options;

  if (!value) {
    return 'N/A';
  }

  let date;
  if (typeof value === 'string') {
    date = new Date(value);
  } else if (value instanceof Date) {
    date = value;
  } else {
    return 'Invalid Date';
  }

  if (isNaN(date.getTime())) {
    return 'Invalid Date';
  }

  // Handle relative time formatting
  if (style === 'relative') {
    return formatRelativeTime(date, { locale });
  }

  const formatOptions = {};

  // Set date format based on style
  switch (style) {
    case 'short':
      formatOptions.dateStyle = 'short';
      break;
    case 'medium':
      formatOptions.dateStyle = 'medium';
      break;
    case 'long':
      formatOptions.dateStyle = 'long';
      break;
    case 'full':
      formatOptions.dateStyle = 'full';
      break;
    default:
      formatOptions.year = 'numeric';
      formatOptions.month = 'short';
      formatOptions.day = 'numeric';
  }

  // Add time if requested
  if (includeTime) {
    formatOptions.timeStyle = 'short';
  }

  try {
    return new Intl.DateTimeFormat(locale, formatOptions).format(date);
  } catch (error) {
    console.warn('Error formatting date:', error);
    return date.toLocaleDateString();
  }
};

/**
 * Format relative time (e.g., "2 hours ago", "in 3 days")
 * @param {Date} date - The date to format
 * @param {Object} options - Formatting options
 * @param {string} options.locale - Locale code (default: 'en-US')
 * @returns {string} Formatted relative time string
 */
export const formatRelativeTime = (date, options = {}) => {
  const { locale = 'en-US' } = options;

  if (!date || !(date instanceof Date) || isNaN(date.getTime())) {
    return 'Invalid Date';
  }

  const now = new Date();
  const diffInSeconds = Math.floor((now - date) / 1000);
  const absDiff = Math.abs(diffInSeconds);

  // Define time units in seconds
  const units = [
    { name: 'year', seconds: 31536000 },
    { name: 'month', seconds: 2592000 },
    { name: 'week', seconds: 604800 },
    { name: 'day', seconds: 86400 },
    { name: 'hour', seconds: 3600 },
    { name: 'minute', seconds: 60 },
    { name: 'second', seconds: 1 }
  ];

  // Find the appropriate unit
  for (const unit of units) {
    if (absDiff >= unit.seconds) {
      const value = Math.floor(absDiff / unit.seconds);
      
      try {
        const rtf = new Intl.RelativeTimeFormat(locale, { numeric: 'auto' });
        return rtf.format(diffInSeconds > 0 ? -value : value, unit.name);
      } catch (error) {
        console.warn('Error formatting relative time:', error);
        const timeAgo = diffInSeconds > 0 ? 'ago' : 'from now';
        return `${value} ${unit.name}${value > 1 ? 's' : ''} ${timeAgo}`;
      }
    }
  }

  return 'just now';
};

/**
 * Format large numbers with appropriate suffixes
 * @param {number|string} value - The number to format
 * @param {Object} options - Formatting options
 * @param {number} options.decimals - Number of decimal places (default: 1)
 * @param {string} options.locale - Locale code (default: 'en-US')
 * @param {boolean} options.compact - Use compact notation (default: true)
 * @returns {string} Formatted number string
 */
export const formatNumber = (value, options = {}) => {
  const {
    decimals = 1,
    locale = 'en-US',
    compact = true
  } = options;

  const numericValue = typeof value === 'string' ? parseFloat(value) : value;
  
  if (isNaN(numericValue)) {
    return '0';
  }

  const formatOptions = {
    minimumFractionDigits: compact ? 0 : decimals,
    maximumFractionDigits: decimals,
  };

  if (compact && Math.abs(numericValue) >= 1000) {
    formatOptions.notation = 'compact';
    formatOptions.compactDisplay = 'short';
  }

  try {
    return new Intl.NumberFormat(locale, formatOptions).format(numericValue);
  } catch (error) {
    console.warn('Error formatting number:', error);
    return numericValue.toLocaleString();
  }
};

/**
 * Format file sizes
 * @param {number} bytes - File size in bytes
 * @param {Object} options - Formatting options
 * @param {number} options.decimals - Number of decimal places (default: 1)
 * @param {boolean} options.binary - Use binary (1024) vs decimal (1000) units (default: false)
 * @returns {string} Formatted file size string
 */
export const formatFileSize = (bytes, options = {}) => {
  const {
    decimals = 1,
    binary = false
  } = options;

  if (bytes === 0) return '0 B';
  if (isNaN(bytes)) return 'N/A';

  const k = binary ? 1024 : 1000;
  const sizes = binary 
    ? ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB']
    : ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];

  const i = Math.floor(Math.log(Math.abs(bytes)) / Math.log(k));
  const size = bytes / Math.pow(k, i);

  return `${size.toFixed(decimals)} ${sizes[i]}`;
};

/**
 * Format duration in seconds to human readable format
 * @param {number} seconds - Duration in seconds
 * @param {Object} options - Formatting options
 * @param {boolean} options.short - Use short format (default: false)
 * @returns {string} Formatted duration string
 */
export const formatDuration = (seconds, options = {}) => {
  const { short = false } = options;

  if (isNaN(seconds) || seconds < 0) {
    return '0s';
  }

  const units = [
    { name: short ? 'y' : 'year', seconds: 31536000 },
    { name: short ? 'd' : 'day', seconds: 86400 },
    { name: short ? 'h' : 'hour', seconds: 3600 },
    { name: short ? 'm' : 'minute', seconds: 60 },
    { name: short ? 's' : 'second', seconds: 1 }
  ];

  const parts = [];

  for (const unit of units) {
    if (seconds >= unit.seconds) {
      const value = Math.floor(seconds / unit.seconds);
      seconds %= unit.seconds;
      
      if (short) {
        parts.push(`${value}${unit.name}`);
      } else {
        parts.push(`${value} ${unit.name}${value > 1 ? 's' : ''}`);
      }
      
      // For short format, only show the two most significant units
      if (short && parts.length >= 2) break;
      // For long format, only show up to 3 units
      if (!short && parts.length >= 3) break;
    }
  }

  return parts.length > 0 ? parts.join(short ? ' ' : ', ') : (short ? '0s' : '0 seconds');
};

/**
 * Truncate text to specified length
 * @param {string} text - Text to truncate
 * @param {number} maxLength - Maximum length (default: 100)
 * @param {string} suffix - Suffix to add when truncated (default: '...')
 * @returns {string} Truncated text
 */
export const truncateText = (text, maxLength = 100, suffix = '...') => {
  if (!text || typeof text !== 'string') {
    return '';
  }

  if (text.length <= maxLength) {
    return text;
  }

  return text.substring(0, maxLength - suffix.length) + suffix;
};

/**
 * Format phone numbers
 * @param {string} phoneNumber - Phone number to format
 * @param {string} format - Format style ('us', 'international', 'dots', 'dashes')
 * @returns {string} Formatted phone number
 */
export const formatPhoneNumber = (phoneNumber, format = 'us') => {
  if (!phoneNumber) return '';

  // Remove all non-digit characters
  const cleaned = phoneNumber.replace(/\D/g, '');

  // Handle different formats
  switch (format) {
    case 'us':
      if (cleaned.length === 10) {
        return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
      } else if (cleaned.length === 11 && cleaned[0] === '1') {
        return `+1 (${cleaned.slice(1, 4)}) ${cleaned.slice(4, 7)}-${cleaned.slice(7)}`;
      }
      break;
    case 'international':
      if (cleaned.length >= 10) {
        return `+${cleaned.slice(0, -10)} ${cleaned.slice(-10, -7)} ${cleaned.slice(-7, -4)} ${cleaned.slice(-4)}`;
      }
      break;
    case 'dots':
      if (cleaned.length === 10) {
        return `${cleaned.slice(0, 3)}.${cleaned.slice(3, 6)}.${cleaned.slice(6)}`;
      }
      break;
    case 'dashes':
      if (cleaned.length === 10) {
        return `${cleaned.slice(0, 3)}-${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
      }
      break;
  }

  // Return original if no format matches
  return phoneNumber;
};

/**
 * Format SSN (Social Security Number) with masking
 * @param {string} ssn - SSN to format
 * @param {boolean} mask - Whether to mask digits (default: true)
 * @returns {string} Formatted SSN
 */
export const formatSSN = (ssn, mask = true) => {
  if (!ssn) return '';

  const cleaned = ssn.replace(/\D/g, '');
  
  if (cleaned.length !== 9) {
    return ssn; // Return original if not valid length
  }

  if (mask) {
    return `XXX-XX-${cleaned.slice(-4)}`;
  } else {
    return `${cleaned.slice(0, 3)}-${cleaned.slice(3, 5)}-${cleaned.slice(5)}`;
  }
};

// Export all formatters as default for convenience
export default {
  formatCurrency,
  formatPercentage,
  formatDate,
  formatRelativeTime,
  formatNumber,
  formatFileSize,
  formatDuration,
  truncateText,
  formatPhoneNumber,
  formatSSN
};