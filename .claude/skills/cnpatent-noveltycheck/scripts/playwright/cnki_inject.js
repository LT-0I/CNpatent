// CNKI advanced search injection
// Placeholder: __QUERY__ = CNKI query with SU= syntax
//   e.g. "(SU='隧道' OR SU='地铁') AND (SU='病害' OR SU='裂缝')"
// Precondition: current tab is on CNKI advanced search page, user is logged in
// Returns: { injected: true, query: string }
() => {
  const q = '__QUERY__';
  const ta = document.querySelector('textarea.textarea-major');
  if (!ta) return { injected: false, error: 'textarea.textarea-major not found' };
  ta.focus();
  ta.value = q;
  ta.dispatchEvent(new Event('input', { bubbles: true }));
  ta.dispatchEvent(new Event('change', { bubbles: true }));

  const btn = document.querySelector('input.btn-search');
  if (!btn) return { injected: true, clicked: false, error: 'btn-search not found' };
  btn.click();
  return { injected: true, clicked: true, query: q.substring(0, 80) };
}
