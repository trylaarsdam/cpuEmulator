const electron = require('electron');
const app = electron.app;
const { Menu } = require('electron');
const BrowserWindow = electron.BrowserWindow;
var XMLHttpRequest = require("xmlhttprequest").XMLHttpRequest;
const Http = new XMLHttpRequest();
var subpy = null;
var rp = require('request-promise');
var subpy = null;
var backup_subpy = null;
var mainWindow = null;
var emulatorWindow = null;
const ipc = require('electron').ipcMain
global.uuid = {get: ""};
global.apikey = {get: ""};
global.uuidenter = {status: null};
global.componentSelection = {get: ""}
const { dialog } = require('electron');
const { platform } = require('os');
const { RSA_PKCS1_OAEP_PADDING } = require('constants');
var expectedExit = false;

app.on('window-all-closed', function() {
  //if (process.platform != 'darwin') {
    app.quit();
  //}
});

var menu = Menu.buildFromTemplate([
  {
    label: 'File',
      submenu: [
        {
          label:'Open code.asm',
          click(){
            if(process.platform == "win32"){
              vscode = require('child_process').spawn("cmd.exe", ["/c", "code ./assembler/code.asm"]);
            }
            else if(process.platform == "darwin"){
              vscode = require('child_process').exec("cd " + __dirname + "; code ../../../assembler/code.asm");
            }
            else{
              vscode = require('child_process').exec("code ./assembler/code.asm");
            }
          }
        },
        {
          label:'Open controlmap.json',
          click(){
            if(process.platform == "win32"){
              vscode = require('child_process').spawn("cmd.exe", ["/c", "code ./controlmap.json"]);
            }
            else if(process.platform == "darwin"){
              vscode = require('child_process').exec("cd " + __dirname + "; code ../../../controlmap.json");
            }
            else{
              vscode = require('child_process').exec("code ./controlmap.json");
            }
          }
        },
        {
          label:'Open opcodes.json',
          click(){
            if(process.platform == "win32"){
              vscode = require('child_process').spawn("cmd.exe", ["/c", "code ./opcodes.json"]);
            }
            else if(process.platform == "darwin"){
              vscode = require('child_process').exec("cd " + __dirname + "; code ../../../opcodes.json");
            }
            else{
              vscode = require('child_process').exec("code ./opcodes.json");
            }
          }
        },
        {
          label:'Reset',
          click(){
            masterReset();
          }
        },
        {
          label:'Exit',
          click(){
            app.quit();
          }
        }
      ]
  },
  {
      label: 'Connect',
          submenu: [
          {
            label:'Connect to Photon', 
            click() { 
              uuidInputPage();
            } 
          },
          {
            label:'Select Hardware Components',
            click() {
              componentSelectPage();
            }
          },
      ]
    },
    {
      label: "Blynk",
      submenu: [
        {
          label: "Set API Key",
          click() {
            setAPIKey();
          }
        }
      ]
    },
    {
      label: "Mode",
      submenu: [
        {
          label: "Microcode",
          click() {
            microcodeMode();
            emulatorWindow.setTitle("CPU Emulator - Microcode Mode")
          }
        },
        {
          label: "Playground",
          click(){
            playgroundMode();
            emulatorWindow.setTitle("CPU Emulator - Playground Mode")
          }
        }
      ]
    },
    {
      label: "Edit",
      submenu: [
          { label: "Undo", accelerator: "CmdOrCtrl+Z", selector: "undo:" },
          { label: "Redo", accelerator: "Shift+CmdOrCtrl+Z", selector: "redo:" },
          { type: "separator" },
          { label: "Cut", accelerator: "CmdOrCtrl+X", selector: "cut:" },
          { label: "Copy", accelerator: "CmdOrCtrl+C", selector: "copy:" },
          { label: "Paste", accelerator: "CmdOrCtrl+V", selector: "paste:" },
          { label: "Select All", accelerator: "CmdOrCtrl+A", selector: "selectAll:" }
      ]
    },
    {
      label: "View",
      submenu: [
        {
          label: "Reload",
          accelerator: "F5",
          click: (item, focusedWindow) => {
            if (focusedWindow) {
              // on reload, start fresh and close any old
              // open secondary windows
              if (focusedWindow.id === 1) {
                BrowserWindow.getAllWindows().forEach(win => {
                  if (win.id > 1) win.close();
                });
              }
              focusedWindow.reload();
            }
          }
        },
        { type: "separator"},
        { role: 'togglefullscreen' },
        { role: 'resetzoom' },
        { role: 'zoomin' },
        { role: 'zoomout' },  
        { type: "separator"},
        {
          label: "Toggle Dev Tools",
          accelerator: "F12",
          click: (item, focusedWindow) => {
            if (focusedWindow) {
              focusedWindow.toggleDevTools();
            }
          }
        }
      ]
  }
])

