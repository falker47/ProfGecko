export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const GOOGLE_CLIENT_ID =
  process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "";

export const ANONYMOUS_LIMIT = parseInt(
  process.env.NEXT_PUBLIC_ANONYMOUS_LIMIT || "3",
  10,
);

export const WELCOME_MESSAGE =
  "Benvenuto! Sono il Professor Gallade, esperto di Pokemon. " +
  "Chiedimi qualsiasi cosa sul mondo dei Pokemon: tipi, statistiche, " +
  "evoluzioni, mosse e molto altro! Puoi anche chiedermi informazioni " +
  "su generazioni specifiche, ad esempio \"Che mosse impara Pikachu in Pokemon Rosso?\". " +
  "Come posso aiutarti oggi?";

export const MAX_HISTORY_MESSAGES = 10;
