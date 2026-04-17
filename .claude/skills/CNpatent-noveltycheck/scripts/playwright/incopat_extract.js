// incoPat selective DOM result extraction
// Placeholder: __TOP_N__ = number of results to extract (default 20)
// Precondition: results have loaded (check #graphicTable .patent_information exists)
// Returns: { total: number, extracted: number, results: Array }
//
// v1.2.1: added an (申请号), family_tag (中国同族/全球同族 count), family_key
// (derived grouping key) to support orchestrator-side patent family merging.
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
    const tagTokens = ['发明申请', '发明授权', '实用新型', '有效', '审中', '失效'];
    const titleCN = lines.slice(pnLineIdx + 1, engIdx > 0 ? engIdx : pnLineIdx + 4)
      .filter(l => !tagTokens.includes(l) && !/^公开|^申请号|^申请日|^申请人|^IPC|同族/.test(l))
      .join(' ');

    // Extract 申请号 (AN)
    const an = field('申请号');

    // Extract 同族 tag: "中国同族 N" / "全球同族 N" / "中国同族"
    // Note: some rows show only "中国同族" with no number; treat as 1 family sibling
    let family_tag = '';
    let family_count = 0;
    const familyMatch = text.match(/(中国同族|全球同族)\s*(\d+)?/);
    if (familyMatch) {
      family_tag = familyMatch[0].trim();
      family_count = familyMatch[2] ? parseInt(familyMatch[2], 10) : 1;
    }

    // family_key for orchestrator-side grouping:
    // incoPat family members share the same 申请号 prefix (CC + year + 6-10 digits).
    // We take the first 10 chars of AN as a conservative family key (country+year+base
    // application number). Example: "CN202410123456.8" -> "CN20241012" as family_key.
    // If two rows share the same family_key, they are likely same-family members.
    const anDigits = an.replace(/[^0-9A-Z]/g, '');
    const family_key = anDigits.substring(0, 10) || '';

    const pn = row.querySelector('span.tit-name1')?.innerText.trim() || '';

    return {
      pn,
      an,
      family_key,
      family_tag,
      family_count,
      title_cn: titleCN,
      ad: field('申请日'),
      pd: field('公开\\(公告\\)日'),
      applicant: field('申请人').replace(/;$/, ''),
      ipc: field('IPC分类号').replace(/;$/, '')
    };
  });

  return { total, extracted: results.length, results };
}
