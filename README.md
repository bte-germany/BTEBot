# BTEBot
A simple Bot for the BTE-Germany team to remotely manage Minecraft-servers

## Features
- [x] Start / Stop a server
- [x] Get the current status of a server
- [x] Reset Playerdata (by Name or UUID)
- [x] Delete a world
- [ ] Set allowed commands (e.g. only `start` and `status` but not `stop`)
- [ ] Support for multiple Servers via ssh

## Configuration

To get started, create the config.json file from config.json.example:
```
cp config.json.example config.json
```
Then edit the config to fit your needs, an explanation for the different settings can be found below:
```
{
    "token": "", // The token for your bot-user on Discord
    "prefix": "$", // The prefix the bot should listen to, default is "$"
    "channel_id": 0, // The id of the channel the bot should listen on on your Discord-server
    "server_file": "/home/to/server/dir/server.jar", // Where the .jar file for your server is located
    "screen_name": "minecraft", // Under which name the screen for this server configuration should run. This should be unique to all servers run by this bot
    "world_name": "world", // The name of your world as configured in server.properties
    "java_args": "" // If you want to provide more arguments directly to the java process, you can out them here. Example: "-Xmx2G -Xms2G"
}
```
