# Telegram C2C - Chat to Chat Forwarding Bot

This Telegram bot allows you to forward messages from multiple source chats to multiple destination chats (not strictly channels). It is built using Python and the Telethon library.

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

3. Create a `config.py` file and add your Telegram API credentials (these are just examples, use your own! Get API/Hash from [here](https://my.telegram.org/) and IDs from [@getidsbot](t.me/getidsbot)):

   ```python
   API_ID = YOUR_API_ID # '1234567'
   API_HASH = YOUR_API_HASH # 'd6s7687nm7hf5ndgb6d8ssv7dg'
   CHAT_IDS = [
     [-1001112223333, -1001112223334] # source group 1
     [-1001112223335] # source group 2
   ]
   TARGET_IDS = [
     'mychannel1' # destination chat 1
     'mychannel2' # destination chat 2
   ]
   # Ignore messages containing any of these words
   excluded_words = ['t.me','joinchat','amazon','prezz','🔥']
   ```

4. Run the bot:

   ```bash
   python Telegram_C2C.py
   ```

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvement, please open an issue or submit a pull request.

## License

This project is licensed under the [MIT License](LICENSE).