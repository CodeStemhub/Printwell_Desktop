#!/usr/bin/env node
/**
 * Generate icon.png and icon.ico from icon-source.png using pure JS (no native builds)
 * Uses png-to-ico package (install: npm install --save-dev png-to-ico)
 */

const pngToIco = require('png-to-ico');
const fs = require('fs');
const path = require('path');

// For CI: use this if jimp is not available, fallback to simple resize via shell
const { createCanvas, loadImage } = require('canvas'); // fallback if needed

(async () => {
  const root = process.cwd();
  const srcPath = path.join(root, 'icon-source.png');

  if (!fs.existsSync(srcPath)) {
    console.error('❌ icon-source.png not found. Exiting.');
    process.exit(1);
  }

  console.log('📦 Generating icon files from icon-source.png...');

  try {
    // Generate multiple PNG sizes for ICO
    const sizes = [16, 24, 32, 48, 64, 128, 256];
    const pngPaths = [];

    for (const size of sizes) {
      const outPath = path.join(root, 'tools', `icon-${size}.png`);
      fs.mkdirSync(path.dirname(outPath), { recursive: true });

      // Use canvas to resize (if available) or copy source
      try {
        const image = await loadImage(srcPath);
        const canvas = createCanvas(size, size);
        const ctx = canvas.getContext('2d');
        ctx.drawImage(image, 0, 0, size, size);
        const buffer = canvas.toBuffer('image/png');
        fs.writeFileSync(outPath, buffer);
        pngPaths.push(outPath);
        console.log(`  ✅ Generated ${size}x${size}.png`);
      } catch (err) {
        console.warn(`  ⚠️  Could not generate ${size}x${size} using canvas, copying source...`);
        fs.copyFileSync(srcPath, outPath);
        pngPaths.push(outPath);
      }
    }

    // Create large icon.png (512x512) in root
    try {
      const image = await loadImage(srcPath);
      const canvas = createCanvas(512, 512);
      const ctx = canvas.getContext('2d');
      ctx.drawImage(image, 0, 0, 512, 512);
      const buffer = canvas.toBuffer('image/png');
      fs.writeFileSync(path.join(root, 'icon.png'), buffer);
      console.log(`  ✅ Generated icon.png (512x512) in root`);
    } catch (err) {
      console.warn(`  ⚠️  Could not generate 512x512 icon, copying source...`);
      fs.copyFileSync(srcPath, path.join(root, 'icon.png'));
    }

    // Create ICO file
    if (pngPaths.length > 0) {
      const icoBuffer = await pngToIco(pngPaths);
      const icoPath = path.join(root, 'icon.ico');
      fs.writeFileSync(icoPath, icoBuffer);
      console.log(`  ✅ Generated icon.ico in root`);
    }

    console.log('✨ Icon generation complete!');
  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
})();
