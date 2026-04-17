// CNKI cookie consent / CAPTCHA overlay dismissal
// No placeholders
// Precondition: CNKI page is loaded
// Returns: { dismissed: boolean, type: string }
// NOTE: This only handles cookie consent. Slider CAPTCHA requires user interaction.
() => {
  // Try to dismiss cookie consent overlay
  const closeBtns = Array.from(document.querySelectorAll(
    '.cookie-close, .layui-layer-close, .close-btn, [class*="close"]'
  )).filter(el => el.offsetParent !== null);

  for (const btn of closeBtns) {
    try { btn.click(); } catch(e) {}
  }

  // Check for slider CAPTCHA. Selectors are narrow to avoid matching unrelated
  // carousels. CNKI uses Alibaba nc_wrapper or self-hosted verify-wrap variants.
  const captcha = document.querySelector(
    '.verify-wrap, .nc_wrapper, .nc-container, [class*="captcha-wrap"], [class*="slide-verify"], [class*="verify-slider"]'
  );
  if (captcha && captcha.offsetParent !== null) {
    return { dismissed: false, type: 'slider_captcha', message: 'Slider CAPTCHA detected. User must solve manually.' };
  }

  // Try to close any modal dialogs
  const modalClose = Array.from(document.querySelectorAll(
    '.modal-close, .dialog-close, .ui-dialog-titlebar-close'
  )).filter(el => el.offsetParent !== null);

  for (const btn of modalClose) {
    try { btn.click(); } catch(e) {}
  }

  return { dismissed: closeBtns.length > 0 || modalClose.length > 0, type: 'overlay' };
}
