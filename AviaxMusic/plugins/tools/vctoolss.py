import time  # For tracking join/leave times
from AviaxMusic import app  # Assuming 'app' is an instance of Client from AviaxMusic
from pyrogram.raw.types import UpdateGroupCallParticipants
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Dictionary to store join times
join_times = {}

# Notifications are enabled by default
notifications_enabled = True

# Listen for raw updates (voice chat participant changes)
@app.on_raw_update()
async def vc_participants_updated(client, update, users, chats):
    global join_times, notifications_enabled

    if not notifications_enabled:
        return

    # Check if the update is about group call participants
    if isinstance(update, UpdateGroupCallParticipants):
        try:
            chat_id = None
            if update.group_call and update.group_call.channel_id in chats:
                chat_id = chats[update.group_call.channel_id].id
            if not chat_id:
                return

            # Try to fetch the chat invite link
            invite_link = await client.export_chat_invite_link(chat_id)

            text_join = "**🎉 #JoinVideoChat 🎉**\n\n"
            text_leave = "**😢 #LeftVideoChat 😢**\n\n"
            join_flag = False
            leave_flag = False

            for participant in update.participants:
                user_id = participant.user_id
                user = users.get(user_id)
                
                # Skip if user information is missing
                if not user:
                    continue

                # Participant joined
                if participant.joined_date:
                    join_flag = True
                    join_times[user_id] = time.time()
                    text_join += (
                        f"**Name:** {user.first_name}\n"
                        f"**ID:** `{user_id}`\n"
                        f"**Action:** Joined\n\n"
                    )
                
                # Participant left
                elif participant.can_be_muted is False:  # Indicates left or removed
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

            # Send notifications for join/leave events
            if join_flag:
                await client.send_message(
                    chat_id,
                    text_join,
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("🔗 Join the Video Chat", url=invite_link)]]
                    ),
                )
            if leave_flag:
                await client.send_message(
                    chat_id,
                    text_leave,
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("🔗 Rejoin the Video Chat", url=invite_link)]]
                    ),
                )

        except Exception as e:
            print(f"Error: {e}")
