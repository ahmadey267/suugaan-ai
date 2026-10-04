// Shared by the Pages Function (functions/api/contact.ts) and the tests.
// Plain TypeScript with no runtime dependencies.

export const ROLE_OPTIONS = ['Funder', 'Institution', 'Researcher', 'Technology provider', 'Other'] as const;

export const HONEYPOT_FIELD = 'company_website';

export const LIMITS = {
  name: 200,
  organisation: 200,
  email: 254,
  message: 5000,
} as const;

export interface ContactMessage {
  name: string;
  organisation: string;
  email: string;
  role: string;
  message: string;
}

export type FieldName = keyof ContactMessage;

export type ValidationResult =
  | { ok: true; spam: false; data: ContactMessage }
  | { ok: true; spam: true }
  | { ok: false; errors: Partial<Record<FieldName, 'required' | 'email' | 'too_long' | 'invalid'>> };

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function str(v: unknown): string {
  return typeof v === 'string' ? v.trim() : '';
}

export function validateContact(input: Record<string, unknown>): ValidationResult {
  // Bots fill every field. Pretend success so they learn nothing.
  if (str(input[HONEYPOT_FIELD]) !== '') return { ok: true, spam: true };

  const data: ContactMessage = {
    name: str(input.name),
    organisation: str(input.organisation),
    email: str(input.email),
    role: str(input.role),
    message: str(input.message),
  };

  const errors: Partial<Record<FieldName, 'required' | 'email' | 'too_long' | 'invalid'>> = {};

  if (!data.name) errors.name = 'required';
  else if (data.name.length > LIMITS.name) errors.name = 'too_long';

  if (data.organisation.length > LIMITS.organisation) errors.organisation = 'too_long';

  if (!data.email) errors.email = 'required';
  else if (data.email.length > LIMITS.email) errors.email = 'too_long';
  else if (!EMAIL_RE.test(data.email)) errors.email = 'email';

  if (!data.role) errors.role = 'required';
  else if (!(ROLE_OPTIONS as readonly string[]).includes(data.role)) errors.role = 'invalid';

  if (!data.message) errors.message = 'required';
  else if (data.message.length > LIMITS.message) errors.message = 'too_long';

  if (Object.keys(errors).length > 0) return { ok: false, errors };
  return { ok: true, spam: false, data };
}
