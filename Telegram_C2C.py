from telethon import TelegramClient, events
from config import API_ID, API_HASH, CHAT_IDS, TARGET_IDS, excluded_words

with TelegramClient('name', API_ID, API_HASH) as client:
    client.start()
    print("Client created!")

    @client.on(events.NewMessage(chats=sum(CHAT_IDS, []))) # Flatten CHAT_IDS for event filter
    async def my_event_handler(event):
        message = event.message
        message_txt = message.message

        # Get chat name
        chat_id = message.peer_id.channel_id
        chat_entity = await client.get_entity(chat_id)
        chat_name = chat_entity.title

        # Find the index of the chat ID group in CHAT_IDS
        chat_group_index = next((i for i, chats in enumerate(CHAT_IDS) if str(message.peer_id.channel_id) in str(chats[i])), None)

        print(f"New message received from {chat_name} (ID:{chat_id}, Group:{chat_group_index}): " + message_txt)

        if chat_group_index is not None:
            # Retrieve the destination chat ID for the chat group
            target_id = TARGET_IDS[chat_group_index]

            # Build message append
            message_append = f"Source: [{chat_name}](t.me/c/{chat_id}/{message.id})"

            # Ignore messages containing excluded words
            if not any(word in message_txt.lower() for word in excluded_words):
                if message.media:
                    caption = utils.parse_mode(message_append, 'md')
                    await client.send_file(target_id, message.media, caption=caption) # remove original text for media
                else:
                    await client.send_message(target_id, message_txt+"\n\n"+message_append, parse_mode='md') # forward full text for non-media
            else:
                print("Dirty message ignored ;)")


    client.run_until_disconnected()