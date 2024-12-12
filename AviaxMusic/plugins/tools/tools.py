from pyrogram import Client
from pyrogram.raw.types import UpdateGroupCallParticipants
from pyrogram.types import Message


@app.on_raw_update()
async def handle_video_chat_participants(client, update, users, chats):
    if isinstance(update, UpdateGroupCallParticipants):
        try:
            # `chat_id` and participant details
            chat_id = next(iter(chats.values())).id  # Extract chat ID from the raw update
            participants = update.participants

            for participant in participants:
                if participant.just_joined:  # Participant joined
                    user = await client.get_users(participant.user_id)
                    text = f"🎉 #JoinVideoChat 🎉\n\n**Name**: {user.mention}\n**Action**: Joined\n\n"
                    await client.send_message(chat_id, text)
                elif participant.left:  # Participant left
                    user = await client.get_users(participant.user_id)
                    text = f"😕 #LeftVideoChat 😕\n\n**Name**: {user.mention}\n**Action**: Left\n\n"
                    await client.send_message(chat_id, text)
        except Exception as e:
            print(f"Error handling participants: {e}")
