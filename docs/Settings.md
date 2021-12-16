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


# Actions
Additional database functionality.

## Manual Media Files Import
So far this depends on the video you are trying to import to be still available on YouTube to get the metadata. Add the files you like to import to the */cache/import* folder. Then start the process from the settings page *Manual Media Files Import*. Make sure to follow one of the two methods below.

### Method 1:
Add a matching *.json* file with the media file. Both files need to have the same base name, for example:
- For the media file: \<base-name>.mp4
- For the JSON file: \<base-name>.info.json
- Alternate JSON file: \<base-name>.json

**Tube Archivist** then looks for the 'id' key within the JSON file to identify the video.

### Method 2:
Detect the YouTube ID from filename, this accepts the default yt-dlp naming convention for file names like:
- \<base-name>[\<youtube-id>].mp4
- The YouTube ID in square brackets at the end of the filename is the crucial part.

### Some notes:
- This will **consume** the files you put into the import folder: Files will get converted to mp4 if needed (this might take a long time...) and moved to the archive, *.json* files will get deleted upon completion to avoid having duplicates on the next run.
- Maybe start with a subset of your files to import to make sure everything goes well...
- Follow the logs to monitor progress and errors: `docker-compose logs -f tubearchivist`.

## Embed thumbnails into media file
This will write or overwrite all thumbnails in the media file using the downloaded thumbnail. This is only necessary if you didn't download the files with the option *Embed Thumbnail* enabled or want to make sure all media files get the newest thumbnail. Follow the docker-compose logs to monitor progress.

## Backup Database
This will backup your metadata into a zip file. The file will get stored at *cache/backup* and will contain the necessary files to restore the Elasticsearch index formatted **nd-json** files plus a complete export of the index in a set of conventional **json** files.  

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

BE AWARE: There is no undo.
