from telethon import TelegramClient, events

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
    from config import INCLUDE_WORDS # import global excluded words
except ImportError:
    print("Note: couldn't get INCLUDE_WORDS from config.py. Using default value (empty).")
    INCLUDE_WORDS = []

try: from config import IGNORE_BUTTONS
except ImportError: IGNORE_BUTTONS = False

import os, json # manage history of messages already processed since last uptime
import asyncio # manage async telethon calls (to get message history)

# Core functions
async def print_chat_names(client):
    for chat in CHATS:
        target_entity = await client.get_entity(chat['target'])
        target_name = target_entity.title
        bannedWords = chat['bannedWords'] if 'bannedWords' in chat else []

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
        print("🟣 Global filtering active: any message containing buttons will be ignored.")
    if len(BANNED_WORDS) > 0:
        print("🟣 Global filtering active: any message containing any of these words will be ignored: ")
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

        toprint = f"🆕 New message received from {chat_name} (ID:{chat_id}): "

        # Find the index of the chat ID group in each sources group
        chat_group_index = next((i for i, chat_group in enumerate([chat['sources'] for chat in CHATS]) if any(str(chat_id) in str(chat) for chat in chat_group)), None)

        if chat_group_index is not None:
            CHAT = CHATS[chat_group_index]
            msgtxt = message.raw_text.lower()
            # Including logic (force):
            bMessageHasIncludeWords = False
            for word in CHAT['includeWords'] + INCLUDE_WORDS:
                if word.lower() in msgtxt:
                    bMessageHasIncludeWords = True
                    # bMessageHasButtons = False # ignore buttons
                    # bMessageHasBannedWords = False # ignore banned words
                    break
            # Ignoring logic: (if not forcefully included)
            bIgnoreMessage = False
            if not bMessageHasIncludeWords:
                # - check if ignore all
                bIgnoreAll = 'ignoreAll' in CHAT and CHAT['ignoreAll']
                if bIgnoreAll:
                    bIgnoreMessage = True
                else:
                    # - check buttons
                    try:
                        amount_of_buttons = len(message.reply_markup.__dict__["rows"])
                        bMessageHasButtons = IGNORE_BUTTONS and amount_of_buttons > 0
                    except:
                        bMessageHasButtons = False
                    # - check excluded words (global + group-specific)
                    banned_words_in_message = []
                    for word in BANNED_WORDS + CHAT['bannedWords']:
                        if word.lower() in msgtxt:
                            banned_words_in_message.append(word)
                    bMessageHasBannedWords = len(banned_words_in_message) > 0
                    bIgnoreMessage = bMessageHasButtons or bMessageHasBannedWords

            if not bIgnoreMessage or bMessageHasIncludeWords:
            # if chat_group_index is not None:
                # Get target chat name
                target_id = CHAT['target']
                target_entity = await client.get_entity(target_id)
                target_name = target_entity.title
                print(toprint + f"🔜 Forwarding to >> {target_name}...")

                # Build message text
                if CHAT['printSource']:
                    message_src = f"\n\nSource: [{chat_name}](t.me/c/{chat_id}/{message.id})"
                else:
                    message_src = ""

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
            else:
                if bIgnoreAll:
                    print(toprint + f"🚫 ignored - group is set to ignore all messages, except those containing: {CHAT['includeWords']}")
                elif bMessageHasBannedWords:
                    print(toprint + f"🚫 ignored - contains excluded words: {banned_words_in_message[0] if len(banned_words_in_message)==1 else banned_words_in_message}")
                elif bMessageHasButtons:
                    print(toprint + "🚫 ignored - contains buttons)")
                else:
                    print(toprint + "🚫 ignored ;)")
            print(message_txt)
            await client.send_read_acknowledge(entity=message.peer_id, message=message) # mark as read and also forwards all the previously unreads...?

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
