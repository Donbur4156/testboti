import interactions as di
from interactions.api.models.flags import Intents
from interactions.ext.persistence import *
import logging

import config as c
import buttons as b

TOKEN = c.token
pres = di.PresenceActivity(
    type=di.PresenceActivityType.GAME,
    name="/help test"
)
bot = di.Client(token=TOKEN, intents=Intents.ALL | Intents.GUILD_MESSAGE_CONTENT, disable_sync=c.disable_sync, presence=di.ClientPresence(activities=[pres]))
logging.basicConfig(filename=c.logdir + c.logfilename, level=c.logginglevel, format='%(levelname)s - %(asctime)s: %(message)s', datefmt='%d.%m.%Y %H:%M:%S')
commandchannel = None
bot.load("interactions.ext.persistence", cipher_key=c.cipher_key)
bot.load("shedules")

@bot.event
async def on_ready():
    print("online")

@bot.command(
    name="test",
    description="Test Command"
)
async def test(ctx: di.CommandContext):
    await ctx.send(f"Hallo {ctx.author.name}")

@bot.command(
    name="buttons",
    description="Erzeugt 2 Buttons",
    options=[
        di.Option(
        name="number",
        type=di.OptionType.INTEGER,
        description="Gib eine Zahl ein",
        required=True
        )
    ]
)
async def buttons(ctx: di.CommandContext, number: int):
    but_plus = b.button_plus(bot=bot, number=number)
    but_min = b.button_min(bot=bot, number=number)
    row = di.ActionRow(components=[but_plus, but_min])
    await ctx.send(f"Die Zahl ist **{number}**", components=row)

@bot.persistent_modal("test")
@bot.persistent_component("but_min")
@bot.persistent_component("but_plus")
async def button_math(ctx: di.CommandContext, package: int):
    number = package
    but_plus = b.button_plus(bot=bot, number=number)
    but_min = b.button_min(bot=bot, number=number)
    row = di.ActionRow(components=[but_plus, but_min])
    await ctx.edit(f"Die Zahl ist **{number}**", components=row)


if __name__ == "__main__":
    bot.start()
