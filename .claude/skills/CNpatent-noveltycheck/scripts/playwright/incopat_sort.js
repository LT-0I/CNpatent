// incoPat sort switch to AD DESC (申请日倒序)
// No placeholders
// Precondition: results page is loaded
// Returns: { sorted: true }
() => {
  const sortText = document.querySelector('#sortText');
  if (!sortText) return { sorted: false, error: 'sortText not found' };
  sortText.click();

  const adDesc = document.querySelector('#AD_DESC');
  if (!adDesc) return { sorted: false, error: 'AD_DESC not found' };
  adDesc.click();

  // Click confirm button (visible input.retrieval with value containing '确定')
  const confirmBtns = Array.from(document.querySelectorAll('input.retrieval'))
    .filter(b => b.value.includes('确定') && b.offsetParent !== null);
  if (confirmBtns.length > 0) {
    confirmBtns[0].click();
    return { sorted: true, method: 'input.retrieval' };
  }
  // Fallback: try <button> elements
  const fallbackBtns = Array.from(document.querySelectorAll('button'))
    .filter(b => b.innerText.trim() === '确定' && b.offsetParent !== null);
  if (fallbackBtns.length > 0) {
    fallbackBtns[0].click();
    return { sorted: true, method: 'button' };
  }
  return { sorted: false, error: 'no confirm button found' };
}
