/* D-pad / arrow-key spatial navigation for the Fire TV remote. Every element with [data-nav] is a target. */
(function () {
  function targets() {
    return Array.from(document.querySelectorAll('[data-nav]')).filter(el => {
      const r = el.getBoundingClientRect();
      return r.width > 0 && r.height > 0 && !el.disabled;
    });
  }

  function center(r) { return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; }

  function move(dir) {
    const all = targets();
    const cur = document.activeElement && document.activeElement.hasAttribute('data-nav') ? document.activeElement : null;
    if (!cur) { (document.querySelector('.tabs button.on') || all[0])?.focus(); return; }
    const a = cur.getBoundingClientRect();
    const ac = center(a);
    let best = null, bestScore = Infinity;
    for (const el of all) {
      if (el === cur) continue;
      const b = el.getBoundingClientRect();
      const bc = center(b);
      const dx = bc.x - ac.x, dy = bc.y - ac.y;
      let main, cross;
      if (dir === 'left') { if (b.right > a.left + 1 && dx >= -1) continue; main = -dx; cross = Math.abs(dy); }
      if (dir === 'right') { if (b.left < a.right - 1 && dx <= 1) continue; main = dx; cross = Math.abs(dy); }
      if (dir === 'up') { if (b.bottom > a.top + 1 && dy >= -1) continue; main = -dy; cross = Math.abs(dx); }
      if (dir === 'down') { if (b.top < a.bottom - 1 && dy <= 1) continue; main = dy; cross = Math.abs(dx); }
      if (main <= 0) continue;
      const score = main + cross * 2.5;
      if (score < bestScore) { bestScore = score; best = el; }
    }
    if (best && (dir === 'left' || dir === 'right' || isOnScreen(best))) {
      best.focus({ preventScroll: false });
      best.scrollIntoView({ block: 'nearest', inline: 'nearest' });
    } else if (dir === 'up' || dir === 'down') {
      // Nothing focusable that way on screen (stat panels aren't focusable): scroll the page instead.
      window.scrollBy({ top: (dir === 'down' ? 1 : -1) * window.innerHeight * 0.45, behavior: 'smooth' });
    }
  }

  function isOnScreen(el) {
    const r = el.getBoundingClientRect();
    return r.bottom > 0 && r.top < window.innerHeight;
  }

  const keys = { ArrowLeft: 'left', ArrowRight: 'right', ArrowUp: 'up', ArrowDown: 'down' };
  document.addEventListener('keydown', e => {
    const dir = keys[e.key];
    if (dir) {
      const active = document.activeElement;
      if (active && active.tagName === 'INPUT') return;
      e.preventDefault();
      move(dir);
    } else if (e.key === 'Enter' && document.activeElement && document.activeElement.hasAttribute('data-nav')) {
      // Fire TV's centre button sends Enter; buttons handle it natively, other elements get a click.
      if (document.activeElement.tagName !== 'BUTTON') { e.preventDefault(); document.activeElement.click(); }
    }
  });

  window.Nav = { move };
})();
