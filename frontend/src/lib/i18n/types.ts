/**
 * Every translatable string in the public-facing UI.
 * Keys are grouped by feature area.
 *
 * Adding a key here will cause a TypeScript error in both it.ts and en.ts
 * until the translation is provided — guaranteeing completeness.
 */

export type Locale = "it" | "en";

export interface Translations {
  // -- Layout / Header --
  siteTitle: string;
  siteSubtitle: string;

  // -- Welcome screen --
  welcomeMessage: string;
  suggestedQuestions: string[];

  // -- Chat input --
  chatPlaceholder: string;
  chatPlaceholderExhausted: string;
  sendButton: string;

  // -- Chat container --
  newChat: string;

  // -- Message bubble --
  you: string;
  feedbackCorrect: string;
  feedbackWrong: string;

  // -- Credit badge --
  credits: string;
  creditBadgeTooltip: (free: number, paid: number) => string;

  // -- User menu --
  freeCreditsLabel: string;
  paidCreditsLabel: string;
  logout: string;

  // -- Credits exhausted --
  creditsExhaustedTitle: string;
  creditsExhaustedMessage: string;

  // -- Login prompt --
  loginPromptBold: string;
  loginPromptText: (boldPart: string) => string;

  // -- API / streaming errors (frontend-side) --
  errorConnection: string;
  errorCreditsExhausted: string;
  errorServer: (status: number) => string;
  errorStreamingUnsupported: string;
  errorInternalServer: string;

  // -- Google Sign-In locale --
  googleButtonLocale: string;
}
