# Channels Overview and Channel Detail Page

The channels are organized on two different levels, similar as the [playlists](Playlists):

## Channels Overview
Accessible at `/channel/` of your Tube Archivist, the **Overview Page** shows a list of all channels you have indexed. 
- You can filter that list to show or hide subscribed channels with the toggle. Clicking on the channel banner or the channel name will direct you to the *Channel Detail Page*.
- If you are subscribed to a channel a *Unsubscribe* button will show, if you aren't subscribed, a *Subscribe* button will show instead. 

The **Subscribe to Channels** button <img src="assets/icon-add.png?raw=true" alt="add icon" width="20px" style="margin:0 5px;"> opens a text field to subscribe to a channel. You have a few options:
- Enter the YouTube channel ID, a 25 character alphanumeric string. For example *UCBa659QWEk1AI4Tg--mrJ2A*
- Enter the URL to the channel page on YouTube. For example *https://www.youtube.com/channel/UCBa659QWEk1AI4Tg--mrJ2A*
- Enter the channel name for example: *https://www.youtube.com/c/TomScottGo*.
- Enter the video URL for any video and let Tube Archivist extract the channel ID for you. For example *https://www.youtube.com/watch?v=2tdiKTSdE9Y*
- Add one per line.

You can search your indexed channels by clicking on the search icon <img src="assets/icon-search.png?raw=true" alt="search icon" width="20px" style="margin:0 5px;">. This will open a dedicated page.

## Channel Detail
Each channel will get a dedicated channel detail page accessible at `/channel/<channel-id>/` of your Tube Archivist. This page shows all the videos you have downloaded from this channel plus additional metadata. 
- If you are subscribed to the channel, an *Unsubscribe* button will show, else the *Subscribe* button will show.
- You can *Show* the channel description, that matches with the *About* tab on YouTube.
- The **Mark as Watched** button will mark all videos of this channel as watched.
- The button **Delete Channel** will delete the channel plus all videos of this channel, both media files and metadata additionally this will also delete playlists metadata belonging to that channel.
- The button **Show Playlists** will go to the [playlists](Playlists) page and filter the list to only show playlists from this channel.

### Channel Customize
Clicking on the *Configure* button will open a form with options to configure settings on a per channel basis. Any configurations here will overwrite your settings from the [settings](Settings) page.
- **Download Format**: Overwrite the download qualities for videos from this channel.
- **Auto Delete**: Automatically delete watched videos from this channel after selected days.
- **Index Playlists**: Automatically add all Playlists with at least a video downloaded to your index. Only do this for channels where you care about playlists as this will slow down indexing new videos for having to check which playlist this belongs to.
- **SponsorBlock**: Using [SponsorBlock](https://sponsor.ajay.app/) to get and skip sponsored content. Customize per channel: You can *disable* or *enable* SponsorBlock for certain channels only to overwrite the behavior set on the [Settings](settings) page. Selecting *unset* will remove the overwrite and your setting will fall back to the default on the settings page.
