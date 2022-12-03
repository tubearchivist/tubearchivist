# Settings Page
Accessible at `/settings/` of your **Tube Archivist**, this page holds all the configurations and additional functionality related to the database.

Click on **Update Settings** at the bottom of the form to apply your configurations.

## Color scheme
Switch between the easy on the eyes dark theme and the burning bright theme.

## Archive View
- **Page Size**: Defines how many results get displayed on a given page. Same value goes for all archive views.

## Subscriptions
Settings related to the channel management.
- **Channel Page Size**: Defines how many pages will get analyzed by **Tube Archivist** each time you click on *Rescan Subscriptions*. The default page size used by yt-dlp is **50**, that's also the recommended value to set here. Any value higher will slow down the rescan process, for example if you set the value to 51, that means yt-dlp will have to go through 2 pages of results instead of 1 and by that doubling the time that process takes.

## Downloads
Settings related to the download process.
- **Download Limit**: Stop the download process after downloading the set quantity of videos.
- **Download Speed Limit**: Set your download speed limit in KB/s. This will pass the option `--limit-rate` to yt-dlp.
- **Throttled Rate Limit**: Restart download if the download speed drops below this value in KB/s. This will pass the option `--throttled-rate` to yt-dlp. Using this option might have a negative effect if you have an unstable or slow internet connection.
- **Sleep Interval**: Time in seconds to sleep between requests to YouTube. It's a good idea to set this to **3** seconds. Might be necessary to avoid throttling.
- **Auto Delete Watched Videos**: Automatically delete videos marked as watched after selected days. If activated, checks your videos after download task is finished.

