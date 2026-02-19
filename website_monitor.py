import requests, os, time, json
import sys
import logger
import difflib
import io
from datetime import datetime



previous_data_filename = "last_status.json"
project_dir = os.path.dirname(__file__)
if not "history" in os.listdir(project_dir):
    os.mkdir("history")

logger.new_log("main", os.path.join(os.path.dirname(__file__), "log"), overwrite=False)


def log(*msg, end="\n"):
    logger.log(*msg, target_logs_names=["main"], end=end)

def logToDiscord(*msg, webhook_url, webhook_username, text_as_file=None):
    logger.log(*msg)
    data = {
        "username": webhook_username,
        "content": " ".join(list(msg))
    }
    files = None
    if text_as_file is not None:
        file_data = io.BytesIO(text_as_file.encode('utf-8'))
        files = {"file": ("content.html", file_data)}
    try:
        response = requests.post(webhook_url, json=data, files=files)
    except requests.ConnectionError as e:
        log(f"Error sending message to discord webhook: {e}")
        return
    try:
        response.raise_for_status()  # Raise an exception for bad status codes
        return "Message sent successfully."
    except requests.exceptions.HTTPError as err:
        return f"Error: {err}"

log("Loading config.json...")
try:
    config_path = os.path.join(project_dir, "config.json")
    with open(config_path) as f:
        config = json.load(f)
except FileNotFoundError:
    log("Error: config.json not found. This program requires config.json to run.\nCopy content of config_template.json into config.json and add your webhook and website url.")
    sys.exit()
except json.JSONDecodeError as e:
    log(f"Error loading config.json: JSON decoder couldn't decode the file. Check your syntax. (Full error: {e})")
    sys.exit()
except Exception as e:
    log(f"Error loading config.json: {e}")
    sys.exit()

log(f"Loaded config.json: {config}")
log("Started...")

default_url_prefix:str = config["default_url_prefix"]

if previous_data_filename in os.listdir(project_dir):
    try:
        with open(os.path.join(project_dir, previous_data_filename), "r") as f:
            old_data = json.load(f)
    except Exception as e:
        log(f"Error loading previous data: {e}")
        old_data = {}
else:
    log(f"Previous data not found ({previous_data_filename} doesn't exist)")
    old_data = {}

targets = config["targets"]
for target in targets:
    target_url:str = target["url"].strip()
    if target_url and target_url.startswith(("http://", "https://", default_url_prefix)):
        target["url"] = target_url
    else:
        target["url"] = default_url_prefix + target_url

class DummyResponse:
    def __init__(self, status_code):
        self.status_code = status_code
        self.content = "".encode()

def write_content_change(status_code, content, old_content, file_path):
    history = []
    # Load existing history if file exists
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            try:
                history = json.load(f)
            except json.JSONDecodeError:
                history = []
    # Only save if the content is different
    if content != old_content:
        # Generate a Git-style diff for reference
        diff = list(difflib.ndiff(old_content.splitlines(), content.splitlines()))
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "status_code":status_code,
            "diff": diff
        }
        history.append(entry)
        # Write the updated list back to the same file
        with open(file_path, 'w') as f:
            json.dump(history, f, indent=4)
        return "New version saved to JSON."
    return "No changes detected."

def make_safe_filename(input_string):
    safe_name = input_string
    safe_name = safe_name.replace(":",".")
    safe_name = safe_name.replace("/","_")
    safe_name = safe_name.replace("\\","_")
    safe_name = safe_name.replace("?","-")
    safe_name = safe_name.replace("*","-")
    return safe_name[:200]

online_reference_url:str = config["online_check_reference"].strip()
if not online_reference_url.startswith(("https://", "http://", default_url_prefix)):
    online_reference_url = default_url_prefix + online_reference_url

