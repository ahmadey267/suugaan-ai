/**
 * All site copy and editable settings live here.
 *
 * To add the Somali version later: fill in `so` with the same shape as `en`,
 * then add src/pages/so/index.astro (see docs/handover.md).
 *
 * Copy rules: no em dashes or en dashes, no invented statistics, partners,
 * scores, testimonials or demo output.
 */

export type Locale = 'en' | 'so';

export type PhaseStatus = 'done' | 'in-progress' | 'next' | 'planned';

export interface Item {
  title: string;
  body: string;
}

export interface SiteContent {
  locale: Locale;
  meta: {
    title: string;
    description: string;
    siteName: string;
    ogImageAlt: string;
  };
  links: {
    /** Concept note PDF. Placeholder until the real file is supplied. */
    conceptNote: string;
    conceptNoteIsPlaceholder: boolean;
    /** LinkedIn page. Placeholder until supplied. */
    linkedin: string;
    linkedinIsPlaceholder: boolean;
  };
  ui: {
    skipToContent: string;
    menuOpen: string;
    menuClose: string;
    primaryNavLabel: string;
    placeholderLabel: string;
    photoPlaceholder: string;
    labStatus: string;
    statusLabels: Record<PhaseStatus, string>;
    phaseWord: string;
    required: string;
    selectPlaceholder: string;
    honeypotLabel: string;
    terminalCommand: string;
    nextWord: string;
    pending: string;
    benchColumns: [string, string, string];
    now: string;
    sending: string;
  };
  nav: {
    items: { label: string; href: string }[];
    cta: { label: string; href: string };
  };
  hero: {
    headline: string;
    supporting: string;
    primary: { label: string; href: string };
    secondary: { label: string };
    small: string;
    /** Rows in the hero lab status panel. Each row takes its status from a roadmap phase. */
    labStatus: { label: string; phase: number }[];
    alphabetLabel: string;
    alphabetCaption: string;
    alphabetSummary: string;
  };
  problem: {
    eyebrow: string;
    heading: string;
    body: string;
    /** addressedBy lists building block titles (from build.blocks) that answer each gap. */
    gaps: (Item & { addressedBy: string[] })[];
    columns: [string, string, string];
  };
  build: {
    eyebrow: string;
    heading: string;
    /** Each block's small panel only restates what its body says. No invented output. */
    blocks: (Item & { detail: string[] })[];
    dataTags: string[];
    closing: string;
  };
  approach: {
    eyebrow: string;
    heading: string;
    principles: Item[];
  };
  roadmap: {
    eyebrow: string;
    heading: string;
    phases: { number: number; name: string; focus: string; status: PhaseStatus }[];
    note: string;
  };
  useCases: {
    eyebrow: string;
    heading: string;
    items: Item[];
  };
  team: {
    eyebrow: string;
    heading: string;
    founders: { name: string; role: string; bio: string; photo?: string }[];
    note: string;
  };
  partner: {
    eyebrow: string;
    heading: string;
    body: string;
    /** role preselects the matching "I am a" option in the contact form. */
    audiences: (Item & { role: string })[];
    cta: { label: string; href: string };
  };
  contact: {
    eyebrow: string;
    heading: string;
    fields: {
      name: string;
      organisation: string;
      email: string;
      role: string;
      roleOptions: string[];
      message: string;
    };
    submit: string;
    confirmation: string;
    error: string;
    validation: {
      required: string;
      email: string;
      tooLong: string;
    };
  };
  footer: {
    name: string;
    line: string;
    linkedin: string;
    conceptNote: string;
    copyright: string;
  };
  /** Hook for a real model demo after Phase 1. Keep false until one exists. */
  demo: { enabled: boolean };
}

