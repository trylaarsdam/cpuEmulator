const electron = require('electron');
const app = electron.app;
const ipc = electron.ipcRenderer
var remote = require('electron').remote;
var window = remote.getCurrentWindow();
const BrowserWindow = electron.BrowserWindow;
const parent = remote.getCurrentWindow().getParentWindow();
textbox = document.getElementById("apikey");

textbox.setAttribute('value', remote.getGlobal('apikey').get.toString());
function sendUUID() {
    _uuidEntry = document.getElementById("apikey");
    console.log(_uuidEntry.value);
    console.log(remote.getGlobal('apikey'));
    remote.getGlobal('apikey').get = _uuidEntry.value;
    console.log(remote.getGlobal('apikey'));
    ipc.send('apikey', 'hello');
    window.close();
}

function closeWindow() {
    window.close();
}