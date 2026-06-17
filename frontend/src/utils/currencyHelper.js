// =========================================
// Currency formatting & conversion helper
// =========================================
 
export const CURRENCY_SYMBOLS = {
  INR: '₹',
  USD: '$',
  EUR: '€',
  GBP: '£',
  AUD: 'A$',
  CAD: 'C$',
  JPY: '¥',
  AED: 'AED ',
}
 
export const CURRENCY_LABELS = {
  INR: 'Indian Rupee (₹)',
  USD: 'US Dollar ($)',
  EUR: 'Euro (€)',
  GBP: 'British Pound (£)',
  AUD: 'Australian Dollar (A$)',
  CAD: 'Canadian Dollar (C$)',
  JPY: 'Japanese Yen (¥)',
  AED: 'UAE Dirham (AED)',
}
 
/**
 * Converts an amount (assumed stored in INR in the database)
 * into the user's preferred currency using live rates.
 */
export function convertFromINR(amountInINR, targetCurrency, rates) {
  if (!rates || !targetCurrency || targetCurrency === 'INR') {
    return Number(amountInINR || 0)
  }
  const rate = rates[targetCurrency]
  if (!rate) return Number(amountInINR || 0)
  return Number(amountInINR || 0) * rate
}
 
/**
 * Formats a number with the right currency symbol and
 * locale-aware thousands separators.
 */
export function formatCurrency(amount, currency = 'INR') {
  const symbol = CURRENCY_SYMBOLS[currency] || currency + ' '
  const value = Number(amount || 0)
 
  const formatted = value.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
 
  return `${symbol}${formatted}`
}
 
/**
 * One-shot helper: takes a raw INR amount + user's currency + rates,
 * returns a ready-to-display formatted string.
 */
export function displayAmount(amountInINR, currency, rates) {
  const converted = convertFromINR(amountInINR, currency, rates)
  return formatCurrency(converted, currency)
}
 