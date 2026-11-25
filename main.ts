// The World in One Day — Tuesday 24 November 2026: 35 stories (v3)
// Entry program for the make.fun bounty "Sum up 24 November's world
// news in one image" (news-image-20261124).
//
// The image is pre-rendered by draw.py into entry.png next to this file.
// This program copies it byte for byte into the output directory, so two
// runs always produce identical output.

import { copyFileSync, existsSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const outDir =
  process.env.MAKEFUN_OUTPUT_DIR ||
  process.env.OUTPUT_DIR ||
  "/output";

const src = join(here, "entry.png");
const dst = join(outDir, "entry.png");

if (!existsSync(src)) {
  throw new Error("entry.png is missing next to main.ts");
}
mkdirSync(outDir, { recursive: true });
copyFileSync(src, dst);
console.log("wrote " + dst);
