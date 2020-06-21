import os

import discord
from discord import Message, Embed, Colour, User
from discord import TextChannel

bot_prefix = '!'
channel_id = 0


# noinspection PyMethodMayBeStatic
class Bot(discord.Client):

    async def on_ready(self):
        global bot_prefix, channel_id
        if os.path.isfile('PREFIX'):
            file_handle = open('PREFIX')
            bot_prefix = file_handle.readline()
            file_handle.close()

        if os.path.isfile('CHANNEL_ID'):
            file_handle = open('CHANNEL_ID')
            channel_id = int(file_handle.readline())
            file_handle.close()

    async def on_message(self, message: Message):
        global bot_prefix, channel_id
        message_string: str
        channel: TextChannel
        channel = message.channel

        if channel_id is not None and channel.id == channel_id and self.user.id != message.author.id:
            message_string = message.content
            message_author = message.author

            if message_string.startswith(bot_prefix):
                message_string = message_string[1:]
                split_command = message_string.split(' ')
                if len(split_command) > 0:
                    command = split_command[0].lower()
                    args = split_command[1:]

                    if command in ['start', 'stop', 'playerdata', 'help', 'prefix']:
                        if command == 'help':
                            await self.bot_response(channel=channel, author=message_author, result=self.command_help(), action=command.capitalize())
                        elif command == 'prefix':
                            await self.bot_response(channel=channel, author=message_author, result=self.command_prefix(args=args), action=command.capitalize())
                        elif command == 'start':
                            await self.bot_response(channel=channel, author=message_author, result=self.command_start(), action=command.capitalize())
                        elif command == 'stop':
                            await self.bot_response(channel=channel, author=message_author, result=self.command_stop(), action=command.capitalize())
                        elif command == 'playerdata':
                            await self.bot_response(channel=channel, author=message_author, result=self.command_playerdata(args=args), action=command.capitalize())
                        else:
                            await self.bot_response(channel=channel, author=message_author, result='Etwas ist schief gelaufen, bitte versuche es erneut')
                    else:
                        await self.bot_response(channel, message_author, 'Unbekanntes Kommando! benutze `{0}help` für eine Liste aller Kommandos.'.format(bot_prefix))

    async def bot_response(self, channel: TextChannel, author: User, result: str, action=None):
        embed = Embed(title=self.user.display_name + ' sagt', colour=Colour.blue())
        embed.add_field(name='Angefragt von:', value=author.display_name, inline=False)
        if action is not None:
            embed.add_field(name='Befehl:', value=action, inline=False)

        embed.add_field(name='Ergebnis:', value=result, inline=False)
        await channel.send(embed=embed)

    def command_help(self) -> str:
        return 'Folgende Kommands werden unterstützt:\n\n`{0}help`:    Zeigt die Hilfe an.\n\n`{0}prefix <neues Prefix>`:    Ändert das Prefix, welches der Bot verwendet.\n\n`{0}start`:    Startet den MC-Server, sofern er nicht bereits läuft.\n\n`{0}stop`:    Stoppt den server, sofern er läuft.\n\n`{0}playerdata <Name>`:    Löscht die Daten des angegebenen Spielers, wodurch er wieder mit leerem Inventar am Spawn spawnt.'.format(bot_prefix)

    def command_prefix(self, args: list) -> str:
        return 'prefix'

    def command_start(self) -> str:
        return 'start'

    def command_stop(self) -> str:
        return 'stop'

    def command_playerdata(self, args: list) -> str:
        return 'playerdata'


if os.path.isfile('BOT_TOKEN'):
    fh = open('BOT_TOKEN')
    token = fh.readline()
    fh.close()

    client = Bot()
    client.run(token)
else:
    print('Konnte Bot nicht starten!')
