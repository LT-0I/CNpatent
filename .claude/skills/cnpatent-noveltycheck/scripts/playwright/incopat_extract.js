// incoPat selective DOM result extraction
// Placeholder: __TOP_N__ = number of results to extract (default 20)
// Precondition: results have loaded (check #graphicTable .patent_information exists)
// Returns: { total: number | string, extracted: number, results: Array, family_merged: boolean }
//
// v1.2.1: added `an` (申请号) to enable cross-channel same-application dedup.
// Patent-family merging itself is handled by incoPat's on-site widget
// (see incopat_merge_family.js), not by this script. When merge is active,
// #totalCount reads "N个专利族" instead of "共N条", and each row is already
// a family representative.
() => {
  const topN = __TOP_N__;

  // Parse total count. After 合并同族 it reads "N个专利族"; otherwise "共N条".
  const totalEl = document.getElementById('totalCount');
  const totalText = totalEl ? totalEl.textContent.trim() : '';
  const totalMatch = totalText.match(/\d+/);
  const total = totalMatch ? parseInt(totalMatch[0], 10) : 0;
  const family_merged = /专利族|同族/.test(totalText);

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
      an: field('申请号'),
      title_cn: titleCN,
      ad: field('申请日'),
      pd: field('公开\\(公告\\)日'),
      applicant: field('申请人').replace(/;$/, ''),
      ipc: field('IPC分类号').replace(/;$/, '')
    };
  });

  return { total, total_text: totalText, family_merged, extracted: results.length, results };
}
