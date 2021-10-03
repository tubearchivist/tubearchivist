![Tube Archivist](assets/tube-archivist-banner.jpg?raw=true "Tube Archivist Banner")  

<center><h1>Your self hosted YouTube media server</h1></center>

## Table of contents:
* [Wiki](https://github.com/bbilly1/tubearchivist/wiki) for a detailed documentation
* [Core functionality](#core-functionality)
* [Screenshots](#screenshots)
* [Problem Tube Archivist tries to solve](#problem-tube-archivist-tries-to-solve)
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

## Installing and updating
Take a look at the example `docker-compose.yml` file provided. Tube Archivist depends on three main components split up into separate docker containers:  

### Tube Archivist
The main Python application that displays and serves your video collection, built with Django.
  - Serves the interface on port `8000`
  - Needs a mandatory volume for the video archive at **/youtube**
  - And another recommended volume to save the cache for thumbnails and artwork at **/cache**.
  - The environment variables `ES_URL` and `REDIS_HOST` are needed to tell Tube Archivist where Elasticsearch and Redis respectively are located.
  - The environment variables `HOST_UID` and `HOST_GID` allows Tube Archivist to `chown` the video files to the main host system user instead of the container user.

### Elasticsearch
Stores video meta data and makes everything searchable. Also keeps track of the download queue.
  - Needs to be accessible over the default port `9200`
  - Needs a volume at **/usr/share/elasticsearch/data** to store data

Follow the [documentation](https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html) for additional installation details.

### Redis JSON
Functions as a cache and temporary link between the application and the file system. Used to store and display messages and configuration variables.
  - Needs to be accessible over the default port `6379`
  - Takes an optional volume at **/data** to make your configuration changes permanent.

### Redis on a custom port
For some architectures it might be required to run Redis JSON on a nonstandard port. To for example change the Redis port to **6380**, set the following values:
- Set the environment variable `REDIS_PORT=6380` to the *tubearchivist* service.
- For the *archivist-redis* service, change the ports to `6380:6380`
- Additionally set the following value to the *archivist-redis* service: `command: --port 6380 --loadmodule /usr/lib/redis/modules/rejson.so`

### Updating Tube Archivist
You will see the current version number of **Tube Archivist** in the footer of the interface so you can compare it with the latest release to make sure you are running the *latest and greatest*.  
* There can be breaking changes between updates, particularly as the application grows, new environment variables or settings might be required for you to set in the your docker-compose file. Any breaking changes will be marked in the **release notes**.  
* All testing and development is done with the Elasticsearch version number as mentioned in the provided *docker-compose.yml* file. This will be updated when a new release of Elasticsearch is available. Running an older version of Elasticsearch is most likely not going to result in any issues, but it's still recommended to run the same version as mentioned.

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

## Getting Started
1. Go through the **settings** page and look at the available options. Particularly set *Download Format* to your desired video quality before downloading. **Tube Archivist** downloads the best available quality by default.
2. Subscribe to some of your favorite YouTube channels on the **channels** page. 
3. On the **downloads** page, click on *Rescan subscriptions* to add videos from the subscribed channels to your Download queue or click on *Add to download queue* to manually add Video IDs, links, channels or playlists.
4. Click on *Start download* and let **Tube Archivist** to it's thing. 
5. Enjoy your archived collection!
  
## Roadmap
This should be considered as a **minimal viable product**, there is an extensive list of future functions and improvements planned.

### Functionality
- [ ] Access control
- [ ] User roles
- [ ] Delete videos and channel
- [ ] Create playlists
- [ ] Podcast mode to serve channel as mp3
- [ ] Implement [PyFilesystem](https://github.com/PyFilesystem/pyfilesystem2) for flexible video storage
- [ ] Add thumbnail embed option
- [X] Un-ignore videos [2021-10-03]
- [X] Dynamic download queue [2021-09-26]
- [X] Backup and restore [2021-09-22]
- [X] Scan your file system to index already downloaded videos [2021-09-14]

### UI
- [ ] Show similar videos on video page
- [ ] Multi language support
- [ ] Show total video downloaded vs total videos available in channel
- [X] Grid and list view for both channel and video list pages [2021-10-03]
- [X] Create a github wiki for user documentation [2021-10-03]


## Known limitations
- Video files created by Tube Archivist need to be **mp4** video files for best browser compatibility.
- Every limitation of **yt-dlp** will also be present in Tube Archivist. If **yt-dlp** can't download or extract a video for any reason, Tube Archivist won't be able to either.
- For now this is meant to be run in a trusted network environment. There is *no* security.


## Donate
The best donation to **Tube Archivist** is your time, take a look at the [contribution page](CONTRIBUTING.md) to get started.  
Second best way to support the development is to provide for caffeinated beverages:
* [Paypal.me](https://paypal.me/bbilly1) for a one time coffee
* [Paypal Subscription](https://www.paypal.com/webapps/billing/plans/subscribe?plan_id=P-03770005GR991451KMFGVPMQ) for a monthly coffee
* [co-fi.com](https://ko-fi.com/bbilly1) for an alternative platform
