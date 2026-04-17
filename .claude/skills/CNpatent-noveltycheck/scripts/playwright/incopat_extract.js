// incoPat selective DOM result extraction
// Placeholder: __TOP_N__ = number of results to extract (default 20)
// Precondition: results have loaded (check #graphicTable .patent_information exists)
// Returns: { total: number, extracted: number, results: Array }
() => {
  const topN = __TOP_N__;

  // Parse total count
  const totalEl = document.getElementById('totalCount');
  const totalText = totalEl ? totalEl.textContent : '';
  const totalMatch = totalText.match(/\d+/);
  const total = totalMatch ? parseInt(totalMatch[0], 10) : 0;

  // Extract rows
  const rows = document.querySelectorAll('#graphicTable .patent_information');
  const results = Array.from(rows).slice(0, topN).map(row => {
    const text = row.innerText;
    const field = (label) => {
      const m = text.match(new RegExp(label + '[：:]\\s*([^\\n]+)'));
      return m ? m[1].trim() : '';
    };
    const lines = text.split('\n').map(s => s.trim()).filter(Boolean);
    const pnLineIdx = lines.findIndex(l => /^[A-Z]{2}\d{6,}/.test(l));
    const engIdx = lines.findIndex(l => l.startsWith('[英]'));
    const tagTokens = ['发明申请', '发明授权', '实用新型', '有效', '审中', '中国同族', '失效'];
    const titleCN = lines.slice(pnLineIdx + 1, engIdx > 0 ? engIdx : pnLineIdx + 4)
      .filter(l => !tagTokens.includes(l) && !/^公开|^申请号|^申请日|^申请人|^IPC/.test(l))
      .join(' ');
    return {
      pn: row.querySelector('span.tit-name1')?.innerText.trim() || '',
      title_cn: titleCN,
      ad: field('申请日'),
      pd: field('公开\\(公告\\)日'),
      applicant: field('申请人').replace(/;$/, ''),
      ipc: field('IPC分类号').replace(/;$/, '')
    };
  });

  return { total, extracted: results.length, results };
}
