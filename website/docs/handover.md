# Sugan AI website: Handover

The marketing site for Sugan AI. One static page, nine sections, built with Astro and Tailwind CSS, deployed to Cloudflare Pages. It lives in the `website/` folder of the `suugaan-ai` repository, next to the translation API and training code.

## Design direction

The live design is direction C, chosen by Ahmed from three hero mockups: a dark lab look with light Outfit display type, and the Somali Latin alphabet set as a waveform in the hero (one bar per letter, gold for sounds English does not have; bar heights are decorative, not measured audio). It replaces the light editorial direction in `design-spec.md`, which is kept as the record of the original research. Tokens for the current design are at the top of `src/styles/global.css`.

## 1. Run it locally

Requires Node 22.12 or newer.

```bash
cd website
npm install
npm run dev        # http://localhost:4321, live reload, no contact function
```

To run the site together with the contact function, exactly as Cloudflare will:

```bash
npm run build
npx wrangler pages dev ./dist --kv CONTACT_MESSAGES
# http://localhost:8788
```

Messages sent locally are stored in a local KV simulation. List them with:

```bash
npx wrangler kv key list --namespace-id CONTACT_MESSAGES --local --persist-to .wrangler/state
```

Tests for the form validation:

```bash
npm test
```

## 2. Deploy to Cloudflare Pages

1. Cloudflare dashboard, Workers and Pages, Create, Pages, Connect to Git, choose `ahmadey267/suugaan-ai`.
2. Build settings:
   - Framework preset: Astro
   - Root directory: `website`
   - Build command: `npm run build`
   - Build output directory: `dist`
   - Environment variable `NODE_VERSION` = `22`
   - Environment variable `SITE_URL` = the final address, for example `https://sugan.ai` (used for canonical links, Open Graph, sitemap and robots.txt). If unset it defaults to `https://sugan-ai.pages.dev`.
3. Create the message store: Workers and Pages, KV, Create namespace, name it `sugan-contact-messages`.
4. Bind it: your Pages project, Settings, Bindings, Add, KV namespace. Variable name **`CONTACT_MESSAGES`**, namespace `sugan-contact-messages`. Do this for Production (and Preview if you want to test there).
5. Redeploy so the binding takes effect.

The `functions/` folder is picked up automatically because it sits inside the root directory.

## 3. Environment variables and bindings

| Name | Type | Required | Purpose |
| --- | --- | --- | --- |
| `CONTACT_MESSAGES` | KV binding | Yes, before launch | Where contact form messages are stored. Without it the form shows the error message and nothing is saved. |
| `SITE_URL` | Build variable | Recommended | Production address for canonical and social links. |
| `NODE_VERSION` | Build variable | Recommended | Pins Node 22 on the build machine. |

There are no API keys, no secrets and no email settings. **The site does not send email**, as decided after the spec review.

## 4. Reading contact messages

Cloudflare dashboard, Workers and Pages, KV, `sugan-contact-messages`. Each message is one key named `message:<time>:<id>`. The key list shows name, organisation and role, so you can scan without opening each one. Open a key to read the full message and email address.

There is no notification when a message arrives. Someone needs to check the store, ideally daily, because the confirmation message promises a reply within two working days.

## 5. Editing content

All copy, links and statuses live in `src/content/site.ts`. No component contains text.

- **Roadmap progress:** change `status` on a phase (`'done'`, `'in-progress'`, `'next'`, `'planned'`). The timeline, the gold marker and the hero "Lab status" panel all update from these values.
- **Lab status rows:** `hero.labStatus` maps each building block to a roadmap phase.
- **Links:** `links.conceptNote` and `links.linkedin`. Set the matching `...IsPlaceholder` flag to `false` when you add the real URL.
- **Founder photos:** add files to `public/team/` and set `photo: '/team/ahmed.jpg'` on the founder. Use a 4:5 portrait, at least 440 by 550 pixels.

### Adding the Somali version

1. Add a `so` object to `content` in `src/content/site.ts` with the same shape as `en` (TypeScript will flag anything missing).
2. Create `src/pages/so/index.astro`:
   ```astro
   ---
   import Page from '../../components/Page.astro';
   import { content } from '../../content/site';
   ---
   <Page c={content.so!} />
   ```
3. `lang`, `hreflang` alternates and the sitemap update automatically. Add a language link to the header when ready.

## 6. Placeholders still to replace

| Placeholder | Where | What is needed |
| --- | --- | --- |
| Logo / wordmark | Header and footer show "Sugan AI" as text. `public/favicon.svg`, `favicon.ico`, `apple-touch-icon.png` use a temporary "S" mark. | Logo as SVG. Then regenerate icons with `scripts/render-images.mjs`. |
| Founder photos | Team section, labelled "Photo placeholder" | Two portrait photos, 4:5. |
| Concept note PDF | Hero secondary button and footer link point to `#concept-note-placeholder` | The PDF. Put it in `public/` (for example `public/sugan-ai-concept-note.pdf`) and update `links.conceptNote`. |
| LinkedIn | Footer link points to `#linkedin-placeholder` | The company page URL. |
| Social share image | `public/og.png`, generated from the headline | Fine to keep. Regenerate after the logo arrives. |
| Domain | `SITE_URL` | The final domain. |

Search for `data-placeholder` in `dist/index.html` after a build to confirm none are left.

## 7. Review results

Checked on the Cloudflare local runtime (`wrangler pages dev`) with Chromium.

| Check | Result |
| --- | --- |
| Lighthouse, mobile | Performance 99, Accessibility 100, Best Practices 100, SEO 100. LCP 2.0s, CLS 0 (local static server without compression) |
| Lighthouse, desktop | 100, 100, 100, 100. LCP 0.5s, CLS 0 |
| Widths 360, 768, 1280, 1440 | No horizontal scroll, every section checked visually |
| Keyboard | Skip link is the first tab stop, visible focus everywhere, menu opens and closes with Escape and returns focus |
| Reduced motion | Reveals and smooth scroll disabled |
| No JavaScript | All content visible; the form still submits and shows the result |
| Contact function | Valid message stored; invalid input returns field errors; honeypot accepted silently and not stored; GET returns 405 |
| Copy | No em or en dashes in source or output |

Page weight: one HTML file with inlined CSS, about 32KB of Outfit and 40KB of JetBrains Mono (both Latin only), and under 3KB of JavaScript.

## 8. Open questions

1. **Name spelling.** The brief and the site say "Sugan AI". The repository is `suugaan-ai` and its Modelfile says "suugaan". Which is the public name? Changing it is one edit in `site.ts` plus the icons.
2. **Message notifications.** With email off, nobody is told when a message arrives. If that becomes a problem, the least effort option is a Cloudflare Queue or a daily scheduled Worker that posts a summary to a chat channel. Not built.
3. **Spam.** The honeypot stops simple bots. If spam gets through, add Cloudflare Turnstile (free, no puzzles for users).
4. **Small interface labels not in the brief.** Section labels (for example "The problem"), "Lab status", "Select" in the dropdown, "(required)" on fields and the field error messages were added as interface text. They make no claims. Edit them in `site.ts` if you want different wording.
5. **Real demo.** `src/components/DemoSlot.astro` is the hook, switched off by `demo.enabled: false`. The NLLB translation API in `../api` is a candidate once it is deployed with its own published scores.
6. **The old `landing/` mockup** in this repository advertises things that do not exist (pricing, SLA, SOC 2). It is not deployed, but consider deleting it so nobody publishes it by mistake.
