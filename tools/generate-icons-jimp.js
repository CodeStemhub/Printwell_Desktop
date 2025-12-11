// tools/generate-icons-jimp.js
const Jimp = require('jimp');
const pngToIco = require('png-to-ico');
const fs = require('fs');
const path = require('path');

(async () => {
  const root = process.cwd();
  const src = path.join(root, 'icon-source.png');
  if (!fs.existsSync(src)) {
    console.error('icon-source.png not found in project root.');
    process.exit(1);
  }

  // sizes to create for ICO (common set)
  const sizes = [16,24,32,48,64,128,256];

  // generate each png in tools/
  const outDir = path.join(root, 'tools');
  for (const s of sizes) {
    const out = path.join(outDir, `icon-${s}.png`);
    const img = await Jimp.read(src);
    await img.clone().resize(s, s).writeAsync(out);
  }

  // create large app icon (512x512) as icon.png at project root
  const big = await Jimp.read(src);
  await big.clone().resize(512, 512).writeAsync(path.join(root, 'icon.png'));

  // create .ico from generated pngs
  const pngPaths = sizes.map(s => path.join(outDir, `icon-${s}.png`));
  const icoBuffer = await pngToIco(pngPaths);
  fs.writeFileSync(path.join(root, 'icon.ico'), icoBuffer);

  console.log('Done: icon.png and icon.ico created in project root.');
})();