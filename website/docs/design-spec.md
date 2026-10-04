# Sugan AI: Design Spec

Phase 2. This is the contract for the build. Every component should be traceable to a token or rule here. Rationale for each choice lives in `design-research.md`, especially the "Patterns to adopt" list.

**Concept in one line:** a research paper set as a website. Warm paper, ink, one gold accent, numbered sections, ruled lists, a very large light headline, and almost no decoration.

---

## 1. Changes to the starting brand constraints

| Constraint | Change | Why |
| --- | --- | --- |
| Accent #C9A227 for links | Kept as the brand gold, but **never used as text on light surfaces**. Links on light are ink text with a gold underline. Where gold coloured text is needed on light, use `gold-ink` #7A5E0E. | #C9A227 is 2.28:1 on #FAF8F3, which fails WCAG AA for any text. On ink it is 8.19:1 and works. |
| Gold for "one button style" | The gold button is used **only on dark surfaces** (the Partner band). On light surfaces the primary button is ink. | A gold fill on off white has a 2.28:1 boundary, so the button edge is weak. On ink it is crisp. |
| Background | Warm off white #FAF8F3, with pure white reserved for form inputs. | Warm grounds read as considered (research pattern 4) and make white inputs stand out without heavy borders. |
| Dark surfaces | Two: the Partner band (section 8) and the footer. The hero stays light. | Keeps the headline readable and lets the conversion band stand out. Partner copy is short (one sentence per item), so it does not break the "no long text on dark" rule. |

