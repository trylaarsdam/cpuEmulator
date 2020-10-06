const electron = require('electron');
const app = electron.app;

function buttonClicked(id){
    console.log(process.cwd())
    //console.log(__dirname)
    //process.chdir(__dirname)
    //console.log(process.cwd())
    if (process.platform == 'win32'){
        if(id == "assembler"){
            assembler = require('child_process').exec('python ./assembler/main.py ./assembler/code.asm -o ./opcodes.json');
        }
        else if(id == "microassembler"){
            microassembler = require('child_process').exec('python ./microassembler/main.py -c ./controlmap.json -o ./opcodes.json');
        }
    }
    else if(process.platform == 'darwin'){
        console.log(__dirname)
        process.chdir(__dirname)
        if(id == "assembler"){
            require('child_process').spawn('bash', [String(__dirname) + '/runassembler.sh'], {stdio: [process.stdin, process.stdout, process.stderr], detached: false});
        } 
        else if(id == "microassembler"){
            require('child_process').spawn('bash', [String(__dirname) + '/runmicroassembler.sh'], {stdio: [process.stdin, process.stdout, process.stderr], detached: false});
        }
    }
    else {
        if(id == "assembler"){
            console.log(__dirname);
            require('child_process').exec('python3 ./assembler/main.py ./assembler/code.asm', {stdio: [process.stdin, process.stdout, process.stderr], detached: false});
        } 
        else if(id == "microassembler"){
            require('child_process').exec('python3 ./microassembler/main.py -c ./controlmap.json -o ./opcodes.json', {stdio: [process.stdin, process.stdout, process.stderr], detached: false});
        }
    }
}
