import json
import os
import re
import shutil
from shutil import copyfile
from uuid import UUID

import discord
import paramiko
from discord import Message, Embed, Colour, User, TextChannel

from mcuuidButWorks.api import GetPlayerData


# noinspection PyMethodMayBeStatic
class Bot(discord.Client):
    _config: dict = {}

    def __init__(self):
        super().__init__()
        self.load_config()
        self.run(self._config["token"])

    def save_config(self):
        with open("config.json", "w") as config_file:
            json.dump(self._config, config_file, indent=4)

    def load_config(self):
        if not os.path.isfile("config.json"):
            copyfile("config.json.example", "config.json")

        with open("config.json") as config_file:
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
                split_command = message_string.split(" ")
                if len(split_command) > 0:
                    command = split_command[0].lower()
                    args = split_command[1:]

                    if command in ["start", "stop", "status", "playerdata", "help", "prefix", "config", "deleteworld"] and command not in self._config["forbidden_commands"]:
                        if command == "help":
                            await self.bot_response(channel=channel, author=message_author, result=self.command_help(), action=command.capitalize())
                        elif command == "prefix":
                            await self.bot_response(channel=channel, author=message_author, result=self.command_prefix(args=args), action=command.capitalize())
                        elif command == "start":
                            await self.bot_response(channel=channel, author=message_author, result=self.command_start(args=args), action=command.capitalize())
                        elif command == "stop":
                            await self.bot_response(channel=channel, author=message_author, result=self.command_stop(args=args), action=command.capitalize())
                        elif command == "status":
                            await self.bot_response(channel=channel, author=message_author, result=self.command_status(args=args), action=command.capitalize())
                        elif command == "playerdata":
                            await self.bot_response(channel=channel, author=message_author, result=self.command_playerdata(args=args), action=command.capitalize())
                        elif command == "config":
                            await self.bot_response(channel=channel, author=message_author, result=self.command_config(), action=command.capitalize())
                        elif command == "deleteworld":
                            await self.bot_response(channel=channel, author=message_author, result=self.command_deleteworld(args=args), action=command.capitalize())
                        else:
                            await self.bot_response(channel=channel, author=message_author, result="Etwas ist schief gelaufen, bitte versuche es erneut")
                    else:
                        await self.bot_response(channel, message_author, "Unbekanntes Kommando! benutze `{0}help` für eine Liste aller Kommandos.".format(bot_prefix))

    async def bot_response(self, channel: TextChannel, author: User, result: str, action=None):
        embed = Embed(title=self.user.display_name + " sagt", colour=Colour.blue())
        embed.add_field(name="Angefragt von:", value=author.display_name, inline=False)
        if action is not None:
            embed.add_field(name="Befehl:", value=action, inline=False)

        embed.add_field(name="Ergebnis:", value=result, inline=False)
        await channel.send(embed=embed)

    def command_help(self) -> str:
        help_text = "Folgende Kommandos werden unterstützt:\n\n"
        help_text += "`{0}config`:    Lädt die Konfiguration aus config.json neu.\n\n"
        help_text += "`{0}deleteworld <Server> <Name>`:    Löscht die angegebene Welt. **Dies kann nicht rückgängig gemacht werden!**\n\n"
        help_text += "`{0}help`:    Zeigt die Hilfe an.\n\n"
        help_text += "`{0}playerdata <Server> <Name>`:    Löscht die Daten des angegebenen Spielers, wodurch er wieder mit leerem Inventar am Spawn spawnt.\n\n"
        help_text += "`{0}prefix <neues Prefix>`:    Ändert das Prefix, welches der Bot verwendet.\n\n"
        help_text += "`{0}start <Server>`:    Startet den MC-Server, sofern er nicht bereits läuft.\n\n"
        help_text += "`{0}status <Server>`:    Überprüft den aktuellen Serverstatus.\n\n"
        help_text += "`{0}stop <Server>`:    Stoppt den Server, sofern er läuft."

        return help_text.format(self._config["prefix"])

    def command_prefix(self, args: list) -> str:
        if len(args) > 0:
            new_prefix = args[0][0]
            self._config["prefix"] = new_prefix
            self.save_config()

            return "Neues Prefix: " + new_prefix
        else:
            return "Kein neues Prefix angegeben."

    def is_server_running(self, server: str) -> bool:
        server_config = self._config["servers"][server]
        screen_name = re.sub(r'\W+', '', server_config["screen_name"])

        ssh_output = self.send_ssh_command(server_config=server_config, command="""sh -c 'screen -list | grep {0} | cat'""".format(screen_name))

        return len(ssh_output) > 0

    def command_start(self, args: list) -> str:
        if len(args) > 0:
            server = args[0]
            if self._config.get("servers").get(server) is not None:
                server_config = self._config["servers"][server]
                if self.is_server_running(server=server):
                    return "Server läuft bereits."
                else:
                    self.send_ssh_command(server_config=server_config, command="cd \"{0}\"; screen -AmdS {1} java {2} -jar {3}; sleep 1s".format(
                        os.path.dirname(server_config["server_file"]),
                        re.sub(r'\W+', '', server_config["screen_name"]),
                        server_config["java_args"],
                        server_config["server_file"]
                    ))

                    return "Server wurde gestartet."
            else:
                return "Unbekannter Server {0}".format(server)
        else:
            return "Du musst einen Servernamen angeben!"

    def command_stop(self, args: list) -> str:
        if len(args) > 0:
            server = args[0]
            if self._config.get("servers").get(server) is not None:
                server_config = self._config["servers"][server]
                if self.is_server_running(server=server):
                    self.send_ssh_command(server_config=server_config, command="screen -S {0} -X stuff stop^M".format(server_config["screen_name"]))

                    return "Server wurde beendet."
                else:
                    return "Server läuft nicht."
            else:
                return "Unbekannter Server {0}".format(server)
        else:
            return "Du musst einen Servernamen angeben!"

    def command_status(self, args: list) -> str:
        if len(args) > 0:
            server = args[0]
            if self._config.get("servers").get(server) is not None:
                if self.is_server_running(server=server):
                    return "Server ist online."
                else:
                    return "Server ist offline."
            else:
                return "Unbekannter Server {0}".format(server)
        else:
            return "Du musst einen Servernamen angeben!"

    def command_playerdata(self, args: list) -> str:
        if len(args) > 0:
            server = args[0]
            if self._config.get("servers").get(server) is not None:
                server_config = self._config["servers"][server]
                if len(args) > 1:
                    player = GetPlayerData(args[1])

                    if player.valid is True:
                        server_path = os.path.dirname(server_config["server_file"])
                        player_uuid = str(UUID(player.uuid))
                        player_file = server_path + "/" + server_config["world_name"] + "/" + "playerdata" + "/" + player_uuid + ".dat"

                        ssh_output = self.send_ssh_command(server_config=server_config, command="if test -f \"{0}\"; then echo \"1\"; else echo \"0\"; fi".format(player_file)).replace("\n", "")
                        if ssh_output == "1":
                            self.send_ssh_command(server_config=server_config, command="rm \"{0}\"".format(player_file))

                            return "Spielerdaten für {0} ({1}) erfolgreich gelöscht".format(player.username, player.uuid)
                        else:
                            return "Keine Spielerdaten für {0} ({1}) gefunden.".format(player.username, player_uuid)
                    else:
                        return "Konnte Spieler mit der Kennung {0} nicht finden.".format(args[0])
                else:
                    return "Du musst einen Spielernamen oder eine UUID angeben! `" + self._config["prefix"] + "playerdata <Server> <Name oder UUID>`"
            else:
                return "Unbekannter Server {0}".format(server)
        else:
            return "Du musst einen Servernamen angeben!"

    def command_config(self) -> str:
        self.load_config()
        return "Konfiguration erfolgreich geladen."

    def command_deleteworld(self, args: list) -> str:
        if len(args) > 0:
            server = args[0]
            if len(args) > 1:
                if self._config.get("servers").get(server) is not None:
                    server_config = self._config["servers"][server]
                    if self.is_server_running(server):
                        return "Der Server muss aus sein, bevor die Welt gelöscht werden kann."
                    else:
                        world_name = args[0]
                        world_nether_name = world_name + "_nether"
                        world_the_end__name = world_name + "_the_end"

                        server_path = os.path.dirname(server_config["server_file"])
                        world_path = server_path + os.path.sep + world_name
                        world_nether_path = server_path + os.path.sep + world_nether_name
                        world_the_end_path = server_path + os.path.sep + world_the_end__name

                        if os.path.isdir(world_path):
                            shutil.rmtree(world_path, ignore_errors=True)
                            shutil.rmtree(world_nether_path, ignore_errors=True)
                            shutil.rmtree(world_the_end_path, ignore_errors=True)
                            return "Welt erfolgreich gelöscht."
                        else:
                            return "Konnte Welt {0} nicht finden.".format(world_name)
                else:
                    return "Unbekannter Server {0}".format(server)
            else:
                return "Du musst den Namen der Welt angeben: {0}deleteworld <Server> <Name>".format(self._config["prefix"])
        else:
            return "Du musst einen Servernamen angeben!"

    def send_ssh_command(self, server_config: dict, command: str) -> str:
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=server_config["host"], username=server_config["username"], password=server_config["password"], port=server_config["port"])
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(command=command)
        return ssh_stdout.read().decode()


Bot()
