export async function sendChatMessage(conversationId: string, message: string, nResults = 3) {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ conversation_id: conversationId, message, n_results: nResults }),
  });
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
} 