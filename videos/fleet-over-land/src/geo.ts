// Map geometry in "world" units (~6 m each), north up. Schematic, not survey-accurate.
export type Pt = [number, number];

/** Catmull-Rom spline through the points, as an SVG path. */
export const smooth = (pts: Pt[], closed = false) => {
  const n = pts.length;
  const get = (i: number) => (closed ? pts[(i + n) % n] : pts[Math.max(0, Math.min(n - 1, i))]);
  let d = `M${pts[0][0]},${pts[0][1]}`;
  for (let i = 0; i < (closed ? n : n - 1); i++) {
    const [p0, p1, p2, p3] = [get(i - 1), get(i), get(i + 1), get(i + 2)];
    const c1 = [p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6];
    const c2 = [p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6];
    d += ` C${c1[0]},${c1[1]} ${c2[0]},${c2[1]} ${p2[0]},${p2[1]}`;
  }
  return closed ? d + "Z" : d;
};

/** Dense samples along the same Catmull-Rom curve, for moving things along it. */
export const sampleSpline = (pts: Pt[], per = 12): Pt[] => {
  const n = pts.length;
  const get = (i: number) => pts[Math.max(0, Math.min(n - 1, i))];
  const out: Pt[] = [];
  for (let i = 0; i < n - 1; i++) {
    const [p0, p1, p2, p3] = [get(i - 1), get(i), get(i + 1), get(i + 2)];
    for (let k = 0; k < per; k++) {
      const t = k / per, t2 = t * t, t3 = t2 * t;
      const f = (a: number, b: number, c: number, d: number) =>
        0.5 * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t2 + (-a + 3 * b - 3 * c + d) * t3);
      out.push([f(p0[0], p1[0], p2[0], p3[0]), f(p0[1], p1[1], p2[1], p3[1])]);
    }
  }
  out.push(pts[n - 1]);
  return out;
};

export const polyLength = (pts: Pt[]) => {
  let len = 0;
  for (let i = 1; i < pts.length; i++) len += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
  return len;
};

/** Point and heading (degrees) at fraction s (0..1) of the polyline's length. */
export const along = (pts: Pt[], s: number) => {
  const total = polyLength(pts);
  let target = Math.max(0, Math.min(1, s)) * total;
  for (let i = 1; i < pts.length; i++) {
    const [a, b] = [pts[i - 1], pts[i]];
    const seg = Math.hypot(b[0] - a[0], b[1] - a[1]);
    if (target <= seg || i === pts.length - 1) {
      const u = seg === 0 ? 0 : Math.min(1, target / seg);
      return { x: a[0] + (b[0] - a[0]) * u, y: a[1] + (b[1] - a[1]) * u, angle: (Math.atan2(b[1] - a[1], b[0] - a[0]) * 180) / Math.PI };
    }
    target -= seg;
  }
  const p = pts[pts.length - 1];
  return { x: p[0], y: p[1], angle: 0 };
};

/** Prefix of a polyline up to fraction s, as an SVG path. */
export const partialPath = (pts: Pt[], s: number) => {
  if (s <= 0) return "";
  const total = polyLength(pts) * Math.min(1, s);
  let acc = 0;
  let d = `M${pts[0][0]},${pts[0][1]}`;
  for (let i = 1; i < pts.length; i++) {
    const seg = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
    if (acc + seg >= total) {
      const u = (total - acc) / seg;
      d += ` L${pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * u},${pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * u}`;
      return d;
    }
    acc += seg;
    d += ` L${pts[i][0]},${pts[i][1]}`;
  }
  return d;
};

export const inPolygon = ([x, y]: Pt, poly: Pt[]) => {
  let inside = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i], [xj, yj] = poly[j];
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
};

// --- coastlines -----------------------------------------------------------

// European side: everything west of the Bosphorus and north of the Sea of Marmara.
// The Golden Horn is drawn on top of it as water.
export const EUROPE: Pt[] = [
  [-700, -1100], [990, -1100], [835, -700], [815, -400], [800, -120], [808, 150], [790, 300], [770, 400],
  [745, 480], [704, 542], [727, 662], [706, 720], [650, 756], [560, 796], [450, 836], [330, 872],
  [200, 902], [0, 925], [-300, 950], [-700, 960],
];

export const ASIA: Pt[] = [
  [1080, -1100], [1700, -1100], [1700, 900], [960, 870], [890, 815], [880, 700], [900, 560], [888, 400],
  [872, 200], [880, -120], [905, -400], [935, -700],
];

// Golden Horn shores (east to west)
export const HORN_NORTH: Pt[] = [
  [704, 542], [640, 533], [580, 503], [520, 469], [450, 430], [380, 390], [300, 341], [220, 292], [140, 252], [60, 218], [0, 207], [-50, 222],
];
export const HORN_SOUTH: Pt[] = [
  [-50, 222], [0, 262], [60, 272], [140, 306], [220, 350], [300, 396], [380, 450], [450, 500], [520, 541], [580, 575], [640, 609], [690, 632], [727, 662],
];
export const HORN: Pt[] = [[790, 520], ...HORN_NORTH, ...HORN_SOUTH.slice(1), [790, 690]];
// just the Horn itself, closed across its mouth (for highlighting)
export const HORN_INNER: Pt[] = [...HORN_NORTH, ...HORN_SOUTH.slice(1)];

// Theodosian land walls, Golden Horn to the Sea of Marmara
export const LAND_WALLS: Pt[] = [[233, 356], [222, 440], [212, 540], [204, 640], [196, 740], [190, 840], [186, 905]];
// sea walls along the Golden Horn, land walls to Seraglio Point
export const HORN_WALLS: Pt[] = [[233, 356], ...HORN_SOUTH.filter(([x]) => x > 233)];
export const MARMARA_WALLS: Pt[] = [[727, 662], [706, 720], [650, 756], [560, 796], [450, 836], [330, 872], [200, 902], [186, 905]];

// the city inside the walls
export const CITY: Pt[] = [...LAND_WALLS, ...MARMARA_WALLS.slice().reverse().slice(1), ...HORN_WALLS.slice().reverse()];

export const GALATA: Pt[] = [[604, 512], [612, 468], [646, 446], [700, 474], [712, 540], [650, 536]];
export const GALATA_TOWER: Pt = [645, 466];

// the boom across the mouth of the Golden Horn: Galata to the Eugenius Gate
export const CHAIN_A: Pt = [684, 540];
export const CHAIN_B: Pt = [706, 643];

// Ottoman overland route: Double Columns on the Bosphorus, over the hill behind Galata,
// down to the Valley of the Springs on the Golden Horn
export const ROUTE_KEYS: Pt[] = [[822, 408], [771, 400], [728, 384], [682, 367], [635, 359], [590, 366], [551, 386], [519, 414], [500, 450], [488, 482]];
export const ROUTE = sampleSpline(ROUTE_KEYS, 14);
// fraction of the route that is on land (between the two shorelines)
export const ROUTE_LAND = [0.11, 0.9] as const;

export const HAGIA_SOPHIA: Pt = [655, 700];
