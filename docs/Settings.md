# Settings Page
Accessible at `/settings/` of your **Tube Archivist**, this page holds all the configurations and additional functionality related to the database.

Click on **Update Settings** at the bottom of the form to apply your configurations.

## Color scheme
Switch between the easy on the eyes dark theme and the burning bright theme.

## Archive View
These default values will get applied on container restart. 
- **Default Sort**: This defines the default sort order as described on the [Main](Main.md) page.
- **Default Hide Watched**: Hide watched videos by default.
- **Show Subscribed Channels Only**: This controls the filter on the *Channel Overview Page*. 
- **Page Size**: Defines how many results get displayed on a given page. Same value goes for all archive views.

## Subscriptions
Settings related to the channel management.
- **Channel Page Size**: Defines how many pages will get analyzed by **Tube Archivist** each time you click on *Rescan Subscriptions*. The default page size used by yt-dlp is **50**, that's also the recommended value to set here. Any value higher will slow down the rescan process, for example if you set the value to 51, that means yt-dlp will have to go through 2 pages of results instead of 1 and by that doubling the time that process takes.

## Downloads
Settings related to the download process.
- **Download Limit**: Stop the download process after downloading the set quantity of videos.
- **Download Speed Limit**: Set your download speed limit in KB/s. This will pass the option `--limit-rate` to yt-dlp.
- **Sleep Interval**: Time in seconds to sleep between requests to YouTube. It's a good idea to set this to **3** seconds. Might be necessary to avoid throttling.

## Download Format
Additional settings passed to yt-dlp.
- **Format**: This controls which streams get downloaded and is equivalent to passing `--format` to yt-dlp. Use one of the recommended one or look at the documentation of [yt-dlp](https://github.com/yt-dlp/yt-dlp#format-selection). Please note: The option `--merge-output-format mp4` is automatically passed to yt-dlp to guarantee browser compatibility.
- **Embed Metadata**: This saves the available tags directly into the media file by passing `--embed-metadata` to yt-dlp.


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

## Backup Database
This will backup your metadata into a zip file. The file will get stored at *cache/backup* and will contain the necessary files to restore the Elasticsearch index formatted **nd-json** files plus a complete export of the index in a set of conventional **json** files.  

BE AWARE: This will **not** backup any media files, just the metadata from the Elasticsearch.

## Restore From Backup
The restore functionality will expect the same zip file in *cache/backup* as created from the **Backup database** function. This will recreate the index from the snapshot. If there are multiple backup files in the folder, the newest one will take priority. 

BE AWARE: This will **replace** your current index with the one from the backup file. This won't restore any media files.