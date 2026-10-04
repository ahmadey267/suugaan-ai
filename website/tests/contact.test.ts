import { test } from 'node:test';
import assert from 'node:assert/strict';
import { validateContact, HONEYPOT_FIELD, LIMITS } from '../src/lib/contact.ts';

const valid = {
  name: 'Amina Yusuf',
  organisation: 'Example Foundation',
  email: 'amina@example.org',
  role: 'Funder',
  message: 'We would like to talk about Phase 1.',
};

test('accepts a complete message and trims whitespace', () => {
  const r = validateContact({ ...valid, name: '  Amina Yusuf  ' });
  assert.equal(r.ok, true);
  assert.ok(r.ok && !r.spam);
  if (r.ok && !r.spam) assert.equal(r.data.name, 'Amina Yusuf');
});

test('organisation is optional', () => {
  const r = validateContact({ ...valid, organisation: '' });
  assert.equal(r.ok, true);
});

test('reports every missing required field', () => {
  const r = validateContact({});
  assert.equal(r.ok, false);
  if (!r.ok) {
    assert.deepEqual(Object.keys(r.errors).sort(), ['email', 'message', 'name', 'role']);
    assert.equal(r.errors.name, 'required');
  }
});

test('rejects a malformed email', () => {
  const r = validateContact({ ...valid, email: 'not an email' });
  assert.equal(r.ok, false);
  if (!r.ok) assert.equal(r.errors.email, 'email');
});

test('rejects a role that is not one of the form options', () => {
  const r = validateContact({ ...valid, role: 'Admin' });
  assert.equal(r.ok, false);
  if (!r.ok) assert.equal(r.errors.role, 'invalid');
});

test('rejects over long fields', () => {
  const r = validateContact({ ...valid, message: 'x'.repeat(LIMITS.message + 1) });
  assert.equal(r.ok, false);
  if (!r.ok) assert.equal(r.errors.message, 'too_long');
});

test('ignores non string values', () => {
  const r = validateContact({ ...valid, name: { $gt: '' } });
  assert.equal(r.ok, false);
  if (!r.ok) assert.equal(r.errors.name, 'required');
});

test('flags a filled honeypot as spam without validating the rest', () => {
  const r = validateContact({ [HONEYPOT_FIELD]: 'https://spam.example' });
  assert.deepEqual(r, { ok: true, spam: true });
});