const en: SiteContent = {
  locale: 'en',
  meta: {
    title: 'Sugan AI | Somali Language AI Lab',
    description:
      'Sugan AI is a research lab building datasets, models and benchmarks for the Somali language.',
    siteName: 'Sugan AI',
    ogImageAlt: 'Sugan AI. AI that speaks Somali.',
  },
  links: {
    conceptNote: '#concept-note-placeholder',
    conceptNoteIsPlaceholder: true,
    linkedin: '#linkedin-placeholder',
    linkedinIsPlaceholder: true,
  },
  ui: {
    skipToContent: 'Skip to content',
    menuOpen: 'Menu',
    menuClose: 'Close',
    primaryNavLabel: 'Primary',
    placeholderLabel: 'Placeholder',
    photoPlaceholder: 'Photo placeholder',
    labStatus: 'Lab status',
    statusLabels: {
      done: 'Done',
      'in-progress': 'In progress',
      next: 'Next',
      planned: 'Planned',
    },
    phaseWord: 'Phase',
    required: '(required)',
    selectPlaceholder: 'Select',
    honeypotLabel: 'Leave this field empty',
    terminalCommand: 'sugan status',
    nextWord: 'next',
    pending: 'pending',
    benchColumns: ['task', 'metric', 'native speakers'],
    now: 'Now',
    sending: 'Sending',
  },
  nav: {
    items: [
      { label: 'What we build', href: '#build' },
      { label: 'Approach', href: '#approach' },
      { label: 'Roadmap', href: '#roadmap' },
      { label: 'Team', href: '#team' },
    ],
    cta: { label: 'Partner with us', href: '#partner' },
  },
  hero: {
    headline: 'AI that speaks Somali.',
    supporting:
      'Sugan AI is a research lab building the datasets, models and benchmarks that make artificial intelligence work properly in the Somali language.',
    primary: { label: 'Partner with us', href: '#partner' },
    secondary: { label: 'Read the concept note' },
    small: 'A research initiative of AIVERSE Africa.',
    labStatus: [
      { label: 'Data', phase: 1 },
      { label: 'Models', phase: 1 },
      { label: 'Benchmark', phase: 1 },
      { label: 'Voice', phase: 3 },
    ],
    alphabetLabel: 'The Somali Latin alphabet: 21 consonants and 5 vowels, each shown with its sound.',
    alphabetCaption: 'The Somali Latin alphabet, set as a waveform. Gold letters are sounds English does not have.',
    alphabetSummary: '26 letters · 21 consonants · 5 vowels',
  },
  problem: {
    eyebrow: 'The problem',
    heading: 'More than 20 million speakers. Almost no AI built for them.',
    body: 'Somali is spoken across Somalia, Ethiopia, Kenya, Djibouti and a global diaspora. Yet the AI tools the world now relies on handle it poorly. That leaves governments, businesses and students working in a second language, or going without.',
    columns: ['Gap', 'What goes wrong', 'What we build'],
    gaps: [
      {
        title: 'Text.',
        body: 'General purpose models write weak Somali, mix dialects and mistranslate formal, legal and religious vocabulary.',
        addressedBy: ['Data', 'Models'],
      },
      {
        title: 'Voice.',
        body: 'Somali culture is deeply oral, but speech tools for the language are limited.',
        addressedBy: ['Voice'],
      },
      {
        title: 'Measurement.',
        body: 'There is no widely accepted benchmark to show which models are good enough for real work.',
        addressedBy: ['Benchmark'],
      },
      {
        title: 'Ownership.',
        body: 'The little capability that exists sits inside foreign systems, outside the control of Somali institutions.',
        addressedBy: ['Models', 'Data'],
      },
    ],
  },
  build: {
    eyebrow: 'What we build',
    heading: 'Four building blocks for Somali AI.',
    blocks: [
      {
        title: 'Data.',
        body: 'A curated Somali corpus drawn from government documents, news, literature and religious texts. Cleaned, tagged by dialect and domain, with clear provenance.',
        detail: ['government', 'news', 'literature', 'religious'],
      },
      {
        title: 'Models.',
        body: 'Efficient open weight models adapted for Somali. Small enough to run locally, offline and on modest hardware.',
        detail: ['open weights', 'runs locally', 'works offline', 'modest hardware'],
      },
      {
        title: 'Benchmark.',
        body: 'A public evaluation suite for Somali covering translation, comprehension and formal writing, scored by both metrics and native speakers.',
        detail: ['translation', 'comprehension', 'formal writing'],
      },
      {
        title: 'Voice.',
        body: 'Speech recognition for Somali, so people can use AI the way they already communicate.',
        detail: [],
      },
    ],
    dataTags: ['dialect', 'domain', 'provenance'],
    closing: 'We publish what we measure. Every model we release comes with its scores.',
  },
  approach: {
    eyebrow: 'Approach',
    heading: 'How we work.',
    principles: [
      {
        title: 'Data first.',
        body: 'Anyone can fine tune a model. The hard part is clean, rights cleared Somali data. That is where we put most of our effort.',
      },
      {
        title: 'Small models, real use.',
        body: 'We adapt efficient models that run where our users are: on limited connectivity, limited budgets and local infrastructure.',
      },
      {
        title: 'Evidence over claims.',
        body: 'We test every model against a Somali benchmark and against native speaker judgement before we say anything about it.',
      },
    ],
  },
  roadmap: {
    eyebrow: 'Roadmap',
    heading: 'Where we are.',
    phases: [
      {
        number: 1,
        name: 'Model sprint',
        focus: 'First corpus, first fine tuned model, benchmark, public demo',
        status: 'in-progress',
      },
      {
        number: 2,
        name: 'Validation',
        focus: 'Pilots with institutional partners on real documents and queries',
        status: 'next',
      },
      {
        number: 3,
        name: 'Voice and scale',
        focus: 'Somali speech recognition, wider dialect coverage, published benchmark',
        status: 'planned',
      },
      {
        number: 4,
        name: 'Sustainability',
        focus: 'Licensing to commercial partners, long term research funding',
        status: 'planned',
      },
    ],
    note: 'We move to each phase only when the previous one has delivered measurable results.',
  },
  useCases: {
    eyebrow: 'Use cases',
    heading: 'What Somali AI makes possible.',
    items: [
      {
        title: 'Public services.',
        body: 'Ministries and agencies drafting, translating and answering in the language citizens speak.',
      },
      {
        title: 'Banking and telecoms.',
        body: 'Customer service that understands Somali, in text and voice.',
      },
      {
        title: 'Education.',
        body: "Tutoring and learning tools in a student's mother tongue.",
      },
      {
        title: 'Translation.',
        body: 'Reliable English and Somali translation for institutions, media and NGOs.',
      },
    ],
  },
  team: {
    eyebrow: 'Team',
    heading: 'Who is behind Sugan AI.',
    founders: [
      {
        name: 'Ahmed Siyad Abdirahman',
        role: 'Founder',
        bio: "Software engineer and Founder of AIVERSE Africa. Member of Kenya's national AI policy committee. Pursuing an MSc in Artificial Intelligence at Liverpool John Moores University.",
      },
      {
        name: 'Abdirahman Bashir',
        role: 'Founder',
        bio: 'CEO of Opal Ridge Partners. Leads institutional relationships and partnerships.',
      },
    ],
    note: 'Sugan AI is a research initiative of AIVERSE Africa, an AI consulting, training and product development company based in Nairobi.',
  },
  partner: {
    eyebrow: 'Partner with us',
    heading: 'Help build Somali AI.',
    body: 'We are working with a small group of early partners. If one of these describes you, we would like to talk.',
    audiences: [
      {
        title: 'Funders and foundations.',
        body: 'Support the first phases of an open, measurable contribution to Somali language technology.',
        role: 'Funder',
      },
      {
        title: 'Government and public institutions.',
        body: 'Bring documents and use cases, and get early access to Somali AI tools.',
        role: 'Institution',
      },
      {
        title: 'Universities and researchers.',
        body: 'Collaborate on data, annotation and evaluation.',
        role: 'Researcher',
      },
      {
        title: 'Compute and technology providers.',
        body: 'Contribute infrastructure and become part of a reference case in African language AI.',
        role: 'Technology provider',
      },
    ],
    cta: { label: 'Start a conversation', href: '#contact' },
  },
  contact: {
    eyebrow: 'Contact',
    heading: 'Get in touch.',
    fields: {
      name: 'Name',
      organisation: 'Organisation',
      email: 'Email',
      role: 'I am a',
      roleOptions: ['Funder', 'Institution', 'Researcher', 'Technology provider', 'Other'],
      message: 'Message',
    },
    submit: 'Send message',
    confirmation: 'Thank you. We will reply within two working days.',
    error: 'Something went wrong. Please try again or email us directly.',
    validation: {
      required: 'Please fill in this field.',
      email: 'Please enter a valid email address.',
      tooLong: 'This is too long.',
    },
  },
  footer: {
    name: 'Sugan AI',
    line: 'Sugan AI. A research initiative of AIVERSE Africa. Nairobi, Kenya.',
    linkedin: 'LinkedIn',
    conceptNote: 'Concept note',
    copyright: 'Copyright 2026 Sugan AI.',
  },
  demo: { enabled: false },
};

export const content: Partial<Record<Locale, SiteContent>> & { en: SiteContent } = {
  en,
};

export const defaultLocale: Locale = 'en';

/** The phase currently marked in progress, or the first not yet done. */
export function currentPhase(c: SiteContent) {
  const phases = c.roadmap.phases;
  return (
    phases.find((p) => p.status === 'in-progress') ??
    phases.find((p) => p.status !== 'done') ??
    phases[phases.length - 1]
  );
}
