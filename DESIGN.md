---
name: LaabhMitra
description: Government benefits copilot for small businesses, in an editorial serif style adapted for phones and three scripts.
colors:
  accent: "#b8860b"
  accent-strong: "#8a6508"
  accent-deep: "#6f5106"
  accent-secondary: "#d4a84b"
  accent-wash: "#f8f2e3"
  success: "#2e6b3e"
  success-wash: "#e6f0e4"
  warning: "#9a4f0a"
  warning-wash: "#fbe9d5"
  info: "#2a5a8c"
  info-wash: "#e4ecf5"
  danger: "#9c2f22"
  danger-wash: "#f7e3de"
  background: "#fafaf8"
  foreground: "#1a1a1a"
  muted: "#f5f3f0"
  muted-foreground: "#6b6b6b"
  card: "#ffffff"
  border: "#e8e4df"
  border-hover: "#cfc8bf"
typography:
  display:
    fontFamily: "Playfair Display Variable, Noto Serif Kannada Variable, Noto Serif Devanagari Variable, Georgia, serif"
    fontSize: "clamp(2.5rem, 7vw, 3.75rem)"
    fontWeight: 500
    lineHeight: 1.1
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "Playfair Display Variable, Noto Serif Kannada Variable, Noto Serif Devanagari Variable, Georgia, serif"
    fontSize: "clamp(1.9rem, 4vw, 2.5rem)"
    fontWeight: 500
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  title:
    fontFamily: "Playfair Display Variable, Noto Serif Kannada Variable, Noto Serif Devanagari Variable, Georgia, serif"
    fontSize: "1.25rem"
    fontWeight: 600
    lineHeight: 1.2
  body:
    fontFamily: "Source Sans 3 Variable, Noto Sans Kannada Variable, Noto Sans Devanagari Variable, Nirmala UI, system-ui, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 400
    lineHeight: 1.7
    letterSpacing: "0.01em"
  label:
    fontFamily: "IBM Plex Mono, ui-monospace, monospace"
    fontSize: "0.75rem"
    fontWeight: 500
    letterSpacing: "0.15em"
  figure:
    fontFamily: "Source Sans 3 Variable, Noto Sans Kannada Variable, Noto Sans Devanagari Variable, Nirmala UI, system-ui, sans-serif"
    fontWeight: 600
    fontFeature: "tnum, lnum"
rounded:
  sm: "4px"
  md: "6px"
  lg: "8px"
  full: "9999px"
spacing:
  gutter: "16px"
  card: "20px"
  card-wide: "32px"
  tap: "44px"
components:
  button-primary:
    backgroundColor: "{colors.accent-strong}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: "0 20px"
    height: "{spacing.tap}"
  button-primary-hover:
    backgroundColor: "{colors.accent-deep}"
  button-outline:
    textColor: "{colors.foreground}"
    rounded: "{rounded.md}"
    padding: "0 16px"
    height: "{spacing.tap}"
  button-outline-hover:
    backgroundColor: "{colors.muted}"
    textColor: "{colors.accent-strong}"
  chip:
    backgroundColor: "{colors.card}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.full}"
    padding: "0 16px"
    height: "{spacing.tap}"
  card:
    backgroundColor: "{colors.card}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.lg}"
    padding: "{spacing.card}"
  input:
    backgroundColor: "{colors.card}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.md}"
    padding: "0 12px"
    height: "{spacing.tap}"
  tier-badge-ready:
    backgroundColor: "{colors.success-wash}"
    textColor: "{colors.success}"
    rounded: "{rounded.md}"
    padding: "2px 8px"
---

# Design System: LaabhMitra

## Overview

**Creative North Star: "Serif"** (the editorial system supplied by the team, adapted)

Typographic elegance through restraint: a warm ivory page, rich black text, white cards held by thin warm rules, serif headlines and a single burnished-gold accent. It should feel like a well-set printed page, calm and trustworthy, with nothing shouting.

The supplied system was written for an English marketing site. This app is a task tool used on budget phones in Kannada, Hindi and English, so four things are adapted on purpose:

