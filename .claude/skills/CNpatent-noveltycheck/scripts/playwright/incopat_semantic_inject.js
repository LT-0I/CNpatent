// incoPat semantic search injection
// Placeholder: __SEMANTIC_TEXT__ = natural language description (2-3 sentences)
// Precondition: current tab is on /semanticSearch/init
// Returns: { injected: true, query: string }
() => {
  const q = '__SEMANTIC_TEXT__';
  const ta = document.getElementById('querytext');
  if (!ta) return { injected: false, error: 'querytext textarea not found' };
  ta.focus();
  ta.value = q;
  ta.dispatchEvent(new Event('input', { bubbles: true }));
  ta.dispatchEvent(new Event('change', { bubbles: true }));

  // Click semantic search button
  const btn = document.getElementById('semanticButton');
  if (!btn) return { injected: true, clicked: false, error: 'semanticButton not found' };
  btn.click();
  return { injected: true, clicked: true, query: q.substring(0, 80) };
}
