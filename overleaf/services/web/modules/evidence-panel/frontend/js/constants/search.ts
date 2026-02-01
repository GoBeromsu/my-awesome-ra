/**
 * Constants for evidence search configuration.
 * These values should match backend API limits.
 */

/**
 * Debounce delay (ms) before checking paragraph changes.
 * 500ms balances responsiveness with API efficiency.
 */
export const PARAGRAPH_CHANGE_DEBOUNCE_MS = 500

/**
 * Maximum number of results to return from search.
 * Must match backend EvidenceSearchRequest.top_k max (le=20).
 */
export const SEARCH_TOP_K = 20

/**
 * Minimum similarity threshold for search results.
 * Results below this score are filtered out.
 */
export const SEARCH_THRESHOLD = 0.2
