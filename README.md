![Tube Archivist](assets/tube-archivist-banner.jpg?raw=true "Tube Archivist Banner")  

<h1 align="center">Your self hosted YouTube media server</h1>
<div align="center">
<a href="https://github.com/bbilly1/tilefy" target="_blank"><img src="https://tiles.tilefy.me/t/tubearchivist-docker.png" alt="tubearchivist-docker" title="Tube Archivist Docker Pulls" height="50" width="190"/></a>
<a href="https://github.com/bbilly1/tilefy" target="_blank"><img src="https://tiles.tilefy.me/t/tubearchivist-github-star.png" alt="tubearchivist-github-star" title="Tube Archivist GitHub Stars" height="50" width="190"/></a>
<a href="https://github.com/bbilly1/tilefy" target="_blank"><img src="https://tiles.tilefy.me/t/tubearchivist-github-forks.png" alt="tubearchivist-github-forks" title="Tube Archivist GitHub Forks" height="50" width="190"/></a>
<a href="https://www.tubearchivist.com/discord" target="_blank"><img src="https://tiles.tilefy.me/t/tubearchivist-discord.png" alt="tubearchivist-discord" title="TA Discord Server Members" height="50" width="190"/></a>
</div>

![home screenshot](assets/tube-archivist-screenshot-home.png?raw=true "Tube Archivist Home")
[*more screenshots and video*](SHOWCASE.MD)

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
* Download Videos using **yt-dlp**
* Index and make videos searchable
* Play videos
* Keep track of viewed and unviewed videos
  
