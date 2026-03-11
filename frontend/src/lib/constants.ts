export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const GOOGLE_CLIENT_ID =
  process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "";

export const ANONYMOUS_LIMIT = parseInt(
  process.env.NEXT_PUBLIC_ANONYMOUS_LIMIT || "3",
  10,
);

export const MAX_HISTORY_MESSAGES = 10;

/** How many suggested questions to display on the welcome screen. */
export const SUGGESTED_QUESTIONS_COUNT = 4;
