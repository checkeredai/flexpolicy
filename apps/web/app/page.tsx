'use client';

import { useEffect, useState, FormEvent } from 'react';
import { supabase } from '../lib/supabaseClient';

export default function Home() {
  const [status, setStatus]   = useState<'loading' | 'ok' | 'error'>('loading');
  const [items,  setItems]    = useState<string[]>([]);
  const [text,   setText]     = useState('');

  /** 1️⃣  FastAPI health-check */
  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/health`)
      .then((r) => (r.ok ? setStatus('ok') : setStatus('error')))
      .catch(()  => setStatus('error'));
  }, []);

  /** 2️⃣  Initial Supabase fetch */
  useEffect(() => {
    supabase.from('demo_items').select('name').then((r) => {
      if (!r.error && r.data) setItems(r.data.map((row) => row.name));
    });
  }, []);

  /** 3️⃣  Submit handler → FastAPI → Supabase */
  async function addItem(e: FormEvent) {
    e.preventDefault();
    if (!text.trim()) return;

    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/items`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: text.trim() }),
    });

    if (res.ok) {
      setItems((prev) => [...prev, text.trim()]);
      setText('');
    } else {
      console.error('Failed to insert', await res.text());
    }
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <h1 className="text-3xl font-bold mb-6">FlexPolicy Dev Stack</h1>

      {/* FastAPI status */}
      {status === 'loading' && <p>Checking API…</p>}
      {status === 'ok'      && <p className="text-green-600">✅ FastAPI is reachable!</p>}
      {status === 'error'   && <p className="text-red-600">❌ Can’t reach FastAPI</p>}

      {/* List */}
      <ul className="mt-6 text-lg">
        {items.map((n) => (
          <li key={n}>• {n}</li>
        ))}
      </ul>

      {/* Add item form */}
      <form onSubmit={addItem} className="mt-6 flex gap-2">
        <input
          className="border rounded px-3 py-1"
          placeholder="New item"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <button
          type="submit"
          className="bg-blue-600 text-white rounded px-4 py-1 disabled:opacity-50"
          disabled={!text.trim()}
        >
          Add
        </button>
      </form>
    </main>
  );
}