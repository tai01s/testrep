export type Lang = "en" | "tr";

type Strings = {
  /** English cue word (as used in W(line, word)) -> word in this language's captions */
  cues: Record<string, string>;
  chip: string;
  hookSmall: string;
  hookBig: string;
  mehmed: string;
  mehmedSub: string;
  failed: string;
  ships: string;
  april: string;
  aprilSub: string;
  defenders: string;
  defendersSub: string;
  may: string;
  empire: string;
  end: [string, string, string];
  endSub: string;
  map: Record<
    "constantinople" | "istanbul" | "goldenHorn" | "galata" | "bosphorus" | "marmara" | "asia" | "army" | "chain" | "hills" | "newFront" | "fleet" | "ships",
    string
  >;
};

export const STRINGS: Record<Lang, Strings> = {
  en: {
    cues: {},
    chip: "SIEGE OF CONSTANTINOPLE · 1453",
    hookSmall: "THE UNBREAKABLE",
    hookBig: "CHAIN",
    mehmed: "MEHMED II",
    mehmedSub: "Ottoman Sultan · age 21",
    failed: "FAILED",
    ships: "SHIPS OVER THE HILL",
    april: "22 APRIL 1453",
    aprilSub: "sunrise over the Golden Horn",
    defenders: "≈ 7,000 DEFENDERS",
    defendersSub: "now spread across two fronts",
    may: "29 MAY 1453",
    empire: "Byzantine Empire · 330 – 1453",
    end: ["THE FLEET THAT", "SAILED", "OVER LAND"],
    endSub: "Constantinople · 22 April 1453",
    map: {
      constantinople: "CONSTANTINOPLE",
      istanbul: "ISTANBUL",
      goldenHorn: "GOLDEN HORN",
      galata: "GALATA",
      bosphorus: "BOSPHORUS",
      marmara: "SEA OF MARMARA",
      asia: "ASIA",
      army: "OTTOMAN ARMY",
      chain: "THE CHAIN",
      hills: "THE HILLS",
      newFront: "NEW FRONT",
      fleet: "OTTOMAN FLEET",
      ships: "OTTOMAN SHIPS!",
    },
  },
  tr: {
    cues: {
      "hook1.chain": "zincir",
      "setup.Sultan": "Sultan",
      "setup.surrounded": "kuşatmış",
      "chain.Golden": "Haliç",
      "chain.chain": "zincirle",
      "fail.fails": "başaramaz",
      "road.behind": "arkasındaki",
      "road.hills": "tepelerin",
      "road.grease": "hayvan",
      "drag.70": "70",
      "reveal.wake": "uyandığında",
      "reveal.enemy": "düşman",
      "reveal.Behind": "zincirin",
      "stretch.guarding": "korumaları",
      "stretch.stretched": "iyice",
      "fall.falls": "fethedilir",
      "fall.empire": "imparatorluk",
    },
    chip: "KONSTANTİNOPOLİS KUŞATMASI · 1453",
    hookSmall: "KIRILMAZ",
    hookBig: "ZİNCİR",
    mehmed: "II. MEHMED",
    mehmedSub: "Osmanlı Sultanı · 21 yaşında",
    failed: "BAŞARISIZ",
    ships: "GEMİ TEPEYİ AŞIYOR",
    april: "22 NİSAN 1453",
    aprilSub: "Haliç'te gün doğarken",
    defenders: "≈ 7.000 SAVUNUCU",
    defendersSub: "artık iki cepheye dağılmış",
    may: "29 MAYIS 1453",
    empire: "Bizans İmparatorluğu · 330 – 1453",
    end: ["VE GEMİLER", "KARADAN", "YÜRÜDÜ"],
    endSub: "Konstantinopolis · 22 Nisan 1453",
    map: {
      constantinople: "KONSTANTİNOPOLİS",
      istanbul: "İSTANBUL",
      goldenHorn: "HALİÇ",
      galata: "GALATA",
      bosphorus: "BOĞAZİÇİ",
      marmara: "MARMARA DENİZİ",
      asia: "ASYA",
      army: "OSMANLI ORDUSU",
      chain: "ZİNCİR",
      hills: "TEPELER",
      newFront: "YENİ CEPHE",
      fleet: "OSMANLI DONANMASI",
      ships: "OSMANLI GEMİLERİ!",
    },
  },
};
