'use client';

import { useState } from 'react';
import { streamDraft } from '../lib/streamDraft';

export default function Home() {
  const [prompt, setPrompt] = useState('');
  const [draft, setDraft]   = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError]   = useState<string|null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!prompt.trim()) return;

    setDraft('');
    setError(null);
    setLoading(true);

    const stop = await streamDraft(
      prompt.trim(),
      (t) => setDraft((d) => d + t), // accumulate tokens
      (msg) => { setError(msg); setLoading(false); }
    );

    // auto-stop after 2 minutes or when user reloads
    setTimeout(stop, 120_000);
  }

  return (
    <main className="flex flex-col items-center p-8 gap-6">
      <h1 className="text-2xl font-bold">FlexPolicy Dev Stack</h1>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          className="border rounded px-3 py-1 w-96"
          placeholder="Ask GPT-4o to draft a policy..."
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
        />
        <button
          type="submit"
          className="bg-blue-600 text-white rounded px-4 py-1 disabled:opacity-50"
          disabled={loading || !prompt.trim()}
        >
          {loading ? 'Drafting…' : 'Draft'}
        </button>
      </form>

      {error && <p className="text-red-500">{error}</p>}

      <pre className="whitespace-pre-wrap border rounded p-4 w-full max-w-3xl">
        {draft || (loading ? 'Streaming tokens…' : 'Draft will appear here.')}
      </pre>
    </main>
  );
}