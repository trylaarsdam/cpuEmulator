const electron = require('electron');
const app = electron.app;
const ipc = electron.ipcRenderer
var remote = require('electron').remote;
var window = remote.getCurrentWindow();
const BrowserWindow = electron.BrowserWindow;
const parent = remote.getCurrentWindow().getParentWindow();
textbox = document.getElementById("uuid");

textbox.setAttribute('value', remote.getGlobal('uuid').get.toString());
function sendUUID() {
    _uuidEntry = document.getElementById("uuid");
    console.log(_uuidEntry.value);
    console.log(remote.getGlobal('uuid'));
    remote.getGlobal('uuid').get = _uuidEntry.value;
    console.log(remote.getGlobal('uuid'));
    ipc.send('uuid', 'hello');
    window.close();
}

function closeWindow() {
    window.close();
}