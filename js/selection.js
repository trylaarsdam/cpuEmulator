const electron = require('electron');
const app = electron.app;
const ipc = electron.ipcRenderer
var remote = require('electron').remote;
var window = remote.getCurrentWindow();
const BrowserWindow = electron.BrowserWindow;
const parent = remote.getCurrentWindow().getParentWindow();
//var oldjson = JSON.parse(remote.getGlobal('componentSelection').json)
var json = {};
//json.componentStatus = [];

function checkboxClicked(id) {
    _component = document.getElementById(id);
    console.log(_component.value);
    json[id] = {"checked": false, "device": ""};
    json[id].checked = _component.checked;
    console.log(json);    
    console.log(JSON.stringify(json));
}

function closeWindow() {
    Object.keys(json).forEach((key, index) => {
        _comp = document.getElementById(key.toString() + "_device");
        json[key].device = _comp.value;
    })
    remote.getGlobal('componentSelection').get = JSON.stringify(json);
    console.log(JSON.stringify(json));
    ipc.send('components', JSON.stringify(json));
    window.close();
}