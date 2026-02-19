# Website monitor - a simple utility for tracking website changes
## Installation
1. Clone the repository `git clone https://github.com/Hacaric/website_monitor`
2. Copy `config_template.json` into `config.json`. (`cp config_template.json config.json`)
3. Setup your `config.json`:
```text
{
    "check_delay_seconds":7200,
    "online_check_reference":"google.com", //If this website is reachable, we are online, otherwise we are offline. Choose a website that is never offline!
    "online_check_delay_seconds":30,  //How long to wait between checking "online_check_reference"
    "default_url_prefix":"https://",  //If url doesn't have prefix, this will be use
    "ignore_inital_status_check":true,  //Do not consider first website rewrite a 'change' - do not send notification to discord. Initial run is detected when last_status.json doesn't exist
    "targets":[{
        "url":WEBSITE_URL,
        "require_ssl_certificate":true,
        "webhook":YOUR_DISCORD_WEBHOOK,  //Make sure it has https:// prefix!
        "save_diffs":true,  //Save website changes? They will be stored in history/ directory. Similar to git changes (library: difflib)
        "webhook_username":"Website monitoring bot",  //Shown as author of message in discord
        "use_webhook_on_status_change":true,  //Send message to discord when status changes
        "ping_on_status_change":false,  //Ping @everyone when status changes (only applies if use_webhook_on_status_change is true)
        "check_content_changes":true,  //Check html for changes?
        "use_webhook_on_content_change":false  //Write discord message when html changes?
    }]
}
```
4. Run `python website_monitor.py`
