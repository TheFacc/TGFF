from telethon import TelegramClient, events

try:
    from config import API_ID, API_HASH # import connection data from config.py
except ImportError:
    print("ERROR: couldn't get API_ID or API_HASH from config.py. Make sure you have a config.py file in the same directory as this script.")
    exit()

try:
    from config import CHAT_IDS, TARGET_IDS # import source/destination chats
except ImportError:
    print("ERROR: couldn't get CHAT_IDS or TARGET_IDS from config.py. Make sure you have a config.py file in the same directory as this script.")
    exit()

try:
    from config import EXCLUDED_WORDS # import global excluded words
except ImportError:
    print("Note: couldn't get EXCLUDED_WORDS from config.py. Using default value.")
    EXCLUDED_WORDS = []

try:
    from config import EXCLUDED_WORDS_GROUP # import excluded words for each chat gorup
except ImportError:
    print("Note: couldn't get EXCLUDED_WORDS_GROUP from config.py. Using default value.")
    EXCLUDED_WORDS_GROUP = []

import os, json # manage history of messages already processed since last uptime
import asyncio # manage async telethon calls (to get message history)

ignore_messages_with_buttons = True

# Core functions
async def print_chat_names(client):
    for chat_group, target_id in zip(CHAT_IDS, TARGET_IDS):
        target_entity = await client.get_entity(target_id)
        target_name = target_entity.title
        print(f"🔵 All messages from the following chats will be forwarded to target chat >> {target_name}")
        for chat_id in chat_group:
            try:
                chat_entity = await client.get_entity(chat_id)
                chat_name = chat_entity.title
                print(f"    - {chat_name}")
            except:
                print(f"    - ❌ Chat ID {chat_id} not found! Make sure your account is a member of this chat.")
    print("🟣 Messages containing these words will be ignored: ")
    badwords = ""
    for word in EXCLUDED_WORDS:
        badwords += word + ", "
    print(f"    {badwords[:-2]}")

async def forward_message(client, message):
        message_txt = message.text

        # Get chat name
        chat_id = message.peer_id.channel_id
        chat_entity = await client.get_entity(chat_id)
        chat_name = chat_entity.title

        print(f"🆕 New message received from {chat_name} (ID:{chat_id}):\n" + message_txt)

        # Find the index of the chat ID group in CHAT_IDS
        chat_group_index = next((i for i, chat_group in enumerate(CHAT_IDS) if any(str(chat_id) in str(chat) for chat in chat_group)), None)

        if chat_group_index is not None:
            # Ignoring logic:
            # - buttons
            try:
                amount_of_buttons = len(message.reply_markup.__dict__["rows"])
                bMessageHasButtons = ignore_messages_with_buttons and amount_of_buttons > 0
            except:
                bMessageHasButtons = False
            # - excluded words (global)
            msgtxt = message.raw_text.lower()
            excluded_words_in_message = []
            for word in EXCLUDED_WORDS:
                if word in msgtxt:
                    excluded_words_in_message.append(word)
            # - excluded words (group specific)
            if len(EXCLUDED_WORDS_GROUP) > chat_group_index:
                for word in EXCLUDED_WORDS_GROUP[chat_group_index]:
                    if word in msgtxt:
                        excluded_words_in_message.append(word)
            bMessageHasWords = len(excluded_words_in_message) > 0

            bIgnoreMessage = bMessageHasButtons or bMessageHasWords

            if not bIgnoreMessage:
            # if chat_group_index is not None:
                # Get target chat name
                target_id = TARGET_IDS[chat_group_index]
                target_entity = await client.get_entity(target_id)
                target_name = target_entity.title
                print(f"🔜 Forwarding to >> {target_name}...")

                # Build message append
                message_append = f"Source: [{chat_name}](t.me/c/{chat_id}/{message.id})"

                # Forward message
                if message.media:
                    if hasattr(message.media, 'webpage') and message.media.webpage:
                        # Handle messages with link previews separately
                        await client.send_message(target_id, message_txt+"\n\n"+message_append, parse_mode='md')
                    else:
                        # For other media types, use send_file
                        await client.send_file(target_id, message.media, caption=message_append, parse_mode='md') # remove original caption for media
                else:
                    await client.send_message(target_id, message_txt+"\n\n"+message_append, parse_mode='md') # forward full text for non-media
            else:
                if bMessageHasWords:
                    print(f"🚫 Message ignored - contains excluded words: {excluded_words_in_message}")
                elif bMessageHasButtons:
                    print(f"🚫 Message ignored - contains buttons)")
                else:
                    print("🚫 Message ignored ;)")

# Main program
with TelegramClient('name', API_ID, API_HASH) as client:
    client.start()
    print("****************************************************")
    print("**   Telegram C2C - Chat to Chat Forwarding bot   **")
    print("****************************************************")
    print("🟢 Client started!")
    client.loop.run_until_complete(print_chat_names(client))
    print("🟢 Listening...")

    @client.on(events.NewMessage(chats=sum(CHAT_IDS, []))) # Flatten CHAT_IDS for event filter
    async def my_event_handler(event):
        message = event.message
        await forward_message(client=client, message=message)
        
    client.run_until_disconnected()