const electron = require('electron');
var mqtt = require('mqtt');
var client = null;
const app = electron.app;
var XMLHttpRequest = require("xmlhttprequest").XMLHttpRequest;
const Http = new XMLHttpRequest();
const stopBtn = document.getElementById('stopBtn');
const ipc = electron.ipcRenderer
console.log("render.js ran");
console.log(stopBtn);
var remote = require('electron').remote;
var numOfComponents = 0;
var window = remote.getCurrentWindow();
var componentData = null;
var hardwareComponents = {};
var mqttSent = false;
var rp = require('request-promise');
var blockNextPublish = false;
client = mqtt.connect('mqtt://lab.thewcl.com', {username: Math.floor(Math.random() * Math.floor(500000)).toString()})
var autoClock = false;

function runMicroassembler(){
  //spawn microassembler process in terminal window
}

function runAssembler(){
  //spawn assembler process in terminal window
}

require('electron').ipcRenderer.on('ping', (event, message) => {
  console.log(message);
  if(message == "uuid"){
    //uuidSet();
  }
  else if(message == "component"){
    subscribeToHardware();
  }
  else if(message == "apikey"){
    client.publish("CPU-WCL/" + remote.getGlobal('uuid').get.toString() + "/blynkAPI", remote.getGlobal('apikey').get.toString());
  }
})

function publishToMQTT() {
    if(remote.getGlobal('uuid').get.toString() != ""){
      Object.keys(hardwareComponents).forEach((key, index) => {
        if(hardwareComponents[key].checked == true){
          console.log(key, hardwareComponents[key])
          console.log(componentData[key].ctrlByte);
          client.publish("CPU-WCL/" + remote.getGlobal('uuid').get.toString() + "/components/" + hardwareComponents[key].device + "/" + componentData[key].busPosition.toString() + "/controlDown", componentData[key].ctrlByte.toString())
          if(componentData[key].drivingBus == true && componentData["bus"].isFloating == false){
            client.publish("CPU-WCL/" + remote.getGlobal('uuid').get.toString() + "/drivingBus", componentData[key].busPosition.toString())
          }
        }
      })
      client.publish("CPU-WCL/" + remote.getGlobal('uuid').get.toString() + "/busValueDown", componentData["bus"].currentValue.toString())
      if(componentData["bus"].isFloating == true) {
        client.publish("CPU-WCL/" + remote.getGlobal('uuid').get.toString() + "/drivingBus", "-1"); 
      }
      else{
        var floating = true;
        for(key in hardwareComponents){
          if(componentData[key].drivingBus.toString() == "true"){
            floating = false;
          }
        }
        if(floating){
          client.publish("CPU-WCL/" + remote.getGlobal('uuid').get.toString() + "/drivingBus", "-1"); 
        }
      }
    }
  }


function subscribeToHardware() {
  hardwareComponents = JSON.parse(remote.getGlobal('componentSelection').get)
    Object.keys(hardwareComponents).forEach((key, index) => {
      if(hardwareComponents[key].checked == true){
        document.getElementById(key + "_button").disabled = true;
        console.log(key, hardwareComponents[key])
        console.log(componentData[key].ctrlByte);
        client.publish("CPU-WCL/" + remote.getGlobal('uuid').get.toString() + "/components/" + hardwareComponents[key].device + "/" + componentData[key].busPosition.toString() + "/controlDown", componentData[key].ctrlByte.toString())
        client.subscribe("CPU-WCL/" + remote.getGlobal('uuid').get.toString() + "/components/" + hardwareComponents[key].device + "/" + componentData[key].busPosition.toString() + "/controlUp")
        if(componentData[key].componentType == "ALU"){
          client.publish("CPU-WCL/" + remote.getGlobal('uuid').get.toString() + "/ALU/" + hardwareComponents[key].device + "/" + componentData[key].busPosition.toString(), "true");
        }
        if(componentData[key].drivingBus == true && componentData["bus"].isFloating == false){
          client.publish("CPU-WCL/" + remote.getGlobal('uuid').get.toString() + "/drivingBus", componentData[key].busPosition.toString())
        }
      }
      else{
        document.getElementById(key.toString() + "_button").disabled = false;
      }

      if(componentData["bus"].isFloating == true) {
        client.publish("CPU-WCL/" + remote.getGlobal('uuid').get.toString() + "/drivingBus", "none");
      }
    })
  client.publish("CPU-WCL/" + remote.getGlobal('uuid').get.toString() + "/busValueDown", componentData["bus"].currentValue.toString())
    //find OE ctrl line
}

