#!/usr/bin/env node
// Serves the dashboard with fake data so you can work on the UI without launching Rain World.
//   node tools/mock-server.js [port] [slugcat]     e.g. node tools/mock-server.js 8787 Artificer
const http = require('http');
const fs = require('fs');
const path = require('path');

const port = +process.argv[2] || 8787;
const slug = process.argv[3] || 'Artificer';
const www = path.join(__dirname, '..', 'mod', 'raindash', 'www');

const COLORS = { White: '#ffffff', Yellow: '#ffff73', Red: '#ff7373', Gourmand: '#f0c296', Artificer: '#70233c', Rivulet: '#91ccf0', Spear: '#4f2e69', Saint: '#aaf156' };

// ---------- deterministic random
let seed = 7;
const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);

// ---------- fake region: rooms with cave-ish terrain
function makeRegion(id, name) {
  seed = id.charCodeAt(0) * 31 + id.charCodeAt(1);
  const rooms = [], connections = [];
  const cols = 9, rowsN = 5;
  const subs = ['Lower ' + name, 'Upper ' + name, 'The Depths'];
  for (let gy = 0; gy < rowsN; gy++) {
    for (let gx = 0; gx < cols; gx++) {
      if (rnd() < 0.18) continue;
      const w = 30 + Math.floor(rnd() * 50), h = 20 + Math.floor(rnd() * 40);
      const r = {
        name: `${id}_${String.fromCharCode(65 + gy)}${String(gx).padStart(2, '0')}`,
        x: gx * 95 + rnd() * 10, y: gy * 75 + rnd() * 10, layer: 0, sub: subs[Math.min(2, Math.floor(gy / 2))],
        w, h, water: rnd() < 0.2 ? Math.floor(h * 0.3) : -1,
      };
      let tiles = '';
      for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
        const edge = x < 2 || y < 2 || x >= w - 2 || y >= h - 2;
        const blob = Math.sin(x * 0.35 + gx) * Math.cos(y * 0.3 + gy) > 0.55;
        const floor = y === Math.floor(h * 0.6) && x % 9 < 6;
        tiles += edge || blob ? '1' : floor ? '3' : (y === h - 3 && x % 5 === 0 ? '2' : '0');
      }
      r.tiles = tiles;
      rooms.push(r);
    }
  }
  rooms[3].shelter = true; rooms[11].shelter = true; rooms[20].shelter = true;
  rooms[rooms.length - 2].shelter = true; rooms[25].ancientShelter = true; rooms[25].shelter = true;
  const gateA = rooms[0], gateB = rooms[rooms.length - 1];
  gateA.name = `GATE_${id}_HI`; gateA.gate = true; gateA.lock = { left: '2', right: '1' };
  gateB.name = `GATE_SL_${id}`; gateB.gate = true; gateB.lock = { left: '3', right: '5' };
  for (let i = 0; i < rooms.length - 1; i++) {
    const a = rooms[i], b = rooms[i + 1];
    if (Math.abs(a.y - b.y) < 20) connections.push([a.name, b.name, a.w - 1, Math.floor(a.h / 2), 0, Math.floor(b.h / 2)]);
    const below = rooms.find(r => Math.abs(r.x - a.x) < 20 && r.y > a.y + 40 && r.y < a.y + 100);
    if (below && rnd() < 0.6) connections.push([a.name, below.name, Math.floor(a.w / 2), a.h - 1, Math.floor(below.w / 2), 0]);
  }
  return { id, name, slugcat: slug, subregions: subs, rooms, connections };
}

const REGIONS = [['SU', 'Outskirts'], ['HI', 'Industrial Complex'], ['DS', 'Drainage System'], ['GW', 'Garbage Wastes'], ['SL', 'Shoreline'], ['SH', 'Shaded Citadel'], ['UW', 'The Exterior'], ['SS', 'Five Pebbles'], ['SI', 'Sky Islands'], ['LF', 'Farm Arrays'], ['SB', 'Subterranean'], ['CC', 'Chimney Canopy']];
const maps = {};
const getMap = id => maps[id] || (maps[id] = makeRegion(id, (REGIONS.find(r => r[0] === id) || [id, id])[1]));

