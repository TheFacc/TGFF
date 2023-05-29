from telethon import TelegramClient, events
from config import API_ID, API_HASH, CHAT_IDS, TARGET_IDS, excluded_words

with TelegramClient('name', API_ID, API_HASH) as client:
    client.start()
    print("Client started!")
    print("Source IDs: ", CHAT_IDS)
    print("Target IDs: ", TARGET_IDS)

    @client.on(events.NewMessage(chats=sum(CHAT_IDS, []))) # Flatten CHAT_IDS for event filter
    async def my_event_handler(event):
        message = event.message
        message_txt = message.message

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
            if not any(word in message_txt.lower() for word in excluded_words):
                if message.media:
                    await client.send_file(target_id, message.media, caption=message_append, parse_mode='md') # remove original text for media
                else:
                    await client.send_message(target_id, message_txt+"\n\n"+message_append, parse_mode='md') # forward full text for non-media
            else:
                print("Dirty message ignored ;)")


    client.run_until_disconnected()