function uuidSet(event) {
  console.log("uuidSet");
  client.end();
  client = mqtt.connect('mqtt://lab.thewcl.com', {username: remote.getGlobal('uuid').get.toString()})
  if(remote.getGlobal('uuid').get.toString() != "") {
    let HttpInitRequest = new XMLHttpRequest();
    HttpInitRequest.open("GET", "http://localhost:5000/mqtt/enableMQTT/true");
    HttpInitRequest.send();
    HttpInitRequest.onreadystatechange=(e)=>{
      if(HttpInitRequest.status == 200){
        console.log("init request completed");
        //console.log(HttpInitRequest.responseText);
      }
    };
    let HttpInitRequest2 = new XMLHttpRequest();
    HttpInitRequest2.open("GET", "http://localhost:5000/mqtt/setUUID/" + remote.getGlobal('uuid').get.toString());
    HttpInitRequest2.send();
    HttpInitRequest2.onreadystatechange=(e)=>{
      if(HttpInitRequest2.status == 200){
        console.log("init request completed");
        //console.log(HttpInitRequest.responseText);
      }
    };
    for (var c in componentData) {
      if (c != 'bus'){
        var position = componentData[c].busPosition
        for (var ctrlLine = 0; ctrlLine < 8; ctrlLine++) {
          //client.subscribe("CPU-WCL/" + remote.getGlobal('uuid').get.toString() + "/components/" + position.toString() + "/" + ctrlLine.toString(), function (err) {
            if (!err) {
              //client.publish('cpu-bus/trylaarsdam/substatus', 'Subscribe Success');
            }
            else {
              
            }
          }
          //console.log("CPU-WCL/" + remote.getGlobal('uuid').get.toString() + "/components/" + position.toString() + "/" + ctrlLine.toString())
        }
      }
    }
  else {
    let HttpInitRequest = new XMLHttpRequest();
    HttpInitRequest.open("GET", "http://localhost:5000/mqtt/enableMQTT/false");
    HttpInitRequest.send();
    HttpInitRequest.onreadystatechange=(e)=>{
      if(HttpInitRequest.status == 200){
        console.log("init request completed");
        //console.log(HttpInitRequest.responseText);
      }
    };
  }
  return;
}

let HttpInitRequest = new XMLHttpRequest();
HttpInitRequest.open("GET", "http://localhost:5000/devaccess/bus-access");
HttpInitRequest.send();
HttpInitRequest.onreadystatechange=(e)=>{
  if(HttpInitRequest.status == 200){
    console.log("init request completed");
    //console.log(HttpInitRequest.responseText);
    refreshWindow(HttpInitRequest.responseText);
  }
};

client.on('connect', function() {
  
  client.subscribe('cpu-bus/trylaarsdam/busvalue', function (err) {
    if (!err) {
      client.publish('cpu-bus/trylaarsdam/busvalue', 'Subscribe Success');
    }
  })
  var topic = "CPU-WCL/" + remote.getGlobal('uuid').get.toString() + "/busValueUp"
  console.log("busvaluetopic - " + topic);
  client.subscribe(topic, function (err) {
    if (!err) {
      client.publish('cpu-bus/trylaarsdam/busValueUpSubscription', 'busValueUp subscribed');
    }
  })
  //client.subscribe("CPU-WCL/" + remote.getGlobal('uuid').get.toString() + "/busValueUp", function (err) {
    //if (!err) {
      //client.publish('cpu-bus/trylaarsdam/busValueUpSubscription', 'busValueUp subscribed');
    //}
  //})
});

function mqttBusValue(value, component) {
  rp("http://localhost:5000/mqtt/busValue/" + value.toString() + "/" + component)
    .then(function (jsonString) {
      refreshWindow(jsonString);
    })
    .catch(function (err) {
      console.log(err);
    })
}

client.on('message', function (topic, message) {
  console.log("Topic " + topic.toString());
  console.log("Value " + message.toString());
  var topicArray = topic.split("/");
  if (topicArray[0] == "CPU-WCL"){
    if (topicArray[1] == remote.getGlobal('uuid').get.toString()) {
      if (topicArray[2] == "busValueUp") {
        var drivingComponent = "none";
        for(c in componentData){
          if(c != "bus"){
            if(componentData[c].drivingBus.toString() == 'true'){
              drivingComponent = c;
            }
          }
        }
        console.log("drivingcomponent:" + drivingComponent);
        if(blockNextPublish == false){
          rp("http://localhost:5000/mqtt/busValue/" + message.toString() + "/" + drivingComponent)
          .then(function (jsonString) {
            refreshWindow(jsonString);
          })
          .catch(function (err) {
            console.log(err);
          })
        blockNextPublish = true;
        return
        }
      }
      else if(topicArray[2]== "components") {
        rp("http://localhost:5000/mqtt/controlUp/" + topicArray[4] + "/" + message.toString())
        .then(function (jsonString) {
          refreshWindow(jsonString);
        })
        .catch(function (err) {
          console.log(err);
        })
      }
    }
  }
});

