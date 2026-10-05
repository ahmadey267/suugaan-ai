/**
 * POST /api/contact
 *
 * Validates a contact form submission and stores it in Cloudflare KV.
 * No email is sent and no third party service is called.
 *
 * Binding (set in the Cloudflare Pages dashboard, see docs/handover.md):
 *   CONTACT_MESSAGES  KV namespace that receives each message.
 *
 * Accepts JSON (the enhanced form) or a normal form post (no JavaScript).
 * JSON requests get a JSON response; form posts get a redirect back to #contact.
 */
import { validateContact } from '../../src/lib/contact.ts';

interface Env {
  CONTACT_MESSAGES?: KVNamespace;
}

const MAX_BODY_BYTES = 16 * 1024;

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' },
  });
}

function redirect(request: Request, result: 'sent' | 'error'): Response {
  const url = new URL('/', request.url);
  url.searchParams.set('contact', result);
  url.hash = 'contact';
  return Response.redirect(url.toString(), 303);
}

export const onRequestPost: PagesFunction<Env> = async ({ request, env }) => {
  const type = request.headers.get('content-type') ?? '';
  const wantsJson = type.includes('application/json');

  const length = Number(request.headers.get('content-length') ?? 0);
  if (length > MAX_BODY_BYTES) {
    return wantsJson ? json({ ok: false, error: 'too_large' }, 413) : redirect(request, 'error');
  }

  let input: Record<string, unknown>;
  try {
    if (wantsJson) {
      input = (await request.json()) as Record<string, unknown>;
    } else if (type.includes('application/x-www-form-urlencoded') || type.includes('multipart/form-data')) {
      input = Object.fromEntries(await request.formData());
    } else {
      return json({ ok: false, error: 'unsupported_media_type' }, 415);
    }
  } catch {
    return wantsJson ? json({ ok: false, error: 'bad_request' }, 400) : redirect(request, 'error');
  }

  if (!input || typeof input !== 'object') {
    return wantsJson ? json({ ok: false, error: 'bad_request' }, 400) : redirect(request, 'error');
  }

  const result = validateContact(input);

  if (!result.ok) {
    return wantsJson ? json({ ok: false, errors: result.errors }, 422) : redirect(request, 'error');
  }

  if (result.spam) {
    return wantsJson ? json({ ok: true }) : redirect(request, 'sent');
  }

  if (!env.CONTACT_MESSAGES) {
    console.error('contact: CONTACT_MESSAGES KV binding is not configured; message not stored');
    return wantsJson ? json({ ok: false, error: 'not_configured' }, 503) : redirect(request, 'error');
  }

  const receivedAt = new Date().toISOString();
  const key = `message:${receivedAt}:${crypto.randomUUID()}`;
  const record = { ...result.data, receivedAt, country: request.cf?.country ?? null };

  try {
    await env.CONTACT_MESSAGES.put(key, JSON.stringify(record), {
      // Metadata shows in the dashboard key list, so messages can be scanned without opening each one.
      metadata: { name: record.name, organisation: record.organisation, role: record.role, receivedAt },
    });
  } catch (err) {
    console.error('contact: failed to store message', err);
    return wantsJson ? json({ ok: false, error: 'storage_failed' }, 500) : redirect(request, 'error');
  }

  return wantsJson ? json({ ok: true }) : redirect(request, 'sent');
};

export const onRequest: PagesFunction<Env> = async () =>
  new Response('Method Not Allowed', { status: 405, headers: { allow: 'POST' } });
