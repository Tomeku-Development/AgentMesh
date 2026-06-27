# Design System

# AgentMesh

**Version:** 1.0.0

**Status:** Design System Specification

**Design Language:** McLaren × Cyberpunk × Apple × Vercel

**Developed by:** Tomeku

**Website:** https://tomeku.com

**Socials**

* Facebook: OfficialTomeku
* X: OfficialTomeku
* YouTube: OfficialTomeku

---

# Table of Contents

1. Purpose
2. Design Principles
3. Design Tokens
4. Color System
5. Typography Scale
6. Spacing & Layout
7. Radius, Elevation & Glass
8. Motion Tokens
9. Iconography
10. Component Library
11. States & Feedback
12. Accessibility Contract
13. Implementation (Tailwind v4 + shadcn/ui)
14. Governance & Versioning

---

# Purpose

This document is the single source of truth for the AgentMesh visual system.

While `07_UI_UX.md` describes the design philosophy and experience, this document defines the **concrete, implementable tokens and components** used across the website, the dashboard, and the documentation.

Every value here maps directly to code so that design and engineering never drift apart.

---

# Design Principles

The system is built on five enforceable principles.

## 1. Precision

Every token has a purpose. No arbitrary values in product code.

## 2. Consistency

The same scale powers every surface. One spacing scale, one type scale, one palette.

## 3. Dark First

The platform is designed dark-first. Light surfaces are the exception, not the default.

## 4. Motion with Meaning

Animation communicates state and hierarchy. It is mechanical, fast, and never decorative.

## 5. Accessible by Default

Contrast, focus, and motion preferences are part of the token system, not an afterthought.

---

# Design Tokens

Tokens are the atomic decisions of the system. They are grouped into three tiers.

```text
Tier 1 — Primitive tokens   (raw values: #FF6A00, 8px, 200ms)
Tier 2 — Semantic tokens     (intent: --color-brand, --space-md, --motion-fast)
Tier 3 — Component tokens     (scoped: --button-bg, --card-border)
```

Product code consumes **semantic** and **component** tokens only. Primitives live in the theme layer.

---

# Color System

## Surfaces

| Token | Value | Usage |
|-------|-------|-------|
| `--bg-base` | `#050505` | App background |
| `--bg-raised` | `#0D0D0F` | Sections, raised panels |
| `--bg-card` | `#111111` | Cards, modals, popovers |

## Brand

| Token | Value | Usage |
|-------|-------|-------|
| `--brand` | `#FF6A00` | Primary actions, accents, focal points |
| `--brand-hover` | `#FF8C1A` | Hover / active brand state |
| `--brand-muted` | `rgba(255,106,0,.12)` | Tinted backgrounds, chips |

## Status

| Token | Value | Usage |
|-------|-------|-------|
| `--success` | `#00D084` | Confirmed, executed, online |
| `--warning` | `#FFC857` | Pending review, attention |
| `--error` | `#FF4D4F` | Failures, destructive actions |

## Text & Lines

| Token | Value | Usage |
|-------|-------|-------|
| `--text-primary` | `#FFFFFF` | Headings, key values |
| `--text-secondary` | `#A8A8A8` | Body, descriptions |
| `--border-glass` | `rgba(255,255,255,.08)` | Card and glass borders |

> Contrast: body text (`#A8A8A8`) on card (`#111111`) meets WCAG AA for normal text. Never go lighter than `#A8A8A8` for content on dark surfaces.

---

# Typography Scale

**Display / Headings:** Space Grotesk
**Body / UI:** Inter
**Mono:** JetBrains Mono

A modular scale (ratio ≈ 1.25) keeps hierarchy predictable.

| Token | Size / Line height | Weight | Use |
|-------|--------------------|--------|-----|
| `display-xl` | 80 / 0.92 | 800 | Hero headline |
| `display-lg` | 56 / 1.0 | 800 | Section hero |
| `h1` | 40 / 1.1 | 700 | Page titles |
| `h2` | 32 / 1.15 | 700 | Section titles |
| `h3` | 24 / 1.2 | 600 | Card titles |
| `body-lg` | 18 / 1.6 | 400 | Lead paragraphs |
| `body` | 16 / 1.6 | 400 | Default body |
| `caption` | 13 / 1.4 | 500 | Labels, eyebrows |
| `mono` | 14 / 1.5 | 500 | Addresses, code, metrics |

Rules:
* Line length: 65–75 characters for paragraphs.
* Eyebrows and labels use uppercase with `0.18em–0.25em` letter spacing.
* The hero display style is uppercase, italic, with `-0.02em` tracking.

---

# Spacing & Layout

Spacing uses a single base-4 scale.

```text
4 · 8 · 12 · 16 · 24 · 32 · 48 · 64 · 96 · 128
```

| Token | px |
|-------|----|
| `space-1` | 4 |
| `space-2` | 8 |
| `space-3` | 12 |
| `space-4` | 16 |
| `space-6` | 24 |
| `space-8` | 32 |
| `space-12` | 48 |
| `space-16` | 64 |
| `space-24` | 96 |
| `space-32` | 128 |

Grid:

| Breakpoint | Columns | Container |
|------------|---------|-----------|
| Desktop (≥1280) | 12 | 1280–1440px |
| Tablet (≥768) | 8 | fluid |
| Mobile (<768) | 4 | fluid, 20px gutter |

---

# Radius, Elevation & Glass

| Token | Value |
|-------|-------|
| `radius-sm` | 6px |
| `radius-md` | 10px |
| `radius-lg` | 14px |
| `radius-xl` | 20px |

Glass surface recipe:

```css
background: rgba(17, 17, 17, 0.6);
backdrop-filter: blur(20px);
border: 1px solid rgba(255, 255, 255, 0.08);
box-shadow: 0 0 40px -12px rgba(255, 106, 0, 0.25);
```

Glow recipe (focal elements):

```css
background: radial-gradient(closest-side, rgba(255,106,0,0.30), transparent);
```

---

# Motion Tokens

| Token | Value | Use |
|-------|-------|-----|
| `motion-fast` | 150ms | Micro-interactions (hover, focus) |
| `motion-base` | 200ms | Standard transitions |
| `motion-slow` | 400ms | Section reveals |
| `ease-out-expo` | `cubic-bezier(0.16, 1, 0.3, 1)` | Entrances |

Frameworks: GSAP, Framer Motion, Lenis (smooth scroll).

Rule: animate `transform` and `opacity` only. Never animate layout properties (`width`, `height`, `top`). All motion is disabled under `prefers-reduced-motion: reduce`.

---

# Iconography

* Library: **Lucide** (primary), Simple Icons (brand logos only).
* Grid: 24×24 viewBox, `1.5` stroke weight.
* Default render size: `w-5 h-5` inline, `w-6 h-6` standalone.
* Never use emoji as UI icons.
* Icon-only buttons require an `aria-label`.

---

# Component Library

Each component is documented with anatomy, variants, and states.

## Button

Variants: `primary`, `outline`, `secondary`, `ghost`, `link`, `destructive`.
Sizes: `sm (h-7)`, `default (h-8)`, `lg (h-9)`, plus marketing `h-12`.

```text
[ icon? ] Label [ icon? ]
```

* `primary`: brand fill, hover brightens + emits glow.
* All buttons: `cursor-pointer`, visible focus ring, disabled = 50% opacity + `not-allowed`.

## Card

Glass surface, `radius-lg`, `border-glass`. Hover raises background tint (`bg-secondary/50`). Non-interactive cards keep the default cursor.

## Navbar

Fixed, transparent on top, switches to blurred glass after 8px scroll. Mobile collapses to a disclosure menu with a labeled toggle.

## Stat / Metric

Inline label (caption, muted) + value (mono, tabular-nums). Separated by hairline dividers. Live indicator uses a pulsing brand dot.

## Input

Glass field, `radius-md`, focus ring `brand/30`. Always paired with a `<label>` (visible or `sr-only`).

## Badge / Tag

Pill, `brand-muted` background, `brand` text, used for status (Online, Pending, Executed).

## Agent Node

Square glass tile with brand icon, label, and role caption. Used in the network diagram and the dashboard.

---

# States & Feedback

Every interactive component defines five states:

```text
default · hover · focus-visible · active · disabled
```

Async components add: `loading` (spinner or skeleton) and `error` (inline message near the trigger).

| Feedback | Pattern |
|----------|---------|
| Loading | Skeleton screen for content, spinner for buttons |
| Empty | Illustration + one-line guidance + primary action |
| Error | Inline, near the field, with `--error` color and an icon |
| Success | Toast or inline confirmation with `--success` |

---

# Accessibility Contract

* Color contrast ≥ 4.5:1 for normal text, ≥ 3:1 for large text and UI.
* Visible `focus-visible` rings on every interactive element.
* Tab order matches visual order.
* Color is never the only signal — pair with icon or text.
* `prefers-reduced-motion` removes non-essential animation.
* All meaningful images have descriptive `alt`; decorative images use empty `alt`.

---

# Implementation (Tailwind v4 + shadcn/ui)

The reference implementation lives in `web/` (Next.js 16, Tailwind v4, shadcn/ui).

Semantic tokens are declared as CSS custom properties and exposed to Tailwind via `@theme inline`:

```css
:root {
  --background: #050505;
  --card: #111111;
  --brand: #FF6A00;
  --brand-hover: #FF8C1A;
  --foreground: #FFFFFF;
  --muted-foreground: #A8A8A8;
  --border: rgba(255, 255, 255, 0.08);
  --radius: 0.625rem;
}
```

Usage in components:

```tsx
<button className="bg-brand text-background hover:brightness-110
  focus-visible:ring-2 focus-visible:ring-brand/50 cursor-pointer">
  Launch App
</button>
```

> Implementation note: the reference build uses **Sora** as a display alternative to Space Grotesk where the wider, heavier weights better match the brand mark. Both are acceptable display faces; Space Grotesk remains the canonical choice.

---

# Governance & Versioning

* The design system is versioned with semantic versioning (`MAJOR.MINOR.PATCH`).
* Token changes are **MINOR**; breaking renames are **MAJOR**.
* New components require: anatomy, variants, states, a11y notes, and a code reference before merge.
* Design and code review together; no token ships without an implementation mapping.

---

**Built for the Casper Agentic Buildathon — by Tomeku.**