function microcodeMode(){
  rp("http://localhost:5000/mode/0")
  .then(function () {
    rp("http://localhost:5000/reset/buttonClicked")
    .then(function() {

    })
  })
}

function playgroundMode(){
  rp("http://localhost:5000/mode/1")
    .then(function () {
      rp("http://localhost:5000/reset/buttonClicked")
      .then(function() {

      })
    })
}

function masterReset(){
  expectedExit = true;
  if(subpy != null){
    subpy.kill('SIGINT');
  }
  if(backup_subpy != null){
    backup_subpy.kill('SIGINT');
  }
  if (process.platform == 'win32'){
    microassembler = require('child_process').execFile('runmicroassembler.bat'); 
    assembler = require('child_process').execFile('runassembler.bat');
  }
  else if(process.platform == 'darwin'){
    console.log(__dirname)
    process.chdir(__dirname)
    require('child_process').spawn('bash', [String(__dirname) + '/runmicroassembler.sh'], {stdio: [process.stdin, process.stdout, process.stderr], detached: false});
    require('child_process').spawn('bash', [String(__dirname) + '/runassembler.sh'], {stdio: [process.stdin, process.stdout, process.stderr], detached: false});
  }
  else {
    require('child_process').exec('python3 ./microassembler/main.py -c ./controlmap.json -o ./opcodes.json', {stdio: [process.stdin, process.stdout, process.stderr], detached: false});
    require('child_process').exec('python3 ./assembler/main.py ./assembler/code.asm', {stdio: [process.stdin, process.stdout, process.stderr], detached: false});
  }
  setTimeout(() => { console.log("Assembly/Microassembly"); }, 2000);
  if (process.platform == 'win32'){
    //console.log(subpy.pid.toString())
    //var kill = require('child_process').exec("kill", [subpy.pid.toString()])
    console.log(__dirname)
    backup_subpy = require('child_process').spawn('python', ['./resources/app/main.py']); 
    backup_subpy.stdout.on('data', function(data) {
      console.log(data.toString()); 
    });
    backup_subpy.on('exit', (code) => {
      if(!expectedExit){
        console.error(`EMU backup python child process exited with code ${code}`);
        console.error("It is likely that your microcode.o or assembled.o files are invalid.");
        errorWindow = new BrowserWindow({width: 400, height: 400, show: true, webPreferences: {nodeIntegration: true}, frame: true});
        errorWindow.loadFile('errorWindow.html');
      }
      else{
        expectedExit = false;
      }
    });
  }
  else if (process.platform == 'darwin'){
    //var backup_subpy = require('child_process').spawn('open', ['/Applications/Calculator.app']);
    //var backup_subpy = require('child_process').spawn('pwd', {stdio: [process.stdin, process.stdout, process.stderr]});
    console.error("EMU process.cwd = " + String(__dirname) + '/main.py');
    dependencyManager = require('child_process').spawn('bash', [String(__dirname) + '/install-script.sh'], {stdio: [process.stdin, process.stdout, process.stderr], detached: false});    
    dependencyManager.on('exit', (code) => {
      backup_subpy = require('child_process').spawn('/Library/Frameworks/Python.framework/Versions/3.8/bin/python3', [String(__dirname) + '/main.py'], {stdio: [process.stdin, process.stdout, process.stderr], detached: false});
      backup_subpy.on('exit', (code) => {
        if(!expectedExit){
          console.error(`EMU backup python child process exited with code ${code}`);
          if(code != 0){
            console.error("It is likely that your microcode.o or assembled.o files are invalid.");
            errorWindow = new BrowserWindow({width: 400, height: 400, show: true, webPreferences: {nodeIntegration: true}, frame: true});
            errorWindow.loadFile('errorWindow.html');
          }
        }
        else{
          expectedExit = false;
        }
      });
    });
  }
  else{
    console.error("EMU process.cwd = " + String(__dirname) + '/main.py');
    backup_subpy = require('child_process').spawn('python3', [String(__dirname) + '/main.py'], {stdio: [process.stdin, process.stdout, process.stderr], detached: false});
    backup_subpy.on('exit', (code) => {
      if(!expectedExit){
        console.error(`EMU backup python child process exited with code ${code}`);
        if(code != 0){
          console.error("It is likely that your microcode.o or assembled.o files are invalid.");
          errorWindow = new BrowserWindow({width: 400, height: 400, show: true, webPreferences: {nodeIntegration: true}, frame: true});
          errorWindow.loadFile('errorWindow.html');
        }
      }
    });
  }
  setTimeout(() => { emulatorWindow.reload(); }, 1000);
}
function uuidSet() {
  //console.log("main.js");
  emulatorWindow.uuidSet();
}

