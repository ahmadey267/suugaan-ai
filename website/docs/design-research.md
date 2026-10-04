# Sugan AI: Design Research

Phase 1 of the website build. The goal was to understand how leading AI labs and design led technology companies present themselves, then turn that into a short list of concrete decisions for the Sugan AI site.

## Method and source reliability

Read this first, because it affects how much weight each section deserves.

| Site | How it was studied | Reliability |
| --- | --- | --- |
| Anthropic (anthropic.com, /research) | Live fetch of the homepage and research index | High |
| Claude (claude.com, Anthropic's product site) | Published design system teardown (getdesign.md, VoltAgent `awesome-design-md`) | Medium |
| Mistral AI | Live fetch blocked by this environment's network policy. Published teardown plus web search | Medium |
| Cohere / Cohere Labs | Live fetch blocked. Published teardown plus web search on Cohere Labs and Aya | Medium |
| Linear, Vercel, Stripe, Resend | Live fetch blocked. Published teardowns | Medium |
| Sarvam AI | Live fetch blocked, and no teardown exists. Web search on how it publishes models and benchmarks | Low for visual design, medium for credibility patterns |
| Lelapa AI | Live fetch blocked, and no teardown exists. Web search on how it publishes InkubaLM and Vulavula | Low for visual design, medium for credibility patterns |

The teardowns are extracted from the live sites (CSS tokens, measured type sizes, screenshots) by third parties. They are good evidence for type scales, colour use and spacing, but they can lag behind a redesign. Nothing below about Sarvam or Lelapa's visual design is asserted, because it could not be verified.

Recommendation for a later pass: when the site is deployed, open the seven blocked sites in a normal browser and spot check the conclusions below. None of the ten decisions at the end depends on a single source.

---

## 1. Anthropic (anthropic.com)

1. **Layout.** Left aligned, editorial. Hero statement, one featured product item, a short "latest releases" list, a mission statement, then a content grid of six items. Content width around 1200px. Sections are separated by space, not by boxes.
2. **Typography.** A serif display face (Copernicus / Tiempos) at weight 400, never bold, with negative tracking, paired with a humanist sans for body. Display around 64px, section heads 48px. Body 16px with 1.55 line height.
3. **Colour.** Warm cream canvas (#FAF9F5), warm near black ink (#141413). One warm accent (coral #CC785C) used on primary actions only. Dark surfaces reserved for product chrome and the footer.
4. **Hero.** One sentence of positioning ("AI research and products that put safety at the frontier") and one sentence of mission. One primary action in the nav ("Try Claude"). No illustration competing with the sentence.
5. **Navigation and footer.** Six top level items with dropdowns (Research, Policy, Commitments, Learn, News, product). One persistent action button. Footer is dark, dense, multi column.
6. **Motion.** Almost none visible. Restraint is the signal.
7. **Research credibility.** A dedicated research index: a few featured items, then a plain chronological list. Each row is date, team label, title. No summaries in the list. Credibility comes from volume and specificity, not from badges.
8. **Mobile.** Hamburger below about 768px, hero type roughly halves, grids drop to one column.

**Takeaway:** a sentence can be the hero. Warm off white plus one warm accent reads as considered and distinctly "not another blue AI company".

## 2. Mistral AI

1. **Layout.** 1280px max width, 32px gutters. Hero is a two column split. Marketing section rhythm 96px, hero padding 120px.
2. **Typography.** Editorial near serif display (PP Editorial Old) at 84px, weight 400, line height 1.05, tracking about -1.5px. Inter for everything else. Body line height 1.55. Section eyebrows in 11px uppercase with +1px tracking.
3. **Colour.** White canvas, cream panels, one saturated orange for every primary action and for links. A sunset gradient stripe closes every page as a brand signature.
4. **Hero.** Three words ("Frontier AI. In your hands.") over landscape photography.
5. **Navigation and footer.** Nav collapses to a hamburger below 1024px. Five column footer that becomes an accordion on mobile.
6. **Motion.** Atmosphere comes from photography and gradient, not animation.
7. **Research credibility.** Model names, stat callouts in a dedicated large numeric style, and code mockups.
8. **Mobile.** Hero type steps down 84, 64, 52, 40px across breakpoints.

**Takeaway:** a short, declarative, period terminated headline at very large size is enough. The sunset stripe shows how one memorable brand device, repeated, beats many decorative ones. The gradient itself is what we should not copy.

## 3. Cohere and Cohere Labs

1. **Layout.** Huge typographic declaration on white, then wide vertical intervals between claim, proof and call to action. Whitespace is described in their own system as a trust signal.
2. **Typography.** Display at 72 to 96px with line height 1.0 and tight tracking, then settling quickly into 16 to 24px copy. Uppercase mono labels for technical and category markers. Weight stays at 400; size and space carry hierarchy.
3. **Colour.** White canvas, near black primary buttons, deep green or navy bands for product sections. One link blue. No generic UI gradients.
4. **Hero.** One oversized sentence, one primary pill, secondary actions as underlined text links.
5. **Navigation and footer.** Logo left, menu centre, action right. Dark footer.
6. **Motion.** Media led (video, 3D) rather than interface animation.
7. **Research credibility.** Cohere Labs presents research as full width, rule separated lists with date and topic columns, not cards. Aya is framed as an open science initiative: number of languages, open weights, a named paper, and the size of the contributor community.
8. **Mobile.** Two column form rows collapse to one; research rows keep their rules and move metadata under the title.

**Takeaway:** the closest analogue to Sugan AI's mission is Aya (multilingual, underserved languages, open science). Its credibility comes from openness and named artefacts. Rule separated lists look more like research than cards do. Their own guidance says placeholder frames are better than invented product content, which matches our brief exactly.

## 4. Sarvam AI (credibility patterns only)

Visual design could not be verified. What is verifiable: Sarvam frames itself around sovereignty and language coverage, publishes each model release as a long form post with benchmark tables against named baselines (for example Indic benchmarks such as IndicGenBench and MILU), and open sources weights. Credibility is carried by named models, named benchmarks and released weights.

**Takeaway:** "sovereignty" and "ownership" resonate with institutional and government audiences, and our copy already makes that argument in the Ownership gap. Benchmarks must be named and published, never implied. Until Sugan AI has scores, the site should show the method, not numbers.

## 5. Lelapa AI (credibility patterns only)

Visual design could not be verified. What is verifiable: Lelapa describes itself as an Africa centric research and product lab. It publishes InkubaLM with exact, checkable specifics (0.4B parameters, 1.9B training tokens, five named languages, runs on CPU) and pairs research (InkubaLM) with a commercial product (Vulavula). It also publishes position pieces on compute access in Africa.

**Takeaway:** for an African language lab, the most persuasive credibility is precise, modest specifics: languages, data size, hardware it runs on. "Small enough to run locally" is a real differentiator worth giving visual weight. Sugan AI's roadmap should look like the honest, staged plan it is.

## 6. Linear

1. **Layout.** About 1280px max width, 96px between sections, 3 / 2 / 1 column grids.
2. **Typography.** One family from display to body, display at weight 600 with very tight tracking (about 4% of size at 80px). Eyebrows use slight positive tracking to read as taxonomy.
3. **Colour.** Near black canvas, a single lavender accent used scarcely (brand mark, focus, primary button). No second chromatic colour, no gradients.
4. **Hero.** One sentence and product screenshots.
5. **Navigation and footer.** Minimal nav, hamburger below 768px.
6. **Motion.** Subtle, short, on interaction only.
7. **Credibility.** The product is the proof: real screenshots, not illustrations.
8. **Mobile.** Display scales from 80px toward 36 to 40px.

**Takeaway:** one family can do all the work if weight and tracking are disciplined. That is directly relevant because Outfit is our only text face. One accent, used scarcely, reads as confidence.

## 7. Vercel

1. **Layout.** 4px base unit, everything a multiple of 4. Section padding 64 to 96px, hero up to 192px. Gutters 24px desktop, 16px mobile.
2. **Typography.** Geometric sans (Geist) at 600 for display, tracked tight, never heavier than 600. Mono (Geist Mono) at 12 to 13px for every section eyebrow and technical label, never for body. Headlines are sentence case and end with a period.
3. **Colour.** Near white page, near black ink, a single near black primary button. Colour is almost absent from interface chrome.
4. **Hero.** One period terminated sentence, two actions (filled and outlined).
5. **Navigation and footer.** Sticky header with one filled action. Large multi column footer.
6. **Motion.** Quick hover states. The mesh gradient is the only decoration.
7. **Credibility.** Customer logos and numbers. Not available to us, and must not be faked.
8. **Mobile.** Grids collapse to one column; gutters shrink to 16px.

**Takeaway:** a geometric sans plus mono labels is exactly our pairing (Outfit plus JetBrains Mono). Period terminated headlines match our copy ("AI that speaks Somali."). Mono belongs to labels, never to running text.

## 8. Stripe

1. **Layout.** About 1200px container. Section gaps around 96px.
2. **Typography.** Light display weight (300) with negative tracking is the signature. Tabular figures wherever numbers appear.
3. **Colour.** One filled accent button per band. Deep navy ink rather than pure black. Warm cream bands as an interlude.
4. **Hero.** Large thin headline over a gradient mesh.
5. **Navigation and footer.** Mega menu, sticky header.
6. **Motion.** Polished but mostly on product mockups.
7. **Credibility.** Real product UI and real numbers.
8. **Mobile.** Display steps 56, 48, 32px.

**Takeaway:** light display weights at large sizes look expensive. Outfit has a 300 weight, so a light, tightly tracked display is available to us. Tabular figures should be used for phase numbers and any future benchmark tables.

## 9. Resend

1. **Layout.** 1200px body, 96px section padding, 128px on the hero and footer transitions. 64px on small mobile.
2. **Typography.** One very large display headline per page; body changes family rather than weight to carry hierarchy.
3. **Colour.** Fully dark. Accent colours appear only as low opacity glows.
4. **Hero.** Two or three words at 96px.
5. **Navigation and footer.** Wordmark and primary button stay anchored when the nav collapses.
6. **Motion.** Minimal.
7. **Credibility.** Real code samples.
8. **Mobile.** Hero clamps 96, 76, 56, 44px.

**Takeaway:** keep the primary action visible in the header at every breakpoint, including when the nav collapses. Their hero clamp ladder is a good model for ours. Their fully dark approach is what our readability rule forbids, so we take the restraint and not the palette.

---

## Cross site patterns

1. **Type does the work.** Every reference leads with one very large sentence. Display sizes cluster at 72 to 96px on desktop and 40 to 48px on mobile, line height 1.0 to 1.1, negative tracking between 2% and 4% of the size.
2. **Weight restraint.** No reference uses bold display type above 600. The most premium looking ones use 300 to 400.
3. **One accent.** Each site has one chromatic accent, applied to a small number of elements.
4. **Warm off white is the "serious AI" signal.** Anthropic, Claude and Mistral all moved off pure white and away from blue. Our gold and warm off white palette sits in good company without imitating anyone.
5. **Section rhythm of about 96px** on desktop, about 64px on mobile, on a 4px base.
6. **Max width 1200 to 1280px**, with readable text measures inside it.
7. **Mono labels for taxonomy.** Small uppercase mono eyebrows separate "label" from "content".
8. **Research reads as lists, not cards.** Date, label, title, on hairline rules.
9. **Credibility through specifics or through nothing.** Named models, named benchmarks, exact parameter counts. Nobody credible uses vague claims. Where a company has nothing to show yet, the honest move is to show method and plan.
10. **Motion is nearly absent.** Hover states and small reveals at most.

## A finding that changes the brief

The specified gold, **#C9A227, has a contrast ratio of 2.28:1 on warm off white (#FAF8F3) and 2.42:1 on white.** WCAG AA needs 4.5:1 for body text and 3:1 for large text and interface boundaries. Gold therefore cannot be used for link text or any text on a light surface. It works well on ink (8.19:1) and as a fill behind ink text (8.19:1). The spec keeps #C9A227 as the brand accent and adds a darker "gold ink" (#7A5E0E, 5.76:1 on off white) for the few places gold coloured text appears on light backgrounds.

---

## Patterns to adopt

1. **Hero is the headline, set very large in Outfit Light (300) with tight tracking, left aligned.** Every reference leads with one oversized sentence; light weight reads as premium (Stripe, Cohere).
2. **Warm off white canvas (#FAF8F3) with ink #070A0F; dark ink surfaces only for the Partner band and the footer.** Warm light grounds read as serious and keep long text readable (Anthropic, Mistral).
3. **Gold appears in exactly four roles: thin rules, link underlines, the single gold button on dark, and the current roadmap marker.** One scarce accent signals confidence (Linear, Vercel), and the contrast finding above rules out gold text on light.
4. **Asymmetric 12 column grid: section label and heading in the left 4 columns, content in the right 7 or 8.** Breaks the centred template look and reads like a paper's margin headings.
5. **Numbered mono eyebrows on every section ("01  The problem").** Mono labels as taxonomy (Vercel, Cohere) and numbered sections borrow the structure of a research paper.
6. **Lists on hairline rules instead of shadowed cards.** Research presented as ruled lists looks like research (Anthropic, Cohere Labs); avoids three identical cards.
7. **A plain "lab status" panel in the hero that lists the four building blocks and the current phase, driven by the content file.** Honest proof of progress without inventing metrics (Lelapa's modest specifics, Cohere's "placeholder over invented content").
8. **Roadmap as a horizontal four step timeline on desktop and a vertical one on mobile, current phase marked in gold.** Staged plans earn trust for early labs, and the brief asks for a timeline rather than a table.
9. **96 / 128px section rhythm on a 4px scale, 1200px content width, 64ch maximum text measure.** Matches every reference and gives the generous whitespace the brief asks for.
10. **Motion limited to a single 8px fade up on section entry and 150ms hover transitions, disabled under reduced motion.** Every reference is nearly static; calm motion is part of looking serious.

## Sources

- [anthropic.com](https://www.anthropic.com) and [anthropic.com/research](https://www.anthropic.com/research), fetched live
- Design teardowns from [VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md) (getdesign.md): claude, mistral.ai, cohere, linear.app, vercel, stripe, resend
- [Cohere Labs Aya](https://cohere.com/research/aya), [Cohere research](https://cohere.com/research)
- [Sarvam-M release post](https://www.sarvam.ai/blogs/sarvam-m), [Sarvam 30B and 105B release post](https://www.sarvam.ai/blogs/sarvam-30b-105b), [Sarvam AI on Wikipedia](https://en.wikipedia.org/wiki/Sarvam_AI)
- [InkubaLM on Lelapa's blog](https://lelapa.ai/blog/inkubalm-small-language-model), [InkubaLM on Medium](https://medium.com/@lelapa_ai/inkubalm-a-small-language-model-for-low-resource-african-languages-dc9793842dec), [Lelapa on compute access](https://lelapa.ai/locked-out-by-design-the-compute-crisis-undermining-african-innovation/)
