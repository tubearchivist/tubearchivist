![Tube Archivist](assets/tube-archivist-front.jpg?raw=true "Tube Archivist Banner")  
[*more screenshots and video*](SHOWCASE.MD)

<div align="center">
<a href="https://github.com/bbilly1/tilefy" target="_blank"><img src="https://tiles.tilefy.me/t/tubearchivist-docker.png" alt="tubearchivist-docker" title="Tube Archivist Docker Pulls" height="50" width="190"/></a>
<a href="https://github.com/bbilly1/tilefy" target="_blank"><img src="https://tiles.tilefy.me/t/tubearchivist-github-star.png" alt="tubearchivist-github-star" title="Tube Archivist GitHub Stars" height="50" width="190"/></a>
<a href="https://github.com/bbilly1/tilefy" target="_blank"><img src="https://tiles.tilefy.me/t/tubearchivist-github-forks.png" alt="tubearchivist-github-forks" title="Tube Archivist GitHub Forks" height="50" width="190"/></a>
<a href="https://www.tubearchivist.com/discord" target="_blank"><img src="https://tiles.tilefy.me/t/tubearchivist-discord.png" alt="tubearchivist-discord" title="TA Discord Server Members" height="50" width="190"/></a>
</div>

## Table of contents:
* [Docs](https://docs.tubearchivist.com/) with [FAQ](https://docs.tubearchivist.com/faq/), and API documentation
* [Core functionality](#core-functionality)
* [Resources](#resources)
* [Installing](#installing)
* [Getting Started](#getting-started)
* [Known limitations](#known-limitations)
* [Port Collisions](#port-collisions)
* [Common Errors](#common-errors)
* [Roadmap](#roadmap)
* [Donate](#donate)

------------------------

## Core functionality
Once your YouTube video collection grows, it becomes hard to search and find a specific video. That's where Tube Archivist comes in: By indexing your video collection with metadata from YouTube, you can organize, search and enjoy your archived YouTube videos without hassle offline through a convenient web interface. This includes:  
* Subscribe to your favorite YouTube channels
* Download Videos using **[yt-dlp](https://github.com/yt-dlp/yt-dlp)**
* Index and make videos searchable
* Play videos
* Keep track of viewed and unviewed videos
  
## Resources
- [Discord](https://www.tubearchivist.com/discord): Connect with us on our Discord server.
- [r/TubeArchivist](https://www.reddit.com/r/TubeArchivist/): Join our Subreddit.
- [Browser Extension](https://github.com/tubearchivist/browser-extension) Tube Archivist Companion, for [Firefox](https://addons.mozilla.org/addon/tubearchivist-companion/) and [Chrome](https://chrome.google.com/webstore/detail/tubearchivist-companion/jjnkmicfnfojkkgobdfeieblocadmcie)
- [Jellyfin Plugin](https://github.com/tubearchivist/tubearchivist-jf-plugin): Add your videos to Jellyfin
- [Plex Plugin](https://github.com/tubearchivist/tubearchivist-plex): Add your videos to Plex

## Installing
For minimal system requirements, the Tube Archivist stack needs around 2GB of available memory for a small testing setup and around 4GB of available memory for a mid to large sized installation. Minimal with dual core with 4 threads, better quad core plus. 
This project requires docker. Ensure it is installed and running on your system.  

The documentation has additional user provided instructions for [Unraid](https://docs.tubearchivist.com/installation/unraid/), [Synology](https://docs.tubearchivist.com/installation/synology/) and [Podman](https://docs.tubearchivist.com/installation/podman/).

The instructions here should get you up and running quickly, for Docker beginners and full explanation about each environment variable, see the [docs](https://docs.tubearchivist.com/installation/docker-compose/).

Take a look at the example [docker-compose.yml](https://github.com/tubearchivist/tubearchivist/blob/master/docker-compose.yml) and configure the required environment variables.

**TubeArchivist**:  
| Environment Var | Value |  |
| ----------- | ----------- | ----------- |
| TA_HOST | Server IP or hostname | Required |
| TA_USERNAME | Initial username when logging into TA | Required |
| TA_PASSWORD | Initial password when logging into TA | Required |
| ELASTIC_PASSWORD | Password for ElasticSearch | Required |
| REDIS_HOST | Hostname for Redis | Required |
| TZ | Set your timezone for the scheduler | Required |
| TA_PORT | Overwrite Nginx port | Optional |
| TA_UWSGI_PORT | Overwrite container internal uwsgi port | Optional |
| TA_ENABLE_AUTH_PROXY | Enables support for forwarding auth in reverse proxies | [Read more](https://docs.tubearchivist.com/configuration/forward-auth/) |
| TA_AUTH_PROXY_USERNAME_HEADER | Header containing username to log in | Optional |
| TA_AUTH_PROXY_LOGOUT_URL | Logout URL for forwarded auth | Optional |
| ES_URL | URL That ElasticSearch runs on | Optional |
| ES_DISABLE_VERIFY_SSL | Disable ElasticSearch SSL certificate verification | Optional |
| ES_SNAPSHOT_DIR | Custom path where elastic search stores snapshots for master/data nodes | Optional |
| HOST_GID | Allow TA to own the video files instead of container user | Optional |
| HOST_UID | Allow TA to own the video files instead of container user | Optional |
| ELASTIC_USER | Change the default ElasticSearch user | Optional |
| REDIS_PORT | Port that Redis runs on | Optional |
| TA_LDAP | Configure TA to use LDAP Authentication | [Read more](https://docs.tubearchivist.com/configuration/ldap/) |
| ENABLE_CAST | Enable casting support | [Read more](https://docs.tubearchivist.com/configuration/cast/) |
| DJANGO_DEBUG | Return additional error messages, for debug only |  |

**ElasticSearch**  
| Environment Var | Value | State |
| ----------- | ----------- | ----------- |
| ELASTIC_PASSWORD | Matching password `ELASTIC_PASSWORD` from TubeArchivist | Required |
| http.port | Change the port ElasticSearch runs on | Optional |


## Update
Always use the *latest* (the default) or a named semantic version tag for the docker images. The *unstable* tags are only for your testing environment, there might not be an update path for these testing builds. 

You will see the current version number of **Tube Archivist** in the footer of the interface. There is a daily version check task querying tubearchivist.com, notifying you of any new releases in the footer. To update, you need to update the docker images, the method for which will depend on your platform. For example, if you're using `docker-compose`, run `docker-compose pull` and then restart with `docker-compose up -d`. After updating, check the footer to verify you are running the expected version.  

  - This project is tested for updates between one or two releases maximum. Further updates back may or may not be supported and you might have to reset your index and configurations to update. Ideally apply new updates at least once per month.  
  - There can be breaking changes between updates, particularly as the application grows, new environment variables or settings might be required for you to set in the your docker-compose file. *Always* check the **release notes**: Any breaking changes will be marked there.  
  - All testing and development is done with the Elasticsearch version number as mentioned in the provided *docker-compose.yml* file. This will be updated when a new release of Elasticsearch is available. Running an older version of Elasticsearch is most likely not going to result in any issues, but it's still recommended to run the same version as mentioned. Use `bbilly1/tubearchivist-es` to automatically get the recommended version.   

## Getting Started
1. Go through the **settings** page and look at the available options. Particularly set *Download Format* to your desired video quality before downloading. **Tube Archivist** downloads the best available quality by default. To support iOS or MacOS and some other browsers a compatible format must be specified. For example:
```
bestvideo[vcodec*=avc1]+bestaudio[acodec*=mp4a]/mp4
```
2. Subscribe to some of your favorite YouTube channels on the **channels** page. 
3. On the **downloads** page, click on *Rescan subscriptions* to add videos from the subscribed channels to your Download queue or click on *Add to download queue* to manually add Video IDs, links, channels or playlists.
4. Click on *Start download* and let **Tube Archivist** to it's thing. 
5. Enjoy your archived collection!


### Port Collisions  
If you have a collision on port `8000`, best solution is to use dockers *HOST_PORT* and *CONTAINER_PORT* distinction: To for example change the interface to port 9000 use `9000:8000` in your docker-compose file.  

For more information on port collisions, check the docs.

## Common Errors  
Here is a list of common errors and their solutions.  

### `vm.max_map_count`
**Elastic Search** in Docker requires the kernel setting of the host machine `vm.max_map_count` to be set to at least 262144.

To temporary set the value run:  
```
sudo sysctl -w vm.max_map_count=262144
```  
To apply the change permanently depends on your host operating system:  

 - For example on Ubuntu Server add `vm.max_map_count = 262144` to the file `/etc/sysctl.conf`.
 - On Arch based systems create a file `/etc/sysctl.d/max_map_count.conf` with the content `vm.max_map_count = 262144`. 
 - On any other platform look up in the documentation on how to pass kernel parameters.  


### Permissions for elasticsearch
If you see a message similar to `Unable to access 'path.repo' (/usr/share/elasticsearch/data/snapshot)` or `failed to obtain node locks, tried [/usr/share/elasticsearch/data]` and `maybe these locations are not writable` when initially starting elasticsearch, that probably means the container is not allowed to write files to the volume.  
To fix that issue, shutdown the container and on your host machine run:
```
chown 1000:0 -R /path/to/mount/point
```
This will match the permissions with the **UID** and **GID** of elasticsearch process within the container and should fix the issue.  


### Disk usage
The Elasticsearch index will turn to ***read only*** if the disk usage of the container goes above 95% until the usage drops below 90% again, you will see error messages like `disk usage exceeded flood-stage watermark`.  

Similar to that, TubeArchivist will become all sorts of messed up when running out of disk space. There are some error messages in the logs when that happens, but it's best to make sure to have enough disk space before starting to download.

## `error setting rlimit`
If you are seeing errors like `failed to create shim: OCI runtime create failed` and `error during container init: error setting rlimits`, this means docker can't set these limits, usually because they are set at another place or are incompatible because of other reasons. Solution is to remove the `ulimits` key from the ES container in your docker compose and start again.

This can happen if you have nested virtualizations, e.g. LXC running Docker in Proxmox.

## Known limitations
- Video files created by Tube Archivist need to be playable in your browser of choice. Not every codec is compatible with every browser and might require some testing with format selection. 
- Every limitation of **yt-dlp** will also be present in Tube Archivist. If **yt-dlp** can't download or extract a video for any reason, Tube Archivist won't be able to either.
- There is no flexibility in naming of the media files.

## Roadmap
We have come far, nonetheless we are not short of ideas on how to improve and extend this project. Issues waiting for you to be tackled in no particular order:

- [ ] Audio download
- [ ] Podcast mode to serve channel as mp3
- [ ] Random and repeat controls ([#108](https://github.com/tubearchivist/tubearchivist/issues/108), [#220](https://github.com/tubearchivist/tubearchivist/issues/220))
- [ ] Auto play or play next link ([#226](https://github.com/tubearchivist/tubearchivist/issues/226))
- [ ] Multi language support
- [ ] Show total video downloaded vs total videos available in channel
- [ ] Download or Ignore videos by keyword ([#163](https://github.com/tubearchivist/tubearchivist/issues/163))
- [ ] Custom searchable notes to videos, channels, playlists ([#144](https://github.com/tubearchivist/tubearchivist/issues/144))
- [ ] Search comments
- [ ] Search download queue
- [ ] Per user videos/channel/playlists

Implemented:
- [X] Configure shorts, streams and video sizes per channel [2024-07-15]
- [X] User created playlists [2024-04-10]
- [X] User roles, aka read only user [2023-11-10]
- [X] Add statistics of index [2023-09-03]
- [X] Implement [Apprise](https://github.com/caronc/apprise) for notifications [2023-08-05]
- [X] Download video comments [2022-11-30]
- [X] Show similar videos on video page [2022-11-30]
- [X] Implement complete offline media file import from json file [2022-08-20]
- [X] Filter and query in search form, search by url query [2022-07-23]
- [X] Make items in grid row configurable to use more of the screen [2022-06-04]
- [X] Add passing browser cookies to yt-dlp [2022-05-08]
- [X] Add [SponsorBlock](https://sponsor.ajay.app/) integration [2022-04-16]
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

## User Scripts
This is a list of useful user scripts, generously created from folks like you to extend this project and its functionality. Make sure to check the respective repository links for detailed license information.  

This is your time to shine, [read this](https://github.com/tubearchivist/tubearchivist/blob/master/CONTRIBUTING.md#user-scripts) then open a PR to add your script here.

- [danieljue/ta_dl_page_script](https://github.com/danieljue/ta_dl_page_script): Helper browser script to prioritize a channels' videos in download queue.
- [dot-mike/ta-scripts](https://github.com/dot-mike/ta-scripts): A collection of personal scripts for managing TubeArchivist.
- [DarkFighterLuke/ta_base_url_nginx](https://gist.github.com/DarkFighterLuke/4561b6bfbf83720493dc59171c58ac36): Set base URL with Nginx when you can't use subdomains.
- [lamusmaser/ta_migration_helper](https://github.com/lamusmaser/ta_migration_helper): Advanced helper script for migration issues to TubeArchivist v0.4.4 or later.
- [lamusmaser/create_info_json](https://gist.github.com/lamusmaser/837fb58f73ea0cad784a33497932e0dd): Script to generate `.info.json` files using `ffmpeg` collecting information from downloaded videos.
- [lamusmaser/ta_fix_for_video_redirection](https://github.com/lamusmaser/ta_fix_for_video_redirection): Script to fix videos that were incorrectly indexed by YouTube's "Video is Unavailable" response. 
- [RoninTech/ta-helper](https://github.com/RoninTech/ta-helper): Helper script to provide a symlink association to reference TubeArchivist videos with their original titles.
- [tangyjoust/Tautulli-Notify-TubeArchivist-of-Plex-Watched-State](https://github.com/tangyjoust/Tautulli-Notify-TubeArchivist-of-Plex-Watched-State) Mark videos watched in Plex (through streaming not manually) through Tautulli back to TubeArchivist

## Donate
The best donation to **Tube Archivist** is your time, take a look at the [contribution page](CONTRIBUTING.md) to get started.  
Second best way to support the development is to provide for caffeinated beverages:
* [GitHub Sponsor](https://github.com/sponsors/bbilly1) become a sponsor here on GitHub
* [Paypal.me](https://paypal.me/bbilly1) for a one time coffee
* [Paypal Subscription](https://www.paypal.com/webapps/billing/plans/subscribe?plan_id=P-03770005GR991451KMFGVPMQ) for a monthly coffee
* [ko-fi.com](https://ko-fi.com/bbilly1) for an alternative platform

## Notable mentions
This is a selection of places where this project has been featured on reddit, in the news, blogs or any other online media, newest on top.
* **xda-developers.com**: 5 obscure self-hosted services worth checking out - Tube Archivist - To save your essential YouTube videos, [2024-10-13][[link](https://www.xda-developers.com/obscure-self-hosted-services/)]
* **selfhosted.show**: why we're trying Tube Archivist, [2024-06-14][[link](https://selfhosted.show/125)]
* **ycombinator**: Tube Archivist on Hackernews front page, [2023-07-16][[link](https://news.ycombinator.com/item?id=36744395)]
* **linux-community.de**: Tube Archivist bringt Ordnung in die Youtube-Sammlung, [German][2023-05-01][[link](https://www.linux-community.de/ausgaben/linuxuser/2023/05/tube-archivist-bringt-ordnung-in-die-youtube-sammlung/)]
* **noted.lol**: Dev Debrief, An Interview With the Developer of Tube Archivist, [2023-03-30] [[link](https://noted.lol/dev-debrief-tube-archivist/)]
* **console.substack.com**: Interview With Simon of Tube Archivist, [2023-01-29] [[link](https://console.substack.com/p/console-142#%C2%A7interview-with-simon-of-tube-archivist)]
* **reddit.com**: Tube Archivist v0.3.0 - Now Archiving Comments, [2022-12-02] [[link](https://www.reddit.com/r/selfhosted/comments/zaonzp/tube_archivist_v030_now_archiving_comments/)]
* **reddit.com**: Tube Archivist v0.2 - Now with Full Text Search, [2022-07-24] [[link](https://www.reddit.com/r/selfhosted/comments/w6jfa1/tube_archivist_v02_now_with_full_text_search/)]
* **noted.lol**: How I Control What Media My Kids Watch Using Tube Archivist, [2022-03-27] [[link](https://noted.lol/how-i-control-what-media-my-kids-watch-using-tube-archivist/)]
* **thehomelab.wiki**: Tube Archivist - A Youtube-DL Alternative on Steroids, [2022-01-27] [[link](https://thehomelab.wiki/books/news/page/tube-archivist-a-youtube-dl-alternative-on-steroids)]
* **reddit.com**: Celebrating TubeArchivist v0.1, [2022-01-09] [[link](https://www.reddit.com/r/selfhosted/comments/rzh084/celebrating_tubearchivist_v01/)]
* **linuxunplugged.com**: Pick: tubearchivist — Your self-hosted YouTube media server, [2021-09-11] [[link](https://linuxunplugged.com/425)] and [2021-10-05] [[link](https://linuxunplugged.com/426)]
* **reddit.com**: Introducing Tube Archivist, your self hosted Youtube media server, [2021-09-12] [[link](https://www.reddit.com/r/selfhosted/comments/pmj07b/introducing_tube_archivist_your_self_hosted/)]
