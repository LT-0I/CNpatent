// incoPat on-site patent-family merge
// No placeholders (uses 简单同族合并 by default, the most common incoPat setting)
// Precondition: results page loaded (#totalCount present, results rendered)
// Returns: { merged: boolean, before: {...}, after: {...} }
//
// Mechanism: incoPat results page has a built-in family-merge widget. Each mode
// corresponds to a global JS function call:
//   mergeCongeners(0, li) → 不合并 (no merge, default)
//   mergeCongeners(1, li) → 简单同族合并 (simple family merge, recommended)
//   mergeCongeners(2, li) → 扩展同族合并 (extended family merge)
//   mergeCongeners(3, li) → DocDB同族合并 (DocDB family merge)
//
// Live-verified 2026-04-17: 512 hits → 364 patent families after calling (1).
// After merging, totalCount label changes from "共N条" to "N个专利族" and
// subsequent extract returns family-merged rows (one row per family).
() => {
  if (typeof window.mergeCongeners !== 'function') {
    return {
      merged: false,
      error: 'window.mergeCongeners not available — not on results page or JS not loaded'
    };
  }

  // Capture before-state
  const totalBefore = document.getElementById('totalCount')?.textContent?.trim() || '';
  const labelBefore = document.getElementById('show_merge_congeners')?.textContent?.trim() || '';
  const hiddenBefore = document.querySelector('input#mergeCongeners[type="hidden"]')?.value || '';

  // Get the LI#mergeCongeners element (second element with id="mergeCongeners" — the first is a hidden input)
  const liCandidates = Array.from(document.querySelectorAll('[id="mergeCongeners"]'))
    .filter(el => el.tagName === 'LI');
  if (liCandidates.length === 0) {
    return { merged: false, error: 'LI#mergeCongeners not found' };
  }
  const li = liCandidates[0];

  // Invoke the native merge function (1 = simple family merge)
  try {
    window.mergeCongeners(1, li);
  } catch (e) {
    return { merged: false, error: 'mergeCongeners threw: ' + String(e) };
  }

  return {
    merged: true,
    mode: '简单同族合并',
    before: {
      total: totalBefore,
      label: labelBefore,
      hidden_value: hiddenBefore
    },
    note: 'Page will reload results asynchronously; caller should browser_wait_for ~3s before extract'
  };
}