function setAPIKey() {
  if(global.uuid.get != ""){
    inputapikey = new BrowserWindow({width: 400, height: 75, parent: emulatorWindow, webPreferences: {nodeIntegration: true}, frame: false});
    //console.log(input.getParentWindow());
    inputapikey.loadFile("input_blynk.html");
  }
  else {
    dialog.showMessageBox({type: "error", title: "Blynk API Key", message: "You have not defined a UUID!"});
  }
}

function uuidInputPage() {
  //console.log(emulatorWindow);
  input = new BrowserWindow({width: 400, height: 75, parent: emulatorWindow, webPreferences: {nodeIntegration: true}, frame: false});
  //console.log(input.getParentWindow());
  input.loadFile("input.html");
}

function componentSelectPage() {
  if(global.uuid.get != ""){
    select = new BrowserWindow({width: 400, height: 400, parent: emulatorWindow, webPreferences: {nodeIntegration: true}, frame: false})
    select.loadURL("http://localhost:5000/setRealComponents");
  }
  else{
    dialog.showMessageBox({type: "error", title: "Hardware Component Selection", message: "You have not defined a UUID!"});
  }
}

Menu.setApplicationMenu(menu);

app.on('ready', function() {
  // call python?
  mainWindow = new BrowserWindow({width: 800, height: 600, webPreferences: {nodeIntegration: true}, frame: false});
  mainWindow.loadFile('index.html');
  if(process.platform == 'win32'){
    subpy = require('child_process').spawn('python', ['./main.py']);
  }
  else if(process.platform == 'darwin'){
    subpy = require('child_process').spawn('/Library/Frameworks/Python.framework/Versions/3.8/bin/python3', ['./main.py']);
    //var subpy = require('child_process').spawn('pwd');
    //var subpy = require('child_process').spawn('open', ['/Applications/Calculator.app']);
  }
  else{
    subpy = require('child_process').spawn('python3', ['./main.py']);
  }
  
  //var subpy = require('child_process').spawn('./dist/hello.exe');
  
 
  var mainAddr = 'http://localhost:5000';

  var openWindow = async function(){
    emulatorWindow = new BrowserWindow({width: 800, height: 600, show: false, webPreferences: {nodeIntegration: true}, frame: true});
    //mainWindow.loadURL('file://' + __dirname + '/index.html');
    emulatorWindow.loadURL('http://localhost:5000');
    emulatorWindow.once('ready-to-show' , () => {
      emulatorWindow.show();
      emulatorWindow.setTitle("CPU Emulator - Microcode Mode")
      mainWindow.close();
    })
    ipc.on('uuid', (event, arg) => {
      //console.log(event);
      //console.log(arg);
      emulatorWindow.webContents.send('ping', 'uuid');
    })
    ipc.on('apikey', (event, arg) => {
      //console.log(event);
      //console.log(arg);
      emulatorWindow.webContents.send('ping', 'apikey');
    })
    ipc.on('components', (event, arg) => {
      //console.log(event);
      //console.log(arg);
      //console.log(global.componentSelection.get)
      emulatorWindow.webContents.send('ping', 'component');
    })
    emulatorWindow.on('closed', function() {
      emulatorWindow = null;
      if(subpy != null){
        subpy.kill('SIGINT');
      }
      if(backup_subpy != null){
        backup_subpy.kill('SIGINT');
        if(dependencyManager != null){
          dependencyManager.kill('SIGINT');
        }
      }
    });
  };

  var startUp = function(){
    rp(mainAddr)
      .then(function(htmlString){
        console.log('server started!');
        openWindow();
      })
      .catch(function(err){
        //console.log('waiting for the server start...');
        startUp();
      });
  };

  subpy.on('exit', (code) => {
    console.error(`EMU python child process exited with code ${code}`);
    console.error('EMU Attempting to start backup python child process...')
    subpy = null;
    if (process.platform == 'win32'){
      console.log(__dirname)
      dependencyManager = require('child_process').spawn('cmd.exe', ['/c', String(__dirname) + '/install-script.bat']);
      dependencyManager.on('exit', (code) => {
        dependencyManager = null;
        backup_subpy = require('child_process').execFile('python', ['./resources/app/main.py']);
        backup_subpy.stdout.on('data', function(data) {
          console.log(data.toString()); 
        });
        backup_subpy.on('exit', (code) => {
          if(!expectedExit){
            backup_subpy = null;
            console.error(`EMU backup python child process exited with code ${code}`);
            console.error("It is likely that your microcode.o or assembled.o files are invalid.");
            errorWindow = new BrowserWindow({width: 400, height: 400, show: true, webPreferences: {nodeIntegration: true}, frame: true});
            errorWindow.loadFile('errorWindow.html');
          }
          else{
            expectedExit = false;
          }
        });
      });
    }
    else if (process.platform == 'darwin'){
      //var backup_subpy = require('child_process').spawn('open', ['/Applications/Calculator.app']);
      //var backup_subpy = require('child_process').spawn('pwd', {stdio: [process.stdin, process.stdout, process.stderr]});
      console.error("EMU process.cwd = " + String(__dirname) + '/main.py');
      dependencyManager = require('child_process').spawn('bash', [String(__dirname) + '/install-script.sh'], {stdio: [process.stdin, process.stdout, process.stderr], detached: false});    
      dependencyManager.on('exit', (code) => {
        backup_subpy = require('child_process').spawn('/Library/Frameworks/Python.framework/Versions/3.8/bin/python3', [String(__dirname) + '/main.py'], {stdio: [process.stdin, process.stdout, process.stderr], detached: false});
        backup_subpy.on('exit', (code) => {
          if(!expectedExit){
            backup_subpy = null;
            console.error(`EMU backup python child process exited with code ${code}`);
            if(code != 0){
              console.error("It is likely that your microcode.o or assembled.o files are invalid.");
              errorWindow = new BrowserWindow({width: 400, height: 400, show: true, webPreferences: {nodeIntegration: true}, frame: true});
              errorWindow.loadFile('errorWindow.html');
            }
          }
          else{
            expectedExit = false;
          }
        });
      });
    }
    else{
      console.error("EMU process.cwd = " + String(__dirname) + '/main.py');
      dependencyManager = require('child_process').spawn('bash', [String(__dirname) + '/install-script.sh'], {stdio: [process.stdin, process.stdout, process.stderr], detached: false});    
      dependencyManager.on('exit', (code) => {
        backup_subpy = require('child_process').spawn('python3', [String(__dirname) + '/main.py'], {stdio: [process.stdin, process.stdout, process.stderr], detached: false});
        backup_subpy.on('exit', (code) => {
          if(!expectedExit){
            console.error(`EMU backup python child process exited with code ${code}`);
            backup_subpy = null;
            if(code != 0){
              console.error("It is likely that your microcode.o or assembled.o files are invalid.");
              errorWindow = new BrowserWindow({width: 400, height: 400, show: true, webPreferences: {nodeIntegration: true}, frame: true});
              errorWindow.loadFile('errorWindow.html');
            }
          }
          else{
            expectedExit = false;
          }
        });
      });
    }
  });

  // fire!
  startUp();
  Http.open("GET", "http://localhost:5000");
  Http.send();
  
  Http.onreadystatechange=(e)=>{
    //console.log(Http.responseText)
  }
 

});

