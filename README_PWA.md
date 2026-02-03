# Rope Roller Maker - Progressive Web App

A standalone web application for designing and generating custom cable knit texture roller STL Files.

## 📱 Installation Instructions

### Android (Chrome/Edge):
1. Open `rope_roller_maker_standalone.html` in Chrome or Edge
2. Tap the menu (⋮) → "Install app" or "Add to Home screen"
3. The app icon will appear on your home screen
4. Launch it like any native app!

### iOS (Safari):
1. Open `rope_roller_maker_standalone.html` in Safari
2. Tap the Share button (□↑)
3. Scroll down and tap "Add to Home Screen"
4. Tap "Add" in the top right
5. The app icon will appear on your home screen

### Desktop (Chrome/Edge):
1. Open the HTML file in Chrome or Edge
2. Click the install icon (⊕) in the address bar
3. Click "Install"
4. App will open in its own window

## 🌐 Hosting Online

For the PWA to work properly, you need to serve the files. You have several options:

### Option 1: GitHub Pages (Free & Easy)
1. Create a GitHub repository
2. Upload all files:
   - `rope_roller_maker_standalone.html`
   - `manifest.json`
   - `service-worker.js`
   - `icon-192.png` (you'll need to create this from icon.svg)
   - `icon-512.png` (you'll need to create this from icon.svg)
3. Enable GitHub Pages in repository settings
4. Access at: `https://yourusername.github.io/repository-name/rope_roller_maker_standalone.html`

### Option 2: Netlify/Vercel (Free)
1. Create account on Netlify.com or Vercel.com
2. Drag and drop your folder
3. Get instant HTTPS URL

### Option 3: Local Web Server
For testing locally:

**Python:**
```bash
python -m http.server 8000
```

**Node.js:**
```bash
npx http-server
```

Then visit: `http://localhost:8000/rope_roller_maker_standalone.html`

## 🎨 Creating App Icons

The `icon.svg` file is included. Convert it to PNG:

**Using online tools:**
- Go to https://cloudconvert.com/svg-to-png
- Upload `icon.svg`
- Create two versions:
  - `icon-192.png` (192x192 pixels)
  - `icon-512.png` (512x512 pixels)

**Using command line (ImageMagick):**
```bash
convert -background none -resize 192x192 icon.svg icon-192.png
convert -background none -resize 512x512 icon.svg icon-512.png
```

## 📁 Required Files

For the PWA to work, keep these files in the same folder:
- `rope_roller_maker_standalone.html` (main app)
- `manifest.json` (app configuration)
- `service-worker.js` (offline functionality)
- `icon-192.png` (app icon - small)
- `icon-512.png` (app icon - large)

## ✨ Features

- **Works Offline**: After first visit, works without internet
- **Install Anywhere**: Android, iOS, Windows, Mac, Linux
- **No App Store**: Install directly from browser
- **Auto Updates**: Automatically updates when you publish new version
- **Full Screen**: Runs like a native app
- **Custom Parameters**: Design rollers with 8 adjustable parameters
- **Real STL Export**: Generates actual 3D model files

## 🔧 Customization

Edit `manifest.json` to change:
- App name
- Theme colors
- Icon paths
- Display mode

Edit `service-worker.js` to change:
- Cache behavior
- Offline functionality
- Version number

## 📱 Testing PWA Features

**Check if PWA is working:**
1. Open browser DevTools (F12)
2. Go to "Application" tab
3. Check "Service Workers" - should show registered
4. Check "Manifest" - should show all details
5. Try "Offline" mode - app should still work

## 🚀 Quick Start

1. Create PNG icons from the SVG
2. Upload all files to a web server (GitHub Pages recommended)
3. Visit the URL in a mobile browser
4. Install to home screen
5. Enjoy!

## 💡 Tips

- PWAs need HTTPS (except localhost)
- Test on actual devices, not just emulators
- Clear cache if changes don't appear
- Update version in service-worker.js when updating app

## 🐛 Troubleshooting

**"Install" option doesn't appear:**
- Make sure you're using HTTPS (or localhost)
- Check all required files are present
- Try hard refresh (Ctrl+Shift+R)

**App doesn't work offline:**
- Check service worker is registered in DevTools
- Visit the app at least once while online
- Check browser console for errors

**Changes not showing:**
- Update CACHE_NAME version in service-worker.js
- Clear browser cache
- Uninstall and reinstall app

## 📄 License

Open source - use freely for personal or commercial projects.
