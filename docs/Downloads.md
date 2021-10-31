# Downloads Page
Accessible at `/downloads/` of your Tube Archivist, this page handles all the download functionality.


## Rescan Subscriptions
The **Rescan Subscriptions** icon <img src="assets/icon-rescan.png?raw=true" alt="rescan icon" width="20px" style="margin:0 5px;"> will start a background task to look for new videos from the channels you are subscribed to. You can define the channel page size on the [settings page](Settings#subscriptions). With the default channel page size, expect this process to take around 2-3 seconds for each channel you are subscribed to. A status message will show the progress.

Then for every video found, **Tube Archivist** will skip the video if it has already been downloaded or if you added it to the *ignored* list before. All the other videos will get added to the download queue. Expect this to take around 1 second for each video as **Tube Archivist** needs to grab some additional metadata. New videos will get added at the bottom of the download queue.

## Download Queue
The **Start Download** icon <img src="assets/icon-download.png?raw=true" alt="download icon" width="20px" style="margin:0 5px;"> will start the download process starting from the top of the queue. Take a look at the relevant settings on the [Settings Page](Settings#downloads). Once the process started, a progress message will show with additional details and controls: 
- The stop icon <img src="assets/icon-stop.png?raw=true" alt="stop icon" width="20px" style="margin:0 5px;"> will gracefully stop the download process, once the current video has been finished successfully.
- The cancel icon <img src="assets/icon-close-red.png?raw=true" alt="close icon" width="20px" style="margin:0 5px;"> is equivalent to killing the process and will stop the download immediately. Any leftover files will get deleted, the canceled video will still be available in the download queue.

## Add to Download Queue
The **Add to Download Queue** icon <img src="assets/icon-add.png?raw=true" alt="add icon" width="20px" style="margin:0 5px;"> opens a text field to manually add videos to the download queue. You have a few options:
- Add a link to a YouTube video. For example *https://www.youtube.com/watch?v=2tdiKTSdE9Y*.
- Add a YouTube video ID. For example *2tdiKTSdE9Y*.
- Add a link to a YouTube video by providing the shortened URL, for example *https://youtu.be/2tdiKTSdE9Y*.
- Add a Channel ID or Channel URL to add every available video to the download queue. This will ignore the channel page size as described before and is meant for an initial download of the whole channel. You can still ignore selected videos before starting the download.
- Add a channel name like for example *https://www.youtube.com/c/TomScottGo*.
- Add a playlist ID or URL to add every available video in the list to the download queue, for example *https://www.youtube.com/playlist?list=PL96C35uN7xGLLeET0dOWaKHkAlPsrkcha* or *PL96C35uN7xGLLeET0dOWaKHkAlPsrkcha*. Note that when you add a link to a video in a playlist, Tube Archivist assumes you want to download only the specific video and not the whole playlist, for example *https://www.youtube.com/watch?v=CINVwWHlzTY&list=PL96C35uN7xGLLeET0dOWaKHkAlPsrkcha* will only add one video *CINVwWHlzTY* to the queue.
- Add one link per line.

## The Download Queue
Below the three buttons you find the download queue. New items will get added at the bottom of the queue, the next video to download once you click on **Start Download** will be the first in the list.

Every video in the download queue has two buttons:
- **Ignore**: This will remove that video from the download queue and this video will not get added again, even when you **Rescan Subscriptions**.
- **Download now**: This will give priority to this video. If the download process is already running, the prioritized video will get downloaded as soon as the current video is finished. If there is no download process running, this will start downloading this single video and stop after that.

You can flip the view by activating **Show Only Ignored Videos**. This will show all videos you have previously *ignored*.  
Every video in the ignored list has two buttons:
- **Forget**: This will delete the item form the ignored list.
- **Add to Queue**: This will add the ignored video back to the download queue.
