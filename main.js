const { app, BrowserWindow, ipcMain, dialog, Menu } = require('electron');
const path = require('path');
const fs = require('fs');

const isDev = process.env.NODE_ENV === 'development';

function createMainWindow() {
    const win = new BrowserWindow({
        width: 1200,
        height: 900,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false
        },
        icon: path.join(__dirname, 'icon.png')
    });

    win.loadFile(path.join(__dirname, 'index.html'));

    if (isDev) {
        win.webContents.openDevTools();
    }

    return win;
}

app.whenReady().then(() => {
    const mainWindow = createMainWindow();

    const template = [
        {
            label: 'File',
            submenu: [
                { label: 'New Invoice', click: () => mainWindow.webContents.send('new-invoice') },
                { label: 'Open Invoice', click: () => mainWindow.webContents.send('open-invoice') },
                { type: 'separator' },
                { role: 'quit' }
            ]
        },
        {
            label: 'Help',
            submenu: [
                { label: 'About', click: () => mainWindow.webContents.send('show-about') }
            ]
        }
    ];

    const menu = Menu.buildFromTemplate(template);
    Menu.setApplicationMenu(menu);

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) createMainWindow();
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit();
});

// IPC Handlers for settings and products
ipcMain.handle('save-settings', async (event, settings) => {
    try {
        const appDataPath = app.getPath('userData');
        const filePath = path.join(appDataPath, 'printwell_settings.json');
        fs.writeFileSync(filePath, JSON.stringify(settings, null, 2));
        return { success: true };
    } catch (error) {
        console.error('Error saving settings:', error);
        return { success: false, error: error.message };
    }
});

ipcMain.handle('load-settings', async (event) => {
    try {
        const appDataPath = app.getPath('userData');
        const filePath = path.join(appDataPath, 'printwell_settings.json');
        if (fs.existsSync(filePath)) {
            const data = fs.readFileSync(filePath, 'utf8');
            return { success: true, settings: JSON.parse(data) };
        } else {
            const defaultSettings = {
                name: "PRINTWELL",
                motto: "TIME TO DOMINATE!!",
                address: "123 Print Street, Accra, Ghana",
                phone: "+233 24 123 4567",
                email: "info@printwell.com",
                footer: "Thank you for choosing PRINTWELL Factory! For inquiries, contact us at info@printwell.com",
                logo: null,
                customInfo: []
            };
            return { success: true, settings: defaultSettings };
        }
    } catch (error) {
        console.error('Error loading settings:', error);
        return { success: false, error: error.message };
    }
});

ipcMain.handle('save-products', async (event, products) => {
    try {
        const appDataPath = app.getPath('userData');
        const filePath = path.join(appDataPath, 'printwell_products.json');
        fs.writeFileSync(filePath, JSON.stringify(products, null, 2));
        return { success: true };
    } catch (error) {
        console.error('Error saving products:', error);
        return { success: false, error: error.message };
    }
});

ipcMain.handle('load-products', async (event) => {
    try {
        const appDataPath = app.getPath('userData');
        const filePath = path.join(appDataPath, 'printwell_products.json');
        if (fs.existsSync(filePath)) {
            const data = fs.readFileSync(filePath, 'utf8');
            return { success: true, products: JSON.parse(data) };
        } else {
            // return empty or default
            return { success: true, products: {} };
        }
    } catch (error) {
        console.error('Error loading products:', error);
        return { success: false, error: error.message };
    }
});

// Save HTML invoice to user-chosen file
ipcMain.handle('save-invoice-file', async (event, htmlContent, defaultName) => {
    try {
        const win = BrowserWindow.getFocusedWindow();
        const { canceled, filePath } = await dialog.showSaveDialog(win, {
            title: 'Save Invoice',
            defaultPath: defaultName || 'invoice.html',
            filters: [
                { name: 'HTML', extensions: ['html', 'htm'] },
                { name: 'All Files', extensions: ['*'] }
            ]
        });

        if (canceled || !filePath) return { success: false, error: 'cancelled' };

        fs.writeFileSync(filePath, htmlContent, 'utf8');
        return { success: true, path: filePath };
    } catch (error) {
        console.error('Error saving invoice file:', error);
        return { success: false, error: error.message };
    }
});

// Window control events
ipcMain.on('minimize-window', () => {
    const w = BrowserWindow.getFocusedWindow(); if (w) w.minimize();
});
ipcMain.on('maximize-window', () => {
    const w = BrowserWindow.getFocusedWindow(); if (w) w.maximize();
});
ipcMain.on('close-window', () => {
    const w = BrowserWindow.getFocusedWindow(); if (w) w.close();
});