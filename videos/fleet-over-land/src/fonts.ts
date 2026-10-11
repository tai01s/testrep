import { continueRender, delayRender, staticFile } from "remotion";

// Variable fonts (OFL) bundled in public/fonts so rendering needs no network.
const faces = [
  new FontFace("Montserrat", `url(${staticFile("fonts/montserrat.woff2")}) format("woff2")`, { weight: "100 900" }),
  new FontFace("Cinzel", `url(${staticFile("fonts/cinzel.woff2")}) format("woff2")`, { weight: "400 900" }),
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
