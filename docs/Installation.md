# Detailed Installation Instructions for Various Platforms

## Unraid

Tube Archivist, and all if it's dependencies are located in the [community applications](https://forums.unraid.net/topic/38582-plug-in-community-applications/) store. The three containers you will need are as follows:

-   **TubeArchivist-RedisJSON**: This container acts as a cache and temporary link between the application and the file system. Used to store and display messages and configuration variables.
-   **TubeArchivist-ES**: ElasticSearch stores video meta data and makes everything searchable. Also keeps track of the download queue.
-   **TubeArchivist**: Once your YouTube video collection grows, it becomes hard to search and find a specific video. That's where Tube Archivist comes in: By indexing your video collection with metadata from YouTube, you can organize, search and enjoy your archived YouTube videos without hassle offline through a convenient web interface.

### Step 1: Install  `TubeArchivist-RedisJSON`

![enter image description here](https://i.imgur.com/ycAqFRU.png)
This is the easiest container to setup of the thee, just make sure that you do not have any port conflicts, and that your `/data` is mounted to the correct path. The other containers will map to the same directory.

If you need to install `TubeArchivist-RedisJSON`on a different port, you'll have to follow [these steps](https://github.com/bbilly1/tubearchivist#redis-on-a-custom-port) later on when installing the `TubeArchivist` container


### Step 2: Install  `TubeArchivist-ES`
![enter image description here](https://i.imgur.com/o6tsTdt.png)
ElasticSeach is also pretty easy to setup. Again, make sure you have no port conflicts, make sure that you mapped `/usr/share/elasticsearch/data` to the same directory as `RedisJSON`, and make sure to change the default password to something more secure. 

There is three additional settings in the "show more settings" area, but leave those as they are.


### Step 3: Install  `TubeArchivist`

![enter image description here](https://i.imgur.com/dwSCfgO.png)
It's finally time to set up TubeArchivist!

 - `Port:`Again, make sure that you have no port conflicts on 8000.
   
 - `Youtube Media Path:` is where you'll download all of your videos to.
   Make sure that this is an empty directory to not cause confusion when
   starting the application. If you have existing videos that you'd like
   to import into Tube Archivist, please checkout the [settings
   wiki.](https://github.com/bbilly1/tubearchivist/wiki/Settings#manual-media-files-import)
   
   
- `Appdata:` This should be the same base path as the other two containers.
   
 - `TA Username:`This will be your username for TubeArchivist.
   
 - `TA Password:`This will be your password for TubeArchivist.
   
 - `Redis` This will be JUST the ip address of your redis container

 - `ElasticSearch Password:`This is the password you defined in the `TubeArchivist-ES` container.
 - `ElasticSearch:` This seems to cause some confusion, but it's a pretty simple step, just replace the IP and Port to match you `TubeArchivist-ES` container.

 (example: if your IP is 192.168.1.15, the value should be http://192.168.1.15:9200)

 - `Time Zone:` This is an important step for your scheduler, to find your timezone, use a site like [TimeZoneConverter](http://www.timezoneconverter.com/cgi-bin/findzone.tzc) 

### From there, you should be able to start up your containers and you're good to go!
If you're still having trouble, join us on [discord](https://discord.gg/AFwz8nE7BK) and come to the #unraid channel.
