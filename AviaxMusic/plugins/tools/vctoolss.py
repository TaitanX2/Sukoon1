import time  # For tracking join/leave times
from AviaxMusic import app  # Assuming 'app' is an instance of Client from AviaxMusic
from pyrogram.raw.types import UpdateGroupCallParticipants
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Dictionary to store join times
join_times = {}

# Notifications are enabled by default
notifications_enabled = True

@app.on_raw_update()
async def vc_participants_updated(client, update, users, chats):
    """
    Handles updates related to participants joining or leaving group voice/video chats.
    """
    global join_times, notifications_enabled

    # Check if notifications are enabled
    if not notifications_enabled:
        return

    # Check if the update is about group call participants
    if not isinstance(update, UpdateGroupCallParticipants):
        return

    try:
        # Retrieve chat ID from the update
        chat_id = None
        if update.group_call and update.group_call.channel_id in chats:
            chat_id = chats[update.group_call.channel_id].id

        if not chat_id:
            print("Chat ID not found in the update!")
            return

        # Try to fetch the chat invite link
        try:
            invite_link = await client.export_chat_invite_link(chat_id)
        except Exception as e:
            print(f"Failed to fetch invite link: {e}")
            invite_link = None

        text_join = "**🎉 #JoinVideoChat 🎉**\n\n"
        text_leave = "**😢 #LeftVideoChat 😢**\n\n"
        join_flag = False
        leave_flag = False

        for participant in update.participants:
            user_id = participant.user_id
            user = users.get(user_id)

            # Fetch user info if not available in the `users` dictionary
            if not user:
                try:
                    user = await client.get_users(user_id)
                except Exception as e:
                    print(f"Failed to fetch user info for {user_id}: {e}")
                    continue

            # Check if the participant has joined
            if participant.joined_date:
                join_flag = True
                join_times[user_id] = time.time()
                text_join += (
                    f"**Name:** {user.first_name}\n"
                    f"**ID:** `{user_id}`\n"
                    f"**Action:** Joined\n\n"
                )

            # Check if the participant has left
            elif hasattr(participant, 'left_date') and participant.left_date:
                leave_flag = True
                join_time = join_times.pop(user_id, None)
                if join_time:
                    duration = time.time() - join_time
                    formatted_duration = time.strftime("%H:%M:%S", time.gmtime(duration))
                    text_leave += (
                        f"**Name:** {user.first_name}\n"
                        f"**ID:** `{user_id}`\n"
                        f"**Action:** Left\n"
                        f"**Time Spent:** {formatted_duration}\n\n"
                    )
                else:
                    text_leave += (
                        f"**Name:** {user.first_name}\n"
                        f"**ID:** `{user_id}`\n"
                        f"**Action:** Left\n"
                        f"**Time Spent:** Unknown\n\n"
                    )

        # Send notifications for join events
        if join_flag:
            await client.send_message(
                chat_id,
                text_join,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔗 Join the Video Chat", url=invite_link)]]
                    if invite_link else []
                ),
            )

        # Send notifications for leave events
        if leave_flag:
            await client.send_message(
                chat_id,
                text_leave,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔗 Rejoin the Video Chat", url=invite_link)]]
                    if invite_link else []
                ),
            )

    except Exception as e:
        print(f"Error while processing update: {e}")