function buttonClicked(buttonID){
  console.log("button clicked (running from render.js)");
  let Http = new XMLHttpRequest();
  if(document.getElementById(buttonID) != document.getElementById("clock") && document.getElementById(buttonID) != document.getElementById("dumpRAM") && document.getElementById(buttonID) != document.getElementById("autoClock")){
    Http.open("GET", "http://localhost:5000/" + buttonID + "/buttonClicked");
    Http.send();
    Http.onreadystatechange=(e)=>{
      if(Http.readyState === 4){
        console.log(Http.responseText)
        //buttonID.innerHTML = Http.responseText;
        if (document.getElementById(buttonID) == document.getElementById("reset")){
          console.log("RESET Triggered Manually");
          autoClock = false;
          refreshWindow(Http.responseText);
        }
        else if (document.getElementById(buttonID) == document.getElementById("assembler")){
          let _el = document.getElementById(buttonID);
        }
        else {
          let _el = document.getElementById(buttonID);
          refreshWindow(Http.responseText);
        }
      } 
    }
  }
  if (document.getElementById(buttonID) == document.getElementById("clock")){
    console.log("Clock response returned");
    if(remote.getGlobal('uuid').get.toString() == ""){
      rp("http://localhost:5000/" + buttonID + "/buttonClicked")
          .then(function (jsonString) {
            refreshWindow(jsonString);
          })
          .catch(function (err) {
            console.log(err);
          })
    }
    else {
      blockNextPublish = false;
      client.subscribe("CPU-WCL/" + remote.getGlobal('uuid').get.toString() + "/busValueUp");
      client.publish("CPU-WCL/" + remote.getGlobal('uuid').get.toString() + "/clockPulse", "clk");
    }
  }
  else if(document.getElementById(buttonID) == document.getElementById("dumpRAM")){
    var address = ""
    var bytes = ""
    if(document.getElementById("dumpRAM_address").value != ""){
      address = document.getElementById("dumpRAM_address").value;
      console.log("dumpRAM: address")
      console.log(document.getElementById("dumpRAM_address").value);
    }
    else{
      address = "0"
    }
    if(document.getElementById("dumpRAM_bytes").value != ""){
      bytes = document.getElementById("dumpRAM_bytes").value;
      console.log("dumpRAM: bytes")
      console.log(document.getElementById("dumpRAM_bytes").value);
    }
    else{
      bytes = "0"
    }
    rp("http://localhost:5000/devaccess/ram/" + address + "/" + bytes)
    .then(function (ramDump) {
      document.getElementById("dump").innerHTML = ramDump
    })
    .catch(function (err) {
      document.getElementById("dump").innerHTML = "Error fetching RAM. Check console for more details."
      console.log("RAM Dump Error:")
      console.log(err);
    })
  }
  else if(document.getElementById(buttonID) == document.getElementById("autoClock")){
    if(!autoClock){
      autoClock = true;
      if(remote.getGlobal('uuid').get.toString() == ""){
        rp("http://localhost:5000/" + "clock" + "/buttonClicked")
            .then(function (jsonString) {
              refreshWindow(jsonString);
            })
            .catch(function (err) {
              autoClock = false;
              console.log(err);
            })
      }
      else {
        blockNextPublish = false;
        client.subscribe("CPU-WCL/" + remote.getGlobal('uuid').get.toString() + "/busValueUp");
        client.publish("CPU-WCL/" + remote.getGlobal('uuid').get.toString() + "/clockPulse", "clk");
      }
    }
    else{
      autoClock = false;
    }
    
  }
}

function componentButton(buttonID) {
  rp("http://localhost:5000/" + buttonID + "/buttonClicked")
    .then(function (jsonString) {
      refreshWindow(jsonString);
    })
    .catch(function (err) {
      console.log(err);
    })
}

