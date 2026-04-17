// CNKI login state detection
// No placeholders
// Precondition: current tab has navigated to CNKI advanced search page
// Returns: { logged_in: boolean, evidence: {...}, hint: string }
//
// CNKI allows anonymous access to the advanced search form but restricts full
// text and some export features to logged-in users. For our purposes "logged
// in" means (a) the advanced search textarea is usable AND (b) the user menu
// shows a logged-in profile, not just a "登录"/"Login" prompt.
() => {
  const url = window.location.href;

  // Core work element
  const search_textarea = document.querySelector('textarea.textarea-major');
  const work_ready = !!search_textarea;

  // Visible 登录 link (not-logged-in indicator)
  const login_link_visible = Array.from(document.querySelectorAll('a, span, button'))
    .some(el => el.textContent.trim() === '登录' && el.offsetParent !== null);

  // Logout link (logged-in indicator)
  const logout_link_visible = Array.from(document.querySelectorAll('a, span, button'))
    .some(el => /退出|登出/.test(el.textContent) && el.offsetParent !== null);

  // Personal center link (logged-in indicator)
  const personal_center_visible = Array.from(document.querySelectorAll('a, span'))
    .some(el => /个人中心|我的CNKI|我的账户/.test(el.textContent) && el.offsetParent !== null);

  // CAPTCHA check: only counts as blocking if the overlay is actually visible.
  // CNKI preloads hidden CAPTCHA containers; we must check offsetParent != null.
  const captcha_el = document.querySelector(
    '.verify-wrap, .nc_wrapper, .nc-container, [class*="captcha-wrap"], [class*="slide-verify"], [class*="verify-slider"]'
  );
  const captcha_visible = !!(captcha_el && captcha_el.offsetParent !== null);

  let logged_in;
  let hint;
  // Priority: strong login signals first (logout / 个人中心 visible = definitely logged in).
  // Only then consider CAPTCHA as blocker.
  if (logout_link_visible || personal_center_visible) {
    logged_in = true;
    hint = logout_link_visible ? '退出 link visible' : '个人中心 link visible';
  } else if (captcha_visible) {
    logged_in = false;
    hint = 'active CAPTCHA overlay visible — treat as not_logged_in';
  } else if (login_link_visible && !logout_link_visible) {
    logged_in = false;
    hint = '登录 link visible, no logout link';
  } else if (work_ready && !login_link_visible) {
    // Search form usable without login prompt — likely IP-based anonymous access
    logged_in = true;
    hint = 'search form ready, no visible 登录 link (anonymous IP access)';
  } else {
    logged_in = false;
    hint = 'ambiguous — defaulting to not_logged_in';
  }

  return {
    logged_in,
    hint,
    evidence: {
      url,
      work_ready,
      login_link_visible,
      logout_link_visible,
      personal_center_visible,
      captcha_visible
    }
  };
}
