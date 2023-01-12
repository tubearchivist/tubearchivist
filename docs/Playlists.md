# Playlist Overview and Playlist Detail Page
The playlists are organized in two different levels, similar as the [channels](Channels):

## Playlist Overview
Accessible at `/playlist/` of your Tube Archivist, this **Overview Page** shows a list of all playlists you have indexed over all your channels.
- You can filter that list to show only subscribed to playlists with the toggle.

You can index playlists of a channel from the channel detail page as described [here](Channels#channel-detail).

The **Subscribe to Playlist** button <img src="assets/icon-add.png?raw=true" alt="add icon" width="20px" style="margin:0 5px;"> opens a text field to subscribe to playlists. You have a few options:
- Enter the YouTube playlist id, for example: *PL96C35uN7xGLLeET0dOWaKHkAlPsrkcha*
- Enter the Youtube dedicated playlist url, for example: *https://www.youtube.com/playlist?list=PL96C35uN7xGLLeET0dOWaKHkAlPsrkcha*
- Add one per line.
- NOTE: It doesn't make sense to subscribe to a playlist if you are already subscribed the corresponding channel as this will slow down the **Rescan Subscriptions** [task](Downloads#rescan-subscriptions).

You can search your indexed playlists by clicking on the search icon <img src="assets/icon-search.png?raw=true" alt="search icon" width="20px" style="margin:0 5px;">. This will open a dedicated page.

## Playlist Detail
Each playlist will get a dedicated playlist detail page accessible at `/playlist/<playlist-id>/` of your Tube Archivist. This page shows all the videos you have downloaded from this playlist.

- If you are subscribed to the playlist, an Unsubscribe button will show, else the Subscribe button will show.
- The **Mark as Watched** button will mark all videos of this playlist as watched.
- The button **Reindex** will reindex the playlist metadata.
- The button **Reindex Videos** will reindex all videos from this playlist.
- The **Delete Playlist** button will give you the option to delete just the *metadata* which won't delete any media files or *delete all* which will delete metadata plus all videos belonging to this playlist.