"""
Features:
    * Up and down arrows can used to navigate across history of commands 
    * Tab can be used for file auto-completion 
"""

from getpass import getuser
from socket import gethostname
from os import getcwd
from termcolor import colored
from os.path import expanduser, exists
import subprocess
import readline, glob
import argparse
import shlex

def get_ps1():
    user_name = getuser()
    host_name = gethostname()
    directory = getcwd()
    ps1 = f"{user_name}@{host_name} : {directory}$ "  #ps1 => primary prompt variable
    return ps1

def complete_line(text, state):
    return (glob.glob(text+'*')+[None])[state]

def execute_cmd(cmd):
    try:
        cmd_output = subprocess.run(shlex.split(cmd), capture_output= True, text= True, timeout= 120)
        return {"returncode": cmd_output.returncode, "stdout": cmd_output.stdout, "stderr": cmd_output.stderr}
    except subprocess.TimeoutExpired as e:
        return {"returncode": 1, "stdout": "", 
        "stderr": "TIMEOUT Exception: It seems you are running a interative process or your command takes more than 15s for execution, try without -n flag\n"}

def execute_pipe(cmd, pipe_input):
    cmd_output = subprocess.Popen(shlex.split(cmd), stdin = subprocess.PIPE, stdout = subprocess.PIPE)
    out,err = cmd_output.communicate(input= (pipe_input.strip()+"\n").encode())
    cmd_output.wait()

    if out:
        out = out.decode()
    else:
        err = err.decode()

    return {"returncode": cmd_output.returncode, "stdout": out, "stderr": err}

def redirect_out(symbol, location, cmd_output): # '>'
    out = "stdout"
    if len(symbol) == 2 and ord(symbol[0]) == 50:
        out = "stderr"
    with open(location, "w") as f:
        f.writelines(cmd_output[out])

def redirect_in(cmd): # '<'
    if "<" not in cmd.split():
        return cmd

    command, file_name = cmd.rsplit('<',1)
    return f"cat {file_name} | {command}"

def execute_redirection(symbol, location, cmd_output):
    if symbol.endswith(">"):
        redirect_out(symbol, location, cmd_output)

    return {"returncode": 0, 'stdout': "", 'stdin': ""}

def pre_loop(histfile):
    if readline and exists(histfile):
            readline.read_history_file(histfile)

def post_loop(histfile, histfile_size):
    if readline:
        readline.set_history_length(histfile_size)
        readline.write_history_file(histfile)

def parse_inputs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n","--non-interactive", help="Used to run commands in Non-Interative mode", action="store_true")
    args = parser.parse_args()
    return args

def custom_parser(cmd):
    cmd_list = []
    tmp = ""

    for word in cmd.split():
        if word == '|' or word.endswith(">") or  word.endswith("<"):
            cmd_list.append(tmp)
            cmd_list.append(word)
            tmp = ""

        else:
            tmp = tmp + " " + word

    if tmp != "":
        cmd_list.append(tmp)

    return cmd_list

def shell():

    ps1 = get_ps1()
    #for history
    histfile = expanduser('~/.py_unix_shell_history')
    histfile_size = 1000

    #for tab auto completion
    readline.set_completer_delims(' \t\n;')
    readline.parse_and_bind("tab: complete")
    readline.set_completer(complete_line)

    while True:
        pre_loop(histfile)
        cmd = input(colored(ps1,"blue")).strip()
        
        if cmd == "exit":
                break
        
        cmd = redirect_in(cmd)
        cmd_list = custom_parser(cmd)

        pipe_check = 0
        cmd_output_dict = {}
        redirect_check = 0
        redirect_symbol = ""

        for line in cmd_list:
            if line == "|":
                pipe_check = 1
                continue
            elif line.endswith(">") or  line.endswith("<"):
                redirect_symbol = line
                redirect_check = 1
                continue
            
            if pipe_check == 1:
                cmd_output_dict = execute_pipe(line,cmd_output_dict["stdout"])
                pipe_check = 0
            elif redirect_check == 1:
                cmd_output_dict = execute_redirection(redirect_symbol, line, cmd_output_dict)
                redirect_check = 0
                redirect_symbol = ""
            else:
                cmd_output_dict = execute_cmd(line)

        if cmd_output_dict["returncode"]:
            print(colored(cmd_output_dict["stderr"],"red"), end="")
        else:
            print(cmd_output_dict["stdout"], end="")

        post_loop(histfile, histfile_size)

def main():
    shell()

if __name__ == "__main__":
    main()
    
