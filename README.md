![Tube Archivist](assets/tube-archivist-banner.jpg?raw=true "Tube Archivist Banner")  

<h1 align="center">Your self hosted YouTube media server</h1>
<div align="center">
<a href="https://github.com/bbilly1/tilefy" target="_blank"><img src="https://tiles.tilefy.me/t/tubearchivist-docker.png" alt="tubearchivist-docker" title="Tube Archivist Docker Pulls" height="50" width="190"/></a>
<a href="https://github.com/bbilly1/tilefy" target="_blank"><img src="https://tiles.tilefy.me/t/tubearchivist-github-star.png" alt="tubearchivist-github-star" title="Tube Archivist GitHub Stars" height="50" width="190"/></a>
<a href="https://github.com/bbilly1/tilefy" target="_blank"><img src="https://tiles.tilefy.me/t/tubearchivist-github-forks.png" alt="tubearchivist-github-forks" title="Tube Archivist GitHub Forks" height="50" width="190"/></a>
<a href="https://www.tubearchivist.com/discord" target="_blank"><img src="https://tiles.tilefy.me/t/tubearchivist-discord.png" alt="tubearchivist-discord" title="TA Discord Server Members" height="50" width="190"/></a>
</div>

![home screenshot](assets/tube-archivist-screenshot-home.png?raw=true "Tube Archivist Home")

## Table of contents:
* [Wiki](https://github.com/tubearchivist/tubearchivist/wiki) with [FAQ](https://github.com/tubearchivist/tubearchivist/wiki/FAQ)
* [Core functionality](#core-functionality)
* [Connect](#connect)
* [Extended Universe](#extended-universe)
* [Installing and updating](#installing-and-updating)
* [Getting Started](#getting-started)
* [Known limitations](#known-limitations)
* [Donate](#donate)

------------------------

## Core functionality
Once your YouTube video collection grows, it becomes hard to search and find a specific video. That's where Tube Archivist comes in: By indexing your video collection with metadata from YouTube, you can organize, search and enjoy your archived YouTube videos without hassle offline through a convenient web interface. THis includes:  
* Subscribe to your favorite YouTube channels
* Download Videos using **yt-dlp**
* Index and make videos searchable
* Play videos
* Keep track of viewed and unviewed videos


## Showcase
To see more examples of the software in use, check out [Showcase](SHOWCASE.MD)
  
## Connect
- [Discord](https://www.tubearchivist.com/discord): Connect with us on our Discord server.
- [r/TubeArchivist](https://www.reddit.com/r/TubeArchivist/): Join our Subreddit.

## Extended Universe
- [Browser Extension](https://github.com/tubearchivist/browser-extension) Tube Archivist Companion, for [Firefox](https://addons.mozilla.org/addon/tubearchivist-companion/) and [Chrome](https://chrome.google.com/webstore/detail/tubearchivist-companion/jjnkmicfnfojkkgobdfeieblocadmcie)
- [Tube Archivist Metrics](https://github.com/tubearchivist/tubearchivist-metrics) to create statistics in Prometheus/OpenMetrics format.  


## Installing and updating
For minimal system requirements, the Tube Archivist stack needs around 2GB of available memory for a small testing setup and around 4GB of available memory for a mid to large sized installation. Minimal with dual core with 4 threads, better quad core plus. 
This project requires docker. Ensure it is installed and running on your system.  

If you are using Podman, Unraid, TrueNAS, and Synology, visit [https://docs.tubearchivist.com](https://docs.tubearchivist.com) for more dedicated instructions for those systems. Otherwise, continue on.

To get up and running quickly, here are the configuration options that you will need to set to start TubeArchivist:  
| Configuration Option | Value |
| ----------- | ----------- |
| tubearchivist/environment/TA_HOST | Change to the IP/Domain Name of the machine you are running on |
| tubearchivist/environment/TA_PASSWORD | Set your initial password when logging in |
| tubearchivist/environment/TZ | Set your timezone. Format is "America/New_York" |
| tubearchivist/environment/ELASTIC_PASSWORD | Set the password for ElasticSearch |
| archivist-es/environment/ELASTIC_PASSWORD | Match the ElasticSearch password set above |  



To actually start TubeArchvist, `cd` into the directory where the `docker-compose.yml` file is located and run `docker compose up --detach` in terminal. The first time you do this it will download the appropriate images, which can take a minute.

You can follow the logs with `docker compose logs -f`. Once it's ready it will print something like `celery@1234567890ab ready`. At this point you should be able to go to `http://your-host:8000` and log in with the `TA_USER`/`TA_PASSWORD` credentials.

You can bring the application down by running `docker compose down` in the same directory.
Always use the *latest* (the default) or a named semantic version tag for the docker images, unless if you are doing development.

If you want more advanced options, or more detailed instructions on how to set up the containers, you can visit [https://docs.tubearchivist.com/installation/docker](https://docs.tubearchivist.com/installation/docker) or [https://github.com/tubearchivist/docs/tree/master/mkdocs/docs](https://github.com/tubearchivist/docs/tree/master/mkdocs/docs). 

## Getting Started
1. Go through the **settings** page and look at the available options. Particularly set *Download Format* to your desired video quality before downloading. **Tube Archivist** downloads the best available quality by default. To support iOS or MacOS and some other browsers a compatible format must be specified. For example:
```
bestvideo[vcodec*=avc1]+bestaudio[acodec*=mp4a]/mp4
```
2. Subscribe to some of your favorite YouTube channels on the **channels** page. 
3. On the **downloads** page, click on *Rescan subscriptions* to add videos from the subscribed channels to your Download queue or click on *Add to download queue* to manually add Video IDs, links, channels or playlists.
4. Click on *Start download* and let **Tube Archivist** to it's thing. 
5. Enjoy your archived collection!


## Known limitations
- Video files created by Tube Archivist need to be playable in your browser of choice. Not every codec is compatible with every browser and might require some testing with format selection. 
- Every limitation of **yt-dlp** will also be present in Tube Archivist. If **yt-dlp** can't download or extract a video for any reason, Tube Archivist won't be able to either.
- There is currently no flexibility in naming of the media files.

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


## Donate
The best donation to **Tube Archivist** is your time, take a look at the [contribution page](CONTRIBUTING.md) to get started.  
Second best way to support the development is to provide for caffeinated beverages:
* [GitHub Sponsor](https://github.com/sponsors/bbilly1) become a sponsor here on GitHub
* [Paypal.me](https://paypal.me/bbilly1) for a one time coffee
* [Paypal Subscription](https://www.paypal.com/webapps/billing/plans/subscribe?plan_id=P-03770005GR991451KMFGVPMQ) for a monthly coffee
* [ko-fi.com](https://ko-fi.com/bbilly1) for an alternative platform

## Notable mentions
This is a selection of places where this project has been featured on reddit, in the news, blogs or any other online media. Sorted by newest on the top.
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

