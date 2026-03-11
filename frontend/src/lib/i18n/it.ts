import type { Translations } from "./types";

export const it: Translations = {
  // -- Layout / Header --
  siteTitle: "Prof. Gecko",
  siteSubtitle: "Il tuo esperto Pokemon",

  // -- Welcome screen --
  welcomeMessage:
    "Ciao! Sono il Prof. Gecko, il tuo assistente personale sul mondo dei Pokemon. " +
    "Chiedimi tutto quello che vuoi: tipi, mosse, statistiche, evoluzioni, strategie " +
    "e curiosità da qualsiasi generazione!",
  suggestedQuestions: [
    // Basi
    "Quali sono le debolezze del tipo Drago?",
    "Che tipi sono superefficaci contro Acciaio?",
    // Pokemon e statistiche
    "Quali sono le statistiche di Charizard?",
    "Qual è il Pokemon più veloce?",
    "Che abilità ha Garchomp?",
    // Mosse
    "Che mosse impara Garchomp per livello?",
    "Quali sono le mosse più forti di tipo Fuoco?",
    "Lucario può imparare Focalcolpo?",
    // Evoluzioni
    "Come si evolve Eevee in Umbreon?",
    "A che livello si evolve Magikarp?",
    // Generazioni e giochi
    "Quali sono gli starter di Pokemon Platino?",
    "Che mosse impara Pikachu in Pokemon Rosso?",
    "Quali sono i capipalestra di Pokemon Oro?",
    // Curiosità avanzate
    "Quali Pokemon sono esclusivi di Pokemon Spada?",
    "Quali sono le statistiche di Raichu di Alola?",
  ],

  // -- Chat input --
  chatPlaceholder: "Scrivi la tua domanda...",
  chatPlaceholderExhausted: "Crediti esauriti...",
  sendButton: "Invia",

  // -- Chat container --
  newChat: "Nuova chat",

  // -- Message bubble --
  you: "Tu",
  feedbackCorrect: "Corretta",
  feedbackWrong: "Errata",

  // -- Credit badge --
  credits: "crediti",
  creditBadgeTooltip: (free, paid) =>
    `${free} gratuiti + ${paid} acquistati`,

  // -- User menu --
  freeCreditsLabel: "Crediti gratuiti:",
  paidCreditsLabel: "Crediti acquistati:",
  logout: "Esci",

  // -- Credits exhausted --
  creditsExhaustedTitle: "Hai esaurito i crediti giornalieri!",
  creditsExhaustedMessage: "I crediti gratuiti si resettano a mezzanotte.",

  // -- Login prompt --
  loginPromptBold: "10 crediti gratuiti",
  loginPromptText: (boldPart) =>
    `Ti piace Prof. Gecko? Accedi per ottenere ${boldPart} ogni giorno!`,

  // -- API / streaming errors --
  errorConnection:
    "Impossibile connettersi al server. Verifica che il backend sia avviato.",
  errorCreditsExhausted:
    "Hai esaurito i crediti! I crediti gratuiti si resettano a mezzanotte.",
  errorServer: (status) => `Errore dal server: ${status}`,
  errorStreamingUnsupported: "Streaming non supportato dal browser.",
  errorInternalServer: "Errore interno del server.",

  // -- Google Sign-In --
  googleButtonLocale: "it",
};