## Resources
- [Discord](https://www.tubearchivist.com/discord): Connect with us on our Discord server.
- [r/TubeArchivist](https://www.reddit.com/r/TubeArchivist/): Join our Subreddit.
- [Browser Extension](https://github.com/tubearchivist/browser-extension) Tube Archivist Companion, for [Firefox](https://addons.mozilla.org/addon/tubearchivist-companion/) and [Chrome](https://chrome.google.com/webstore/detail/tubearchivist-companion/jjnkmicfnfojkkgobdfeieblocadmcie)
- [Tube Archivist Metrics](https://github.com/tubearchivist/tubearchivist-metrics) to create statistics in Prometheus/OpenMetrics format.  

## Installing
For minimal system requirements, the Tube Archivist stack needs around 2GB of available memory for a small testing setup and around 4GB of available memory for a mid to large sized installation. Minimal with dual core with 4 threads, better quad core plus. 
This project requires docker. Ensure it is installed and running on your system.  

The documentation has additional user provided instructions for [Unraid](https://docs.tubearchivist.com/installation/unraid/), [Synology](https://docs.tubearchivist.com/installation/synology/), [Podman](https://docs.tubearchivist.com/installation/podman/) and [True NAS](https://docs.tubearchivist.com/installation/truenas-scale/).

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
| ES_URL | URL That ElasticSearch runs on | Optional |
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

You will see the current version number of **Tube Archivist** in the footer of the interface. There is a daily version check task querying tubearchivist.com, notifying you of any new releases in the footer. To take advantage of the latest fixes and improvements, make sure you are running the *latest and greatest*. After updating, check the footer to verify you are running the expected version.  

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

## Known limitations
- Video files created by Tube Archivist need to be playable in your browser of choice. Not every codec is compatible with every browser and might require some testing with format selection. 
- Every limitation of **yt-dlp** will also be present in Tube Archivist. If **yt-dlp** can't download or extract a video for any reason, Tube Archivist won't be able to either.
- There is currently no flexibility in naming of the media files.

## Roadmap
We have come far, nonetheless we are not short of ideas on how to improve and extend this project. Issues waiting for you to be tackled in no particular order:

- [ ] User roles
- [ ] Podcast mode to serve channel as mp3
- [ ] Implement [PyFilesystem](https://github.com/PyFilesystem/pyfilesystem2) for flexible video storage
- [ ] Implement [Apprise](https://github.com/caronc/apprise) for notifications ([#97](https://github.com/tubearchivist/tubearchivist/issues/97))
- [ ] User created playlists, random and repeat controls ([#108](https://github.com/tubearchivist/tubearchivist/issues/108), [#220](https://github.com/tubearchivist/tubearchivist/issues/220))
- [ ] Auto play or play next link ([#226](https://github.com/tubearchivist/tubearchivist/issues/226))
- [ ] Multi language support
- [ ] Show total video downloaded vs total videos available in channel
- [ ] Add statistics of index
- [ ] Download speed schedule ([#198](https://github.com/tubearchivist/tubearchivist/issues/198))
- [ ] Download or Ignore videos by keyword ([#163](https://github.com/tubearchivist/tubearchivist/issues/163))
- [ ] Custom searchable notes to videos, channels, playlists ([#144](https://github.com/tubearchivist/tubearchivist/issues/144))

Implemented:
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

## Donate
The best donation to **Tube Archivist** is your time, take a look at the [contribution page](CONTRIBUTING.md) to get started.  
Second best way to support the development is to provide for caffeinated beverages:
* [GitHub Sponsor](https://github.com/sponsors/bbilly1) become a sponsor here on GitHub
* [Paypal.me](https://paypal.me/bbilly1) for a one time coffee
* [Paypal Subscription](https://www.paypal.com/webapps/billing/plans/subscribe?plan_id=P-03770005GR991451KMFGVPMQ) for a monthly coffee
* [ko-fi.com](https://ko-fi.com/bbilly1) for an alternative platform

## Notable mentions
This is a selection of places where this project has been featured on reddit, in the news, blogs or any other online media, newest on top.
* **noted.lol**: Dev Debrief, An Interview With the Developer of Tube Archivist, [2023-03-30] [[link](https://noted.lol/dev-debrief-tube-archivist/)]
* **console.substack.com**: Interview With Simon of Tube Archivist, [2023-01-29] [[link](https://console.substack.com/p/console-142#%C2%A7interview-with-simon-of-tube-archivist)]
* **reddit.com**: Tube Archivist v0.3.0 - Now Archiving Comments, [2022-12-02] [[link](https://www.reddit.com/r/selfhosted/comments/zaonzp/tube_archivist_v030_now_archiving_comments/)]
* **reddit.com**: Tube Archivist v0.2 - Now with Full Text Search, [2022-07-24] [[link](https://www.reddit.com/r/selfhosted/comments/w6jfa1/tube_archivist_v02_now_with_full_text_search/)]
* **noted.lol**: How I Control What Media My Kids Watch Using Tube Archivist, [2022-03-27] [[link](https://noted.lol/how-i-control-what-media-my-kids-watch-using-tube-archivist/)]
* **thehomelab.wiki**: Tube Archivist - A Youtube-DL Alternative on Steroids, [2022-01-27] [[link](https://thehomelab.wiki/books/news/page/tube-archivist-a-youtube-dl-alternative-on-steroids)]
* **reddit.com**: Celebrating TubeArchivist v0.1, [2022-01-09] [[link](https://www.reddit.com/r/selfhosted/comments/rzh084/celebrating_tubearchivist_v01/)]
* **linuxunplugged.com**: Pick: tubearchivist — Your self-hosted YouTube media server, [2021-09-11] [[link](https://linuxunplugged.com/425)] and [2021-10-05] [[link](https://linuxunplugged.com/426)]
* **reddit.com**: Introducing Tube Archivist, your self hosted Youtube media server, [2021-09-12] [[link](https://www.reddit.com/r/selfhosted/comments/pmj07b/introducing_tube_archivist_your_self_hosted/)]


## Sponsor
Big thank you to [Digitalocean](https://www.digitalocean.com/) for generously donating credit for the tubearchivist.com VPS and buildserver. 
<p>
  <a href="https://www.digitalocean.com/">
    <img src="https://opensource.nyc3.cdn.digitaloceanspaces.com/attribution/assets/PoweredByDO/DO_Powered_by_Badge_blue.svg" width="201px">
  </a>
</p>

