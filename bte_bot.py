import json
import os
import subprocess
from shutil import copyfile
from uuid import UUID

import discord
from discord import Message, Embed, Colour, User, TextChannel

from mcuuidButWorks.api import GetPlayerData


# noinspection PyMethodMayBeStatic
class Bot(discord.Client):
    _config = {}

    def __init__(self):
        super().__init__()
        self.load_config()
        self.run(self._config["token"])

    def save_config(self):
        with open('config.json', 'w') as config_file:
            json.dump(self._config, config_file, indent=4)

    def load_config(self):
        if not os.path.isfile('config.json'):
            copyfile('config.json.example', 'config.json')

        with open('config.json') as config_file:
            self._config = json.load(config_file)

    async def on_message(self, message: Message):
        channel_id = self._config["channel_id"]
        bot_prefix = self._config["prefix"]
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

                    if command in ['start', 'stop', 'status', 'playerdata', 'help', 'prefix', 'config']:
                        if command == 'help':
                            await self.bot_response(channel=channel, author=message_author, result=self.command_help(), action=command.capitalize())
                        elif command == 'prefix':
                            await self.bot_response(channel=channel, author=message_author, result=self.command_prefix(args=args), action=command.capitalize())
                        elif command == 'start':
                            await self.bot_response(channel=channel, author=message_author, result=self.command_start(), action=command.capitalize())
                        elif command == 'stop':
                            await self.bot_response(channel=channel, author=message_author, result=self.command_stop(), action=command.capitalize())
                        elif command == 'status':
                            await self.bot_response(channel=channel, author=message_author, result=self.command_status(), action=command.capitalize())
                        elif command == 'playerdata':
                            await self.bot_response(channel=channel, author=message_author, result=self.command_playerdata(args=args), action=command.capitalize())
                        elif command == 'config':
                            await self.bot_response(channel=channel, author=message_author, result=self.command_config(), action=command.capitalize())
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
        help_text = 'Folgende Kommandos werden unterstützt:\n\n'
        help_text += '`{0}config`:    Lädt die Konfiguration aus config.json neu.\n\n'
        help_text += '`{0}help`:    Zeigt die Hilfe an.\n\n'
        help_text += '`{0}playerdata <Name>`:    Löscht die Daten des angegebenen Spielers, wodurch er wieder mit leerem Inventar am Spawn spawnt.\n\n'
        help_text+= '`{0}prefix <neues Prefix>`:    Ändert das Prefix, welches der Bot verwendet.\n\n'
        help_text+= '`{0}start`:    Startet den MC-Server, sofern er nicht bereits läuft.\n\n'
        help_text += '`{0}status`:    Überprüft den aktuellen Serverstatus.\n\n'
        help_text  += '`{0}stop`:    Stoppt den Server, sofern er läuft.'

        return help_text.format(self._config['prefix'])

    def command_prefix(self, args: list) -> str:
        if len(args) > 0:
            new_prefix = args[0][0]
            self._config['prefix'] = new_prefix
            self.save_config()

            return 'Neues Prefix: ' + new_prefix
        else:
            return 'Kein neues Prefix angegeben.'

    def is_server_running(self) -> bool:
        screen_list = subprocess.Popen(["screen", "-list"], stdout=subprocess.PIPE, universal_newlines=True)
        grep_result = subprocess.Popen(["grep", "minecraft"], stdin=screen_list.stdout, stdout=subprocess.PIPE, universal_newlines=True)
        output, error = grep_result.communicate()

        return len(output) > 0

    def command_start(self) -> str:

        if self.is_server_running():
            return 'Server läuft bereits.'
        else:
            screen_command = ["screen", "-d", "-m", "-S", self._config['screen_name']]
            java_command = ["java"]
            java_command = java_command + self._config['java_args'].split(' ')
            java_command = java_command + ["-jar"]
            java_command = java_command + [self._config['server_file']]

            screen_command = screen_command + java_command

            subprocess.Popen(screen_command, cwd=os.path.dirname(os.path.realpath(self._config['server_file'])))

            return 'Server wurde gestartet.'

    def command_stop(self) -> str:
        if self.is_server_running():
            subprocess.Popen(["screen", "-S", self._config['screen_name'], "-X", "stuff", "stop^M"])

            return 'Server wurde beendet.'
        else:
            return 'Server läuft nicht.'

    def command_status(self) -> str:
        if self.is_server_running():
            return 'Server ist online.'
        else:
            return 'Server ist offline.'

    def command_playerdata(self, args: list) -> str:
        if len(args) > 0:
            player = GetPlayerData(args[0])

            if player.valid is True:
                server_path = os.path.dirname(self._config['server_file'])
                player_uuid = str(UUID(player.uuid))
                player_file = server_path + os.path.sep + self._config['world_name'] + os.path.sep + 'playerdata' + os.path.sep + player_uuid + '.dat'

                if os.path.isfile(player_file):
                    os.remove(player_file)

                    return 'Spielerdaten für {0} ({1}) erfolgreich gelöscht'.format(player.username, player.uuid)
                else:
                    return 'Keine Spielerdaten für {0} ({1}) gefunden.'.format(player.username, player_uuid)
            else:
                return 'Konnte Spieler mit der Kennung {0} nicht finden.'.format(args[0])
        else:
            return 'Du musst einen Spielernamen oder eine UUID angeben! `' + self._config['prefix'] + 'playerdata <Name oder UUID>`'

    def command_config(self) -> str:
        self.load_config()
        return 'Konfiguration erfolgreich geladen.'


Bot()