## Download Format
Additional settings passed to yt-dlp.
- **Format**: This controls which streams get downloaded and is equivalent to passing `--format` to yt-dlp. Use one of the recommended one or look at the documentation of [yt-dlp](https://github.com/yt-dlp/yt-dlp#format-selection). Please note: The option `--merge-output-format mp4` is automatically passed to yt-dlp to guarantee browser compatibility. Similar to that, `--check-formats` is passed as well to check that the selected formats are actually downloadable.
- **Embed Metadata**: This saves the available tags directly into the media file by passing `--embed-metadata` to yt-dlp.
- **Embed Thumbnail**: This will save the thumbnail into the media file by passing `--embed-thumbnail` to yt-dlp.

## Subtitles
- **Download Setting**: Select the subtitle language you like to download. Add a comma separated list for multiple languages.
- **Source Settings**: User created subtitles are provided from the uploader and are usually the video script. Auto generated is from YouTube, quality varies, particularly for auto translated tracks.
- **Index Settings**: Enabling subtitle indexing will add the lines to Elasticsearch and will make subtitles searchable. This will increase the index size and is not recommended on low-end hardware.

## Comments
- **Download and index comments**: Set your configuration for downloading and indexing comments. This takes the same values as documented in the `max_comments` section for the youtube extractor of [yt-dlp](https://github.com/yt-dlp/yt-dlp#youtube). Add without space between the four different fields: *max-comments,max-parents,max-replies,max-replies-per-thread*. Example:
  - `all,100,all,30`: Get 100 max-parents and 30 max-replies-per-thread.
  - `1000,all,all,50`: Get a total of 1000 comments over all, 50 replies per thread.
- **Comment sort method**: Change sort method between *top* or *new*. The default is *top*, as decided by YouTube.
- The [Refresh Metadata](#refresh-metadata) background task will get comments from your already archived videos, spreading the requests out over time.  

Archiving comments is slow as only very few comments get returned per request with yt-dlp. Choose your configuration above wisely. Tube Archivist will download comments after the download queue finishes, your videos will be already available while the comments are getting downloaded.

## Cookie
Importing your YouTube Cookie into Tube Archivist allows yt-dlp to bypass age restrictions, gives access to private videos and your *watch later* or *liked videos*.

### Security concerns
Cookies are used to store your session and contain your access token to your google account, this information can be used to take over your account. Treat that data with utmost care as you would any other password or credential. *Tube Archivist* stores your cookie in Redis and will automatically append it to yt-dlp for every request.

### Auto import
Easiest way to import your cookie is to use the **Tube Archivist Companion** [browser extension](https://github.com/tubearchivist/browser-extension) for Firefox and Chrome.

### Alternative Manual Export your cookie
- Install **Cookies.txt** addon for [chrome](https://chrome.google.com/webstore/detail/get-cookiestxt/bgaddhkoddajcdgocldbbfleckgcbcid) or [firefox](https://addons.mozilla.org/firefox/addon/cookies-txt).
- Visit YouTube and login with whichever YouTube account you wish to use to generate the cookies.
- Click on the extension icon in the toolbar - it will drop down showing the active cookies for YT.
- Click Export to export the cookies, filename is by default *cookies.google.txt*.

### Alternative Manual Import your cookie
Place the file *cookies.google.txt* into the *cache/import* folder of Tube Archivist and enable the cookie import. Once you click on *Update Application Configurations* to save your changes, your cookie will get imported and stored internally.

Once imported, a **Validate Cookie File** button will show, where you can confirm if your cookie is working or not.

### Use your cookie
Once imported, additionally to the advantages above, your [Watch Later](https://www.youtube.com/playlist?list=WL) and [Liked Videos](https://www.youtube.com/playlist?list=LL) become a regular playlist you can download and subscribe to as any other [playlist](Playlists).

### Limitation
There is only one cookie per Tube Archivist instance, this will be shared between all users.

## Integrations
All third party integrations of TubeArchivist will **always** be *opt in*.
- **API**: Your access token for the Tube Archivist API.
- **returnyoutubedislike.com**: This will get return dislikes and average ratings for each video by integrating with the API from [returnyoutubedislike.com](https://www.returnyoutubedislike.com/).
- **SponsorBlock**: Using [SponsorBlock](https://sponsor.ajay.app/) to get and skip sponsored content. If a video doesn't have timestamps, or has unlocked timestamps, use the browser addon to contribute to this excellent project. Can also be activated and deactivated as a per [channel overwrite](Settings#channel-customize).
- **Cast**: Enabling the cast integration in the settings page will load an additional JS library from **Google**.  
*NOTE*: This feature is currently broken due to an authentication issue, see #331.
Requirements:
    - HTTPS: To use the cast integration HTTPS needs to be enabled, which can be done using a reverse proxy. This is a requirement by Google as communication to the cast device is required to be encrypted, but the content itself is not.
    - Supported Browser:A supported browser is required for this integration such as Google Chrome. Other browsers, especially Chromium-based browsers, may support casting by enabling it in the settings.
    - Subtitles: Subtitles are supported however they do not work out of the box and require additional configuration. Due to requirements by Google, to use subtitles you need additional headers which will need to be configured in your reverse proxy. See this [page](https://developers.google.com/cast/docs/web_sender/advanced#cors_requirements) for the specific requirements.  
    You need the following headers: Content-Type, Accept-Encoding, and Range. Note that the last two headers, Accept-Encoding and Range, are additional headers that you may not have needed previously.  
    Wildcards "*" cannot be used for the Access-Control-Allow-Origin header. If the page has protected media content, it must use a domain instead of a wildcard.

## Snapshots
System snapshots will automatically make daily snapshots of the Elasticsearch index. The task will start at 12pm your local time. Snapshots are deduplicated, meaning that each snapshot will only have to backup changes since the last snapshot. The initial snapshot may be slow, but subsequent runs will be much faster. There is also a cleanup function implemented, that will remove snapshots older than 30 days.

This will make a snapshot of your metadata index only, no media files or additional configuration variables you have set on the settings page will be backed up.

Due to these improvements compared to the previous backup solution, system snapshots will replace the current backup system in a future version.

Before activating system snapshots, you'll have to add one additional environment variables to the *archivist-es* container:
```
path.repo=/usr/share/elasticsearch/data/snapshot
```
The variable `path.repo` will set the folder where the snapshots will go inside the Elasticsearch container, you can't change it, but the variable needs to be set. Rebuild the container for changes to take effect, e.g `docker compose up -d`.

- **Create snapshot now**: Will start the snapshot process now, outside of the regular daily schedule.
- **Restore**: Restore your index to that point in time.

# Scheduler Setup
Schedule settings expect a cron like format, where the first value is minute, second is hour and third is day of the week. Day 0 is Sunday, day 1 is Monday etc.

Examples:
- **0 15 \***: Run task every day at 15:00 in the afternoon.
- **30 8 \*/2**: Run task every second day of the week (Sun, Tue, Thu, Sat) at 08:30 in the morning.
- **0 \*/3,8-17 \***: Execute every hour divisible by 3, and every hour during office hours (8 in the morning - 5 in the afternoon).
- **0 8,16 \***: Execute every day at 8 in the morning and at 4 in the afternoon.
- **auto**: Sensible default.
- **0**: (zero), deactivate that task.

NOTE:
- Changes in the scheduler settings require a container restart to take effect.
- Cron format as *number*/*number* are none standard cron and are not supported by the scheduler, for example **0 0/12 \*** is invalid, use **0 \*/12 \*** instead.
- Avoid an unnecessary frequent schedule to not get blocked by YouTube. For that reason, the scheduler doesn't support schedules that trigger more than once per hour.

## Rescan Subscriptions
That's the equivalent task as run from the downloads page looking through your channel and playlist and add missing videos to the download queue.

## Start download
Start downloading all videos currently in the download queue.

## Refresh Metadata
Rescan videos, channels and playlists on youtube and update metadata periodically. This will also refresh your subtitles based on your current settings. If an item is no longer available on YouTube, this will deactivate it and exclude it from future refreshes. This task is meant to be run once per day, set your schedule accordingly.

The field **Refresh older than x days** takes a number where TubeArchivist will consider an item as *outdated*. This value is used to calculate how many items need to be refreshed today based on the total indexed. This will spread out the requests to YouTube. Sensible value here is **90** days.

## Thumbnail check
This will check if all expected thumbnails are there and will delete any artwork without matching video.

## Index backup
Create a zip file of the metadata and select **Max auto backups to keep** to automatically delete old backups created from this task.


# Actions
Additional database functionality.

## Delete download queue
The button **Delete all queued** will delete all pending videos from the download queue. The button **Delete all ignored** will delete all videos you have previously ignored.

## Manual Media Files Import
NOTE: This is inherently error prone, as there are many variables, some outside of the control of this project. Read this carefully and use at your own risk. 

Add the files you'd like to import to the */cache/import* folder. Only add files, don't add subdirectories. All files you are adding, need to have the same *base name* as the media file. Then start the process from the settings page *Manual Media Files Import*.

Valid media extensions are *.mp4*, *.mkv* or *.webm*. If you have other file extensions or incompatible codecs, convert them first to mp4. **Tube Archivist** can identify the videos with one of the following methods.

### Method 1:
Add a matching *.info.json* file with the media file. Both files need to have the same base name, for example:
- For the media file: `<base-name>.mp4`
- For the JSON file: `<base-name>.info.json`

The import process then looks for the 'id' key within the JSON file to identify the video.

### Method 2:
Detect the YouTube ID from filename, this accepts the default yt-dlp naming convention for file names like:
- `<base-name>[<youtube-id>].mp4`
- The YouTube ID in square brackets at the end of the filename is the crucial part.

### Offline import:
If the video you are trying to import is not available on YouTube any more, **Tube Archivist** can import the required metadata:
- The file `<base-name>.info.json` is required to extract the required information.
- Add the thumbnail as `<base-name>.<ext>`, where valid file extensions are *.jpg*, *.png* or *.webp*. If there is no thumbnail file, **Tube Archivist** will try to extract the embedded cover from the media file or will fallback to a default thumbnail.
- Add subtitles as `<base-name>.<lang>.vtt` where *lang* is the two letter ISO country code. This will archive all subtitle files you add to the import folder, independent from your configurations. Subtitles can be archived and used in the player, but they can't be indexed or made searchable due to the fact, that they have a very different structure than the subtitles as **Tube Archivist** needs them.
- For videos, where the whole channel is not available any more, you can add the `<channel-id>.info.json` file as generated by *youtube-dl/yt-dlp* to get the full metadata. Alternatively **Tube Archivist** will extract as much info as possible from the video info.json file. 

### Some notes:
- This will **consume** the files you put into the import folder: Files will get converted to mp4 if needed (this might take a long time...) and moved to the archive, *.json* files will get deleted upon completion to avoid having duplicates on the next run.
- For best file transcoding quality, convert your media files with desired settings first before importing.
- Maybe start with a subset of your files to import to make sure everything goes well...
- Follow the logs to monitor progress and errors: `docker-compose logs -f tubearchivist`.

## Embed thumbnails into media file
This will write or overwrite all thumbnails in the media file using the downloaded thumbnail. This is only necessary if you didn't download the files with the option *Embed Thumbnail* enabled or want to make sure all media files get the newest thumbnail. Follow the docker-compose logs to monitor progress.

## Backup Database
This will backup your metadata into a zip file. The file will get stored at *cache/backup* and will contain the necessary files to restore the Elasticsearch index formatted **nd-json** files.  

BE AWARE: This will **not** backup any media files, just the metadata from the Elasticsearch.

## Restore From Backup
The restore functionality will expect the same zip file in *cache/backup* as created from the **Backup database** function. This will recreate the index from the snapshot. There will be a list of all available backup to choose from. The *source* tag can have these different values:
- **manual**: For backups manually created from here on the settings page.
- **auto**: For backups automatically created via a sceduled task.
- **update**: For backups created after a Tube Archivist update due to changes in the index.
- **False**: Undefined.

BE AWARE: This will **replace** your current index with the one from the backup file. This won't restore any media files.

## Rescan Filesystem
This function will go through all your media files and looks at the whole index to try to find any issues:
- Should the filename not match with the indexed media url, this will rename the video files correctly and update the index with the new link.
- When you delete media files from the filesystem outside of the Tube Archivist interface, this will delete leftover metadata from the index.
- When you have media files that are not indexed yet, this will grab the metadata from YouTube like it was a newly downloaded video. This can be useful when restoring from an older backup file with missing metadata but already downloaded mediafiles. NOTE: This only works if the media files are named in the same convention as Tube Archivist does, particularly the YouTube ID needs to be at the same index in the filename, alternatively see above for *Manual Media Files Import*.
-This will also check all of your thumbnails and download any that are missing.

BE AWARE: There is no undo.
