/**
 * Constants for evidence search configuration.
 */

/** Minimum character length for a paragraph to trigger evidence search */
export const MIN_PARAGRAPH_LENGTH_FOR_SEARCH = 50

/** Maximum character length for a paragraph to trigger evidence search */
export const MAX_PARAGRAPH_LENGTH_FOR_SEARCH = 500

/**
 * Debounce delay (ms) before checking paragraph changes.
 * 700ms balances responsiveness with API efficiency.
 */
export const PARAGRAPH_CHANGE_DEBOUNCE_MS = 700
