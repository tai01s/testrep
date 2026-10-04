/* Region map in the style of the Rain World wiki maps: every room drawn from its real terrain, connections
   between room exits, shelters, karma gates with the karma they need, and you as a dot. No GPS zoom —
   the whole region always fits the screen. */
(function () {
  const REGION_COLORS = {
    SU: '#d9c48c', HI: '#93a3c4', DS: '#5fb07d', CC: '#e3c26b', GW: '#b49a5c', SH: '#8f7fe0',
    SL: '#55b6c9', SI: '#a9d8f5', LF: '#a6d673', UW: '#cfcfcf', SS: '#f294cf', SB: '#cf6d48',
    LM: '#66c4bb', DM: '#e0a75e', LC: '#d9b26b', MS: '#5b8fd6', OE: '#ecd29e', HR: '#d44e4e',
    VS: '#9cbf7a', CL: '#c9b8de', RM: '#8a55b3', UG: '#7cbf63', SB_: '#cf6d48',
  };

  function regionColor(id) {
    if (REGION_COLORS[id]) return REGION_COLORS[id];
    let h = 0;
    for (const c of id) h = (h * 31 + c.charCodeAt(0)) % 360;
    return `hsl(${h}, 55%, 65%)`;
  }

  function rgb(color) {
    const c = document.createElement('canvas').getContext('2d');
    c.fillStyle = color;
    const hex = c.fillStyle; // normalised to #rrggbb
    return [1, 3, 5].map(i => parseInt(hex.substr(i, 2), 16));
  }

  function shade([r, g, b], f) {
    return f >= 0
      ? [r + (255 - r) * f, g + (255 - g) * f, b + (255 - b) * f].map(Math.round)
      : [r * (1 + f), g * (1 + f), b * (1 + f)].map(Math.round);
  }

  const icons = {};
  function icon(url, onload) {
    if (icons[url]) return icons[url].ok ? icons[url].img : null;
    const img = new Image();
    icons[url] = { img, ok: false };
    img.onload = () => { icons[url].ok = true; onload && onload(); };
    img.src = url;
    return null;
  }

  class MapView {
    constructor(canvas) {
      this.canvas = canvas;
      this.ctx = canvas.getContext('2d');
      this.data = null;
      this.player = null;      // { room, x, y, color }
      this.base = document.createElement('canvas');
      this.dirty = true;
      this.visible = false;
      new ResizeObserver(() => { this.dirty = true; }).observe(canvas);
      const loop = () => {
        if (this.visible) this.frame();
        setTimeout(() => requestAnimationFrame(loop), 33);
      };
      requestAnimationFrame(loop);
    }

    async load(regionId, slug) {
      const res = await fetch('/api/map/' + encodeURIComponent(regionId) + (slug ? '?slug=' + encodeURIComponent(slug) : ''));
      if (!res.ok) throw new Error('No map for ' + regionId);
      this.setData(await res.json());
    }

    setData(data) {
      this.data = data;
      this.rooms = new Map();
      const base = rgb(regionColor(data.id));
      const subs = data.subregions || [];
      for (const r of data.rooms) {
        r.w = r.w || 48; r.h = r.h || 35;
        const si = Math.max(0, subs.indexOf(r.sub));
        r.rgb = si > 0 ? shade(base, ((si % 4) - 1.5) * 0.12) : base;
        r.img = this.terrain(r);
        this.rooms.set(r.name, r);
      }
      this.k = this.calibrate(data.rooms);
      this.dirty = true;
    }

    /** Terrain bitmap, 1px per tile. */
    terrain(r) {
      if (!r.tiles) return null;
      const c = document.createElement('canvas');
      c.width = r.w; c.height = r.h;
      const g = c.getContext('2d');
      const img = g.createImageData(r.w, r.h);
      const [cr, cg, cb] = r.rgb;
      const waterTop = r.water != null && r.water >= 0 ? r.h - r.water : r.h + 1;
      for (let y = 0; y < r.h; y++) {
        for (let x = 0; x < r.w; x++) {
          const t = r.tiles.charCodeAt(y * r.w + x) - 48;
          const o = (y * r.w + x) * 4;
          let a = 0, R = cr, G = cg, B = cb;
          if (t === 1 || t === 4) a = 255;
          else if (t === 2) a = 220;
          else if (t === 3) a = 140;
          else if (y >= waterTop) { R = 60; G = 110; B = 190; a = 90; }
          img.data[o] = R; img.data[o + 1] = G; img.data[o + 2] = B; img.data[o + 3] = a;
        }
      }
      g.putImageData(img, 0, 0);
      return c;
    }

    /** Map units per tile. Picks the largest candidate scale at which rooms on the same layer don't overlap. */
    calibrate(rooms) {
      const candidates = [1, 1 / 2, 1 / 3, 1 / 4, 1 / 5];
      let best = candidates[candidates.length - 1], bestOverlap = Infinity;
      for (const k of candidates) {
        let overlap = 0, area = 0;
        for (let i = 0; i < rooms.length; i++) {
          const a = rooms[i];
          area += a.w * a.h * k * k;
          for (let j = i + 1; j < rooms.length; j++) {
            const b = rooms[j];
            if ((a.layer || 0) !== (b.layer || 0)) continue;
            const ox = Math.min(a.x + a.w * k, b.x + b.w * k) - Math.max(a.x, b.x);
            const oy = Math.min(a.y + a.h * k, b.y + b.h * k) - Math.max(a.y, b.y);
            if (ox > 0 && oy > 0) overlap += ox * oy;
          }
        }
        const ratio = area ? overlap / area : 0;
        if (ratio < 0.03) return k;
        if (ratio < bestOverlap) { bestOverlap = ratio; best = k; }
      }
      return best;
    }

    setPlayer(p) {
      this.player = p;
    }

    layout() {
      const dpr = window.devicePixelRatio || 1;
      const cw = Math.max(1, Math.round(this.canvas.clientWidth * dpr));
      const ch = Math.max(1, Math.round(this.canvas.clientHeight * dpr));
      if (this.canvas.width !== cw || this.canvas.height !== ch) {
        this.canvas.width = cw; this.canvas.height = ch;
      }
      this.base.width = cw; this.base.height = ch;
      const k = this.k;
      let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
      for (const r of this.data.rooms) {
        minX = Math.min(minX, r.x); minY = Math.min(minY, r.y);
        maxX = Math.max(maxX, r.x + r.w * k); maxY = Math.max(maxY, r.y + r.h * k);
      }
      const pad = 30 * dpr;
      const scale = Math.min((cw - pad * 2) / (maxX - minX || 1), (ch - pad * 2) / (maxY - minY || 1));
      const ox = (cw - (maxX - minX) * scale) / 2, oy = (ch - (maxY - minY) * scale) / 2;
      this.tx = X => ox + (X - minX) * scale;
      this.ty = Y => oy + (maxY - Y) * scale;
      this.scale = scale;
      this.dpr = dpr;
    }

    drawBase() {
      this.layout();
      const g = this.base.getContext('2d');
      const { k, scale, dpr } = this;
      g.clearRect(0, 0, this.base.width, this.base.height);
      g.imageSmoothingEnabled = true;
      const rooms = [...this.data.rooms].sort((a, b) => (b.layer || 0) - (a.layer || 0));

      // connections (under rooms)
      g.strokeStyle = 'rgba(255,255,255,0.55)';
      g.lineWidth = Math.max(1, 1.4 * dpr);
      g.beginPath();
      for (const [a, b, ax, ay, bx, by] of this.data.connections) {
        const ra = this.rooms.get(a), rb = this.rooms.get(b);
        if (!ra || !rb) continue;
        g.moveTo(this.tx(ra.x + ax * k), this.ty(ra.y + ay * k));
        g.lineTo(this.tx(rb.x + bx * k), this.ty(rb.y + by * k));
      }
      g.stroke();

      for (const r of rooms) {
        const x = this.tx(r.x), y = this.ty(r.y + r.h * k);
        const w = r.w * k * scale, h = r.h * k * scale;
        const dim = (r.layer || 0) > 0 ? 0.7 : 1;
        const [cr, cg, cb] = r.rgb;
        g.globalAlpha = dim;
        g.fillStyle = `rgba(${cr},${cg},${cb},0.13)`;
        g.fillRect(x, y, w, h);
        if (r.img) g.drawImage(r.img, x, y, w, h);
        g.strokeStyle = `rgba(${cr},${cg},${cb},0.55)`;
        g.lineWidth = Math.max(1, dpr);
        g.strokeRect(x + 0.5, y + 0.5, w - 1, h - 1);
        g.globalAlpha = 1;
      }

      // subregion labels at the centre of their rooms
      const subs = {};
      for (const r of this.data.rooms) {
        if (!r.sub) continue;
        const s = subs[r.sub] || (subs[r.sub] = { x: 0, y: 0, n: 0 });
        s.x += r.x + r.w * k / 2; s.y += r.y + r.h * k / 2; s.n++;
      }
      g.font = `600 ${13 * dpr}px ${getComputedStyle(document.body).fontFamily}`;
      g.textAlign = 'center';
      g.textBaseline = 'middle';
      for (const [name, s] of Object.entries(subs)) {
        if (s.n < 3) continue;
        const x = this.tx(s.x / s.n), y = this.ty(s.y / s.n);
        g.lineWidth = 4 * dpr; g.strokeStyle = 'rgba(0,0,0,0.85)';
        g.strokeText(name.toUpperCase(), x, y);
        g.fillStyle = 'rgba(255,255,255,0.75)';
        g.fillText(name.toUpperCase(), x, y);
      }

      // shelters and gates on top
      const sz = Math.max(10 * dpr, Math.min(22 * dpr, 30 * k * scale));
      for (const r of this.data.rooms) {
        const cx = this.tx(r.x + r.w * k / 2), cy = this.ty(r.y + r.h * k / 2);
        if (r.shelter) this.shelterIcon(g, cx, cy, sz * 0.8, r.ancientShelter);
        if (r.gate) this.gateIcon(g, r, cx, cy, sz);
      }
      this.dirty = false;
    }

    shelterIcon(g, x, y, s, ancient) {
      g.save();
      g.translate(x, y);
      g.fillStyle = ancient ? '#ffd27a' : '#ffffff';
      g.strokeStyle = '#000';
      g.lineWidth = 2 * this.dpr;
      g.beginPath();
      g.moveTo(0, -s / 2); g.lineTo(s / 2, -s * 0.05); g.lineTo(s / 2, s / 2);
      g.lineTo(-s / 2, s / 2); g.lineTo(-s / 2, -s * 0.05); g.closePath();
      g.stroke(); g.fill();
      g.fillStyle = '#000';
      g.fillRect(-s * 0.14, s * 0.12, s * 0.28, s * 0.38);
      g.restore();
    }

    gateIcon(g, r, cx, cy, s) {
      const lock = r.lock || {};
      const sides = [[lock.left, -1], [lock.right, 1]];
      for (const [req, side] of sides) {
        const x = cx + side * s * 0.62, y = cy;
        g.fillStyle = 'rgba(0,0,0,0.85)';
        g.beginPath(); g.arc(x, y, s * 0.62, 0, Math.PI * 2); g.fill();
        const n = parseInt(req, 10);
        const img = !isNaN(n) && n >= 1 && n <= 10 ? icon('/icon/karma/' + (n - 1), () => { this.dirty = true; }) : null;
        if (img) {
          g.drawImage(img, x - s / 2, y - s / 2, s, s);
        } else {
          g.strokeStyle = '#fff'; g.lineWidth = 1.6 * this.dpr;
          g.beginPath(); g.arc(x, y, s * 0.45, 0, Math.PI * 2); g.stroke();
          g.fillStyle = '#fff';
          g.font = `700 ${s * 0.55}px sans-serif`; g.textAlign = 'center'; g.textBaseline = 'middle';
          g.fillText(req == null ? '?' : String(req), x, y + 1);
        }
      }
      // destination label
      const parts = r.name.split('_');
      const other = parts.slice(1, 3).find(p => p !== this.data.id);
      if (other) {
        g.font = `700 ${11 * this.dpr}px sans-serif`;
        g.textAlign = 'center'; g.textBaseline = 'top';
        g.lineWidth = 3 * this.dpr; g.strokeStyle = '#000';
        g.strokeText('→ ' + other, cx, cy + s * 0.7);
        g.fillStyle = '#fff';
        g.fillText('→ ' + other, cx, cy + s * 0.7);
      }
    }

    frame() {
      if (!this.data) {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        return;
      }
      if (this.dirty) this.drawBase();
      const g = this.ctx;
      g.clearRect(0, 0, this.canvas.width, this.canvas.height);
      g.drawImage(this.base, 0, 0);
      const p = this.player;
      const room = p && this.rooms.get(p.room);
      if (!room) return;
      const k = this.k, dpr = this.dpr;
      // highlight current room
      g.strokeStyle = '#fff';
      g.lineWidth = 2 * dpr;
      g.strokeRect(this.tx(room.x), this.ty(room.y + room.h * k), room.w * k * this.scale, room.h * k * this.scale);
      const x = this.tx(room.x + Math.min(Math.max(p.x, 0), room.w) * k);
      const y = this.ty(room.y + Math.min(Math.max(p.y, 0), room.h) * k);
      const t = performance.now() / 1000;
      const pulse = (t % 1.6) / 1.6;
      g.strokeStyle = `rgba(255,255,255,${1 - pulse})`;
      g.lineWidth = 2 * dpr;
      g.beginPath(); g.arc(x, y, (6 + pulse * 18) * dpr, 0, Math.PI * 2); g.stroke();
      g.fillStyle = '#fff';
      g.beginPath(); g.arc(x, y, 7 * dpr, 0, Math.PI * 2); g.fill();
      g.fillStyle = p.color || '#fff';
      g.beginPath(); g.arc(x, y, 5 * dpr, 0, Math.PI * 2); g.fill();
    }
  }

  window.MapView = MapView;
  window.regionColor = regionColor;
})();
