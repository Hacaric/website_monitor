import os, requests
from datetime import datetime
LOG_FILES = {}
MAIN_LOG = None
STATS_LOG = None

class LogFile:
    def __init__(self, name, path, filename, file_open_mode="w", prefix_format='[%H:%M:%S] ', autoopen=True):
        self.name = name
        self.filename = filename
        self.path = path
        self.file_open_mode = file_open_mode
        self.prefix_format = prefix_format
        self.unwritten_msg = []
        if autoopen:
            self.file = open(os.path.join(path, filename), file_open_mode)
        else:
            self.file = None

    def reopen(self, new_filename=None, new_path=None, new_file_open_mode=None):
        if self.file:
            self.file.close()
        if new_filename:
            self.filename = new_filename
        if new_path:
            self.path = new_path
        if new_file_open_mode:
            self.file_open_mode = new_file_open_mode
        self.file = open(os.path.join(self.path, self.filename), self.file_open_mode)

    def flush(self):
        if self.file:
            self.file.flush()

    def write(self, *msg, end="\n", msg_join=" ", prefix=True, flush=False):
        final_msg = msg_join.join(list(msg)) + end
        if prefix:
            now = datetime.now()
            final_msg = now.strftime(self.prefix_format) + final_msg
        if self.file:
            self.file.write(final_msg)
            if flush:
                self.file.flush()
        else:
            self.unwritten_msg.append(final_msg)

    def close(self):
        if self.file:
            self.file.close()
            self.file = None

class LogToWebHook(LogFile):
    def __init__(self, name, webhook_url, webhook_username):
        self.webhook_url = webhook_url
        self.name = name
        self.webhook_username = webhook_username
        self.active = True

    def reopen(self):
        self.active = True

    def flush(self):
        pass

    def write(self, *msg, end="\n", msg_join=" ", prefix=False, **kwargs):
        print(f"Writing to webhook: {list(msg)}")
        final_msg = msg_join.join(list(msg)) + end
        if prefix:
            now = datetime.now()
            final_msg = now.strftime(self.prefix_format) + final_msg
        try:
            while self.unwritten_msg: 
                data = {
                      "username":self.webhook_username,
                      "content":"Retry: "+self.unwritten_msg.pop(0)
                }
                requests.post(url=self.webhook_url, data=data)

            data = {
                "username":self.webhook_username,
                "content":final_msg
            }
            requests.post(url=self.webhook_url, data=data)
        except Exception as e:
            if self.name == "main":
                print(f"Error sending message via webhook: {e}")
            else:
                log(f"Error sending message via webhook: {e}", target_logs_names=["main"])
            self.unwritten_msg.append(final_msg)

    def close(self):
        self.active = False

def new_webhook_log(name, url, webhook_username):
    global LOG_FILES
    if name in LOG_FILES:
        raise ValueError(f"A log webhook with the name '{name}' already exists.")
    # if name == "main":
    #     raise ValueError("Can't name webhook log 'main' to avoid recursion when logging errors.")
    log_file = LogToWebHook(name, url, webhook_username)
    LOG_FILES[name] = log_file
    return log_file

def new_log(name, path, overwrite=True):
    global LOG_FILES
    now = datetime.now()
    if name in LOG_FILES:
        raise ValueError(f"A log file with the name '{name}' already exists.")
    formatted_date_time = now.strftime("%d-%m-%Y_%H-%M")
    log_file_name = f"log_{name}_{formatted_date_time}.txt"
    if not os.path.exists(path):
        os.makedirs(path)
    elif not overwrite:
        logs = os.listdir(path)
        i = 2
        while log_file_name in logs:
            log_file_name = f"log_{name}_{formatted_date_time}#{i}.txt"
            i += 1
    log_file = LogFile(name, path, log_file_name, autoopen=True)
    LOG_FILES[name] = log_file
    return log_file
    # stats_file_name = f"statisctic_{formatted_date_time}.txt"
    # stats_file = open(os.path.join(os.path.dirname(__file__), "stats", stats_file_name), "wt")

def log(*msg, target_logs_names=[]):
    # now = datetime.now()
    # final_message = f"[{now.strftime('%H:%M:%S')}]"
    final_message = ""
    for text in list(msg):
        if isinstance(text, str):
            final_message += text + " "
        else:
            try:
                text = str(text)
                final_message += text + " "
            except Exception as e:
                # text = f"Error: Can't convert log message to string: {e}"
                final_message += "{Error converting to str} "
    # raise Exception("Failed successfully")
    final_message = final_message[:-1] # Remove unnessecarry space
    if final_message:
        for log_file_name in target_logs_names:
            log_file:LogFile = LOG_FILES[log_file_name]
            log_file.write(final_message, flush=True)

def closeAll():
    for log in LOG_FILES:
        log.close
