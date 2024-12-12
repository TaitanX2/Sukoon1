import time  # For tracking join/leave times
from AviaxMusic import app  # Assuming 'app' is an instance of Client from AviaxMusic
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram import filters
from config import OWNER_ID
import aiohttp
import re

# Participant join/leave handlers
@app.on_message(filters.video_chat_members_joined)
async def joined_members_to_vc(_, message: Message):
    text = f"🎉 #JoinVideoChat 🎉\n\n**Name**: {message.from_user.mention}\n**Action**: Joined\n\n"
    await message.reply(text)

@app.on_message(filters.video_chat_members_left)
async def leave_members_to_vc(_, message: Message):
    text = f"🎉 #LeftVideoChat 🎉\n\n**Name**: {message.from_user.mention}\n**Action**: Left\n\n"
    await message.reply(text)

# Video chat started notification
@app.on_message(filters.video_chat_started)
async def video_chat_started(_, message: Message):
    await message.reply("**😍 Video chat started 🥳**")

# Video chat ended notification
@app.on_message(filters.video_chat_ended)
async def video_chat_ended(_, message: Message):
    await message.reply("**😕 Video chat ended 💔**")

# Invite members to video chat
@app.on_message(filters.video_chat_members_invited)
async def invite_members_to_vc(_, message: Message):
    invited_users = [
        f"[{user.first_name}](tg://user?id={user.id})" for user in message.video_chat_members_invited.users
    ]
    text = f"**{message.from_user.mention} invited:**\n" + "\n".join(invited_users)
    try:
        invite_link = await app.export_chat_invite_link(message.chat.id)
        add_link = f"https://t.me/{app.username}?startgroup=true"
        await message.reply(
            text,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Join VC", url=add_link)]]
            ),
        )
    except Exception as e:
        await message.reply(f"Error creating invite link: {e}")

# Math command
@app.on_message(filters.command("math", prefixes="/"))
async def calculate_math(_, message):
    from sympy import sympify

    try:
        expression = message.text.split("/math ", 1)[1]
        result = sympify(expression)
        await message.reply(f"ᴛʜᴇ ʀᴇsᴜʟᴛ ɪs : `{result}`")
    except Exception as e:
        await message.reply(f"Invalid expression: {e}")

# Google search
@app.on_message(filters.command(["spg"], ["/", "!", "."]))
async def google_search(_, message):
    search_query = " ".join(message.command[1:])
    if not search_query:
        return await message.reply("Please provide a search query!")

    msg = await message.reply("Searching...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://content-customsearch.googleapis.com/customsearch/v1",
                params={"q": search_query, "key": "YOUR_GOOGLE_API_KEY", "cx": "YOUR_SEARCH_ENGINE_ID"},
                timeout=10,
            ) as r:
                response = await r.json()
                if not response.get("items"):
                    return await msg.edit("No results found!")

                results = ""
                for item in response["items"][:5]:  # Limit to 5 results
                    title, link = item["title"], item["link"]
                    results += f"🔗 **{title}**\n{link}\n\n"

                await msg.edit(results[:4000], disable_web_page_preview=True)
    except Exception as e:
        await msg.edit(f"Error occurred: {e}")
