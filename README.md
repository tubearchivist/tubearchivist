![banner-tube-archivist-light.png](assets/tube-archivist-banner.jpg?raw=true "Tube Archivist Banner")  

<center><h1>The Tube Archivist<br>Your self hosted Youtube media server</h1></center>


## Core functionality
* Subscribe to your favourite Youtube channels
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
Once your Youtube video collection grows, it becomes hard to search and find a specific video. That's where Tube Archivist comes in: By indexing your video collection with metadata from Youtube, you can organize, search and enjoy your archived Youtube videos without hassle offline through a convenient web interface.

## Installation
Take a look at the example `docker-compose.yml` file provided. Tube Archivist depends on three main components split up into seperate docker containers:  

### Tube Archivist
The main Python application that displays and serves your video collection, built with Django.
  - Serves the interface on port `8000`
  - Needs a mandatory volume for the video archive at **/youtube**
  - And another recommended volume to save the cache for thumbnails and artwork at **/cache**.
  - The environment variables `ES_URL` and `REDIS_HOST` are needed to tell Tube Archivist where Elasticsearch and Redis respectively are located.
  - The environment variables `HOST_UID` and `HOST_GID` allowes Tube Archivist to `chown` the video files to the main host system user instead of the container user.

### Elasticsearch
Stores video meta data and makes everything searchable. Also keeps track of the download queue.
  - Needs to be accessable over the default port `9200`
  - Needs a volume at **/usr/share/elasticsearch/data** to store data

Follow the [documentation](https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html) for additional installation details.

### Redis JSON
Functions as a cache and temporary link between the application and the filesystem. Used to store and display messages and configuration variables.
  - Needs to be accessable over the default port `6379`
  - Takes an optional volume at **/data** to make your configuration changes permanent.

## Getting Started
1. Go through the **settings** page and look at the available options. Particularly set *Download Format* to you desired video quality before downloading.
2. Subscribe to some of your favourite Youtube channels on the **channels** page. 
3. On the **downloads** page, click on *Rescan subscriptions* to add videos from the subscribed channels to your Download queue or click on *Add to download queue* to manually add Video IDs or links.
4. Click on *Download queue* and let Tube Archivist to it's thing. 
5. Enjoy your archived collection!

## Potential pitfalls
**Elastic Search** in Docker requires the kernel setting of the host machine `vm.max_map_count` to be set to least 262144.

To temporary set the value run:  
```
sudo sysctl -w vm.max_map_count=262144
```  

To apply the change permanently depends on your host operating system:  
- For example on Ubuntu Server add `vm.max_map_count = 262144` to the file */etc/sysctl.conf*.
- On Arch based systems create a file */etc/sysctl.d/max_map_count.conf* with the content `vm.max_map_count = 262144`. 
- On any other platform look up in the documentation on how to pass kernel parameters.


## Roadmap
This should be considered as a **minimal viable product**, there is an exstensive list of future functions and improvements planned: 
- [ ] Scan your filesystem to manually add videos
- [ ] Access controll
- [ ] User roles
- [ ] Delete videos and channel
- [ ] Create playlists
- [ ] Show similar videos on video page
- [ ] Import existing downloaded archive
- [ ] Multi language support
- [ ] Backup and restore


## Known limitations
- Video files created by Tube Archivist need to be **mp4** video files for best browser compatibility.
- Every limitation **yt-dlp** will also be present in Tube Archivist. If yt-dlp can't download or extract a video for any reason, Tube Archivist won't be able to either.
- For now this is meant to be run in a trusted network environment.
