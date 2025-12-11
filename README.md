# PRINTWELL Invoice — Professional Printing Invoice Software

A desktop application for creating, managing, and printing professional invoices for printing services.

## Features

- **Invoice Management**: Create, edit, view, and save invoices
- **Product Catalog**: Manage custom printing products with flexible pricing (fixed or area-based)
- **Invoice History**: Searchable history with customer names, products, dates, and keywords
- **Company Settings**: Customize company info, logo, and footer
- **Multi-Window**: Open multiple invoices concurrently
- **Local Persistence**: All data saved locally; optional cloud sync ready
- **Professional UI**: Clean, responsive interface with Bootstrap 5

## Quick Start

### For Users (Windows Installation)

1. Download the latest installer from [Releases](../../releases)
2. Run `PrintWell_Setup.exe`
3. Follow the on-screen installer instructions
4. Launch PRINTWELL from Start Menu or Desktop shortcut

### For Developers

#### Prerequisites
- Node.js 18+ and npm
- Git

#### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/PrintWell_Desktop.git
cd PrintWell_Desktop

# Install dependencies
npm install

# Start the app in development mode
npm start
```

#### Build (Windows Installer)

```bash
# Build for Windows (requires icon.png and icon.ico in project root)
npm run build:win
```

Installer will be created in `dist/` directory.

#### Build via CI (GitHub Actions)

1. Push to main/master branch
2. GitHub Actions automatically builds and uploads installer artifacts
3. Download from [Actions](../../actions) tab → Latest workflow run → Artifacts

## Project Structure

```
PrintWell_Desktop/
├── index.html          # Main UI
├── main.js             # Electron main process
├── preload.js          # IPC bridge (context isolation)
├── style.css           # Styling
├── package.json        # Dependencies and build config
├── icon.ico            # Windows icon (for installer)
├── icon.png            # App icon (512x512)
├── tools/              # Build utilities
│   └── generate-icons-jimp.js  # Icon generator (if needed)
└── .github/workflows/
    └── build-windows.yml       # CI/CD configuration
```

## Configuration

### Company Settings

Edit settings in the app's Settings tab:
- Company name, address, phone, email
- Custom footer text
- Logo upload

Settings are saved locally in:
- Windows: `%APPDATA%\PrintWell Invoice\`

### Products

Create and customize printing products:
- **Fixed pricing**: per-size prices (e.g., posters, stickers)
- **Area-based pricing**: price per square foot/meter

Products saved locally; can be exported/imported.

## IPC Handlers (Electron)

The app exposes these IPC methods via `window.electronAPI`:

- `saveSettings(settings)` — Save company info
- `loadSettings()` — Load company settings
- `saveProducts(products)` — Save product catalog
- `loadProducts()` — Load products
- `saveInvoiceFile(html, filename)` — Save invoice as HTML file

## Invoice History Search

Use the **Search** field in the Invoice History tab to filter by:
- Customer name
- Invoice number/ID
- Product names
- Notes and keywords

Search is case-insensitive and matches any part of indexed fields.

## Troubleshooting

### npm install fails with ECONNRESET

Network issue. Try:
```bash
npm cache clean --force
npm install --fetch-retries=5 --fetch-retry-factor=2
```

Or use GitHub Actions to build (no local npm needed).

### Missing icon files

If `icon.ico` or `icon.png` are missing:
1. Use an online converter (e.g., icoconvert.com, convertico.com)
2. Upload a PNG image, download ICO and PNG files
3. Place `icon.ico` and `icon.png` in project root
4. Rebuild: `npm run build:win`

### Installer not found after build

Check `dist/` folder for `.exe` file. If missing:
- Ensure `package.json` `build.win.target` is set to `"nsis"`
- Verify `icon.ico` exists in project root

## License

MIT

## Support

For issues or questions, open a GitHub Issue.

---

**Built with Electron, Node.js, and Bootstrap 5**
