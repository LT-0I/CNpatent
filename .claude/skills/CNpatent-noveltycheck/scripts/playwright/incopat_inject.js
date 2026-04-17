// incoPat command search query injection
// Placeholder: __QUERY__ = full query expression (e.g. TIABC=(...) AND IPC=(...))
// Precondition: current tab is on /advancedSearch/init
// Returns: { injected: true, query: string }
() => {
  const q = '__QUERY__';
  const el = document.getElementById('textarea');
  if (!el) return { injected: false, error: 'textarea element not found' };
  el.focus();
  el.textContent = q;
  el.dispatchEvent(new InputEvent('input', { bubbles: true, data: q, inputType: 'insertText' }));
  el.dispatchEvent(new Event('change', { bubbles: true }));
  el.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true }));
  // Click command search button (2nd visible input.retrieval on init page)
  const btns = Array.from(document.querySelectorAll('input.retrieval'))
    .filter(b => b.offsetParent !== null);
  if (btns.length >= 2) {
    btns[1].click();
  } else if (btns.length === 1) {
    // Results page has only 1 visible button
    btns[0].click();
  } else {
    return { injected: true, clicked: false, error: 'no visible search button' };
  }
  return { injected: true, clicked: true, query: q.substring(0, 80) };
}
