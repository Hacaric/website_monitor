import requests, os, time, json
import sys
import logger

MINUTE = 60
HOUR = 60*MINUTE
DAY = 24*HOUR

CHECK_DELAY = HOUR * 2

WEBHOOK_NAME = "Website monitor"


last_status_name = "last_status.json"
curr_dir = os.path.dirname(__file__)

logger.new_log("main", os.path.join(os.path.dirname(__file__), "log"), overwrite=False)
if not "webhook.url" in os.listdir(os.path.dirname(__file__)):
    raise FileNotFoundError("'webhook.url' file is required and missing")

with open(os.path.join(os.path.dirname(__file__), "webhook.url"), "r") as f:
    logger.new_webhook_log("webhook", f.readlines()[0], WEBHOOK_NAME)

def log(*msg):
    print(*msg)
    logger.log(*msg, target_logs_names=["main"])

def logToDiscord(*msg):
    print(*msg)
    logger.log(*msg, target_logs_names=["main", "webhook"])
log("Started...")

try:
    with open(os.path.join(curr_dir, last_status_name), "r") as f:
        saved_status = json.load(f)
except Exception as e:
    log(f"Error loading previous data: {e}")
    saved_status = {}

with open(os.path.join(os.path.dirname(__file__), "targets.txt"), "r") as f:
    targets = f.readlines()

targets_filtered = []
for target in targets:
    if target.strip() and target.strip().startswith(("http://", "https://")):
        targets_filtered.append(target.strip())
targets = targets_filtered

class DummyResponse:
    def __init__(self, status_code):
        self.status_code = status_code

status = None
while status != 200:
        if status != None:
                log("google.com is unreachable... retrying in 30 seconds")
        time.sleep(30)
        try:
                r = requests.get("google.com")
                status = r.status
        except:
                pass

try:
    while True:
        for url in targets:
            log(f"Checking {url}...")
            try:
                if url.startswith("http://"):
                    response = requests.get(url=url, verify=False)
                elif url.startswith("https://"):
                    response = requests.get(url=url, verify=True)
                else:
                    log(f"Invalid url: {url} - doesn't start with 'http://' or 'https://'")
            except Exception as e:
                response = DummyResponse(f"Error:{str(e)}")
            log(f"Got status {response.status_code}")
            if (not url in saved_status) or response.status_code != saved_status[url]["status_code"]:
                if "druzinaroka" in url and response.status_code == 200:
                    logToDiscord(f"@everyone {url} is online!")
                elif response.status_code == 200:
                    logToDiscord(f"{url} is now online!")
                    
            if url in saved_status and response.status_code != saved_status[url]["status_code"]:
                    log(f"Status of {url} changed: {saved_status[url]['status_code']} -> {response.status_code}")
                    saved_status[url]["status_code"] = response.status_code
            elif not url in saved_status:
                saved_status[url] = {"status_code": response.status_code}
                log(f"Added url {url} with status {response.status_code}")


        with open(os.path.join(curr_dir, last_status_name), "w") as f:
            json.dump(saved_status, f)
        time.sleep(CHECK_DELAY)

except KeyboardInterrupt:
    log("\nKeyboardInterrupt - Exiting...")
    saved_status["script_exit"] = "KeyboardInterrupt"
    with open(os.path.join(curr_dir, last_status_name), "w") as f:
        json.dump(saved_status, f)

except Exception as e:
    log(f"Error: {e}")
    saved_status["script_exit"] = str(e)
    with open(os.path.join(curr_dir, last_status_name), "w") as f:
        json.dump(saved_status, f)
