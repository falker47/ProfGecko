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

/** Pool of suggested questions shown on the welcome screen (random subset displayed). */
export const SUGGESTED_QUESTIONS: string[] = [
  // Tipi e debolezze
  "Quali sono le debolezze del tipo Drago?",
  "Che tipi sono superefficaci contro Acciaio?",
  "Quali Pokemon di tipo Spettro resistono al tipo Buio?",
  // Starter e consigli
  "Qual è il miglior starter di Pokemon Smeraldo?",
  "Consigliami un team per Pokemon Platino",
  "Quale starter scegliere in Pokemon Rosso Fuoco?",
  // Mosse e strategie
  "Che mosse impara Garchomp per livello?",
  "Quali sono le mosse più forti di tipo Fuoco?",
  "Lucario può imparare Focalcolpo?",
  // Evoluzioni
  "Come si evolve Eevee in Umbreon?",
  "A che livello si evolve Magikarp?",
  "Come far evolvere Haunter in Gengar?",
  // Curiosità e statistiche
  "Qual è il Pokemon più veloce?",
  "Quanti Pokemon leggendari esistono nella terza generazione?",
  "Quali Pokemon hanno la statistica Attacco più alta?",
  // Generazioni specifiche
  "Che Pokemon esclusivi ci sono in Pokemon Spada?",
  "Quali sono i capipalestra di Pokemon Oro?",
  "Dove trovo Larvitar in Pokemon Argento?",
];

/** How many suggested questions to display on the welcome screen. */
export const SUGGESTED_QUESTIONS_COUNT = 5;
