// CNKI result extraction
// Placeholder: __TOP_N__ = number of results to extract
// Precondition: CNKI results page is loaded
// Returns: { total: number, extracted: number, results: Array }
// NOTE: CNKI DOM structure varies between versions. This targets the kns8s version.
//       If extraction returns 0 results, the subagent should fall back to
//       browser_snapshot and parse the accessibility tree instead.
() => {
  const topN = __TOP_N__;

  // Parse total count - CNKI shows it in multiple possible locations
  let total = 0;
  const countEl = document.querySelector('.pagerTitleCell em') ||
                  document.querySelector('.result-count') ||
                  document.querySelector('#countSearch');
  if (countEl) {
    const m = countEl.textContent.match(/[\d,]+/);
    total = m ? parseInt(m[0].replace(/,/g, ''), 10) : 0;
  }

  // Extract result rows - CNKI kns8s uses table rows
  const rows = document.querySelectorAll('table.result-table-list tbody tr');
  const results = Array.from(rows).slice(0, topN).map(row => {
    const titleEl = row.querySelector('td.name a.fz14');
    const authorEl = row.querySelector('td.author');
    const sourceEl = row.querySelector('td.source');
    const dateEl = row.querySelector('td.date');
    const dbEl = row.querySelector('td.data');

    return {
      title: titleEl ? titleEl.textContent.trim() : '',
      url: titleEl ? titleEl.href : '',
      author: authorEl ? authorEl.textContent.trim().replace(/\s+/g, ' ') : '',
      source: sourceEl ? sourceEl.textContent.trim() : '',
      date: dateEl ? dateEl.textContent.trim() : '',
      database: dbEl ? dbEl.textContent.trim() : ''
    };
  }).filter(r => r.title);

  // If table extraction fails, try list-style layout
  if (results.length === 0) {
    const listItems = document.querySelectorAll('.result-table-list .rst-item, .s-item');
    const fallbackResults = Array.from(listItems).slice(0, topN).map(item => {
      const titleEl = item.querySelector('a.fz14, .res-title a');
      const infoEl = item.querySelector('.res-info, .info');
      return {
        title: titleEl ? titleEl.textContent.trim() : '',
        url: titleEl ? titleEl.href : '',
        info: infoEl ? infoEl.textContent.trim().substring(0, 200) : '',
        _fallback: true
      };
    }).filter(r => r.title);

    return {
      total,
      extracted: fallbackResults.length,
      results: fallbackResults,
      note: 'Used fallback list extraction. If empty, use browser_snapshot instead.'
    };
  }

  return { total, extracted: results.length, results };
}
