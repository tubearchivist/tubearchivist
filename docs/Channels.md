# Channels Overview and Channel Detail Page

The channels are organized on two different levels:

## Channels Overview
Accessible at `/channel/` of your Tube Archivist, the **Overview Page** shows a list of all channels you have indexed. 
- You can filter that list to show or hide subscribed channels from the drop down menu. Clicking on the channel banner or the channel name will direct you to the *Channel Detail Page*.
- If you are subscribed to a channel a *Unsubscribe* button will show.

The **Subscribe to Channels** button <img src="assets/icon-add.png?raw=true" alt="add icon" width="20px" style="margin:0 5px;"> opens a text field to subscribe to a channel. You have a few options:
- Enter the YouTube channel ID, a 25 character alphanumeric string. For example *UCBa659QWEk1AI4Tg--mrJ2A*
- Enter the URL to the channel page on YouTube. For example *https://www.youtube.com/channel/UCBa659QWEk1AI4Tg--mrJ2A*
- Enter the video URL for any video and let Tube Archivist extract the channel ID for you. For example *https://www.youtube.com/watch?v=2tdiKTSdE9Y*
- Add one per line.
- **Note**: Adding a link to a YouTube username will not work, for example: *https://www.youtube.com/c/TomScottGo* will fail, because a user can have multiple channels. On YouTube same as on **Tube Archivist**, you can only subscribe to a channel and *not* a user.

The search icon <img src="assets/icon-search.png?raw=true" alt="search icon" width="20px" style="margin:0 5px;"> opens a text box to search for indexed channel names. Possible matches will show as you type. 

## Channel Detail
Each channel will get a dedicated channel detail page accessible at `/channel/<channel-id>/` of your Tube Archivist. This page shows all the videos you have downloaded from this channel plus additional metadata. 
- If you are subscribed to the channel, an *Unsubscribe* button will show.
- You can *Show* the channel description, that matches with the *About* tab on YouTube.
- The **Mark as Watched** button will mark all videos of this channel as watched.
