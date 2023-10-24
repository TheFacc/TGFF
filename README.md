# Telegram C2C - Chat to Chat Forwarding Bot

This Telegram bot allows you to forward messages from multiple source chats to multiple destination chats (not strictly channels). It is built using Python and the Telethon library.

Features:
- **Filtering**: ignore incoming messages based on various scenarios.
  - option to ignore if it contains buttons (commonly spam)
  - option to ignore if it contains some specific word/string
  - option to force forward if it contains some specific word/string
  - option to ignore all messages, and only forward those forced
- **Print source**: option to include a link in the forwarded message redirecting to the source message
- **Mark as read**: option to mark as read a message when it's processed (forwarded or ignored), so if the bot stops for some reason, you can see what messages it lost (note that if you start it again, for now it will process a new message when it arrives, marking as read all previous messages as well without forwarding them! Forwarding history is a todo feature...)
- **Log to chat**: the bot logs its behaviour in the console, but it's also possible to forward the same log to a Telegram chat, so you can see it on the go.

To do:
- Ability to retrieve message history since last run (currently it forwards only messages received while it's running)
- ~~Add `INCLUDE_WORDS` variable to exclude all messages except those containing those words~~
- ~~handle `*` wildcard word, to ignore all except included words~~
- ~~rewrite structure to better manage additional options~~
- FIX managing handles i think
- FIX cant forward from group (invite link), is it possible at all? with group id maybe (if exists)?
- properly handle groups
- Make an actual bot to manage its functionality and edit its config on the go

_**NOTE (important if you didn't know this was possible!)**: technically it's not really a Telegram bot. It's kind of a headless bot. It runs on your computer and does stuff, but does not link to an actual bot created with BotFather. It simply uses your Telegram session, so it behaves as a user. This is possible with **[Telethon](https://github.com/LonamiWebs/Telethon)**. This is the only way to manage channels like this, since you cannot add a bot to a channel unless you're an admin of the source channel._

## Prerequisites

- Python 3.6+
- [Telethon](https://github.com/LonamiWebs/Telethon) library

## Usage

1. Clone the repository:

   ```bash
   git clone https://github.com/TheFacc/Telegram-C2C.git
   ```

2. Install the required dependencies:

   ```bash
   pip install telethon
   ```

3. Create a `config.py` file containing the following variables, that will be imported by the main file:
   - `API_ID` and `API_HASH` (strings, your Telegram API credentials) taken from [my.telegram.org](https://my.telegram.org/)
   - `CHATS` (list of dictionaries): main data structure. Each element (dictionary) contains:
      - **required keys** (pair):
        - `sources` (list): multiple sources chat IDs
        - `target` (string): single target destination ID
      - **optional keys** (config) for group-specific setting:
        - `printSource` (bool, default True): append to the message text/caption a link to the original message
        - `printMediaCaption` (bool, default True): if True, for medias append the same caption, otherwise remove it
        - `bannedWords` (list of strings): ignore message if it contains a string from this list (for this pair only)
        - `includeWords` (list of strings): _forcefully_ include message if it contains a string from this list (for this pair only)(overrides ANY banned words and button setting!)
        - `ignoreAll` (bool, default False): ignore ALL messages, except those containing words present in `includeWords` (makes `bannedWords` useless)
        - `ignoreButtons` (bool, default False): False = ignore ALL messages containing buttons, True = override global setting that ignore buttons
    
    Global settings:
   - `BANNED_WORDS` (list of strings, optional): same as optional key, but globally for all pairs
   - `INCLUDE_WORDS` (list of strings, optional): same as optional key, but globally for all pairs
   - `IGNORE_BUTTONS` (bool, optional, default False): ignore message globally if it has buttons (common for spam messages)
   - `LOG_TO_CHAT` (string, optional, default empty): target ID of a chat (must be in the format `"telegram.me/+v12a34b56c"`) to log the bot behaviour (same as cli output). It will log ALL forwarded and ignored messages, text only, with the reason for ignoring.
   - `MARK_PROCESSED_AS_READ` (bool, optional, default False): mark source chat as read after forwarding/ignoring the message (note that only the new message will be processed, not all the unread messages! But the full chat will be marked as read. Forward history is todo.)
   The 'ID' can be numeric/handle/link/etc as shown below or in [Telethon documentation](https://docs.telethon.dev/en/stable/concepts/entities.html#getting-entities). You can get the numeric IDs (most reliable) of a chat by forwarding a message from that chat to [@getidsbot](https://t.me/getidsbot).
   
   **Note on the global/specific logic:** the global settings apply to all chats in general, but can be overridden by the group-specific setting with the same name.
   - Include is power: the local `includeWords` and the global `INCLUDE_WORDS` have priority over anything (they override also the local `ignoreAll`!)
   - Words include/ignore has the priority over button include/ignore (e.g. a message containing a banned word will not be forwarded, even if it has buttons and you set `includeButtons=True`)
   - The local `includeWords` overrides both the local `bannedWords`/`ignoreAll` and the global `BANNED_WORDS`
   - The local `ignoreButtons` overrides the global `IGNORE_BUTTONS` in all cases.

   Below is an example configuration. 

   ```python
   ### config.py ###
   # Account connection
   API_ID = YOUR_API_ID # '1234567'
   API_HASH = YOUR_API_HASH # 'd6s7687nm7hf5ndgb6d8ssv7dg'
   # Main data structure: list of dictionaries, each dict is a sources/destination pair, with additional optional settings for each couple
   CHATS = [
      { # first pair: four sources >> one destination
          'sources': [
              -100123333,    # source channel 1 (for destination 1)
              -100123334,    # source channel 2 (for destination 1)
              'some_handle', # source channel 3 (for destination 1)
              -100123456,    # source channel 4 (for destination 1)
          ],
          'target': 'myTargetUsername', # destination for pair 1
          # config example 1: skip messages containing banned words.
          'bannedWords': ['someword','banned from this pair only'] # optional
          'printSource': True, # optional
          'printMediaCaption': False, # optional
      },
      { # second pair: two sources >> one destination
          'sources': [
              -100123789,                # source channel 1 (for destination 2)
              'telegram.me/+v12a34b56c', # source channel 2 (for destination 2)
          ],
          'target': 'telegram.me/+dBRuc123456', # destination for pair 2
          # config example 2: skip all messages except those containing '#free'
          'ignoreAll': True,
          'includeWords': ['#free'],
      },
      { # third pair: one source >> one destination
          'sources': [
              -100123321, # source channel (for destination 3)
          ],
          'target': 'telegram.me/+dBRuc123456', # destination for pair 3
          # config example 3:
          # ...nothing >> it will use default values (i.e. forward all, print caption and source)
      },
      # ... as many pairs as you want
    ]
   # Global filtering options
   IGNORE_BUTTONS = True
   BANNED_WORDS = ['t.me','join now','giveaway','trading','🔥']
   INCLUDE_WORDS = ['if a message contains this','then forward it no matter what']
   # Additional options
   MARK_PROCESSED_AS_READ = True
   LOG_TO_CHAT = "https://t.me/+dBRuc123456"
   ```

4. Run the bot:

   ```bash
   python3 Telegram_C2C.py
   ```

5. It will ask for either your phone number or bot token. You have to enter your phone number in order for the bot to work (e.g. `+393456789000`), and confirm the code you receive. From this moment, the bot will store your session and behave as your user, based on the python code in this repo. Enjoy!

## Note for Nix users

I'm a NixOS user. If you know you know. Here's a Nix shell tailored to run this bot, just run `nix-shell shell_c2c.nix`:
```nix
# shell_c2c.nix
{ pkgs ? import <nixpkgs> {} }:

let
  c2c-python-packages = python-packages: with python-packages; [
    python-telegram-bot
    telethon
  ];
  python-c2c = pkgs.python310.withPackages c2c-python-packages;

in

  pkgs.mkShell {
    nativeBuildInputs = [
      python-c2c
    ];
}
```

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvement, please open an issue, submit a pull request, or [contact me](https://thefacc.github.io/).

## License

This project is licensed under the MIT License.
