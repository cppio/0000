from datetime import timezone
from discord.ext.commands import Bot, command

def get_prefix(bot, message):
    prefixes = ["0000 ", "0000"]

    if not message.guild:
        prefixes.append("")

    return prefixes


bot = Bot(get_prefix)

@command(hidden=True, ignore_extra=False)
async def delta(ctx):
    created_at = ctx.message.created_at.replace(tzinfo=timezone.utc).astimezone()
    timestamp = created_at.replace(tzinfo=timezone.utc).timestamp()

    nearest = 86400 if ctx.guild else 60

    delta = (timestamp + nearest / 2) % nearest - nearest / 2
    delta_ms = round(delta * 1000)

    if not ctx.guild:
        await ctx.send(f"{delta_ms} ms")
    elif -10000 < delta_ms < 60000:
        await ctx.send(f"{ctx.author.mention} {delta_ms} ms")

delta.name = ""

bot.add_command(delta)

if __name__ == "__main__":
    import os

    bot.run(os.environ["TOKEN"])