- **Scripts.** Playfair Display, Source Sans 3 and IBM Plex Mono have no Kannada or Devanagari letters. Each stack adds a matching Noto face, so headings stay serif and body stays sans in all three languages.
- **Gold as text.** Burnished gold (`accent`) is 3.2:1 on white, too light for text. It is kept for rules, focus rings and the card top line. Buttons and links use a darker gold (`accent-strong`, 5.3:1).
- **Status colours stay.** Readiness tiers and check results keep their own colours, retuned warmer to sit on ivory.
- **Spacing.** Generous for a phone, not the 128px+ section padding of a landing page.

Left out: the paper-texture overlay and ambient glow (a full-screen layer costs scroll performance on budget phones), and the pricing, testimonial and stats patterns (the app has no such content and must not invent it).

**Key Characteristics:**

- Serif headlines, sans body, across three scripts.
- White cards on ivory, 1px warm rules, almost no shadow.
- One brand accent (gold); status colours only for status.
- One large serif moment per screen at most (the welcome headline, the results figures).
- Motion limited to 150 to 200ms colour and shadow transitions.

## Colors

Monochrome with warmth, one gold accent, and four status colours that each mean one thing.

### Primary

- **Burnished Gold** (`accent`): rules under headlines, the top line of featured cards, the active navigation underline, focus rings. Never body text.
- **Deep Gold** (`accent-strong`, hover `accent-deep`): primary buttons, links, small-caps labels.

### Secondary

- **Success** (`success` on `success-wash`): Ready tier, met criteria, subsidy amounts, verified badges, "Comfortable" repayment.
- **Warning** (`warning` on `warning-wash`): Likely tier, unknown criteria, "Check current status", trade-off notices, "Tight" repayment.
- **Info** (`info` on `info-wash`): One step away tier, fix and unlock hints.
- **Danger** (`danger` on `danger-wash`): Not now tier, unmet criteria, errors, the DRAFT mark.

### Neutral

- **Ivory** (`background`): the page.
- **Rich Black** (`foreground`): text, selected toggles.
- **Muted** (`muted`): secondary surfaces, chat bubbles, neutral badges.
- **Warm Gray** (`muted-foreground`): secondary text.
- **White** (`card`): card and input surfaces.
- **Warm Rule** (`border`, hover `border-hover`): dividers, card borders, input borders.

### Named Rules

**The Gold Is Not Text Rule.** `accent` is for lines and rings. Anything a person reads or presses in gold uses `accent-strong`.

**The One Meaning Rule.** A status colour is used only for its status, always with an icon and words.

## Typography

**Display Font:** Playfair Display, with Noto Serif Kannada and Noto Serif Devanagari (fallback Georgia)
**Body Font:** Source Sans 3, with Noto Sans Kannada and Noto Sans Devanagari (fallback Nirmala UI, system-ui)
**Label/Mono Font:** IBM Plex Mono (Latin only)

**Character:** A high-contrast serif for headings against a quiet, highly readable sans. All fonts are bundled with the app (`@fontsource`), not loaded from a CDN, so the demo works offline.

### Hierarchy

- **Display** (500, 2.5rem to 3.75rem, 1.1): the welcome headline only, centred.
- **Headline** (500, 1.9rem to 2.5rem, 1.2): page titles, with a short gold rule beneath.
- **Title** (600, 1.25rem, 1.2): section and scheme names inside cards.
- **Body** (400, 1.0625rem, 1.7): sentences. Lines capped near 62 to 72 characters.
- **Label** (500, 0.75rem, tracking 0.15em, uppercase): small-caps labels in Deep Gold.
- **Figure** (600, tabular lining numerals): rupee amounts in rows and tables. The few large numbers use the serif at display size (`display-figure`).

### Named Rules

**The No Capitals Rule.** Kannada and Devanagari have no capitals and read poorly when tracked. In those languages a label is plain sans, 0.875rem, semibold, with no tracking or uppercase.

