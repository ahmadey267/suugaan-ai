// One off: renders public/og.png, apple-touch-icon.png and favicon.ico.
// Run with: node scripts/render-images.mjs (needs Playwright with Chromium).
import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)(process.env.PLAYWRIGHT_PATH ?? 'playwright');
import { writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const here = (p) => new URL(p, import.meta.url);
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1200, height: 630 } });

await page.goto(here('./og.html').href);
await page.evaluate(() => document.fonts.ready);
await page.screenshot({ path: fileURLToPath(here('../public/og.png')) });

const icon = async (size) => {
  await page.setViewportSize({ width: size, height: size });
  await page.goto(here('./icons.html').href);
  await page.evaluate((s) => {
    const i = document.getElementById('i');
    i.width = s;
    i.height = s;
  }, size);
  return page.screenshot({ omitBackground: true, clip: { x: 0, y: 0, width: size, height: size } });
};

writeFileSync(here('../public/apple-touch-icon.png'), await icon(180));

// ICO container holding a single 32px PNG.
const png = await icon(32);
const header = Buffer.alloc(22);
header.writeUInt16LE(0, 0);
header.writeUInt16LE(1, 2);
header.writeUInt16LE(1, 4);
header.writeUInt8(32, 6);
header.writeUInt8(32, 7);
header.writeUInt8(0, 8);
header.writeUInt8(0, 9);
header.writeUInt16LE(1, 10);
header.writeUInt16LE(32, 12);
header.writeUInt32LE(png.length, 14);
header.writeUInt32LE(22, 18);
writeFileSync(here('../public/favicon.ico'), Buffer.concat([header, png]));

await browser.close();
