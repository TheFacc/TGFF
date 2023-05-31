from telethon import TelegramClient, events
from config import API_ID, API_HASH, CHAT_IDS, TARGET_IDS, excluded_words # import data from config.py

async def print_chat_names(client):
    for chat_group, target_id in zip(CHAT_IDS, TARGET_IDS):
        target_entity = await client.get_entity(target_id)
        target_name = target_entity.title
        print(f"🔵 All messages from the following chats will be forwarded to target chat >> {target_name}")
        for chat_id in chat_group:
            chat_entity = await client.get_entity(chat_id)
            chat_name = chat_entity.title
            print(f"    - {chat_name}")
    print("🟣 Messages containing these words will be ignored: ")
    badwords = ""
    for word in excluded_words:
        badwords += word + ", "
    print(f"    {badwords[:-2]}")

async def forward_message(client, message):
        message_txt = message.text

        # Get chat name
        chat_id = message.peer_id.channel_id
        chat_entity = await client.get_entity(chat_id)
        chat_name = chat_entity.title

        # Find the index of the chat ID group in CHAT_IDS
        chat_group_index = next((i for i, chat_group in enumerate(CHAT_IDS) if any(str(chat_id) in str(chat) for chat in chat_group)), None)

        print(f"🆕 New message received from {chat_name} (ID:{chat_id}, Group:{chat_group_index}):\n" + message_txt)

        if chat_group_index is not None:
            # Retrieve the destination chat ID for the chat group
            target_id = TARGET_IDS[chat_group_index]

            # Build message append
            message_append = f"Source: [{chat_name}](t.me/c/{chat_id}/{message.id})"

            # Ignore messages containing excluded words
            if not any(word in message.raw_text.lower() for word in excluded_words):
                if message.media:
                    if message.media.webpage:
                        # Handle messages with link previews separately
                        await client.send_message(target_id, message_txt+"\n\n"+message_append, parse_mode='md')
                    else:
                        # For other media types, use send_file
                        await client.send_file(target_id, message.media, caption=message_append, parse_mode='md') # remove original text for media
                else:
                    await client.send_message(target_id, message_txt+"\n\n"+message_append, parse_mode='md') # forward full text for non-media
            else:
                print(" >> Dirty message ignored ;)")

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
        await forward_message(client=client, message=event.message)

    client.run_until_disconnected()