**The Script Room Rule.** Kannada and Hindi get more line height (1.8 body, 1.45 headings) and no letter spacing.

## Layout

Single column in a centred container up to 64rem wide with a 16px gutter. Cards stack with about 24px between them. Two columns appear only at large widths (onboarding chat beside "Your business", Path A beside Path B).

Card padding is 20px on phones and 32px from the small breakpoint. Main content has 32px vertical padding on phones and 56px on larger screens. Tabs and navigation scroll sideways on narrow screens. Every control is at least 44px tall.

## Elevation & Depth

Nearly flat. Cards carry a very soft shadow (`0 1px 2px rgba(26,26,26,0.04)`); primary buttons deepen it slightly on hover. Structure comes from thin rules, not depth.

### Shadow Vocabulary

- **Subtle lift** (`box-shadow: 0 1px 2px rgba(26,26,26,0.04)`): cards, primary buttons at rest.
- **Hover** (`box-shadow: 0 4px 12px rgba(26,26,26,0.06)`): primary button hover.

### Named Rules

**The No Lift Rule.** Nothing moves on hover. States change colour, border or shadow only.

## Shapes

Gently rounded. Cards 8px, buttons, inputs, badges and notices 6px. Borders are always 1px. Featured cards add a 2px gold line along the top edge. Only answer chips and round icon marks are fully rounded.

## Components

### Buttons

Defined once in `index.css` as `.btn` classes, shared by `<button>`, `<a>` and `<Link>`.

- **Shape:** 6px radius, 44px tall.
- **Primary** (`.btn-primary`): Deep Gold fill, white semibold text, soft shadow. Hover darkens and deepens the shadow.
- **Outline** (`.btn-outline`): transparent with a 1px black border. Hover fills Muted and turns border and text Deep Gold.
- **Chip** (`.btn-chip`): pill for tap answers. Hover takes a gold wash.
- **Focus:** 2px gold ring, 2px offset, on every interactive element.

### Cards / Containers

- **Card** (`.card`): white, 1px Warm Rule, 8px radius, subtle shadow.
- **Featured** (`.card-accent`): adds the 2px gold top line. Used for the results headline, the consent card and Path A.
- Rows inside a card are divided by 1px rules.

### Notices

One pattern (`.notice` with `-success`, `-warning`, `-info`, `-danger`): the tone's wash with a 1px border in the same tone at 30%, 6px radius. No thick side stripe.

### Inputs / Fields

- **Style:** white, 1px `border-hover`, 6px radius, 44px tall. Border turns Deep Gold on hover and focus.
- **Sliders and checkboxes:** native controls with the Deep Gold accent colour.

### Navigation

Ivory header with the serif wordmark and a language select, a thin rule beneath. Text tabs in medium weight; the active tab has a 2px gold underline. The row scrolls sideways on phones.

### Section Label

A small-caps label between two fine rules (`SectionLabel`). Used sparingly, to open a major section.

### Tier Badge (signature)

Icon plus words in the status colour on its wash with a fine border. Never a percentage.

### Headline Entry (signature)

At the top of Results: a featured card with two columns, subsidies and credit, each with a small-caps label and a large serif figure, and a footer line stating they are never added together.

## Do's and Don'ts

### Do:

- **Do** use `accent-strong` for any gold a person reads or presses.
- **Do** pair every status colour with an icon and words.
- **Do** keep subsidies and credit in separate columns or cards.
- **Do** use the shared `.btn`, `.card`, `.notice`, `.link` and `.label` classes instead of one-off styles.
- **Do** keep every tap target at least 44px tall.
- **Do** route every visible string through the three language files.

### Don't:

- **Don't** set body text or small labels in `accent` (#b8860b); it fails contrast.
- **Don't** apply uppercase or letter spacing to Kannada or Hindi text.
- **Don't** use a status colour for decoration.
- **Don't** add a thick coloured border on one side of a box.
- **Don't** move elements on hover.
- **Don't** load fonts or scripts from a CDN; the demo must work offline.
- **Don't** show a "% match", government logos, or invented testimonials and statistics.
