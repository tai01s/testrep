import { continueRender, delayRender, staticFile } from "remotion";

// Variable fonts (OFL) bundled in public/fonts so rendering needs no network.
// The *-ext files are Google's latin-ext subset (Turkish ş, ğ, İ ...).
const LATIN_EXT = "U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C4, U+2113, U+2C60-2C7F, U+A720-A7FF";
const faces = [
  new FontFace("Montserrat", `url(${staticFile("fonts/montserrat.woff2")}) format("woff2")`, { weight: "100 900" }),
  new FontFace("Montserrat", `url(${staticFile("fonts/montserrat-ext.woff2")}) format("woff2")`, { weight: "100 900", unicodeRange: LATIN_EXT }),
  new FontFace("Cinzel", `url(${staticFile("fonts/cinzel.woff2")}) format("woff2")`, { weight: "400 900" }),
  new FontFace("Cinzel", `url(${staticFile("fonts/cinzel-ext.woff2")}) format("woff2")`, { weight: "400 900", unicodeRange: LATIN_EXT }),
];

const handle = delayRender("Loading fonts");
Promise.all(faces.map((f) => f.load()))
  .then((loaded) => {
    loaded.forEach((f) => document.fonts.add(f));
    continueRender(handle);
  })
  .catch((err) => {
    console.error(err);
    continueRender(handle);
  });

export const fonts = { caption: "Montserrat", title: "Cinzel" };
