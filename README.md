# Website monitor - a simple utility for tracking website changes
## Installation
1. Clone the repository `git clone https://github.com/Hacaric/website_monitor`
2. Copy `config_template.json` into `config.json`. (`cp config_template.json config.json`)
3. Setup your `config.json`:
```text
{
    "check_delay_seconds":7200,
    "online_check_reference":"google.com", // If this website is reachable, we are online, otherwise we are offline. Choose a website that is never offline!
    "online_check_delay_seconds":30,  // How long to wait between checking "online_check_reference"
    "default_url_prefix":"https://",  // If url doesn't have prefix, this will be use
    "ignore_inital_status_check":true,  // Do not consider first website rewrite a 'change' - do not send notification to discord. Initial run is detected when last_status.json doesn't exist
    "targets":[{
        "url":WEBSITE_URL,
        "require_ssl_certificate":true,
        "webhook":YOUR_DISCORD_WEBHOOK,  // Make sure it has https:// prefix!
        "save_diffs":true,  // Save website changes? They will be stored in history/ directory. Similar to git changes (library: difflib)

        "loggers":[
            {
                "type":"BOT",
                "token":TOKEN,       // discord bot access token
                "target_type":"CHANNEL",   // "CHANNEL" or "USER"
                "target_id":channel_id,    // if target_type is "CHANNEL", then this is channel id, if target_type is "USER", than it's user id
                "message_format":{         // Configurable formatting of messages
                    "on_start": "Website monitor for url {url} has started!",            // Values: null: no message sent, string: message is sent; `on_start` message is sent once at start/restart of the script.
                    "status_change": "`{url}` changed status code to {status_code}!",    // Values: null: no message sent, string: message is sent; `status_change` message is sent on target status code change (if `use_discord_on_status_change` is enabled)
                    "content_change": "Content of {url} has changed."                    // Values: null: no message sent, string: message is sent; `content_change` message is sent on target content (response's html) change (if `use_discord_on_content_change` is enabled)
                }
            },
            {
                "type":"WEBHOOK",           
                "webhook_url":WEBHOOK_URL,           // What to say? It's just the discord webhook url  (or any other url that accepts discord-formatted POST requests)
                "message_format":{         // Configurable formatting of messages
                    "on_start": "Website monitor for url {url} has started!",            // Values: null: no message sent, string: message is sent; `on_start` message is sent once at start/restart of the script.
                    "status_change": "`{url}` changed status code to {status_code}!",    // Values: null: no message sent, string: message is sent; `status_change` message is sent on target status code change (if `use_discord_on_status_change` is enabled)
                    "content_change": "Content of {url} has changed."                    // Values: null: no message sent, string: message is sent; `content_change` message is sent on target content (response's html) change (if `use_discord_on_content_change` is enabled)
                }
                "webhook_username":"Website monitor of {url}" 
            }],
            "use_discord_on_status_change":true,  //Send message to discord when status changes
            "check_content_changes":true,  //Check html for changes?
            "use_webhook_on_content_change":false  //Write discord message when html changes?
            }
        ]
}
```
4. Run `python website_monitor.py`
5. (Optional) If you're using Linux with systemd, you can setup a service with `sudo python setup_service.py`
