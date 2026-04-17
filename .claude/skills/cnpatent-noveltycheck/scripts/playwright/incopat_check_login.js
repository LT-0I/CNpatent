// incoPat login state detection
// No placeholders
// Precondition: current tab has navigated to /advancedSearch/init or /semanticSearch/init
// Returns: { logged_in: boolean, evidence: {...}, hint: string }
//
// Detection heuristic: if login succeeded (campus IP or cookie), navigating to
// /advancedSearch/init keeps us on that URL with #textarea present. If not
// logged in, the site redirects to / (homepage) where #textarea is absent and
// a visible "登录" link exists in the top nav.
() => {
  const url = window.location.href;
  const pathname = window.location.pathname;
  const on_advanced = /\/advancedSearch\/init/i.test(url);
  const on_semantic = /\/semanticSearch\/init/i.test(url);
  const redirected_home = pathname === '/' || pathname === '/index' || pathname === '/index.html';

  // Core work element check
  const textarea_exists = !!document.getElementById('textarea');        // advanced search
  const querytext_exists = !!document.getElementById('querytext');      // semantic search
  const work_ready = textarea_exists || querytext_exists;

  // Secondary signal: visible 登录 link (homepage top nav when not logged in)
  const login_link_visible = Array.from(document.querySelectorAll('a, span, button'))
    .some(el => el.textContent.trim() === '登录' && el.offsetParent !== null);

  // Tertiary signal: logout link (only visible when logged in)
  const logout_link_visible = Array.from(document.querySelectorAll('a, span, button'))
    .some(el => /退出|登出/.test(el.textContent) && el.offsetParent !== null);

  // Decision
  let logged_in;
  let hint;
  if (work_ready && !redirected_home) {
    logged_in = true;
    hint = 'work element present on target page';
  } else if (redirected_home && login_link_visible) {
    logged_in = false;
    hint = 'redirected to homepage, 登录 link visible';
  } else if (logout_link_visible) {
    logged_in = true;
    hint = '退出/logout link visible';
  } else if (login_link_visible && !work_ready) {
    logged_in = false;
    hint = '登录 link visible, no work element';
  } else {
    // Ambiguous — default to not logged in (conservative)
    logged_in = false;
    hint = 'ambiguous — defaulting to not_logged_in';
  }

  return {
    logged_in,
    hint,
    evidence: {
      url,
      on_advanced,
      on_semantic,
      redirected_home,
      textarea_exists,
      querytext_exists,
      login_link_visible,
      logout_link_visible
    }
  };
}
