/**
 * Frontend Configuration
 *
 * Reads backend API base URL from Vite environment variable VITE_API_URL.
 * Falls back to 'http://localhost:8000' for local development.
 * Automatically trims any trailing slashes to ensure clean URL concatenation.
 */
export const API_BASE_URL = (
  import.meta.env.VITE_API_URL || 'http://localhost:8000'
).replace(/\/+$/, '');