function checkboxClicked(checkboxID){
  console.log("checkbox clicked (running from render.js");
  let Http = new XMLHttpRequest();
  let _el = document.getElementById(checkboxID);
  if(_el.checked == true){
    Http.open("GET", "http://localhost:5000/checkBoxClicked/" + checkboxID + "/1");
  }
  else if(_el.checked == false){
    Http.open("GET", "http://localhost:5000/checkBoxClicked/" + checkboxID + "/0");
  }
  else {
    return null
  }
  Http.onreadystatechange=(e)=>{
    console.log("ready state: " + Http.readyState);
    if(Http.readyState === 4){
      console.log("checkboxClicked Response: " + Http.responseText);
      console.log("response status: " + Http.status);
      refreshWindow(Http.responseText);
    } 
  }
  Http.send();

}

function refreshWindow(json) {
  console.log("refreshWindow initiated");
  console.log(json);
  var data = JSON.parse(json);
  componentData = data;
  if(client != null){
    publishToMQTT();
  }
  numOfComponents = 0;
  for (var c in data) {
    numOfComponents = numOfComponents + 1;
    //console.log(c);
    //console.log(x[c].currentValue);
    //console.log(x.A.currentValue)
    //console.log(x[c].busPosition)
    if (c != 'bus'){
      for (var cw in data[c].ctrlWord) {
        //console.log("cw=" + cw)
        //console.log("ctrlWord[cw]=" + data[c].ctrlWord[cw])
        let _el = 'c_p'
        let _la = _el.replace(/c/, c)
        _la = _la.replace(/p/, cw)
        //console.log(_la);
        let _checkbox = document.getElementById(_la);
        _checkbox.checked = data[c].ctrlWord[cw];
      }
      let _component = 'c_button';
      _component = _component.replace(/c/, c);
      //console.log(_component);
      _button = document.getElementById(_component);
      if (data[c].currentValue == "None") {
        _button.innerHTML = ("None");
      }
      else{
        _button.innerHTML = (data[c].currentValue).toString(16);
      }
      _component = 'c_status';
      _component = _component.replace(/c/, c);
      console.log(_component);
      _status = document.getElementById(_component);
      console.log(c + String(data[c].busPosition % 2));
      if (data[c].drivingBus == true){
        if ((data[c].busPosition % 2) == 0){
          console.log("<<<" + String(c));
          _status.innerHTML = (">>>");
        }
        else if((data[c].busPosition % 2) != 0) {
          console.log(">>>" + String(c));
          _status.innerHTML = ("<<<");
        }
      }
      else if (data[c].readingBus == true){
        if ((data[c].busPosition % 2) == 0){
          console.log(">>>" + String(c));
          _status.innerHTML = ("<<<");
        }
        else if((data[c].busPosition % 2) != 0) {
          console.log("<<<" + String(c));
          _status.innerHTML = (">>>");
        }
      }
      else {
        _status.innerHTML = ("");
      }
    }
    else{
      let _el = document.getElementById("bus_value"); 
      console.log("Bus Value: " + data[c].currentValue);
      bus_value = data[c].currentValue;
      let clockCounter = document.getElementById("clockCounter");
      console.log("Clock Count: " + data[c].clockCounter)
      clockCounter.innerHTML = "Cycles: " + data[c].clockCounter + "&nbsp; &nbsp;"
      _el.innerHTML = (bus_value).toString(16);
      _el = document.getElementById("bus_status");
      console.log("Bus is floating: " + data[c].isFloating);
      console.log("Bus has conflict: " + data[c].hasConflict);
      let _la = document.getElementById("opcode");
      _la.innerHTML = data[c].currentOpcode;
      if(data[c].isFloating == true){
        _el.style.backgroundColor = 'Yellow';
        _el.style.color = 'Black';
        _el.innerHTML = "FLOATING";
      }
      else if(data[c].hasConflict == true){
        _el.style.backgroundColor = 'Red';
        _el.style.color = 'White';
        _el.innerHTML = "BUS CONFLICT";
      }
      else{
        _el.innerHTML = "Normal";
        _el.style.backgroundColor = 'Blue';
        _el.style.color = 'White';
      }
    }
    //console.log(c[0]);
   }
  if(autoClock && data['CTRL'].halt != true){
    setTimeout(() => { if(remote.getGlobal('uuid').get.toString() == ""){
      rp("http://localhost:5000/" + "clock" + "/buttonClicked")
          .then(function (jsonString) {
            refreshWindow(jsonString);
          })
          .catch(function (err) {
            autoClock = false;
            console.log(err);
          })
    }
    else {
      blockNextPublish = false;
      client.subscribe("CPU-WCL/" + remote.getGlobal('uuid').get.toString() + "/busValueUp");
      client.publish("CPU-WCL/" + remote.getGlobal('uuid').get.toString() + "/clockPulse", "clk");
    } }, 100);
  }
  else{
    autoClock = false;
  }
}

function renderTest() {
    return "string from render test";
}