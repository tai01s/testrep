/* RainDash dashboard. Polls the mod's /api/state and renders the active tab. */
(function () {
  'use strict';

  // ------------------------------------------------------------------ reference data

  const SLUGCATS = {
    White: { name: 'The Survivor', color: '#ffffff' },
    Yellow: { name: 'The Monk', color: '#ffff73' },
    Red: { name: 'The Hunter', color: '#ff7373' },
    Gourmand: { name: 'The Gourmand', color: '#f0c296' },
    Artificer: { name: 'The Artificer', color: '#70233c' },
    Rivulet: { name: 'The Rivulet', color: '#91ccf0' },
    Spear: { name: 'The Spearmaster', color: '#4f2e69' },
    Saint: { name: 'The Saint', color: '#aaf156' },
    Inv: { name: 'Inv', color: '#16232e' },
  };

  const CREATURE_NAMES = {
    Fly: 'Batfly', BigEel: 'Leviathan', TempleGuard: 'Guardian', DaddyLongLegs: 'Daddy Long Legs',
    BrotherLongLegs: 'Brother Long Legs', CicadaA: 'Squidcada (white)', CicadaB: 'Squidcada (black)',
    PoleMimic: 'Pole Plant', TentaclePlant: 'Monster Kelp', Overseer: 'Overseer', Slugcat: 'Slugcat',
    LanternMouse: 'Lantern Mouse', JetFish: 'Jetfish', EggBug: 'Egg Bug', FireBug: 'Firebug',
    DropBug: 'Dropwig', SmallNeedleWorm: 'Noodlefly (small)', BigNeedleWorm: 'Noodlefly',
    MirosBird: 'Miros Bird', MirosVulture: 'Miros Vulture', SpitLizard: 'Caramel Lizard',
    ZoopLizard: 'Strawberry Lizard', EelLizard: 'Eel Lizard', TrainLizard: 'Train Lizard',
    ScavengerElite: 'Elite Scavenger', ScavengerKing: 'King Scavenger', StowawayBug: 'Stowaway',
    Hazer: 'Hazer', VultureGrub: 'Vulture Grub', SmallCentipede: 'Infant Centipede',
    AquaCenti: 'Aquapede', BigJelly: 'Giant Jellyfish', JungleLeech: 'Jungle Leech', SeaLeech: 'Sea Leech',
    RedCentipede: 'Red Centipede', MotherSpider: 'Mother Spider', SpitterSpider: 'Spitter Spider',
    BigSpider: 'Wolf Spider', Spider: 'Coalescipede', Deer: 'Rain Deer', GarbageWorm: 'Garbage Worm',
    Inspector: 'Inspector', Yeek: 'Yeek', Snail: 'Snail', Leech: 'Leech', Salamander: 'Salamander',
  };

  const CAUSES = {
    Fell: 'Fell into the abyss', Rain: 'Caught in the rain', Drowned: 'Drowned', Explosion: 'Exploded (overcharge)',
    Starved: 'Starved', Unknown: 'Unknown',
  };

  const EXTRA_LABELS = {
    redsDeath: 'Hunter has perished', redsExtraCycles: 'Pebbles extended cycles', ascended: 'Ascended',
    altEnding: 'Alternate ending reached', moonRevived: 'Looks to the Moon revived',
    pebblesSeenGreenNeuron: 'Pebbles saw the green neuron', pebblesEnergyTaken: 'Rarefaction cell taken',
    moonHeartRestored: "Moon's heart restored", smPearlTagged: 'Pearl delivered (Spearmaster)',
    halcyonStolen: 'Halcyon pearl taken', SSaiConversationsHad: 'Talks with Five Pebbles',
    SSaiThrowOuts: 'Times thrown out by Pebbles', moon_neuronsLeft: "Moon's neurons left",
    moon_totNeuronsGiven: 'Neurons given to Moon', moon_playerEncounters: 'Visits to Moon',
    moon_totalItemsBrought: 'Items brought to Moon', friendsSaved: 'Friends saved', foodReplenishBonus: 'Food bonus',
    chatlogsRead: 'Chatlogs read', redsCycleLimit: 'Cycle limit', hasRobo: 'Has a robo companion',
    pebblesRivuletPostgame: 'Rivulet postgame', energySeenState: 'Energy cell state', cyclesSinceSSai: 'Cycles since Pebbles',
    pebblesHasIncreasedRedsCycles: 'Pebbles increased cycles', sawVoidBathSlideshow: 'Saw the void sea',
    moon_neuronGiveConversationCounter: 'Moon neuron conversations',
  };

  // ------------------------------------------------------------------ helpers

  const $ = s => document.querySelector(s);
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
  const fmt = n => (n == null || n < 0 || isNaN(n)) ? '—' : Math.round(n).toLocaleString('en-US');
  const sum = (arr, f) => (arr || []).reduce((a, x) => a + (f ? f(x) : x), 0);
  const clamp01 = v => Math.max(0, Math.min(1, v));

  function creatureName(type) {
    if (CREATURE_NAMES[type]) return CREATURE_NAMES[type];
    return String(type).replace(/([a-z])([A-Z])/g, '$1 $2').replace(/([A-Z])([A-Z][a-z])/g, '$1 $2');
  }

  function niceKey(k) {
    return EXTRA_LABELS[k] || String(k).replace(/^moon_/, 'Moon ').replace(/([a-z])([A-Z])/g, '$1 $2').replace(/^./, c => c.toUpperCase());
  }

  function duration(sec) {
    if (sec == null || sec < 0) return '—';
    sec = Math.floor(sec);
    const h = Math.floor(sec / 3600), m = Math.floor(sec / 60) % 60, s = sec % 60;
    return h ? `${h}h ${String(m).padStart(2, '0')}m` : `${m}m ${String(s).padStart(2, '0')}s`;
  }

  function clock(sec) {
    sec = Math.max(0, Math.floor(sec));
    return `${Math.floor(sec / 60)}:${String(sec % 60).padStart(2, '0')}`;
  }

  /** Lightens dark slugcat colours (Artificer, Spearmaster, Inv) so they read on black. */
  function accentFor(hex) {
    const c = (hex || '#ffffff').replace('#', '');
    let [r, g, b] = [0, 2, 4].map(i => parseInt(c.substr(i, 2), 16));
    const lum = () => (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
    let guard = 0;
    while (lum() < 0.42 && guard++ < 20) { r += (255 - r) * 0.15; g += (255 - g) * 0.15; b += (255 - b) * 0.15; }
    return `rgb(${Math.round(r)},${Math.round(g)},${Math.round(b)})`;
  }

  function ico(sprite, color, extraClass) {
    return `<i class="ico ${extraClass || ''}" style="--src:url('/icon/${encodeURIComponent(sprite)}');--c:${color || '#fff'}"></i>`;
  }

  const imgOk = {};
  function probe(url) {
    if (imgOk[url] !== undefined) return imgOk[url];
    imgOk[url] = null;
    const i = new Image();
    i.onload = () => { imgOk[url] = true; };
    i.onerror = () => { imgOk[url] = false; };
    i.src = url;
    return null;
  }

  function tile(label, value, note, opts = {}) {
    return `<div class="tile ${opts.hero ? 'hero' : ''}">
      <div class="lbl">${opts.icon || ''}${esc(label)}</div>
      <div class="val rw ${String(value).length > 6 ? 'long' : ''}">${esc(value)}</div>
      ${note ? `<div class="note">${esc(note)}</div>` : ''}
    </div>`;
  }

  function barList(items, opts = {}) {
    if (!items.length) return `<div class="empty">${esc(opts.empty || 'Nothing yet.')}</div>`;
    const max = Math.max(...items.map(i => i.value), 1);
    return `<div class="bars">${items.map(i => `
      <div class="bar-row">
        ${i.icon || '<span></span>'}
        <span class="name">${esc(i.label)}</span>
        <span class="track"><span class="fill" style="width:${(i.value / max * 100).toFixed(1)}%;${i.color ? `background:${i.color}` : ''}"></span></span>
        <span class="num">${fmt(i.value)}</span>
      </div>`).join('')}</div>`;
  }

  function mapToItems(map, labelFn, limit) {
    return Object.entries(map || {})
      .map(([k, v]) => ({ key: k, label: labelFn ? labelFn(k) : k, value: v }))
      .filter(i => i.value > 0)
      .sort((a, b) => b.value - a.value)
      .slice(0, limit || 99);
  }

  // ------------------------------------------------------------------ state

  const app = {
    data: null,          // last /api/state
    view: 'live',        // 'live' or a cached campaign key
    viewData: null,      // { campaign, tracker } for cached views
    cachedList: [],
    tab: 'overview',
    sig: {},
    online: false,
    regions: null,
    regionsSlug: null,
    mapRegion: null,
    mapAuto: true,
  };

  function current() {
    if (app.view === 'live') {
      const d = app.data || {};
      return { campaign: d.campaign, tracker: d.tracker, live: d.status === 'ingame' ? d.live : null, status: d.status };
    }
    const v = app.viewData || {};
    return { campaign: v.campaign, tracker: v.tracker, live: null, status: 'cached' };
  }

  // ------------------------------------------------------------------ polling

  async function poll() {
    try {
      const res = await fetch('/api/state', { cache: 'no-store' });
      app.data = await res.json();
      app.online = true;
    } catch (e) {
      app.online = false;
    }
    try { render(); } catch (e) { console.error(e); }
    setTimeout(poll, app.tab === 'campaign' || app.tab === 'map' ? 250 : 600);
  }

  async function refreshCachedList() {
    try {
      const res = await fetch('/api/campaigns', { cache: 'no-store' });
      app.cachedList = (await res.json()).sort((a, b) => b.updated - a.updated);
    } catch (e) { /* offline */ }
  }

  // ------------------------------------------------------------------ header

  function renderHeader(cur) {
    const c = cur.campaign;
    const live = cur.live;
    const dot = $('#statusDot');
    dot.className = 'dot ' + (!app.online ? '' : cur.status === 'ingame' ? 'live' : 'menu');
    $('#statusText').textContent = !app.online ? 'offline — is Rain World running?'
      : cur.status === 'ingame' ? (live && live.paused ? 'live · paused' : 'live')
      : cur.status === 'cached' ? 'saved snapshot'
      : cur.status === 'arena' ? 'arena (no campaign stats)' : 'in menu · last campaign';

    const slug = c ? SLUGCATS[c.slugcat] || { name: c.slugcat, color: c.color } : null;
    const accent = accentFor(c ? (c.color || slug.color) : '#ffffff');
    document.documentElement.style.setProperty('--accent', accent);
    app.accent = accent;

    const icon = $('#slugIcon');
    icon.style.setProperty('--src', "url('/icon/Kill_Slugcat')");

    RWFont.set($('#slugName'), slug ? slug.name : 'RainDash');
    RWFont.set($('#campaignTabLabel'), slug ? slug.name.replace(/^The /, '') : 'Campaign');

    let where = 'Waiting for Rain World…';
    if (c) {
      const bits = [];
      if (live && live.regionName) bits.push(live.regionName);
      const p = live && live.players && live.players[0];
      if (p && p.room) bits.push(p.room);
      bits.push('Cycle ' + c.cycle);
      if (c.slot != null) bits.push('Slot ' + (c.slot + 1));
      where = bits.join('  ·  ');
    }
    $('#whereText').textContent = where;

    // karma
    const karmaUrl = c ? '/icon/karma/' + c.karma + '/big' : null;
    const kIcon = $('#karmaIcon');
    const ok = karmaUrl ? probe(karmaUrl) : false;
    kIcon.style.display = ok ? '' : 'none';
    if (ok) kIcon.style.setProperty('--src', `url('${karmaUrl}')`);
    RWFont.set($('#karmaFallback'), c && !ok ? String(c.karma + 1) : '');
    $('#karmaIcon').parentElement.title = c ? `Karma ${c.karma + 1} of ${c.karmaCap + 1}${c.reinforced ? ' (protected by a karma flower)' : ''}` : '';

    renderRainRing(live, c);
    renderFood(live, c);
  }

  function renderRainRing(live, c) {
    const svg = $('#rainRing');
    const rain = live && live.rain;
    const reinforced = c && c.reinforced;
    let html = reinforced ? '<circle r="33" fill="none" stroke="#fff" stroke-width="2.5" opacity=".9"/>' : '';
    let text = '';
    if (rain && rain.cycleLength > 0) {
      const n = Math.max(8, Math.min(30, Math.round(rain.cycleLength / 40 / 30)));
      const left = clamp01(rain.timeUntilRain / rain.cycleLength);
      const lit = Math.ceil(left * n);
      for (let i = 0; i < n; i++) {
        const a = -Math.PI / 2 + (i / n) * Math.PI * 2;
        const on = i < lit;
        html += `<circle cx="${(Math.cos(a) * 44).toFixed(2)}" cy="${(Math.sin(a) * 44).toFixed(2)}" r="${on ? 3.4 : 2.2}"
          fill="${on ? '#fff' : 'none'}" stroke="${on ? 'none' : '#6b6773'}" stroke-width="1"/>`;
      }
      const sec = rain.timeUntilRain / 40;
      text = rain.timeUntilRain > 0 ? `Rain in ${clock(sec)}` : 'The rain has come';
      if (rain.timeUntilRain <= 0) html += '<circle r="46" fill="none" stroke="#ff5c4d" stroke-width="2" opacity=".8"/>';
    }
    if (svg._html !== html) { svg.innerHTML = html; svg._html = html; }
    $('#rainText').textContent = text;
  }

  function renderFood(live, c) {
    const p = live && live.players && live.players[0];
    const el = $('#foodPips');
    let html = '';
    if (p && p.realized) {
      for (let i = 0; i < p.maxFood; i++) {
        if (i === p.foodToHibernate) html += '<span class="bar"></span>';
        if (i < p.food) html += '<span class="pip full"></span>';
        else if (i === p.food && p.quarterFood > 0) html += `<span class="pip"><b style="height:${p.quarterFood * 25}%"></b></span>`;
        else html += '<span class="pip"></span>';
      }
    } else if (c) {
      html = `<span class="sub">Food stored: ${fmt(c.food)}</span>`;
    }
    if (el._html !== html) { el.innerHTML = html; el._html = html; }
  }

  // ------------------------------------------------------------------ tabs

  function setTab(name) {
    app.tab = name;
    document.querySelectorAll('.tabs button').forEach(b => b.classList.toggle('on', b.dataset.tab === name));
    document.querySelectorAll('.tab').forEach(t => t.classList.toggle('on', t.id === 'tab-' + name));
    app.sig = {};
    if (map) map.visible = name === 'map';
    render();
  }

  function render() {
    const cur = current();
    renderHeader(cur);
    const renderers = { overview: renderOverview, kills: renderKills, campaign: renderCampaign, passages: renderPassages, map: renderMap, tracker: renderTracker };
    renderers[app.tab](cur);
  }

  /** Only touch the DOM when the tab's inputs changed (keeps the D-pad focus stable on the TV). */
  function paint(tab, sigObj, htmlFn) {
    const sig = JSON.stringify(sigObj);
    if (app.sig[tab] === sig) return;
    app.sig[tab] = sig;
    const el = document.getElementById('tab-' + tab);
    el.innerHTML = htmlFn();
    RWFont.renderAll(el);
  }

  function noData(cur) {
    if (!app.online) return '<div class="banner">Can’t reach the RainDash mod. Start Rain World with the mod enabled — this page reconnects by itself.</div>';
    if (!cur.campaign) return '<div class="banner">No campaign loaded yet. Start or continue a campaign in Rain World and your stats will appear here.</div>';
    return '';
  }

  function viewBanner(cur) {
    if (app.view !== 'live' && cur.campaign) return `<div class="banner">Viewing a saved snapshot of ${esc((SLUGCATS[cur.campaign.slugcat] || {}).name || cur.campaign.slugcat)} (slot ${cur.campaign.slot + 1}). Press the campaign button at the top to go back to live.</div>`;
    if (cur.status !== 'ingame' && cur.campaign) return '<div class="banner">You’re in the menu — showing your last campaign.</div>';
    return '';
  }

  // ---------------- overview

  function renderOverview(cur) {
    const c = cur.campaign, t = cur.tracker, live = cur.live;
    paint('overview', { c, t: t && t.counters, k: live && live.cycleKills, r: live && live.reputation, on: app.online, v: app.view }, () => {
      const empty = noData(cur);
      if (empty) return empty;
      const kills = sum(c.kills, k => k.count);
      const total = c.survives + c.deaths + c.quits;
      const passagesDone = (c.passages || []).filter(p => p.done).length;
      const echoesMet = (c.echoes || []).filter(e => e.value > 0).length;
      const hunter = c.extras && c.extras.redsCycleLimit && c.slugcat === 'Red';

      const topKills = [...(c.kills || [])].sort((a, b) => b.count - a.count).slice(0, 7).map(k => ({
        label: creatureName(k.type), value: k.count, icon: ico(k.sprite, k.color),
      }));
      const deathCauses = mapToItems(t && t.maps && t.maps.deathCauses, k => CAUSES[k] || creatureName(k), 7);

      const cycleKills = (live && live.cycleKills) || [];
      const rep = (live && live.reputation) || {};

      return `${viewBanner(cur)}
      <div class="tiles">
        ${tile('Cycle', hunter ? `${c.cycle} / ${c.extras.redsCycleLimit}` : c.cycle, hunter ? 'cycles until the illness wins' : 'rain cycles survived', { hero: true })}
        ${tile('Sleeps', fmt(c.survives), 'successful hibernations')}
        ${tile('Deaths', fmt(c.deaths), 'saved deaths')}
        ${tile('Quits', fmt(c.quits), 'quit mid-cycle')}
        ${tile('Kills', fmt(kills), `${(c.kills || []).length} kinds of creature`, { icon: ico('Multiplayer_Bones', 'var(--ink-2)') })}
        ${tile('Survival', total ? Math.round(c.survives / total * 100) + '%' : '—', 'cycles that ended in sleep')}
        ${tile('Food eaten', fmt(c.totFood), 'pips, whole campaign')}
        ${tile('Time', duration(c.totTime), 'campaign play time')}
        ${tile('Karma', `${c.karma + 1} / ${c.karmaCap + 1}`, c.reinforced ? 'protected by a karma flower' : 'not protected')}
        ${tile('Echoes', fmt(echoesMet), 'echoes encountered')}
        ${tile('Passages', `${passagesDone} / ${(c.passages || []).length}`, 'passages earned')}
        ${tile('Regions', fmt((c.regionsVisited || []).length), 'regions visited')}
      </div>
      <div class="grid cols-3 mt">
        <div class="panel"><div class="h3">Most hunted</div>${barList(topKills, { empty: 'No kills saved yet — kills are saved when you sleep.' })}</div>
        <div class="panel"><div class="h3">How you died</div>${barList(deathCauses, { empty: 'RainDash hasn’t seen you die yet.' })}</div>
        <div class="panel">
          <div class="h3">This cycle</div>
          ${cycleKills.length ? `<div class="strip">${cycleKills.map(k => `<span class="chip">${ico(k.sprite, k.color)}×${k.count}</span>`).join('')}</div>` : '<div class="empty">No kills this cycle.</div>'}
          <div class="h3 mt">Reputation here</div>
          ${repBars(rep)}
        </div>
      </div>`;
    });
  }

  function repBars(rep) {
    const entries = Object.entries(rep);
    if (!entries.length) return '<div class="empty">Shown while you play.</div>';
    return entries.map(([k, v]) => {
      const w = Math.abs(v) * 50;
      const style = v >= 0 ? `left:50%;width:${w}%;background:var(--good)` : `left:${50 - w}%;width:${w}%;background:var(--bad)`;
      return `<div class="rep"><span class="muted">${esc(k)}</span><span class="axis"><b style="${style}"></b></span><span>${v >= 0 ? '+' : ''}${(v * 100).toFixed(0)}</span></div>`;
    }).join('');
  }

  // ---------------- kills

  function renderKills(cur) {
    const c = cur.campaign, live = cur.live;
    paint('kills', { k: c && c.kills, ck: live && live.cycleKills, tk: cur.tracker && cur.tracker.maps && cur.tracker.maps.killsByType, on: app.online }, () => {
      const empty = noData(cur);
      if (empty) return empty;
      const kills = [...(c.kills || [])].sort((a, b) => b.count - a.count);
      const total = sum(kills, k => k.count);
      const cycle = (live && live.cycleKills) || [];
      const lifetime = cur.tracker && cur.tracker.counters ? cur.tracker.counters.kills : null;
      return `${viewBanner(cur)}
        <div class="row" style="align-items:baseline;gap:2.4rem;margin-bottom:1.2rem">
          <div><span class="rw big-num">${fmt(total)}</span> <span class="muted">saved kills</span></div>
          ${lifetime != null ? `<div class="muted">RainDash has seen <b style="color:#fff">${fmt(lifetime)}</b> kills in total, including cycles lost to death</div>` : ''}
        </div>
        ${cycle.length ? `<div class="panel" style="margin-bottom:1.2rem"><div class="h3">This cycle (saved when you sleep)</div><div class="strip">${cycle.map(k => `<span class="chip">${ico(k.sprite, k.color)}${esc(creatureName(k.type))} ×${k.count}</span>`).join('')}</div></div>` : ''}
        ${kills.length ? `<div class="kill-grid">${kills.map(k => `
          <div class="kill">
            ${ico(k.sprite, k.color)}
            <div class="n rw">${fmt(k.count)}</div>
            <div class="t">${esc(creatureName(k.type))}</div>
          </div>`).join('')}</div>` : '<div class="empty">No kills saved for this campaign yet.</div>'}`;
    });
  }

  // ---------------- campaign-specific

  function renderCampaign(cur) {
    const c = cur.campaign, live = cur.live, t = cur.tracker;
    const p = live && live.players && live.players[0];
    paint('campaign', { c, p, t: t && t.counters, on: app.online }, () => {
      const empty = noData(cur);
      if (empty) return empty;
      const s = (p && p.special) || {};
      const counters = (t && t.counters) || {};
      let main = '';
      switch (c.slugcat) {
        case 'Artificer': main = artificer(c, p, s, counters, live); break;
        case 'Red': main = hunter(c); break;
        case 'Gourmand': main = gourmand(c, s); break;
        case 'Saint': main = saint(c, s); break;
        case 'Rivulet': main = rivulet(c, live); break;
        case 'Spear': main = spearmaster(c, s, counters); break;
        case 'Yellow': main = monk(c); break;
        default: main = survivor(c); break;
      }
      return `${viewBanner(cur)}
        <div class="grid cols-2">
          ${main}
          <div class="grid">
            ${vitals(c, p, live)}
            ${extrasPanel(c)}
          </div>
        </div>`;
    });
  }

  function needLive(p, what) {
    return p && p.realized ? '' : `<div class="empty">${esc(what)} is shown live while you’re in a cycle.</div>`;
  }

  function artificer(c, p, s, counters, live) {
    const cap = s.pyroCapacity || 10;
    const n = s.pyroCounter || 0;
    const frac = n / cap;
    const color = frac >= 0.7 ? 'var(--bad)' : frac >= 0.4 ? 'var(--warn)' : app.accent;
    let segs = '';
    for (let i = 0; i < cap; i++) {
      const isCap = i === cap - 1;
      segs += `<span class="seg ${i < n ? 'on' : ''} ${isCap && i >= n ? 'cap' : ''}" style="${i < n ? `background:${color}` : ''}"></span>`;
    }
    const left = cap - n;
    const status = !p || !p.realized ? '' : left <= 1
      ? '<span class="status-tag bad">✸ Next explosive jump kills you</span>'
      : left <= 3 ? `<span class="status-tag warn">⚠ ${left} explosive jumps until you blow up</span>`
      : `<span class="status-tag good">● Safe — ${left} explosive jumps left</span>`;
    const scavKills = sum((c.kills || []).filter(k => /^Scavenger/.test(k.type)), k => k.count);
    const rep = live && live.reputation && live.reputation.Scavengers;
    return `<div class="panel">
      <div class="h2 rw">Explosion counter</div>
      <div class="muted small">Every explosive jump or parry adds 1. It cools down over time when you stop. At ${cap} you explode.</div>
      ${needLive(p, 'The explosion counter')}
      <div class="row" style="align-items:baseline;gap:1rem;margin-top:1rem"><span class="rw big-num" style="color:${color}">${n}</span><span class="rw" style="font-size:3rem;color:var(--ink-3)">/ ${cap}</span></div>
      <div class="gauge">${segs}</div>
      ${status}
      <div class="kv mt">
        <span>Cooldown before it ticks down</span><span>${s.pyroCooldown != null ? (s.pyroCooldown / 40).toFixed(1) + 's' : '—'}</span>
        <span>Parry cooldown</span><span>${s.pyroParryCooldown != null ? (s.pyroParryCooldown / 40).toFixed(1) + 's' : '—'}</span>
        <span>Explosive jumps (lifetime)</span><span>${fmt(counters.pyroJumps || 0)}</span>
        <span>Highest counter reached</span><span>${fmt(counters.pyroMaxCounter || 0)} / ${cap}</span>
        <span>Times you blew yourself up</span><span>${fmt(counters.explosionDeaths || 0)}</span>
        <span>Scavengers killed</span><span>${fmt(scavKills)}</span>
        <span>Scavenger reputation here</span><span>${rep != null ? (rep >= 0 ? '+' : '') + Math.round(rep * 100) : '—'}</span>
      </div>
      <div class="muted small mt">The counter limit is the Remix setting “Artificer explosion capacity” (default 10).</div>
    </div>`;
  }

  function hunter(c) {
    const x = c.extras || {};
    const limit = x.redsCycleLimit || 19;
    const left = limit - c.cycle;
    const color = left <= 3 ? 'var(--bad)' : left <= 7 ? 'var(--warn)' : app.accent;
    return `<div class="panel">
      <div class="h2 rw">Cycles remaining</div>
      <div class="muted small">The Hunter’s illness is fatal after ${limit} cycles${x.redsExtraCycles ? ' (Five Pebbles gave you more time)' : ''}.</div>
      <div class="rw big-num mt" style="color:${color}">${Math.max(0, left)}</div>
      <div class="meter"><b style="width:${clamp01(left / limit) * 100}%;background:${color}"></b></div>
      <div class="kv mt">
        <span>Current cycle</span><span>${c.cycle}</span>
        <span>Cycle limit</span><span>${limit}</span>
        <span>Moon revived</span><span>${x.moonRevived ? 'Yes' : 'No'}</span>
        <span>The Hunter has perished</span><span>${x.redsDeath ? 'Yes' : 'No'}</span>
      </div>
    </div>`;
  }

  function gourmand(c, s) {
    const quest = (c.passages || []).find(p => p.id === 'Gourmand');
    const aero = s.aerobicLevel || 0;
    return `<div class="panel">
      <div class="h2 rw">Gourmand</div>
      <div class="h3 mt">Exhaustion</div>
      <div class="meter"><b style="width:${clamp01(aero) * 100}%;background:${s.gourmandExhausted ? 'var(--bad)' : aero > 0.6 ? 'var(--warn)' : app.accent}"></b></div>
      ${s.gourmandExhausted ? '<span class="status-tag bad">Exhausted — slow down!</span>' : '<span class="status-tag good">Breathing fine</span>'}
      <div class="h3 mt">Food quest</div>
      ${quest ? `<div class="rw big-num">${fmt(quest.progress)} <span style="font-size:2.6rem;color:var(--ink-3)">/ ${fmt(quest.max)}</span></div>
        <div class="meter"><b style="width:${quest.max ? clamp01(quest.progress / quest.max) * 100 : 0}%"></b></div>` : '<div class="empty">Food quest progress appears once the game starts tracking it.</div>'}
    </div>`;
  }

  function saint(c, s) {
    const max = s.maxGodTime || 0;
    const frac = max ? clamp01((s.godTimer || 0) / max) : 0;
    const echoes = (c.echoes || []).filter(e => e.value > 0).length;
    return `<div class="panel">
      <div class="h2 rw">Ascension</div>
      <div class="muted small">Ascension power drains while you use it and recharges over time.</div>
      <div class="rw big-num mt">${Math.round(frac * 100)}%</div>
      <div class="meter"><b style="width:${frac * 100}%"></b></div>
      ${s.monkAscension ? '<span class="status-tag warn">Ascending</span>' : ''}
      <div class="kv mt">
        <span>Karma</span><span>${c.karma + 1} / ${c.karmaCap + 1}</span>
        <span>Echoes encountered</span><span>${echoes}</span>
        <span>Ascended</span><span>${c.extras && c.extras.ascended ? 'Yes' : 'No'}</span>
      </div>
    </div>`;
  }

  function rivulet(c, live) {
    const x = c.extras || {};
    const rain = live && live.rain;
    const sec = rain ? rain.timeUntilRain / 40 : null;
    return `<div class="panel">
      <div class="h2 rw">Rivulet</div>
      <div class="h3 mt">Until the rain</div>
      <div class="rw big-num">${sec != null ? clock(sec) : '—'}</div>
      ${rain ? `<div class="meter"><b style="width:${clamp01(rain.timeUntilRain / rain.cycleLength) * 100}%"></b></div>` : ''}
      <div class="kv mt">
        <span>Rarefaction cell taken</span><span>${x.pebblesEnergyTaken ? 'Yes' : 'No'}</span>
        <span>Moon’s heart restored</span><span>${x.moonHeartRestored ? 'Yes' : 'No'}</span>
        <span>Energy cell state</span><span>${x.energySeenState != null ? esc(x.energySeenState) : '—'}</span>
      </div>
    </div>`;
  }

  function spearmaster(c, s, counters) {
    const x = c.extras || {};
    const prog = s.needleProgress || 0;
    return `<div class="panel">
      <div class="h2 rw">Spearmaster</div>
      <div class="h3 mt">Next needle</div>
      <div class="meter"><b style="width:${clamp01(prog) * 100}%"></b></div>
      <div class="kv mt">
        <span>Spears thrown (lifetime)</span><span>${fmt(counters.spearsThrown || 0)}</span>
        <span>Pearl delivered</span><span>${x.smPearlTagged ? 'Yes' : 'No'}</span>
        <span>Moon revived</span><span>${x.moonRevived ? 'Yes' : 'No'}</span>
      </div>
    </div>`;
  }

  function monk(c) {
    const kills = sum(c.kills, k => k.count);
    return `<div class="panel">
      <div class="h2 rw">The Monk</div>
      <div class="h3 mt">Pacifism</div>
      <div class="rw big-num">${kills}</div>
      <div class="muted">${kills ? 'creatures killed this campaign' : 'Not a single kill. The Pilgrim would be proud.'}</div>
      ${survivorBits(c)}
    </div>`;
  }

  function survivor(c) {
    return `<div class="panel">
      <div class="h2 rw">${esc((SLUGCATS[c.slugcat] || {}).name || c.slugcat)}</div>
      ${survivorBits(c)}
    </div>`;
  }

  function survivorBits(c) {
    const echoes = (c.echoes || []).filter(e => e.value > 0);
    return `<div class="kv mt">
      <span>Karma</span><span>${c.karma + 1} / ${c.karmaCap + 1}</span>
      <span>Karma flower protection</span><span>${c.reinforced ? 'Yes' : 'No'}</span>
      <span>The Mark of Communication</span><span>${c.theMark ? 'Yes' : 'No'}</span>
      <span>Glowing</span><span>${c.theGlow ? 'Yes' : 'No'}</span>
      <span>Echoes encountered</span><span>${echoes.length}${echoes.length ? ' (' + echoes.map(e => esc(e.id)).join(', ') + ')' : ''}</span>
    </div>`;
  }

  function vitals(c, p, live) {
    if (!p || !p.realized) return `<div class="panel"><div class="h3">Vital signs</div><div class="empty">Shown live while you’re in a cycle.</div></div>`;
    const air = clamp01(p.airInLungs);
    return `<div class="panel">
      <div class="h3">Vital signs</div>
      <div class="kv">
        <span>Food</span><span>${p.food} / ${p.maxFood} (need ${p.foodToHibernate} to sleep)</span>
        <span>Air</span><span>${Math.round(air * 100)}%</span>
        <span>State</span><span>${p.dead ? 'Dead' : p.stun > 0 ? 'Stunned' : 'OK'}${p.malnourished ? ', malnourished' : ''}</span>
        <span>Glowing</span><span>${p.glowing ? 'Yes' : 'No'}</span>
        <span>In stomach</span><span>${p.special && p.special.swallowed ? esc(creatureName(p.special.swallowed)) : '—'}</span>
        <span>Last shelter</span><span>${esc(c.shelter || '—')}</span>
      </div>
      <div class="meter" title="Air"><b style="width:${air * 100}%;background:${air < 0.3 ? 'var(--bad)' : 'var(--ink-2)'}"></b></div>
    </div>`;
  }

  function extrasPanel(c) {
    const x = Object.entries(c.extras || {}).filter(([k, v]) => v !== false && v !== 0 && v !== '' && v != null && k !== 'redsCycleLimit');
    return `<div class="panel">
      <div class="h3">Story progress</div>
      ${x.length ? `<div class="kv">${x.map(([k, v]) => `<span>${esc(niceKey(k))}</span><span>${v === true ? 'Yes' : esc(v)}</span>`).join('')}</div>` : '<div class="empty">Nothing notable yet.</div>'}
    </div>`;
  }

  // ---------------- passages

  function renderPassages(cur) {
    const c = cur.campaign;
    paint('passages', { p: c && c.passages, on: app.online }, () => {
      const empty = noData(cur);
      if (empty) return empty;
      const ps = [...(c.passages || [])].sort((a, b) => (b.done - a.done) || (b.progress / (b.max || 1)) - (a.progress / (a.max || 1)));
      if (!ps.length) return `${viewBanner(cur)}<div class="empty">No passages tracked yet. They show up after you reach karma 5 and sleep.</div>`;
      return `${viewBanner(cur)}<div class="passages">${ps.map(p => `
        <div class="panel passage ${p.done ? 'done' : ''}">
          ${ico(p.sprite, null)}
          <div>
            <div class="pn rw">${esc(p.name)}</div>
            ${p.max ? `<div class="meter"><b style="width:${clamp01(p.progress / p.max) * 100}%;background:${p.done ? app.accent : 'var(--ink-2)'}"></b></div>
            <div class="muted small">${p.done ? 'Earned' : `${fmt(p.progress)} / ${fmt(p.max)}`}</div>` : `<div class="muted small">${p.done ? 'Earned' : 'In progress'}</div>`}
          </div>
        </div>`).join('')}</div>`;
    });
  }

  // ---------------- tracker (lifetime)

  function renderTracker(cur) {
    const t = cur.tracker;
    paint('tracker', { t, on: app.online }, () => {
      const empty = noData(cur);
      if (empty) return empty;
      if (!t) return '<div class="empty">No RainDash history for this campaign yet.</div>';
      const c = t.counters || {}, m = t.maps || {};
      return `${viewBanner(cur)}
        <div class="muted small" style="margin-bottom:1rem">Counted by RainDash since you installed it. Unlike the save file these keep counting through deaths and save rollbacks.</div>
        <div class="tiles">
          ${tile('Time in cycles', duration(c.timePlayed))}
          ${tile('Sleeps', fmt(c.sleeps || 0), `${fmt(c.starvingSleeps || 0)} while starving`)}
          ${tile('Deaths', fmt(c.deaths || 0))}
          ${tile('Kills', fmt(c.kills || 0))}
          ${tile('Jumps', fmt(c.jumps || 0))}
          ${tile('Throws', fmt(c.throws || 0), `${fmt(c.spearsThrown || 0)} spears`)}
          ${tile('Things eaten', fmt(c.itemsEaten || 0))}
          ${tile('Rooms explored', fmt((t.roomsVisited || []).length), `${fmt(c.roomTransitions || 0)} room changes`)}
          ${c.pyroJumps != null ? tile('Explosive jumps', fmt(c.pyroJumps), `max counter ${fmt(c.pyroMaxCounter || 0)}`) : ''}
          ${c.explosionDeaths != null ? tile('Self-explosions', fmt(c.explosionDeaths)) : ''}
        </div>
        <div class="grid cols-3 mt">
          <div class="panel"><div class="h3">Causes of death</div>${barList(mapToItems(m.deathCauses, k => CAUSES[k] || creatureName(k), 8))}</div>
          <div class="panel"><div class="h3">Eaten</div>${barList(mapToItems(m.eaten, creatureName, 8))}</div>
          <div class="panel"><div class="h3">Thrown</div>${barList(mapToItems(m.thrown, creatureName, 8))}</div>
        </div>`;
    });
  }

  // ---------------- map

  let map = null;

  function renderMap(cur) {
    if (!map) {
      map = new MapView($('#mapCanvas'));
      map.visible = app.tab === 'map';
    }
    const live = cur.live;
    const c = cur.campaign;
    const slug = c ? c.slugcat : null;
    const p = live && live.players && live.players[0];

    if (app.online && (!app.regions || app.regionsSlug !== slug)) {
      app.regionsSlug = slug;
      app.regions = [];
      fetch('/api/regions' + (slug ? '?slug=' + encodeURIComponent(slug) : ''))
        .then(r => r.json()).then(list => {
          app.regions = list;
          app.sig.mapList = null;
          const sel = list.find(x => x.id === app.mapRegion);
          if (sel) RWFont.set($('#mapTitle'), sel.name);
          renderMap(current());
        })
        .catch(() => { app.regions = null; });
    }

    const here = live && live.region;
    if (app.mapAuto && here && app.mapRegion !== here) selectRegion(here, slug, false);
    if (!app.mapRegion && app.regions && app.regions.length && !here) selectRegion(app.regions[0].id, slug, false);

    const listSig = JSON.stringify([app.regions, app.mapRegion, here]);
    if (app.sig.mapList !== listSig) {
      app.sig.mapList = listSig;
      const el = $('#regionList');
      const focused = document.activeElement && document.activeElement.dataset.region;
      el.innerHTML = (app.regions || []).map(r => `
        <button data-nav data-region="${esc(r.id)}" class="${r.id === app.mapRegion ? 'sel' : ''}">
          <span>${esc(r.name)}</span>${r.id === here ? '<span class="here" title="You are here"></span>' : ''}
        </button>`).join('') || '<div class="empty">Loading regions…</div>';
      if (focused) { const b = el.querySelector(`[data-region="${focused}"]`); if (b) b.focus({ preventScroll: true }); }
    }

    map.setPlayer(p && here === app.mapRegion ? { room: p.room, x: p.x, y: p.y, color: app.accent } : null);
    $('#mapSub').textContent = !app.mapRegion ? ''
      : here === app.mapRegion ? `You are in ${p && p.room ? p.room : 'this region'}`
      : here ? `You are in ${live.regionName || here}` : '';
  }

  let loadToken = 0;
  function selectRegion(id, slug, manual) {
    if (manual) app.mapAuto = false;
    app.mapRegion = id;
    const r = (app.regions || []).find(x => x.id === id);
    RWFont.set($('#mapTitle'), r ? r.name : id);
    const token = ++loadToken;
    map.load(id, slug).catch(() => {
      if (token === loadToken) { map.data = null; RWFont.set($('#mapTitle'), (r ? r.name : id) + ' (no map)'); }
    });
    app.sig.mapList = null;
  }

  // ------------------------------------------------------------------ input

  $('#tabs').addEventListener('click', e => {
    const b = e.target.closest('button[data-tab]');
    if (b) setTab(b.dataset.tab);
  });

  $('#regionList').addEventListener('click', e => {
    const b = e.target.closest('button[data-region]');
    if (!b) return;
    const c = current().campaign;
    if (b.dataset.region === (current().live || {}).region) app.mapAuto = true;
    selectRegion(b.dataset.region, c && c.slugcat, true);
    renderMap(current());
  });

  $('#campaignBtn').addEventListener('click', async () => {
    await refreshCachedList();
    const options = ['live', ...app.cachedList.map(x => x.key)];
    const next = options[(options.indexOf(app.view) + 1) % options.length];
    app.view = next;
    app.sig = {};
    app.regions = null;
    if (next === 'live') {
      app.viewData = null;
      $('#campaignBtn').textContent = 'Live campaign';
    } else {
      const [slot, ...slug] = next.replace(/^slot/, '').split('_');
      const name = (SLUGCATS[slug.join('_')] || {}).name || slug.join('_');
      $('#campaignBtn').textContent = `${name} · slot ${+slot + 1}`;
      try {
        app.viewData = await (await fetch('/api/campaign/' + encodeURIComponent(next))).json();
      } catch (e) { app.viewData = null; }
    }
    render();
  });

  document.addEventListener('keydown', e => {
    // Fire TV remote: rewind / fast-forward switch tabs, Back returns to the tab bar.
    const tabs = [...document.querySelectorAll('.tabs button')];
    const i = tabs.findIndex(b => b.dataset.tab === app.tab);
    if (e.key === 'MediaRewind' || e.key === '[') { setTab(tabs[(i + tabs.length - 1) % tabs.length].dataset.tab); }
    if (e.key === 'MediaFastForward' || e.key === ']') { setTab(tabs[(i + 1) % tabs.length].dataset.tab); }
    if (e.key === 'Escape' || e.key === 'GoBack' || e.key === 'BrowserBack') {
      const on = document.querySelector('.tabs button.on');
      if (on && document.activeElement !== on) { e.preventDefault(); on.focus(); }
    }
  });

  /** Called by the Fire TV app on the remote's Back button. Returns true if handled. */
  window.rdBack = function () {
    const on = document.querySelector('.tabs button.on');
    if (on && document.activeElement !== on) { on.focus(); return true; }
    return false;
  };

  // ------------------------------------------------------------------ boot

  if (matchMedia('(prefers-reduced-motion: reduce)').matches) document.body.classList.add('reduce');
  RWFont.load('DisplayFont');
  refreshCachedList();
  poll();
  setTimeout(() => { const on = document.querySelector('.tabs button.on'); if (on) on.focus(); }, 300);
})();