// ---------- fake state
const start = Date.now();
function state() {
  const t = (Date.now() - start) / 1000;
  const m = getMap('SU');
  const room = m.rooms[Math.floor(t / 6) % m.rooms.length];
  const pyro = Math.floor(t / 1.5) % 11;
  const kills = [
    ['GreenLizard', 'Kill_Green_Lizard', '#33ff33', 7], ['PinkLizard', 'Kill_Standard_Lizard', '#ff33ff', 4],
    ['Scavenger', 'Kill_Scavenger', '#a9a4b2', 23], ['ScavengerElite', 'Kill_ScavengerElite', '#a9a4b2', 5],
    ['Vulture', 'Kill_Vulture', '#d4ca6e', 2], ['BigSpider', 'Kill_BigSpider', '#a9a4b2', 3],
    ['Fly', 'Kill_Bat', '#a9a4b2', 41], ['Centipede', 'Kill_Centipede2', '#ffa600', 3], ['DropBug', 'Kill_DropBug', '#a9a4b2', 2],
  ].map(([type, sprite, color, count]) => ({ type, sprite, color, count, intData: 0 }));
  return {
    mod: '1.0.0', time: Date.now(), status: 'ingame', url: `http://localhost:${port}/`,
    campaign: {
      key: `slot0_${slug}`, slot: 0, slugcat: slug, color: COLORS[slug] || '#fff', cycle: 37, karma: 4, karmaCap: 6, reinforced: true,
      deaths: 21, survives: 34, quits: 3, food: 2, totFood: 268, totTime: 61234, theMark: true, theGlow: false, shelter: 'SU_S04',
      kills,
      echoes: [{ id: 'CC', value: 2 }, { id: 'SH', value: 1 }, { id: 'SI', value: 0 }],
      passages: [
        { id: 'Survivor', name: 'The Survivor', sprite: 'SurvivorA', done: true, progress: 5, max: 5 },
        { id: 'Hunter', name: 'The Hunter', sprite: 'HunterA', done: false, progress: 7, max: 12 },
        { id: 'Saint', name: 'The Saint', sprite: 'SaintA', done: false, progress: 2, max: 12 },
        { id: 'Traveller', name: 'The Wanderer', sprite: 'TravellerA', done: false, progress: 6, max: 12 },
        { id: 'Chieftain', name: 'The Chieftain', sprite: 'ChieftainA', done: false, progress: 0.42, max: 1 },
        { id: 'Monk', name: 'The Monk', sprite: 'MonkA', done: true, progress: 5, max: 5 },
        { id: 'Gourmand', name: 'The Gourmand', sprite: 'GourmandA', done: false, progress: 9, max: 22 },
      ],
      regionsVisited: ['SU', 'HI', 'DS', 'GW', 'SL', 'SH', 'CC'],
      extras: { moonRevived: false, SSaiConversationsHad: 2, moon_neuronsLeft: 5, moon_playerEncounters: 3, redsCycleLimit: 19, pebblesEnergyTaken: true },
      updated: Date.now(),
    },
    tracker: {
      key: `slot0_${slug}`,
      counters: { timePlayed: 48211 + t, sleeps: 39, starvingSleeps: 4, deaths: 33, kills: 128, jumps: 15342, throws: 902, spearsThrown: 611, itemsEaten: 412, roomTransitions: 1840, pyroJumps: 377, pyroMaxCounter: 10, explosionDeaths: 6 },
      maps: {
        deathCauses: { Fell: 9, Rain: 5, GreenLizard: 6, Explosion: 6, Vulture: 3, Drowned: 2, Scavenger: 2 },
        eaten: { DangleFruit: 120, Mushroom: 4, SSOracleSwarmer: 2, Fly: 160, EggBugEgg: 30, WaterNut: 50, SlimeMold: 46 },
        thrown: { Spear: 611, Rock: 210, ScavengerBomb: 81 },
        killsByType: { Scavenger: 40 },
      },
      roomsVisited: m.rooms.slice(0, 30).map(r => r.name),
    },
    live: {
      region: 'SU', regionName: 'Outskirts',
      rain: { timeUntilRain: Math.max(0, 40 * (420 - t * 3)), cycleLength: 40 * 600, timer: 0, preTimer: 0 },
      players: [{
        index: 0, realized: true, room: room.name, x: (t * 3) % room.w, y: room.h / 2, dead: false,
        food: 5, quarterFood: 2, maxFood: 9, foodToHibernate: 6, malnourished: false, airInLungs: 0.8, stun: 0, glowing: false,
        special: { pyroCounter: pyro, pyroCapacity: 10, pyroCooldown: 60 - (t * 40) % 60, pyroParryCooldown: 0, aerobicLevel: (t % 10) / 10, gourmandExhausted: t % 10 > 8, godTimer: 300, maxGodTime: 400, needleProgress: (t % 5) / 5, swallowed: 'Rock' },
      }],
      cycleKills: [kills[2], { ...kills[6], count: 3 }],
      reputation: { Scavengers: -0.35, Lizards: 0.12 },
      paused: false,
    },
  };
}

