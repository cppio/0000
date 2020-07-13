from datetime import timezone
from discord import Client


class Bot(Client):
    async def on_message(self, message):
        if message.author.bot:
            return

        if not message.guild:
            delta = (message.created_at.timestamp() + 30) % 60 - 30

            await message.channel.send(f"{delta * 1000:.0f} ms")
        elif message.content == "0000":
            created_at = message.created_at.replace(tzinfo=timezone.utc).astimezone()
            timestamp = created_at.replace(tzinfo=timezone.utc).timestamp()
            delta = (timestamp + 43200) % 86400 - 43200
            delta_ms = round(delta * 1000)

            if -10000 < delta_ms < 60000:
                await message.channel.send(f"{message.author.mention} {delta_ms} ms")


if __name__ == "__main__":
    import os

    Bot().run(os.environ["TOKEN"])
