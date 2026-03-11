import type { Translations } from "./types";

export const en: Translations = {
  // -- Layout / Header --
  siteTitle: "Prof. Gallade",
  siteSubtitle: "Your Pokemon Expert",

  // -- Welcome screen --
  welcomeMessage:
    "Hi there! I'm Prof. Gallade, your personal Pokemon assistant. " +
    "Ask me anything: types, moves, stats, evolutions, strategies " +
    "and trivia from every generation!",
  suggestedQuestions: [
    // Basics
    "What are the weaknesses of the Dragon type?",
    "Which types are super effective against Steel?",
    // Pokemon and stats
    "What are Charizard's stats?",
    "What is the fastest Pokemon?",
    "What ability does Garchomp have?",
    // Moves
    "What moves does Garchomp learn by level?",
    "What are the strongest Fire-type moves?",
    "Can Lucario learn Focus Blast?",
    // Evolutions
    "How does Eevee evolve into Umbreon?",
    "At what level does Magikarp evolve?",
    // Generations and games
    "What are the starters in Pokemon Platinum?",
    "What moves does Pikachu learn in Pokemon Red?",
    "Who are the Gym Leaders in Pokemon Gold?",
    // Advanced trivia
    "Which Pokemon are exclusive to Pokemon Sword?",
    "What are Alolan Raichu's stats?",
  ],

  // -- Chat input --
  chatPlaceholder: "Type your question...",
  chatPlaceholderExhausted: "Credits exhausted...",
  sendButton: "Send",

  // -- Chat container --
  newChat: "New chat",

  // -- Message bubble --
  you: "You",
  feedbackCorrect: "Correct",
  feedbackWrong: "Wrong",

  // -- Credit badge --
  credits: "credits",
  creditBadgeTooltip: (free, paid) =>
    `${free} free + ${paid} purchased`,

  // -- User menu --
  freeCreditsLabel: "Free credits:",
  paidCreditsLabel: "Purchased credits:",
  logout: "Sign out",

  // -- Credits exhausted --
  creditsExhaustedTitle: "You've run out of daily credits!",
  creditsExhaustedMessage: "Free credits reset at midnight.",

  // -- Login prompt --
  loginPromptBold: "10 free credits",
  loginPromptText: (boldPart) =>
    `Enjoying Prof. Gallade? Sign in to get ${boldPart} every day!`,

  // -- API / streaming errors --
  errorConnection:
    "Cannot connect to server. Make sure the backend is running.",
  errorCreditsExhausted:
    "You've run out of credits! Free credits reset at midnight.",
  errorServer: (status) => `Server error: ${status}`,
  errorStreamingUnsupported: "Streaming is not supported by this browser.",
  errorInternalServer: "Internal server error.",

  // -- Google Sign-In --
  googleButtonLocale: "en",
};
