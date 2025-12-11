const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
    // File operations
    saveData: (data) => ipcRenderer.invoke('save-data', data),
    loadData: () => ipcRenderer.invoke('load-data'),
    
    // Settings operations - ADD THESE
    saveSettings: (settings) => ipcRenderer.invoke('save-settings', settings),
    loadSettings: () => ipcRenderer.invoke('load-settings'),
    saveProducts: (products) => ipcRenderer.invoke('save-products', products),
    loadProducts: () => ipcRenderer.invoke('load-products'),
    saveInvoiceFile: (html, filename) => ipcRenderer.invoke('save-invoice-file', html, filename),
    
    // Window controls
    minimizeWindow: () => ipcRenderer.send('minimize-window'),
    maximizeWindow: () => ipcRenderer.send('maximize-window'),
    closeWindow: () => ipcRenderer.send('close-window'),
    
    // Menu actions
    onNewInvoice: (callback) => ipcRenderer.on('new-invoice', callback),
    onSaveInvoice: (callback) => ipcRenderer.on('save-invoice', callback),
    onPrintInvoice: (callback) => ipcRenderer.on('print-invoice', callback),
    onOpenSettings: (callback) => ipcRenderer.on('open-settings', callback),
    onShowAbout: (callback) => ipcRenderer.on('show-about', callback)
});