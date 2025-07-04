// apps/web/lib/streamDraft.ts
export async function streamDraft(
    prompt: string,
    onToken: (t: string) => void,
    onError: (msg: string) => void
  ) {
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/draft`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt }),
        },
      );
  
      if (!res.ok) {
        onError(`HTTP ${res.status}`);
        return () => {};
      }
  
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
  
      let buffer = '';
  
      async function read() {
        const { value, done } = await reader.read();
        if (done) return;
  
        buffer += decoder.decode(value, { stream: true });
  
        // split on event delimiters
        const parts = buffer.split('\n\n');
        buffer = parts.pop() || '';
  
        for (const part of parts) {
          const line = part.trim();
          if (!line.startsWith('data:')) continue;
  
          const payload = line.slice(5).trim();
          if (payload.startsWith('429')) {
            onError('Azure quota exceeded (TPS = 0).');
            reader.cancel();
            return;
          }
          onToken(payload);
        }
        await read();
      }
  
      read();
  
      // return cancel function
      return () => reader.cancel();
    } catch (e: any) {
      onError(e.message);
      return () => {};
    }
  }