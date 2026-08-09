# 
# Example usage: 
#
# from gameLogger import *
# new_log_file("./log/", "server.log")
# log("Hello world!")
# close_log_files()
#
# 
# Note: please close files properly (with close_log_files()) so repeated messages are logged correctly 

import os
import datetime
ENDC = '\033[0m' #end color effects
colorNames = {
    "header": '\033[95m',
    "blue": '\033[94m',
    "cyan": '\033[96m',
    "green": '\033[92m',
    "warning": '\033[93m',
    "fail": '\033[91m',
    "error": '\033[91m',
    "red": '\033[91m',
    "endc": '\033[0m',
    "bold": '\033[1m',
    "underline": '\033[4m',
    "italic": '\033[3m',
    "endc": '\033[0m'
}
def getColorCodes(color:str|None) -> tuple[str, str]:
    """
    Return color codes for the given color
    Supported colors:
    - RGB in format: "#RRGGBB" 
    - Font variations: "bold", "underline", "italic"
    - Color names: "header", "blue", "cyan", "green", "warning", "fail", "error", "red"
    - Special: "endc" (end of formatting)
    Supported formats:
    - color:str
    - [color1:str, color2:str, ...]
    """
    if type(color) == list:
        colors = []
        for i in color:
            colors.append(getColorCodes(i)[0])
        return "".join(colors), ENDC
    if type(color) == str and len(color) == 7 and color[0] == "#":
        return f"\033[38;2;{int(color[1:3], 16)};{int(color[3:5], 16)};{int(color[5:], 16)}m", ENDC
    if color == None:
        return "", ""
    if color in colorNames:
        return colorNames[color], ENDC
    return f"(color:{color})", ""
log_files = []
last_date = -1
input_global = False
input_prefix_global = " >> "
last_log = ""
last_log_repeated = 0
MAX_REPEAT = 3

def new_log_file(dir, name, replace=False, input_=input_global, input_prefix=input_prefix_global):
    global log_file, input_global, input_prefix_global
    input_global, input_prefix_global = input_, input_prefix
    if not os.path.exists(dir):
        os.makedirs(dir)
    if not replace:
        files = os.listdir(dir)
        idx = 0
        name = name.split(".")
        name = [".".join(name[:-1]), "."+name[-1]]
        while name[0]+str(idx)+name[1] in files:
            idx += 1
        name = name[0]+str(idx)+name[1]
    file = open(os.path.join(dir, name), "w")
    log_files.append(file)
def write_to_files(message, flush=False):
    for log_file in log_files:
        if log_file.closed:
            print(f"Log file {log_file.name} is closed. Removing from log files.")
            log_files.remove(log_file)
            continue
        log_file.write(message)
        if flush:
            log_file.flush()
def get_time():
    time = datetime.datetime.now()
    return str(time.hour)+":"+str(time.minute)+":"+str(time.second)
def log(*message, before="", color:str|list[str]|None=None, handle_repeat=True, print_only=False, disable_autocolor=False):
    """
    Log a message to the console and all log files (if it exists)
    Console message can be colorful
    Messages starting with "Error" and "Debug" trigger automatic color unless disabled by disable_autocolor kwarg
    @param:
        *message: The message to log
        color: The color of the message:
            - Formatting: a) one color name b) list of color names
            - Supported color names: a) rgb in format: "#RRGGBB" b) name from list: "header", "blue", "cyan", "green", "warning", "fail", "endc", "bold", "underline", "italic", "red", "error"
    @kwargs:
        handle_repeat (default:True): If True, the message will be logged only few times if it is repeated
        print_only (default:False): If True, the message will be printed only to the console and not to the log files, repeating will not be handled
        disable_autocolor: If True, messages starting with "Error" and "Debug" are automatically applied (with the smallest color priority = added to the start of color list)
    
    """
    global last_date, last_log, last_log_repeated

    if not color:
        color = []
    if not isinstance(color, list):
        color = [color]

    message = list(message)
    if len(message) == 1 and isinstance(message[0], str) and not disable_autocolor:
        if message[0][0:5] == "Error":
            color = ["fail"] + color
        if message[0][0:5] == "Debug":
            color = ["#0000ff"] + color
    else:
        message = " ".join([str(i) for i in list(message)])

    if log_files and last_date != datetime.datetime.now().date():
        write_to_files(f"{"-"*20}\nNew date: {datetime.datetime.now().date()}\n{"-"*20}\n", flush=True)
        last_date = datetime.datetime.now().date()

    if print_only:
        colorCodes = getColorCodes(color)
        print(colorCodes[0], "[LOG]: ", *message, colorCodes[1], sep="")

        if input_global:
            print(input_prefix_global)
        return

    
    parsed_log = " ".join([str(i) for i in list(message)])
    if handle_repeat:
        if last_log == parsed_log:
            if last_log_repeated == MAX_REPEAT:
                log("Log frozen (repeating messages)", color="warning", handle_repeat=False, print_only=True)
            last_log_repeated += 1
        if last_log_repeated > MAX_REPEAT and last_log == parsed_log:
            return
        elif last_log_repeated > MAX_REPEAT and last_log != parsed_log:
            log(f"Above log repeated {last_log_repeated - MAX_REPEAT} more times.", color="warning", handle_repeat=False)
            last_log_repeated = 0
    # if not (handle_repeat and last_log_repeated > MAX_REPEAT and last_log == parsed_log):
    last_log = parsed_log
    if log_files:
        write_to_files(f"{before}[LOG] [time:{get_time()}]: {str("\n\t".join([str(i) for i in list(message)]))}\n", flush=True)
    colorCodes = getColorCodes(color)
    print(colorCodes[0], f"{before}[LOG]: ", *message, colorCodes[1], sep="")

    if input_global:
        print(input_prefix_global)
def close_log_files():
    log(f"=== Closed on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    for log_file in log_files:
        try:
            log_file.close()
        except Exception as e:
            print(f"Error closing log file: {e}")