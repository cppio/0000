from datetime import timezone
from discord.ext.commands import Bot, MinimalHelpCommand
from discord.utils import escape_mentions


def get_prefix(bot, message):
    prefixes = ["0000 ", "0000"]

    if not message.guild:
        prefixes.append("")

    return prefixes


class HelpCommand(MinimalHelpCommand):
    def __init__(self, **options):
        options.setdefault("no_category", "Commands")
        super().__init__(**options)

    def get_opening_note(self):
        return f"Use `{self.clean_prefix}{self.invoked_with} [command]` for more info on a command."


bot = Bot(get_prefix, HelpCommand())


@bot.event
async def on_command_error(ctx, error):
    await ctx.send(escape_mentions(str(error)))


@bot.command(aliases=[""], hidden=True, ignore_extra=False)
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


if __name__ == "__main__":
    import os

    bot.run(os.environ["TOKEN"])