try:
    while True:

        log("Checking internet access..")
        online_check_delay_seconds = config["online_check_delay_seconds"]
        online = False
        offline_message_was_sent = False
        while not online:
                try:
                    response = requests.get(online_reference_url)
                    online = True
                    log(f"We are online! ({online_reference_url} returned status code: {response.status_code})")
                except Exception as e:
                    if not offline_message_was_sent:
                        log(f"We are offline! (Error connection to reference url {online_reference_url}: {e})\nWaiting for internet access. ")
                        offline_message_was_sent = True
                    # else:
                    #     log("#", end="")
                    time.sleep(online_check_delay_seconds)



        for target in targets:
            url = target["url"]
            log(f"Checking {url}...")
            try:
                if url.startswith("http://"):
                    response = requests.get(url=url, verify=target.get("require_ssl_certificate"))
                elif url.startswith("https://"):
                    response = requests.get(url=url, verify=target.get("require_ssl_certificate"))
                elif url.startswith(default_url_prefix):
                    response = requests.get(url=url, verify=target.get("require_ssl_certificate"))
                else:
                    log(f"Invalid url: {url} - doesn't start with 'http://' or 'https://'")
            except Exception as e:
                response = DummyResponse(f"Error:{str(e)}")

            status_code = response.status_code
            log(f"Got status {status_code}")

            something_changed = False

            this_is_first_status_check = False
            if not url in old_data:
                this_is_first_status_check = True
                something_changed = True
                old_data[url] = {}
                old_data[url]["status_code"] = status_code
                log(f"Added url {url} with status {status_code}")

            if status_code != old_data[url]["status_code"] and (not target.get("ignore_inital_status_check") or not this_is_first_status_check):
                if target.get("use_webhook_on_status_change"):
                    if target.get("ping_on_status_change"):
                        logToDiscord(f"@everyone `{url}` changed status code to {status_code}!", webhook_url=target.get("url"), webhook_username=target.get("webhook_username"))
                    else:
                        logToDiscord(f"`{url}` changed status code to {status_code}!", webhook_url=target.get("url"), webhook_username=target.get("webhook_username"))
                old_data[url]["status_code"] = status_code
                something_changed = True

            if target.get("check_content_changes"):
                try:
                    log(f"Decoding response.content with encoding {response.apparent_encoding}...  ", end="")
                    current_content = response.content.decode(encoding=response.apparent_encoding)
                    log("Done.")
                except Exception as e:
                    log(f"Error decoding response.content: {e}")
                    current_content = ""

                if not url in old_data:
                    old_data[url] = {}
                    old_data[url]["content"] = ""
                    old_content = ""
                elif not "content" in old_data[url]:
                    old_data[url]["content"] = ""
                    old_content = ""
                else:
                    old_content = old_data[url]["content"]


                if current_content != old_content:
                    log(f"Website content has changed!")
                    something_changed = True
                    old_data[url]["content"] = current_content
                    if target.get("use_webhook_on_content_change") and (target.get("ignore_inital_status_check") or not this_is_first_status_check):
                        logToDiscord(f"Content of {url} has changed.", text_as_file=current_content, webhook_url=target.get("url"), webhook_username=config["webhook_username"])

            else:
                current_content = ""
            if something_changed:
                log("Writing changes...")
                target_file = os.path.join(project_dir, "history", f"target_diffs_{make_safe_filename(url)}.json")
                msg = write_content_change(status_code, current_content, old_content, target_file)
                log(f"Wrote changes. Got message: {msg}")
            else:
                log("Nothing changed.")
        with open(os.path.join(project_dir, previous_data_filename), "w") as f:
            json.dump(old_data, f)
        # log(f"Sleeping for {config["check_delay_seconds"]}s...")
        time.sleep(config["check_delay_seconds"])

except KeyboardInterrupt:
    log("\nKeyboardInterrupt - Exiting...")
    old_data["script_exit"] = "KeyboardInterrupt"
    with open(os.path.join(project_dir, previous_data_filename), "w") as f:
        json.dump(old_data, f, indent=4)

except Exception as e:
    log(f"Error in the main loop: {e}")
    old_data["script_exit"] = str(e)
    with open(os.path.join(project_dir, previous_data_filename), "w") as f:
        json.dump(old_data, f)
