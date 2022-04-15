![Tube Archivist](assets/tube-archivist-banner.jpg?raw=true "Tube Archivist Banner")  

<center><h1>Your self hosted YouTube media server</h1></center>

Tube Archivist has a new home: https://github.com/tubearchivist/tubearchivist

## Table of contents:
* [Wiki](https://github.com/tubearchivist/tubearchivist/wiki) for a detailed documentation, with [FAQ](https://github.com/tubearchivist/tubearchivist/wiki/FAQ)
* [Core functionality](#core-functionality)
* [Screenshots](#screenshots)
* [Problem Tube Archivist tries to solve](#problem-tube-archivist-tries-to-solve)
* [Connect](#connect)
* [Installing and updating](#installing-and-updating)
* [Getting Started](#getting-started)
* [Potential pitfalls](#potential-pitfalls)
* [Roadmap](#roadmap)
* [Known limitations](#known-limitations)
* [Donate](#donate)

------------------------

## Core functionality
* Subscribe to your favorite YouTube channels
* Download Videos using **yt-dlp**
* Index and make videos searchable
* Play videos
* Keep track of viewed and unviewed videos

## Tube Archivist on YouTube
[![ibracorp-youtube-video-thumb](assets/tube-archivist-ibracorp-O8H8Z01c0Ys.jpg)](https://www.youtube.com/watch?v=O8H8Z01c0Ys)

## Screenshots
![home screenshot](assets/tube-archivist-screenshot-home.png?raw=true "Tube Archivist Home")  
*Home Page*

![channels screenshot](assets/tube-archivist-screenshot-channels.png?raw=true "Tube Archivist Channels")  
*All Channels*

![single channel screenshot](assets/tube-archivist-screenshot-single-channel.png?raw=true "Tube Archivist Single Channel")  
*Single Channel*

![video page screenshot](assets/tube-archivist-screenshot-video.png?raw=true "Tube Archivist Video Page")  
*Video Page*

![video page screenshot](assets/tube-archivist-screenshot-download.png?raw=true "Tube Archivist Video Page")  
*Downloads Page*
  
## Problem Tube Archivist tries to solve
Once your YouTube video collection grows, it becomes hard to search and find a specific video. That's where Tube Archivist comes in: By indexing your video collection with metadata from YouTube, you can organize, search and enjoy your archived YouTube videos without hassle offline through a convenient web interface.

## Connect
- [Discord](https://discord.gg/AFwz8nE7BK): Connect with us on our Discord server.
- [r/TubeArchivist](https://www.reddit.com/r/TubeArchivist/): Join our Subreddit.

## Installing and updating
Take a look at the example `docker-compose.yml` file provided. Use the *latest* or the named semantic version tag. The *unstable* tag is for intermediate testing and as the name implies, is **unstable** and not be used on your main installation but in a [testing environment](CONTRIBUTING.md).  

Tube Archivist depends on three main components split up into separate docker containers:  

### Tube Archivist
The main Python application that displays and serves your video collection, built with Django.
  - Serves the interface on port `8000`
  - Needs a volume for the video archive at **/youtube**
  - And another volume to save application data at **/cache**.
  - The environment variables `ES_URL` and `REDIS_HOST` are needed to tell Tube Archivist where Elasticsearch and Redis respectively are located.
  - The environment variables `HOST_UID` and `HOST_GID` allows Tube Archivist to `chown` the video files to the main host system user instead of the container user. Those two variables are optional, not setting them will disable that functionality. That might be needed if the underlying filesystem doesn't support `chown` like *NFS*. 
  - Change the environment variables `TA_USERNAME` and `TA_PASSWORD` to create the initial credentials. 
  - `ELASTIC_PASSWORD` is for the password for Elasticsearch. The environment variable `ELASTIC_USER` is optional, should you want to change the username from the default *elastic*.
  - For the scheduler to know what time it is, set your timezone with the `TZ` environment variable, defaults to *UTC*.

### Port collisions
If you have a collision on port `8000`, best solution is to use dockers *HOST_PORT* and *CONTAINER_PORT* distinction: To for example change the interface to port 9000 use `9000:8000` in your docker-compose file.  

Should that not be an option, the Tube Archivist container takes these two additional environment variables:
- **TA_PORT**: To actually change the port where nginx listens, make sure to also change the ports value in your docker-compose file.
- **TA_UWSGI_PORT**: To change the default uwsgi port 8080 used for container internal networking between uwsgi serving the django application and nginx.  

Changing any of these two environment variables will change the files *nginx.conf* and *uwsgi.ini* at startup using `sed` in your container.

### Elasticsearch
**Note**: Newest Tube Archivist depends on Elasticsearch version 7.17 to provide an automatic updatepath in the future. 

Use `bbilly1/tubearchivist-es` to automatically get the recommended version, or use the official image with the version tag in the docker-compose file.

Stores video meta data and makes everything searchable. Also keeps track of the download queue.
  - Needs to be accessible over the default port `9200`
  - Needs a volume at **/usr/share/elasticsearch/data** to store data

Follow the [documentation](https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html) for additional installation details.

### Redis JSON
Functions as a cache and temporary link between the application and the file system. Used to store and display messages and configuration variables.
  - Needs to be accessible over the default port `6379`
  - Needs a volume at **/data** to make your configuration changes permanent.

### Redis on a custom port
For some architectures it might be required to run Redis JSON on a nonstandard port. To for example change the Redis port to **6380**, set the following values:
- Set the environment variable `REDIS_PORT=6380` to the *tubearchivist* service.
- For the *archivist-redis* service, change the ports to `6380:6380`
- Additionally set the following value to the *archivist-redis* service: `command: --port 6380 --loadmodule /usr/lib/redis/modules/rejson.so`

### Updating Tube Archivist
You will see the current version number of **Tube Archivist** in the footer of the interface so you can compare it with the latest release to make sure you are running the *latest and greatest*.  
* There can be breaking changes between updates, particularly as the application grows, new environment variables or settings might be required for you to set in the your docker-compose file. *Always* check the **release notes**: Any breaking changes will be marked there.  
* All testing and development is done with the Elasticsearch version number as mentioned in the provided *docker-compose.yml* file. This will be updated when a new release of Elasticsearch is available. Running an older version of Elasticsearch is most likely not going to result in any issues, but it's still recommended to run the same version as mentioned. Use `bbilly1/tubearchivist-es` to automatically get the recommended version.

### Alternative installation instructions:
- **arm64**: The Tube Archivist container is multi arch, so is Elasticsearch. RedisJSON doesn't offer arm builds, you can use `bbilly1/rejson`, an unofficial rebuild for arm64.
- **Synology**: There is a [discussion thread](https://github.com/tubearchivist/tubearchivist/discussions/48) with Synology installation instructions.
- **Unraid**: The three containers needed are all in the Community Applications. First install `TubeArchivist RedisJSON` followed by `TubeArchivist ES`, and finally you can install `TubeArchivist`. If you have unraid specific issues, report those to the [support thread](https://forums.unraid.net/topic/114073-support-crocs-tube-archivist/ "support thread").
- **Helm Chart**: There is a Helm Chart available at https://github.com/insuusvenerati/helm-charts. Mostly self-explanatory but feel free to ask questions in the discord / subreddit.


## Potential pitfalls
### vm.max_map_count
**Elastic Search** in Docker requires the kernel setting of the host machine `vm.max_map_count` to be set to at least 262144.

To temporary set the value run:  
```
sudo sysctl -w vm.max_map_count=262144
```  

To apply the change permanently depends on your host operating system:  
- For example on Ubuntu Server add `vm.max_map_count = 262144` to the file */etc/sysctl.conf*.
- On Arch based systems create a file */etc/sysctl.d/max_map_count.conf* with the content `vm.max_map_count = 262144`. 
- On any other platform look up in the documentation on how to pass kernel parameters.

### Permissions for elasticsearch
If you see a message similar to `AccessDeniedException[/usr/share/elasticsearch/data/nodes]` when initially starting elasticsearch, that means the container is not allowed to write files to the volume.  
That's most likely the case when you run `docker-compose` as an unprivileged user. To fix that issue, shutdown the container and on your host machine run:
```
chown 1000:0 /path/to/mount/point
```
This will match the permissions with the **UID** and **GID** of elasticsearch within the container and should fix the issue.

### Disk usage
The Elasticsearch index will turn to *read only* if the disk usage of the container goes above 95% until the usage drops below 90% again. Similar to that, TubeArchivist will become all sorts of messed up when running out of disk space. There are some error messages in the logs when that happens, but it's best to make sure to have enough disk space before starting to download.

## Getting Started
1. Go through the **settings** page and look at the available options. Particularly set *Download Format* to your desired video quality before downloading. **Tube Archivist** downloads the best available quality by default. To support iOS or MacOS and some other browsers a compatible format must be specified. For example:
```
bestvideo[VCODEC=avc1]+bestaudio[ACODEC=mp4a]/mp4
```
2. Subscribe to some of your favorite YouTube channels on the **channels** page. 
3. On the **downloads** page, click on *Rescan subscriptions* to add videos from the subscribed channels to your Download queue or click on *Add to download queue* to manually add Video IDs, links, channels or playlists.
4. Click on *Start download* and let **Tube Archivist** to it's thing. 
5. Enjoy your archived collection!
  
## Roadmap
We have come far, nonetheless we are not short of ideas on how to improve and extend this project. Issues waiting for you to be tackled in no particular order:

- [ ] User roles
- [ ] Podcast mode to serve channel as mp3
- [ ] Implement [PyFilesystem](https://github.com/PyFilesystem/pyfilesystem2) for flexible video storage
- [ ] Implement [Apprise](https://github.com/caronc/apprise) for notifications ([#97](https://github.com/tubearchivist/tubearchivist/issues/97))
- [ ] Add [SponsorBlock](https://sponsor.ajay.app/) integration
- [ ] Add passing browser cookies to yt-dlp ([#199](https://github.com/tubearchivist/tubearchivist/issues/199))
- [ ] User created playlists, random and repeat controls ([#108](https://github.com/tubearchivist/tubearchivist/issues/108), [#220](https://github.com/tubearchivist/tubearchivist/issues/220))
- [ ] Auto play or play next link
- [ ] Show similar videos on video page
- [ ] Multi language support
- [ ] Show total video downloaded vs total videos available in channel
- [ ] Make items in grid row configurable to use more of the screen
- [ ] Add statistics of index
- [ ] Implement complete offline media file import from json file ([#138](https://github.com/tubearchivist/tubearchivist/issues/138))
- [ ] Filter and query in search form, search by url query ([#134](https://github.com/tubearchivist/tubearchivist/issues/134), [#139](https://github.com/tubearchivist/tubearchivist/issues/139))
- [ ] Auto ignore videos by keyword ([#163](https://github.com/tubearchivist/tubearchivist/issues/163))
- [ ] Custom searchable notes to videos, channels, playlists ([#144](https://github.com/tubearchivist/tubearchivist/issues/144))

Implemented:
- [X] Implement per channel settings [2022-03-26]
- [X] Subtitle download & indexing [2022-02-13]
- [X] Fancy advanced unified search interface [2022-01-08]
- [X] Auto rescan and auto download on a schedule [2021-12-17]
- [X] Optional automatic deletion of watched items after a specified time [2021-12-17]
- [X] Create playlists [2021-11-27]
- [X] Access control [2021-11-01]
- [X] Delete videos and channel [2021-10-16]
- [X] Add thumbnail embed option [2021-10-16]
- [X] Create a github wiki for user documentation [2021-10-03]
- [X] Grid and list view for both channel and video list pages [2021-10-03]
- [X] Un-ignore videos [2021-10-03]
- [X] Dynamic download queue [2021-09-26]
- [X] Backup and restore [2021-09-22]
- [X] Scan your file system to index already downloaded videos [2021-09-14]

## Known limitations
- Video files created by Tube Archivist need to be playable in your browser of choice. Not every codec is compatible with every browser and might require some testing with format selection. 
- Every limitation of **yt-dlp** will also be present in Tube Archivist. If **yt-dlp** can't download or extract a video for any reason, Tube Archivist won't be able to either.
- For now this is meant to be run in a trusted network environment. Not everything is properly authenticated.
- There is currently no flexibility in naming of the media files.


## Donate
The best donation to **Tube Archivist** is your time, take a look at the [contribution page](CONTRIBUTING.md) to get started.  
Second best way to support the development is to provide for caffeinated beverages:
* [Paypal.me](https://paypal.me/bbilly1) for a one time coffee
* [Paypal Subscription](https://www.paypal.com/webapps/billing/plans/subscribe?plan_id=P-03770005GR991451KMFGVPMQ) for a monthly coffee
* [ko-fi.com](https://ko-fi.com/bbilly1) for an alternative platform
