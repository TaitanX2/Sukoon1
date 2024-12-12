import time  # For tracking join/leave times
from AviaxMusic import app  # Assuming 'app' is an instance of Client from AviaxMusic
from pyrogram.raw.types import UpdateGroupCallParticipants
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram import filters
from AviaxMusic.utils.database import get_assistant
from config import OWNER_ID
from telethon.tl.functions.phone import (
    CreateGroupCallRequest,
    DiscardGroupCallRequest,
    GetGroupCallRequest,
    InviteToGroupCallRequest,
)

# Dictionary to store join times
join_times = {}

# Notifications are enabled by default
notifications_enabled = True

# Handle participant updates (join/leave events)
@app.on_raw_update()
async def vc_participants_updated(client, update, users, chats):
    global join_times, notifications_enabled

    if not notifications_enabled or not isinstance(update, UpdateGroupCallParticipants):
        return

    try:
        chat_id = None
        if update.group_call and update.group_call.channel_id in chats:
            chat_id = chats[update.group_call.channel_id].id

        if not chat_id:
            print("Chat ID not found in the update!")
            return

        try:
            invite_link = await client.export_chat_invite_link(chat_id)
        except Exception as e:
            print(f"Failed to fetch invite link: {e}")
            invite_link = None

        text_join, text_leave = "**🎉 #JoinVideoChat 🎉**\n\n", "**😢 #LeftVideoChat 😢**\n\n"
        join_flag, leave_flag = False, False

        for participant in update.participants:
            user_id = participant.user_id
            user = users.get(user_id, await client.get_users(user_id))

            if participant.joined_date:
                join_flag = True
                join_times[user_id] = time.time()
                text_join += f"**Name:** {user.first_name}\n**ID:** `{user_id}`\n**Action:** Joined\n\n"

            elif hasattr(participant, 'left_date') and participant.left_date:
                leave_flag = True
                join_time = join_times.pop(user_id, None)
                duration = time.time() - join_time if join_time else 0
                formatted_duration = time.strftime("%H:%M:%S", time.gmtime(duration)) if join_time else "Unknown"
                text_leave += f"**Name:** {user.first_name}\n**ID:** `{user_id}`\n**Action:** Left\n**Time Spent:** {formatted_duration}\n\n"

        if join_flag:
            await client.send_message(
                chat_id, text_join, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Join the Video Chat", url=invite_link)]] if invite_link else [])
            )
        if leave_flag:
            await client.send_message(
                chat_id, text_leave, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Rejoin the Video Chat", url=invite_link)]] if invite_link else [])
            )
    except Exception as e:
        print(f"Error while processing update: {e}")

# Video chat started notification
@app.on_message(filters.video_chat_started)
async def video_chat_started(_, msg):
    await msg.reply("**😍 ᴠɪᴅᴇᴏ ᴄʜᴀᴛ sᴛᴀʀᴛᴇᴅ 🥳**")

# Video chat ended notification
@app.on_message(filters.video_chat_ended)
async def video_chat_ended(_, msg):
    await msg.reply("**😕 ᴠɪᴅᴇᴏ ᴄʜᴀᴛ ᴇɴᴅᴇᴅ 💔**")

# Invite members to video chat
@app.on_message(filters.video_chat_members_invited)
async def invite_members_to_vc(_, message: Message):
    text = f"➻ {message.from_user.mention}\n\n**๏ Inviting in VC to:**\n\n"
    for user in message.video_chat_members_invited.users:
        text += f"[{user.first_name}](tg://user?id={user.id}) "

    try:
        invite_link = await app.export_chat_invite_link(message.chat.id)
        add_link = f"https://t.me/{app.username}?startgroup=true"
        await message.reply(
            f"{text} 🤭🤭",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("๏ Join VC ๏", url=add_link)]]),
        )
    except Exception as e:
        print(f"Error: {e}")

# Math command
@app.on_message(filters.command("math", prefixes="/"))
def calculate_math(_, message):
    try:
        expression = message.text.split("/math ", 1)[1]
        result = eval(expression)
        response = f"ᴛʜᴇ ʀᴇsᴜʟᴛ ɪs : {result}"
    except:
        response = "ɪɴᴠᴀʟɪᴅ ᴇxᴘʀᴇssɪᴏɴ"
    message.reply(response)

# Google search
@app.on_message(filters.command(["spg"], ["/", "!", "."]))
async def google_search(_, message):
    import aiohttp  # Importing aiohttp for HTTP requests
    import re  # Import regex for URL handling

    search_query = " ".join(message.command[1:])
    if not search_query:
        return await message.reply("Please provide a search query!")

    msg = await message.reply("Searching...")
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://content-customsearch.googleapis.com/customsearch/v1",
            params={"q": search_query, "key": "YOUR_GOOGLE_API_KEY", "cx": "YOUR_SEARCH_ENGINE_ID"},
        ) as r:
            response = await r.json()
            if not response.get("items"):
                return await msg.edit("No results found!")

            results = ""
            for item in response["items"]:
                title, link = item["title"], item["link"]
                link = re.sub(r"\/\d|\/s", "", link.split("?")[0])  # Clean URLs
                results += f"{title}\n{link}\n\n"

            await msg.edit(results[:4000], disable_web_page_preview=True)  # Telegram has a 4096-char limit.
