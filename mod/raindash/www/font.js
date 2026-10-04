/* Renders text with Rain World's own bitmap font (exported from the game by the mod at /font/DisplayFont.*).
   Each glyph is a span masked by the font sheet, so it inherits `color` like normal text.
   Falls back to the CSS font when the export isn't available (e.g. the mock server). */
(function () {
  const RWFont = { ready: false, font: null };
  window.RWFont = RWFont;

  RWFont.load = async function (name) {
    try {
      const res = await fetch('/font/' + name + '.json');
      if (!res.ok) return false;
      const meta = await res.json();
      const img = new Image();
      img.src = '/font/' + name + '.png';
      await img.decode();
      const glyphs = meta.glyphs || {};
      if (!Object.keys(glyphs).length) return false;
      // Line metrics: tallest glyph box incl. its top offset.
      let line = meta.lineHeight || 0;
      if (!line) for (const g of Object.values(glyphs)) line = Math.max(line, g[5] + g[3]);
      RWFont.font = { url: img.src, w: img.naturalWidth, h: img.naturalHeight, glyphs, line };
      RWFont.ready = true;
      document.documentElement.classList.add('bmfont');
      RWFont.renderAll(document);
      return true;
    } catch (e) {
      return false;
    }
  };

  /** Sets the text of `el`, using the bitmap font when available. Skips work if unchanged. */
  RWFont.set = function (el, text) {
    text = String(text);
    if (!el || el._rwText === text) return;
    el._rwText = text;
    if (!RWFont.ready) { el.textContent = text; return; }
    render(el, text);
  };

  RWFont.renderAll = function (root) {
    root.querySelectorAll('.rw').forEach(el => {
      const t = el._rwText != null ? el._rwText : el.textContent;
      el._rwText = null;
      RWFont.set(el, t);
    });
  };

  function render(el, text) {
    const f = RWFont.font;
    const px = parseFloat(getComputedStyle(el).fontSize) || 16;
    const s = (px * 1.15) / f.line;
    el.classList.add('bm');
    el.setAttribute('aria-label', text);
    const frag = document.createDocumentFragment();
    for (const ch of text) {
      const g = f.glyphs[ch.codePointAt(0)] || f.glyphs[String(ch.toUpperCase().codePointAt(0))];
      const box = document.createElement('span');
      box.className = 'bm-g';
      box.setAttribute('aria-hidden', 'true');
      if (!g) {
        box.style.width = (ch === ' ' ? f.line * 0.3 : f.line * 0.5) * s + 'px';
        box.style.height = f.line * s + 'px';
        frag.appendChild(box);
        continue;
      }
      const [gx, gy, gw, gh, ox, oy, adv] = g;
      box.style.width = (adv || gw) * s + 'px';
      box.style.height = f.line * s + 'px';
      if (gw > 0 && gh > 0) {
        const i = document.createElement('i');
        i.style.left = ox * s + 'px';
        i.style.top = oy * s + 'px';
        i.style.width = gw * s + 'px';
        i.style.height = gh * s + 'px';
        const mask = `url(${f.url}) ${-gx * s}px ${-gy * s}px / ${f.w * s}px ${f.h * s}px no-repeat`;
        i.style.webkitMask = mask;
        i.style.mask = mask;
        box.appendChild(i);
      }
      frag.appendChild(box);
    }
    el.textContent = '';
    el.appendChild(frag);
  }
})();