// ---------- icons: a simple placeholder shape (the real mod serves sprites from the game)
const ICON_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M10 2c4 0 7 3 7 7 0 3-2 5-3 7h-8c-1-2-3-4-3-7 0-4 3-7 7-7z" fill="#fff"/></svg>';
const KARMA_SVG = k => `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40"><circle cx="20" cy="20" r="17" fill="none" stroke="#fff" stroke-width="3"/><text x="20" y="27" font-size="19" text-anchor="middle" fill="#fff" font-family="sans-serif" font-weight="700">${+k + 1}</text></svg>`;

const MIME = { '.html': 'text/html', '.js': 'application/javascript', '.css': 'text/css', '.png': 'image/png' };

http.createServer((req, res) => {
  const url = new URL(req.url, 'http://x');
  const p = decodeURIComponent(url.pathname);
  const json = obj => { res.writeHead(200, { 'Content-Type': 'application/json' }); res.end(JSON.stringify(obj)); };
  if (p === '/api/state') return json(state());
  if (p === '/api/regions') return json(REGIONS.map(([id, name]) => ({ id, name })));
  if (p.startsWith('/api/map/')) return json(getMap(p.slice(9)));
  if (p === '/api/campaigns') return json([{ key: `slot0_${slug}`, updated: Date.now() }, { key: 'slot0_Red', updated: Date.now() - 1e7 }]);
  if (p.startsWith('/api/campaign/')) { const s = state(); return json({ campaign: { ...s.campaign, slugcat: p.split('_').pop(), color: COLORS[p.split('_').pop()] }, tracker: s.tracker }); }
  if (p.startsWith('/icon/karma/')) { res.writeHead(200, { 'Content-Type': 'image/svg+xml' }); return res.end(KARMA_SVG(p.split('/')[3])); }
  if (p.startsWith('/icon/')) { res.writeHead(200, { 'Content-Type': 'image/svg+xml' }); return res.end(ICON_SVG); }
  if (p.startsWith('/font/')) { const f = process.env.MOCK_FONT_DIR && path.join(process.env.MOCK_FONT_DIR, path.basename(p)); if (!f || !fs.existsSync(f)) { res.writeHead(404); return res.end(); } res.writeHead(200, { 'Content-Type': MIME[path.extname(f)] || 'application/json' }); return fs.createReadStream(f).pipe(res); }
  const file = path.join(www, p === '/' ? 'index.html' : p);
  if (!file.startsWith(www) || !fs.existsSync(file)) { res.writeHead(404); return res.end('not found'); }
  res.writeHead(200, { 'Content-Type': MIME[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
}).listen(port, () => console.log(`RainDash mock at http://localhost:${port}/ (slugcat ${slug})`));
