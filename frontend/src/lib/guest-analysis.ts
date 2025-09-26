/**
 * @fileoverview Guest Analysis State Management
 * Utilities for managing guest analysis IDs in session storage
 * Used for claiming readings when guests decide to authenticate
 */

const GUEST_ANALYSIS_KEY = 'guestAnalysisId';

/**
 * Store a guest analysis ID in session storage
 * This allows the guest to claim the reading later if they authenticate
 */
export function storeGuestAnalysisId(analysisId: string | number): void {
  if (typeof window === 'undefined') return;

  try {
    sessionStorage.setItem(GUEST_ANALYSIS_KEY, String(analysisId));
  } catch (error) {
    console.warn('Failed to store guest analysis ID:', error);
  }
}

/**
 * Retrieve the stored guest analysis ID
 * Returns null if no analysis ID is stored or if we're on the server
 */
export function getGuestAnalysisId(): string | null {
  if (typeof window === 'undefined') return null;

  try {
    return sessionStorage.getItem(GUEST_ANALYSIS_KEY);
  } catch (error) {
    console.warn('Failed to retrieve guest analysis ID:', error);
    return null;
  }
}

/**
 * Clear the stored guest analysis ID
 * Should be called after successfully claiming a reading
 */
export function clearGuestAnalysisId(): void {
  if (typeof window === 'undefined') return;

  try {
    sessionStorage.removeItem(GUEST_ANALYSIS_KEY);
  } catch (error) {
    console.warn('Failed to clear guest analysis ID:', error);
  }
}

/**
 * Check if there's a guest analysis waiting to be claimed
 */
export function hasGuestAnalysis(): boolean {
  return getGuestAnalysisId() !== null;
}

/**
 * For backward compatibility with existing 'returnToAnalysis' key
 * This can be removed once all flows are migrated to the new approach
 */
export function migrateFromReturnToAnalysis(): void {
  if (typeof window === 'undefined') return;

  try {
    const oldAnalysisId = sessionStorage.getItem('returnToAnalysis');
    if (oldAnalysisId && !hasGuestAnalysis()) {
      storeGuestAnalysisId(oldAnalysisId);
      sessionStorage.removeItem('returnToAnalysis');
    }
  } catch (error) {
    console.warn('Failed to migrate from returnToAnalysis:', error);
  }
}