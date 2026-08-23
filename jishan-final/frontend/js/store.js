/*
 * Legacy mock store intentionally retired.
 *
 * The application now uses the backend API as the single source of truth via
 * frontend/js/utils.js. Keeping duplicate localStorage complaints, users, and
 * plaintext demo passwords here caused UI/backend state to drift and made
 * authorization bugs much harder to reason about.
 *
 * This file is retained only so an old cached page that still references
 * store.js does not fail with a 404. Do not add application state here.
 */
