from telethon import TelegramClient, events
from datetime import datetime
import os, json # manage history of messages already processed since last uptime
import asyncio # manage async telethon calls (to get message history)

try:
    from config import API_ID, API_HASH # import connection data from config.py
except ImportError:
    print("ERROR: couldn't get API_ID or API_HASH from config.py. Make sure you have a config.py file in the same directory as this script.")
    exit()

try:
    from config import CHATS # import source/destination chats
except ImportError:
    print("ERROR: couldn't get CHATS from config.py. Make sure you have a config.py file in the same directory as this script.")
    exit()

for chat in CHATS:
    # check required fields
    if not 'sources' in chat or not 'sources':
        print("ERROR: one or more 'sources' fields is missing or empty in CHATS in config.py.")
        exit()
    if not 'target' in chat or not 'target':
        print("ERROR: one or more 'target' fields is missing or empty in CHATS in config.py.")
        exit()
    # set defaults for missing fields
    if not 'printSource' in chat:
        chat['printSource'] = True
    if not 'printMediaCaption' in chat:
        chat['printMediaCaption'] = True
    if not 'bannedWords' in chat:
        chat['bannedWords'] = []
    if not 'includeWords' in chat:
        chat['includeWords'] = []

try:
    from config import BANNED_WORDS # import global excluded words
except ImportError:
    print("Note: couldn't get BANNED_WORDS from config.py. Using default value (empty).")
    BANNED_WORDS = []
try:
    from config import INCLUDE_WORDS # import global forcefully-included words
except ImportError:
    print("Note: couldn't get INCLUDE_WORDS from config.py. Using default value (empty).")
    INCLUDE_WORDS = []

try: from config import IGNORE_BUTTONS
except ImportError: IGNORE_BUTTONS = False

try: from config import MARK_PROCESSED_AS_READ
except ImportError: MARK_PROCESSED_AS_READ = False

try: from config import LOG_TO_CHAT # Chat ID to log messages to (optional, same log as printed to console)
except ImportError: LOG_TO_CHAT = ""

# Core functions
async def print_chat_names(client):
    for chat in CHATS:
        target_entity = await client.get_entity(chat['target'])
        target_name = target_entity.title
        bannedWords = chat['bannedWords'] if 'bannedWords' in chat else []

        # if ignoreall but there are no includewords, then warning:
        if 'ignoreAll' in chat and chat['ignoreAll'] and len(chat['includeWords']) == 0:
            print(f"🔴 WARNING ⚠ group with target '{target_name}' is set to ignore all messages, but there are no includeWords set. This means that NO messages will be forwarded to the target chat.")
        else:
            print(f"🔵 All messages from the following chats will be forwarded to target chat >> {target_name}")
            if len(bannedWords) > 0:
                print(f"   > Group filtering active: messages containing these words will be ignored for this group: {bannedWords}")

            for chat_id in chat['sources']:
                try:
                    chat_entity = await client.get_entity(chat_id)
                    chat_name = chat_entity.title
                    print(f"    - {chat_name}")
                except:
                    print(f"    - ❌ Chat ID {chat_id} not found! Make sure your account is a member of this chat.")

    if IGNORE_BUTTONS:
        print("🟣 Global filtering active: any message containing BUTTONS will be ignored.")
    if len(BANNED_WORDS) > 0:
        print("🟣 Global filtering active: any message containing any of these WORDS will be ignored: ")
        badwords = ""
        for word in BANNED_WORDS:
            badwords += word + ", "
        print(f"    {badwords[:-2]}")

