from datetime import timezone
from discord import Embed, Member
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
cur = None


@bot.event
async def on_connect():
    global cur

    if cur is None:
        cur = conn.cursor()

        cur.execute("create table if not exists messages (message, author, channel, guild, delta)")
        conn.commit()


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

        cur.execute("insert into messages values (?, ?, ?, ?, ?)", (
            ctx.message.id,
            ctx.author.id,
            ctx.channel.id,
            ctx.guild.id,
            delta_ms,
        ))
        conn.commit()


@bot.command()
async def best(ctx, *, user: Member = None):
    if not ctx.guild and not user:
        user = ctx.author

    query = ["select message, author, channel, guild, delta from messages where"]
    parameters = []

    if user:
        title = f"{user.mention}'s best times"

        query.append("author = ? and")
        parameters.append(user.id)
    else:
        title = f"Best times"

    if ctx.guild:
        query.append("guild = ? and")
        parameters.append(ctx.guild.id)

    query.append("delta >= 0 order by delta limit 10")

    cur.execute(" ".join(query), parameters)

    lines = [f"**{title}**"]

    for i, (message, author, channel, guild, delta) in enumerate(cur.fetchall(), 1):
        url = f"https://discordapp.com/channels/{guild}/{channel}/{message}"

        if user:
            name = ""
        else:
            name = f"<@!{author}> "

        lines.append(f"{i}. {name}[{delta} ms]({url})")

    await ctx.send(embed=Embed(description="\n".join(lines)))


if __name__ == "__main__":
    import os, sqlite3

    conn = sqlite3.connect("bot.db")

    bot.run(os.environ["TOKEN"])
