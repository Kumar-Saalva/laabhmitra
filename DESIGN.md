---
name: LaabhMitra
description: Government benefits copilot for small businesses, drawn as a bank passbook.
colors:
  ink: "#14304a"
  leaf: "#1b7447"
  leaf-wash: "#e2f1e8"
  turmeric: "#8f5f00"
  turmeric-wash: "#faecc4"
  step: "#1f5fa8"
  step-wash: "#e1ecf9"
  sindoor: "#a8321f"
  sindoor-wash: "#f8e4df"
  paper: "#e9f0ec"
  sheet: "#fbfcfa"
  soft: "#4d6377"
  rule: "#c7d5cd"
  slate-wash: "#e6ebef"
typography:
  display:
    fontFamily: "Anek Latin Variable, Anek Kannada Variable, Anek Devanagari Variable, Nirmala UI, system-ui, sans-serif"
    fontSize: "clamp(2.2rem, 6vw, 3rem)"
    fontWeight: 650
    lineHeight: 1.15
    letterSpacing: "-0.01em"
  headline:
    fontFamily: "Anek Latin Variable, Anek Kannada Variable, Anek Devanagari Variable, Nirmala UI, system-ui, sans-serif"
    fontSize: "clamp(1.75rem, 4vw, 2.1rem)"
    fontWeight: 650
    lineHeight: 1.15
    letterSpacing: "-0.01em"
  title:
    fontFamily: "Anek Latin Variable, Anek Kannada Variable, Anek Devanagari Variable, Nirmala UI, system-ui, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 650
    lineHeight: 1.15
  body:
    fontFamily: "Anek Latin Variable, Anek Kannada Variable, Anek Devanagari Variable, Nirmala UI, system-ui, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Anek Latin Variable, Anek Kannada Variable, Anek Devanagari Variable, Nirmala UI, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.43
  figure:
    fontFamily: "Anek Latin Variable, Anek Kannada Variable, Anek Devanagari Variable, Nirmala UI, system-ui, sans-serif"
    fontWeight: 650
    fontFeature: "tnum"
    fontVariation: "'wdth' 88"
rounded:
  sm: "4px"
  md: "6px"
  lg: "8px"
  full: "9999px"
spacing:
  gutter: "16px"
  panel: "20px"
  tap: "44px"
components:
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.sheet}"
    rounded: "{rounded.md}"
    padding: "0 20px"
    height: "{spacing.tap}"
  button-quiet:
    backgroundColor: "{colors.sheet}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "0 16px"
    height: "{spacing.tap}"
  chip:
    backgroundColor: "{colors.sheet}"
    textColor: "{colors.ink}"
    rounded: "{rounded.full}"
    padding: "0 16px"
    height: "{spacing.tap}"
  ledger-panel:
    backgroundColor: "{colors.sheet}"
    textColor: "{colors.ink}"
    padding: "{spacing.panel}"
  tier-badge-ready:
    backgroundColor: "{colors.leaf-wash}"
    textColor: "{colors.leaf}"
    rounded: "{rounded.sm}"
    padding: "2px 8px"
  input:
    backgroundColor: "#ffffff"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "0 12px"
    height: "{spacing.tap}"
  header:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.sheet}"
---

# Design System: LaabhMitra

## Overview

**Creative North Star: "The Passbook"**

The interface borrows from the bank passbook, an object every small merchant in India already trusts and can read: pale ledger paper, indigo ink, a red margin line, and figures set in columns. Each scheme is an entry on a ruled page, not a floating card. Money you keep and money you repay sit in separate columns, the way credits and debits do.

The system is calm and dense enough to scan on a small phone. Colour is spent almost entirely on meaning: each readiness tier owns one colour and one icon, and nothing else uses them.

This record describes the implementation as it exists in `frontend/src/index.css` and the components. The North Star name and the named rules below were drafted from the code and have not yet been confirmed by the team.

**Key Characteristics:**

- Ruled ledger panels with a red double margin line, in place of shadowed cards.
- One typeface family across English, Kannada and Hindi.
- Rupee amounts in tabular, slightly condensed figures.
- One colour and one icon per readiness tier.
- Flat surfaces; depth comes from paper against page, not shadow.

## Colors

A cool, paper-and-ink palette with four signal colours that each mean one thing.

### Primary

- **Passbook Indigo** (`ink`): all body text, the header band, and primary buttons. The default colour of anything the merchant should read or press.

### Secondary

- **Leaf Green** (`leaf`, with `leaf-wash`): Ready tier, met criteria, subsidy amounts, "Comfortable" repayment, verified badges.
- **Turmeric** (`turmeric`, with `turmeric-wash`): Likely tier, unknown criteria, "Check current status", conflict and trade-off warnings.
- **Step Blue** (`step`, with `step-wash`): One step away tier, fix actions and unlock hints, focus ring.
- **Sindoor Red** (`sindoor`, with `sindoor-wash`): Not now tier, unmet criteria, errors, the DRAFT mark, and the ledger margin line.

### Neutral

