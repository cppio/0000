from datetime import datetime, timezone
from discord import Embed, Member
from discord.ext.commands import Bot, guild_only, MemberConverter, MinimalHelpCommand, TooManyArguments
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


def calc_score(delta_ms):
    delta = delta_ms / 1000
    return round(200 - 5 / 3 * delta + 800 / 16 ** delta)


@bot.event
async def on_connect():
    global cur

    if cur is None:
        conn.create_function("score", 1, calc_score, deterministic=True)

        cur = conn.cursor()

        cur.execute("create table if not exists messages (message, author, channel, guild, delta, target)")
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
        target = round(timestamp - delta)

        cur.execute("select count(*) from messages where author = ? and guild = ? and target = ?", (
            ctx.author.id,
            ctx.guild.id,
            target,
        ))

        previous, = cur.fetchone()

        if previous or delta_ms < 0:
            points = ""
        else:
            suffix = "!" * (5 - delta_ms // 200)
            points = f" **(+{calc_score(delta_ms)} points{suffix})**"

        cur.execute("insert into messages values (?, ?, ?, ?, ?, ?)", (
            ctx.message.id,
            ctx.author.id,
            ctx.channel.id,
            ctx.guild.id,
            delta_ms,
            target,
        ))
        conn.commit()

        await ctx.send(f"{ctx.author.mention} {delta_ms} ms{points}")


@bot.command()
async def best(ctx, *, user=None):
    if ctx.guild:
        user = user and await MemberConverter().convert(ctx, user)
    elif user:
        raise TooManyArguments(f"Too many arguments passed to best")
    else:
        user = ctx.author

    query = ["select message, author, channel, guild, delta, target from messages where"]
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

    for i, (message, author, channel, guild, delta, target) in enumerate(cur.fetchall(), 1):
        url = f"https://discordapp.com/channels/{guild}/{channel}/{message}"

        name = "" if user else f"<@!{author}> "

        lines.append(f"{i}. {name}[{delta} ms]({url}) on {datetime.utcfromtimestamp(target).date()}")

    await ctx.send(embed=Embed(description="\n".join(lines)))


@bot.command(ignore_extra=False)
@guild_only()
async def top(ctx):
    inner = "select author, score(min(delta)) as scores from messages where guild = ? group by author, target having min(delta) >= 0"

    cur.execute(f"select author, sum(scores) from ({inner}) group by author order by sum(scores) desc limit 10", (
        ctx.guild.id,
    ))

    lines = ["**Top scores**"]

    for i, (author, score) in enumerate(cur.fetchall(), 1):
        lines.append(f"{i}. <@!{author}> {score}")

    await ctx.send(embed=Embed(description="\n".join(lines)))


@bot.command()
@guild_only()
async def score(ctx, *, user: Member = None):
    user = user or ctx.author

    inner = "select score(min(delta)) as scores from messages where author = ? and guild = ? group by target having min(delta) >= 0"

    cur.execute(f"select sum(scores) from ({inner})", (
        user.id,
        ctx.guild.id,
    ))

    score, = cur.fetchone()

    await ctx.send(embed=Embed(description=f"{user.mention} has a score of {score or 0}"))


if __name__ == "__main__":
    import os, sqlite3

    conn = sqlite3.connect("bot.db")

    bot.run(os.environ["TOKEN"])