Everything else (Outfit, JetBrains Mono for labels and data only, ink #070A0F) is kept as specified.

---

## 2. Design tokens

### 2.1 Colour

| Token | Hex | Use | Contrast |
| --- | --- | --- | --- |
| `ink` | #070A0F | Headings, primary text, primary button fill, dark surfaces | 18.68 on paper |
| `ink-2` | #3A3D44 | Body text | 10.25 on paper |
| `muted` | #5C6069 | Secondary text, captions, metadata | 5.94 on paper |
| `paper` | #FAF8F3 | Page background | |
| `paper-2` | #F3EFE6 | Alternate band (Roadmap, Team), placeholder fills | ink-2 9.48, muted 5.49 |
| `white` | #FFFFFF | Form inputs only | |
| `line` | #E4DFD3 | Hairline rules and dividers (decorative) | |
| `line-strong` | #857F70 | Input borders, interactive boundaries | 3.99 on white, passes 3:1 |
| `gold` | #C9A227 | Rules, underlines, gold button fill, current roadmap marker, text on dark | 8.19 on ink |
| `gold-ink` | #7A5E0E | Gold coloured text on light (status label "In progress") | 5.76 on paper |
| `on-dark` | #FAF8F3 | Text on ink | 18.68 |
| `on-dark-muted` | #A9ADB5 | Secondary text on ink | 8.81 |
| `line-dark` | rgba(250,248,243,0.14) | Rules on ink | |
| `error` | #B42318 | Form errors | 6.19 on paper |
| `success` | #1F6B3A | Form confirmation | 6.14 on paper |

Rules:
- Gold is never a background for a full section, never a gradient, never a glow.
- Body text is always `ink-2` on `paper`, `paper-2` or `white`.
- Only `on-dark` and `on-dark-muted` appear on `ink`.

### 2.2 Typography

Families:
- `font-sans`: Outfit variable (weights 300 to 600), self hosted via Fontsource, `font-display: swap`, with a metric adjusted local fallback (`size-adjust`, `ascent-override`) to prevent layout shift on swap.
- `font-mono`: JetBrains Mono variable, self hosted, labels and data only. Never body text.

Scale (fluid with `clamp`, 360px to 1440px):

| Token | Size | Weight | Line height | Tracking | Use |
| --- | --- | --- | --- | --- | --- |
| `display` | clamp(2.75rem, 1.2rem + 6.9vw, 6.5rem) = 44 to 104px | 300 | 1.0 | -0.035em | Hero h1 only |
| `h2` | clamp(2rem, 1.35rem + 2.9vw, 3.5rem) = 32 to 56px | 300 | 1.08 | -0.025em | Section headings |
| `h3` | clamp(1.25rem, 1.1rem + 0.5vw, 1.5rem) = 20 to 24px | 500 | 1.25 | -0.01em | Item titles (Data, Models...) |
| `lead` | clamp(1.125rem, 1rem + 0.55vw, 1.375rem) = 18 to 22px | 400 | 1.5 | -0.005em | Hero supporting line, section intros |
| `body` | 1.0625rem = 17px | 400 | 1.65 | 0 | Running text |
| `small` | 0.9375rem = 15px | 400 | 1.55 | 0 | Footer, captions, form help |
| `label` | 0.75rem = 12px | 500 | 1.4 | 0.08em, uppercase | Mono eyebrows, status, table heads |
| `button` | 0.9375rem = 15px | 500 | 1 | 0 | Buttons and nav |

Rules:
- One `h1` (hero). Each section has one `h2`. Items are `h3`.
- Text measure capped at 64ch for body, 38ch for `lead`, 18ch for `h2`.
- Display never goes above weight 300; h3 never above 500. Hierarchy comes from size and space.
- Headlines are sentence case and keep the period from the copy.
- `font-variant-numeric: tabular-nums` on phase numbers and any numeric data.
- No em or en dashes anywhere in rendered copy.

### 2.3 Spacing

4px base. Tailwind's default numeric scale is used (1 = 4px), restricted in practice to:

`4, 8, 12, 16, 24, 32, 48, 64, 96, 128, 160`

Section vertical padding:

| Breakpoint | Padding top and bottom |
| --- | --- |
| < 768px | 64px |
| 768 to 1023px | 96px |
| ≥ 1024px | 128px |

Hero: 96px top on mobile, 160px on desktop (header height added on top).

### 2.4 Radius

| Token | Value | Use |
| --- | --- | --- |
| `radius-sm` | 4px | Inputs, buttons, focus ring |
| `radius-full` | 9999px | Status pills, roadmap markers |
| none | 0 | Everything else. No rounded cards. |

### 2.5 Shadow

None. Depth comes from hairlines and the paper / ink contrast. The only "shadow" is the focus ring.

### 2.6 Focus

- Light surfaces: `outline: 2px solid ink; outline-offset: 3px`.
- Dark surfaces: `outline: 2px solid gold; outline-offset: 3px`.
- Only on `:focus-visible`. Never removed.

### 2.7 Breakpoints

Tailwind defaults: `sm` 640, `md` 768, `lg` 1024, `xl` 1280. Designed and checked at 360, 768, 1280 and 1440.

---

## 3. Layout

- **Container:** max width 1200px content, centred. Side padding 20px (< 640), 32px (640 to 1023), 48px (≥ 1024).
- **Grid:** 12 columns from `lg`, 24px gutter (32px from `xl`). Below `lg`, a single column.
- **Section pattern (the default):**
  - `lg`: columns 1 to 4 hold the eyebrow and `h2`, sticky is not used. Columns 6 to 12 hold content.
  - Below `lg`: eyebrow, `h2`, then content, stacked, 32px apart.
- **Hero pattern:** `h1` spans columns 1 to 10. Supporting line and buttons sit under it in columns 1 to 6. The lab status panel sits in columns 9 to 12, aligned to the buttons' baseline. Below `lg` the panel stacks under the buttons.
- **Rules:** every section begins with a full container width 1px `line` rule; the eyebrow sits 24px below it.
- **Bands:** `paper` by default. `paper-2` for Roadmap and Team. `ink` for Partner and footer.

---

## 4. Components

### Header
- Sticky, 64px tall, `paper` at 92% opacity with `backdrop-filter: blur(8px)` (falls back to solid `paper`). A 1px `line` bottom border appears once the page is scrolled.
- Left: wordmark "Sugan AI" set in Outfit 500 (placeholder until the logo is supplied). Links to `#top`.
- Centre/right (`lg` and up): nav links What we build, Approach, Roadmap, Team (15px, `ink-2`, hover `ink` with gold underline).
- Right, always visible at every width: "Partner with us" primary button, small size.
- Below `lg`: a "Menu" text button opens a full width panel under the header with the links stacked at 24px. Implemented with a `<button aria-expanded aria-controls>` and a few lines of vanilla JS. Escape closes it; focus returns to the toggle.
- A "Skip to content" link is the first focusable element.

### Button
| Variant | Surface | Fill | Text | Border | Hover |
| --- | --- | --- | --- | --- | --- |
| `primary` | light | ink | paper | none | fill #1A1F27 |
| `secondary` | light | transparent | ink | 1px ink | fill `paper-2` |
| `gold` | dark only | gold | ink | none | fill #D6B243 |
| `ghost-dark` | dark only | transparent | on-dark | 1px `line-dark` | border on-dark |

- Height 48px (default) or 40px (header). Horizontal padding 20px / 16px. `radius-sm`. Label 15px / 500.
- Optional trailing arrow drawn as inline SVG (not an emoji, not an icon font), moves 2px right on hover.
- Links styled as buttons stay `<a>`; actions stay `<button>`.

### Section heading
- Eyebrow: mono `label`, `muted` (`on-dark-muted` on ink), format `01  The problem` with two spaces, number in tabular figures. A 24px by 1px gold rule sits 12px above it.
- `h2` in `h2` style, `ink`.
- Optional intro paragraph in `lead`, `ink-2`, 24px below.

### Ruled item (replaces cards)
- Top border 1px `line`, padding 24px top, 32px bottom.
- `h3` title, then `body` text 8px below.
- Used in 2 by 2 grids (What we build, Use cases, Partner) and single column lists (Problem gaps, Approach).
- On dark: border `line-dark`, title `on-dark`, text `on-dark-muted`.

### Status pill
- Mono `label`, height 24px, padding 0 10px, `radius-full`.
- `In progress`: 1px gold border, `gold-ink` text, 6px gold dot.
- `Next`: 1px `line-strong` border, `ink-2` text.
- `Planned`: 1px `line` border, `muted` text.

### Table (data table, reserved)
- Not used visually for the roadmap, but the roadmap markup is an ordered list with the same data so it reads correctly without CSS.
- Spec for future benchmark tables: mono `label` header row in `muted`, rows separated by `line`, numbers right aligned in tabular figures, no zebra stripes, no vertical rules.

### Form field
- Label above field, 15px / 500, `ink`. Required marker is the word "(required)" in `muted`, not an asterisk alone.
- Input: height 48px (textarea 160px), `white` fill, 1px `line-strong` border, `radius-sm`, 16px text (prevents iOS zoom), padding 12px 14px.
- Focus: border `ink` plus the standard focus ring.
- Error: border `error`, message under the field in `small` `error`, linked with `aria-describedby`, `aria-invalid="true"`.
- Select uses the native element with a custom SVG chevron.
- Honeypot: a visually hidden field named `company_website`, `tabindex="-1"`, `autocomplete="off"`, `aria-hidden="true"` on its wrapper.
- Status region: `role="status" aria-live="polite"` under the submit button for the confirmation and error messages.

### Footer
- `ink` band, 64px padding (96px on `lg`).
- Row 1: wordmark and the line "Sugan AI. A research initiative of AIVERSE Africa. Nairobi, Kenya." in `on-dark-muted`.
- Row 2: links LinkedIn and Concept note (`on-dark`, gold underline on hover), and "Copyright 2026 Sugan AI." in `small`.
- A 1px `line-dark` rule between rows.

### Lab status panel (hero)
- A bordered block (1px `line`, no fill, no radius), padding 24px.
- Mono `label` header "Lab status".
- Four rows: Data, Models, Benchmark, Voice, each with a short state taken from the content file (initial value for all four: the Phase 1 status "In progress"). Rows separated by `line`.
- Footer row: "Phase 1. Model sprint" with the status pill.
- All values come from `site.ts`. No numbers are shown until real ones exist.

### Demo slot (hook only)
- A `DemoSlot.astro` component placed after "What we build", rendered only when `site.demo.enabled` is `true`. Ships disabled. Nothing about a demo appears on the page.

### Founder photo placeholder
- 4:5 box, `paper-2` fill, 1px `line` border, centred mono `label` "Photo placeholder". Fixed aspect ratio so swapping in a real photo causes no layout shift.

---

## 5. Motion rules

1. **Reveal:** section contents fade from opacity 0 to 1 and translate 8px to 0, 500ms, `cubic-bezier(0.2, 0.7, 0.2, 1)`, triggered once by IntersectionObserver at 15% visibility. Items in a grid stagger by 60ms, maximum 4 steps.
2. **No reveal above the fold.** The hero renders immediately, so nothing important waits for JS and Largest Contentful Paint is unaffected.
3. **Progressive enhancement:** the hidden state is only applied when JS adds a class to `<html>`, so content is always visible without JS.
4. **Hover and focus:** colour and border transitions at 150ms ease. Arrow nudge 2px.
5. **Header:** bottom border fades in at 150ms after scroll passes 8px.
6. **Anchor scrolling:** `scroll-behavior: smooth` with `scroll-margin-top` equal to the header height plus 16px.
7. **Reduced motion:** under `prefers-reduced-motion: reduce`, reveals are disabled, smooth scrolling is off, and transitions drop to 0ms.
8. **Never:** parallax, scroll hijacking, looping animation, animated gradients, typing effects, counters.

---

## 6. Section wireframes

Notation: `[ ]` element, `|` column split at `lg`, `...` repeats. Mobile stacks everything in reading order.

### 0. Header (sticky)
```
[Sugan AI]          What we build  Approach  Roadmap  Team   [Partner with us]
mobile: [Sugan AI]                                    [Menu] [Partner with us]
```

### 1. Hero (paper, id="top")
```
[h1: AI that speaks Somali.]                       <- display, columns 1 to 10

[lead: Sugan AI is a research lab building ...]  |  [Lab status panel]
[Partner with us] [Read the concept note ->]     |    Data       In progress
[small: A research initiative of AIVERSE Africa.]|    Models     In progress
                                                 |    Benchmark  In progress
                                                 |    Voice      In progress
                                                 |    Phase 1. Model sprint  (In progress)
```
No eyebrow above the `h1`: it would add copy that is not in the brief. The hero starts directly with the headline. The "Lab status" label and the row names (Data, Models, Benchmark, Voice) reuse words already in the copy.

### 2. The problem (paper, id="problem")
```
------------------------------------------------------------------ rule
01  The problem                 |  [lead: Somali is spoken across ...]
[h2: More than 20 million       |
 speakers. Almost no AI         |  ----------------------------------
 built for them.]               |  Text        General purpose models ...
                                |  ----------------------------------
                                |  Voice       Somali culture is ...
                                |  ----------------------------------
                                |  Measurement There is no widely ...
                                |  ----------------------------------
                                |  Ownership   The little capability ...
```
Each gap: `h3` in a 3 column sub grid at `md` and up, text in the remaining columns.

### 3. What we build (paper, id="build")
```
------------------------------------------------------------------ rule
02  What we build               |
[h2: Four building blocks       |
 for Somali AI.]                |
                                |
-------------------------------------------------------------------
Data                  |  Models               (2 by 2 ruled grid spanning
[text]                |  [text]                columns 1 to 12 at lg,
--------------------- | ---------------------  1 column on mobile)
Benchmark             |  Voice
[text]                |  [text]
-------------------------------------------------------------------
[closing line, lead, ink: We publish what we measure. Every model we
 release comes with its scores.]   <- with a 24px gold rule above
[DemoSlot: hidden]
```

### 4. Approach (paper, id="approach")
```
------------------------------------------------------------------ rule
03  Approach                    |  1  Data first.
[h2: How we work.]              |     [text]
                                |  ---------------------------------
                                |  2  Small models, real use.
                                |     [text]
                                |  ---------------------------------
                                |  3  Evidence over claims.
                                |     [text]
```
Ordered list. Numbers in mono, tabular, `muted`.

### 5. Roadmap (paper-2, id="roadmap")
```
04  Roadmap
[h2: Where we are.]

desktop (lg):
 (o)================( )-----------------( )-----------------( )
 Phase 1            Phase 2            Phase 3            Phase 4
 Model sprint       Validation         Voice and scale    Sustainability
 [focus text]       [focus text]       [focus text]       [focus text]
 [In progress]      [Next]             [Planned]          [Planned]

mobile: same items stacked vertically, line runs down the left edge.

[line under: We move to each phase only when the previous one has
 delivered measurable results.]
```
- Markup: `<ol>` of four `<li>`. Current phase marker is a filled gold dot with a 4px `paper-2` ring; others are hollow `line-strong` dots. The track is solid ink up to the current phase and a 1px `line-strong` line after it.
- Which phase is current is derived from the status values in `site.ts`, not hard coded.

### 6. Use cases (paper, id="use-cases")
```
------------------------------------------------------------------ rule
05  Use cases                   |  Public services      Banking and telecoms
[h2: What Somali AI makes       |  [text]               [text]
 possible.]                     |  ------------------   -------------------
                                |  Education            Translation
                                |  [text]               [text]
```

### 7. Team (paper-2, id="team")
```
06  Team
[h2: Who is behind Sugan AI.]

[photo 4:5]                         [photo 4:5]
Ahmed Siyad Abdirahman              Abdirahman Bashir
Founder  (mono label)               Founder
[bio]                               [bio]

------------------------------------------------------------------ rule
[Sugan AI is a research initiative of AIVERSE Africa, an AI consulting,
 training and product development company based in Nairobi.]
```
Photos at roughly 280px wide on desktop so the section stays text led.

### 8. Partner with us (ink, id="partner")
```
07  Partner with us   (on-dark-muted)
[h2: Help build Somali AI.]     |  [lead: We are working with a small group ...]
                                |
--------------------------------+----------------------------------
Funders and foundations          |  Government and public institutions
[text]                           |  [text]
-------------------------------- | ---------------------------------
Universities and researchers     |  Compute and technology providers
[text]                           |  [text]
-------------------------------------------------------------------
[Start a conversation ->]  (gold button, links to #contact)
```

### 9. Contact (paper, id="contact") and footer (ink)
```
08  Contact
[h2: Get in touch.]              |  Name                 Organisation
                                 |  [__________]         [__________]
                                 |  Email                I am a
                                 |  [__________]         [Funder      v]
                                 |  Message
                                 |  [_________________________________]
                                 |  [_________________________________]
                                 |  [Send message]
                                 |  (status region)
==================================================================== footer (ink)
Sugan AI                 Sugan AI. A research initiative of AIVERSE Africa. Nairobi, Kenya.
LinkedIn   Concept note                                   Copyright 2026 Sugan AI.
```
Fields pair into two columns from `md`; single column below.

Section numbering note: eight numbered sections (01 to 08) because the hero is not numbered.

---

## 7. Content model

- All copy lives in `src/content/site.ts` as a typed object: `export const content: Record<Locale, SiteContent>`, with only `en` populated. `Locale = 'en' | 'so'`.
- Components receive the locale's object as props; no component contains copy.
- Roadmap status values, lab status rows, link URLs (LinkedIn, concept note) and the `demo.enabled` flag live in the same file.
- A Somali version is added later by filling `so` and adding `src/pages/so/index.astro`, which renders the same page component with `content.so`. `<html lang>` and `hreflang` alternates are driven by the locale.

## 8. Technical decisions that affect design

- **Astro (static) + Tailwind CSS v4**, tokens declared in `@theme` so they are available as utilities (`bg-paper`, `text-ink-2`, `font-mono`).
- **No UI framework.** The only client JS: menu toggle, header border on scroll, reveal observer, and the form submit handler. Inline, under 3KB total.
- **Fonts:** Fontsource variable packages, Latin subset, woff2 only, the Outfit file preloaded.
- **Images:** none required at launch other than OG image and favicon. Founder photos, when supplied, go through `astro:assets` with explicit width and height.
- **Contact:** Cloudflare Pages Function at `functions/api/contact.ts`. Validates server side, rejects honeypot hits silently, and stores each message in a Cloudflare KV namespace bound as `CONTACT_MESSAGES`. **No email is sent and no third party service is used** (decision from Ahmed after the spec review). Messages are read in the Cloudflare dashboard. The form posts with `fetch` and also works as a plain HTML form post (the function returns a redirect when the request is not JSON).