- **Ledger Paper** (`paper`): the page background behind every panel.
- **Sheet** (`sheet`): the surface of ledger panels, quiet buttons and the footer.
- **Soft Ink** (`soft`): secondary text, notes, the Watchlist tier.
- **Rule Line** (`rule`): borders and the dividers between ledger rows.
- **Slate Wash** (`slate-wash`): background for neutral and unknown badges.

### Named Rules

**The One Meaning Rule.** A signal colour is used only for its tier or state. Green is never decoration; red is never emphasis.

**The Wash Pair Rule.** Signal text sits on its own wash (`leaf` on `leaf-wash`), never on another signal's wash.

## Typography

**Display Font:** Anek Latin Variable, with Anek Kannada Variable and Anek Devanagari Variable (fallback Nirmala UI, system-ui)
**Body Font:** the same family

**Character:** One multi-script family, so a screen in Kannada has the same weight and rhythm as the same screen in English. Fonts are bundled with the app, not loaded from a CDN, so the demo works offline.

### Hierarchy

- **Display** (650, 2.2rem to 3rem, 1.15): the welcome headline only.
- **Headline** (650, 1.75rem to 2.1rem, 1.15): page titles.
- **Title** (650, 1.25rem, 1.15): section and scheme names inside panels.
- **Body** (400, 1.0625rem, 1.5): everything read as a sentence. Lines are capped near 62 to 72 characters.
- **Label** (400, 0.875rem): notes, sources, criteria counts, in Soft Ink.
- **Figure** (650, tabular numerals, width axis 88): every rupee amount, count and ratio.

### Named Rules

**The Script Room Rule.** Kannada and Hindi get more line height (1.65 body, 1.35 headings) and no negative letter spacing, because their marks sit above and below the line.

**The Figure Rule.** Any number a merchant might compare is set in the figure style so digits line up.

## Layout

Single column, mobile-first, in a centred container up to 64rem wide with a 16px side gutter. Panels stack vertically with 20px between them. Two columns appear only at large widths, for the onboarding chat beside the "Your business" card and for Path A beside Path B.

Inside panels, label and value pairs sit in a two-column grid from the small breakpoint up and stack below it. Tabs and the main navigation scroll sideways on narrow screens instead of wrapping. Every interactive control is at least 44px tall.

## Elevation & Depth

Flat. There are no shadows anywhere in the system. Depth is tonal: Sheet panels sit on Ledger Paper, separated by a 1px Rule Line border.

### Named Rules

**The No Shadow Rule.** A panel is distinguished by its border and its margin line, never by a shadow or a gradient.

## Shapes

Mostly square. Ledger panels have no corner radius and carry a 3px double Sindoor line on the left edge, the passbook margin. Buttons and inputs are gently rounded (6px). Tier badges are nearly square (4px) with a 1.5px outline in their own colour, like a rubber stamp. Only answer chips and round icon marks are fully rounded.

## Components

### Buttons

- **Shape:** gently rounded (6px), 44px tall.
- **Primary:** Passbook Indigo fill with Sheet text, semibold, 20px side padding. One per panel at most.
- **Quiet:** Sheet fill, 1px Indigo border at 30% opacity that becomes solid on hover.
- **Focus:** 3px Step Blue outline, 2px offset.

### Chips

- **Style:** pill shape, Sheet fill, 1px Indigo border, 44px tall. Used for tap answers in the chat.
- **State:** "Skip" and "Prefer not to say" use a dashed border.

### Cards / Containers

- **Corner Style:** square.
- **Background:** Sheet on Ledger Paper.
- **Shadow Strategy:** none (see Elevation & Depth).
- **Border:** 1px Rule Line, with the 3px double Sindoor margin line on the left.
- **Internal Padding:** 20px. Rows inside are divided by Rule Line.

### Inputs / Fields

- **Style:** white fill, 1px Indigo border at 30% opacity, 6px radius, 44px tall.
- **Focus:** the shared 3px Step Blue outline.
- **Sliders:** native range inputs with the Indigo accent colour.

### Navigation

- **Style:** an Indigo header band with the product name and a language select, and a row of text tabs beneath. The active tab is semibold with a 3px Sheet underline; inactive tabs are Sheet at 75% opacity. The row scrolls sideways on phones.

### Tier Badge (signature)

An icon plus words in the tier's colour on its wash, with a 1.5px outline in the same colour. Ready uses a check, Likely a question mark, One step away a stair, Not now a cross, Watchlist a clock. Never a percentage.

### Headline Entry (signature)

At the top of Results: two ledger columns, "Subsidies (not repaid)" and "Collateral-free credit (to be repaid)", with a footer line stating they are never added together.

## Do's and Don'ts

### Do:

- **Do** pair every status colour with an icon and words.
- **Do** set every rupee amount in the figure style and Indian grouping (₹2,80,000).
- **Do** keep subsidies and credit in separate columns or panels.
- **Do** keep every tap target at least 44px tall.
- **Do** route every visible string through the three language files.
- **Do** respect reduced motion; the only animation is the loading spinner.

### Don't:

- **Don't** add shadows or gradients to panels.
- **Don't** use a signal colour for decoration or emphasis.
- **Don't** show a "% match" or any figure that reads as approval odds.
- **Don't** use government logos or emblems.
- **Don't** load fonts or scripts from a CDN; the demo must work offline.