async def forward_message(client, message):
        message_txt = message.text

        # Get chat name
        chat_id = message.peer_id.channel_id
        chat_entity = await client.get_entity(chat_id)
        chat_name = chat_entity.title

        print("\n","_"*100)
        toprint = f"🆕 **New message from {chat_name} (ID:{chat_id}):\n🕓 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        # Find the index of the chat ID group in each sources group
        chat_group_index = next((i for i, chat_group in enumerate([chat['sources'] for chat in CHATS]) if any(str(chat_id) in str(chat) for chat in chat_group)), None)

        if chat_group_index is not None:
            CHAT = CHATS[chat_group_index]
            msgtxt = message.raw_text.lower()

            # INCLUDE logic (force):
            # - force forward if it contains includeWords
            bMessageHasIncludeWords = False
            for word in CHAT['includeWords'] + INCLUDE_WORDS:
                if word.lower() in msgtxt:
                    bMessageHasIncludeWords = True
                    break

            # IGNORE logic: (if not forcefully included by including words)
            if bMessageHasIncludeWords:
                bIgnoreMessage = False
            else:
                # -0- check if ignore all
                bIgnoreAll = 'ignoreAll' in CHAT and CHAT['ignoreAll']
                if bIgnoreAll:
                    bIgnoreMessage = True
                else:
                    # -1- check excluded words (global + group-specific)
                    banned_words_in_message = []
                    for word in BANNED_WORDS + CHAT['bannedWords']:
                        if word.lower() in msgtxt:
                            banned_words_in_message.append(word)
                    bMessageHasBannedWords = len(banned_words_in_message) > 0
                    if bMessageHasBannedWords: # has banned words, we dont even need to check buttons
                        bIgnoreMessage = True
                    else:
                        # -2- check buttons
                        if 'ignoreButtons' in CHAT: # a group-specific setting was set, so use that and override global button setting
                            bIgnoreButtons = CHAT['ignoreButtons']
                        else: # use global
                            bIgnoreButtons = IGNORE_BUTTONS
                        if bIgnoreButtons: # if we need to ignore buttons, check if the message has buttons
                            try:
                                amount_of_buttons = len(message.reply_markup.__dict__["rows"])
                                bMessageHasButtons = amount_of_buttons > 0
                                bIgnoreMessage = bMessageHasButtons
                            except:
                                bIgnoreMessage = False
                        else:
                            bIgnoreMessage = False

            # Build message/log text
            if CHAT['printSource']:
               message_src = f"\n\nSource: [{chat_name}](t.me/c/{chat_id}/{message.id})"
            else:
               message_src = ""

            if not bIgnoreMessage:
                # Get target chat name
                target_id = CHAT['target']
                target_entity = await client.get_entity(target_id)
                target_name = target_entity.title
                toprint += f"\n🔜 Forwarding to >> {target_name} ({target_id})...**"

                # Forward message
                if message.media:
                    if hasattr(message.media, 'webpage') and message.media.webpage:
                        # Handle messages with link previews separately
                        await client.send_message(target_id, message_txt+message_src, parse_mode='md')
                    else:
                        # For other media types, use send_file
                        await client.send_file(target_id, message.media, caption=(message_txt+message_src) if CHAT["printMediaCaption"] else message_src, parse_mode='md')
                else:
                    await client.send_message(target_id, message_txt+message_src, parse_mode='md') # forward full text for non-media
            else: # ignore message
                if bIgnoreAll:
                    toprint += f"\n🚫 ignored - group is set to ignore all messages, except those containing: {CHAT['includeWords']}**"
                elif bMessageHasBannedWords:
                    toprint += f"\n🚫 ignored - contains excluded words: {banned_words_in_message[0] if len(banned_words_in_message)==1 else banned_words_in_message}**"
                elif bMessageHasButtons:
                    toprint += "\n🚫 ignored - contains buttons)**"
                else:
                    toprint += "\n🚫 ignored ;)**"
            toprint += "\n\n" + message_txt
            print(toprint)
            if LOG_TO_CHAT:
                await client.send_message(LOG_TO_CHAT, toprint+message_src, parse_mode='md') # save log to private channel
            if MARK_PROCESSED_AS_READ:
                await client.send_read_acknowledge(entity=message.peer_id, message=message) # mark processed message as read

# Main program
with TelegramClient('name', API_ID, API_HASH) as client:
    client.start()
    print("****************************************************")
    print("**   Telegram C2C - Chat to Chat Forwarding bot   **")
    print("****************************************************")
    print("🟢 Client started!")
    client.loop.run_until_complete(print_chat_names(client))
    print("🟢 Listening...")

    @client.on(events.NewMessage(chats=sum([chat['sources'] for chat in CHATS],[]))) # Flatten all CHAT sources together, to manage events from all chats
    async def my_event_handler(event):
        message = event.message
        await forward_message(client=client, message=message)

    client.run_until_disconnected()
