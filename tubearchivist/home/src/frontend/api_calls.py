"""
Functionality:
- collection of functions and tasks from frontend
- called via user input
"""

from home.src.download.queue import PendingInteract
from home.src.download.subscriptions import (
    ChannelSubscription,
    PlaylistSubscription,
)
from home.src.frontend.watched import WatchState
from home.src.index.channel import YoutubeChannel
from home.src.index.playlist import YoutubePlaylist
from home.src.index.video import YoutubeVideo
from home.src.ta.helper import UrlListParser
from home.src.ta.ta_redis import RedisArchivist, RedisQueue
from home.tasks import (
    download_pending,
    download_single,
    index_channel_playlists,
    kill_dl,
    re_sync_thumbs,
    rescan_filesystem,
    run_backup,
    run_manual_import,
    run_restore_backup,
    subscribe_to,
    update_subscribed,
)


class PostData:
    """
    map frontend http post values to backend funcs
    handover long running tasks to celery
    """

    def __init__(self, post_dict, current_user):
        self.post_dict = post_dict
        self.to_exec, self.exec_val = list(post_dict.items())[0]
        self.current_user = current_user

    def run_task(self):
        """execute and return task result"""
        to_exec = self.exec_map()
        task_result = to_exec()
        return task_result

    def exec_map(self):
        """map dict key and return function to execute"""
        exec_map = {
            "watched": self._watched,
            "un_watched": self._un_watched,
            "change_view": self._change_view,
            "change_grid": self._change_grid,
            "rescan_pending": self._rescan_pending,
            "ignore": self._ignore,
            "dl_pending": self._dl_pending,
            "queue": self._queue_handler,
            "unsubscribe": self._unsubscribe,
            "subscribe": self._subscribe,
            "sort_order": self._sort_order,
            "hide_watched": self._hide_watched,
            "show_subed_only": self._show_subed_only,
            "dlnow": self._dlnow,
            "show_ignored_only": self._show_ignored_only,
            "forgetIgnore": self._forget_ignore,
            "addSingle": self._add_single,
            "deleteQueue": self._delete_queue,
            "manual-import": self._manual_import,
            "re-embed": self._re_embed,
            "db-backup": self._db_backup,
            "db-restore": self._db_restore,
            "fs-rescan": self._fs_rescan,
            "delete-video": self._delete_video,
            "delete-channel": self._delete_channel,
            "delete-playlist": self._delete_playlist,
            "find-playlists": self._find_playlists,
        }

        return exec_map[self.to_exec]

    def _watched(self):
        """mark as watched"""
        WatchState(self.exec_val).mark_as_watched()
        return {"success": True}

    def _un_watched(self):
        """mark as unwatched"""
        WatchState(self.exec_val).mark_as_unwatched()
        return {"success": True}

    def _change_view(self):
        """process view changes in home, channel, and downloads"""
        origin, new_view = self.exec_val.split(":")
        key = f"{self.current_user}:view:{origin}"
        print(f"change view: {key} to {new_view}")
        RedisArchivist().set_message(key, {"status": new_view})
        return {"success": True}

    def _change_grid(self):
        """process change items in grid"""
        grid_items = int(self.exec_val)
        grid_items = max(grid_items, 3)
        grid_items = min(grid_items, 7)

        key = f"{self.current_user}:grid_items"
        print(f"change grid items: {grid_items}")
        RedisArchivist().set_message(key, {"status": grid_items})
        return {"success": True}

    @staticmethod
    def _rescan_pending():
        """look for new items in subscribed channels"""
        print("rescan subscribed channels")
        update_subscribed.delay()
        return {"success": True}

    def _ignore(self):
        """ignore from download queue"""
        video_id = self.exec_val
        print(f"{video_id}: ignore video from download queue")
        PendingInteract(video_id=video_id, status="ignore").update_status()
        # also clear from redis queue
        RedisQueue(queue_name="dl_queue").clear_item(video_id)
        return {"success": True}

    @staticmethod
    def _dl_pending():
        """start the download queue"""
        print("download pending")
        running = download_pending.delay()
        task_id = running.id
        print(f"{task_id}: set task id")
        RedisArchivist().set_message("dl_queue_id", task_id)
        return {"success": True}

    def _queue_handler(self):
        """queue controls from frontend"""
        to_execute = self.exec_val
        if to_execute == "stop":
            print("stopping download queue")
            RedisQueue(queue_name="dl_queue").clear()
        elif to_execute == "kill":
            task_id = RedisArchivist().get_message("dl_queue_id")
            if not isinstance(task_id, str):
                task_id = False
            else:
                print("brutally killing " + task_id)
            kill_dl(task_id)

        return {"success": True}

    def _unsubscribe(self):
        """unsubscribe from channels or playlists"""
        id_unsub = self.exec_val
        print(f"{id_unsub}: unsubscribe")
        to_unsub_list = UrlListParser(id_unsub).process_list()
        for to_unsub in to_unsub_list:
            unsub_type = to_unsub["type"]
            unsub_id = to_unsub["url"]
            if unsub_type == "playlist":
                PlaylistSubscription().change_subscribe(
                    unsub_id, subscribe_status=False
                )
            elif unsub_type == "channel":
                ChannelSubscription().change_subscribe(
                    unsub_id, channel_subscribed=False
                )
            else:
                raise ValueError("failed to process " + id_unsub)

        return {"success": True}

    def _subscribe(self):
        """subscribe to channel or playlist, called from js buttons"""
        id_sub = self.exec_val
        print(f"{id_sub}: subscribe")
        subscribe_to.delay(id_sub)
        return {"success": True}

    def _sort_order(self):
        """change the sort between published to downloaded"""
        sort_order = {"status": self.exec_val}
        if self.exec_val in ["asc", "desc"]:
            RedisArchivist().set_message(
                f"{self.current_user}:sort_order", sort_order
            )
        else:
            RedisArchivist().set_message(
                f"{self.current_user}:sort_by", sort_order
            )
        return {"success": True}

    def _hide_watched(self):
        """toggle if to show watched vids or not"""
        key = f"{self.current_user}:hide_watched"
        message = {"status": bool(int(self.exec_val))}
        print(f"toggle {key}: {message}")
        RedisArchivist().set_message(key, message)
        return {"success": True}

    def _show_subed_only(self):
        """show or hide subscribed channels only on channels page"""
        key = f"{self.current_user}:show_subed_only"
        message = {"status": bool(int(self.exec_val))}
        print(f"toggle {key}: {message}")
        RedisArchivist().set_message(key, message)
        return {"success": True}

    def _dlnow(self):
        """start downloading single vid now"""
        youtube_id = self.exec_val
        print(f"{youtube_id}: downloading now")
        running = download_single.delay(youtube_id=youtube_id)
        task_id = running.id
        print("set task id: " + task_id)
        RedisArchivist().set_message("dl_queue_id", task_id)
        return {"success": True}

    def _show_ignored_only(self):
        """switch view on /downloads/ to show ignored only"""
        show_value = self.exec_val
        key = f"{self.current_user}:show_ignored_only"
        value = {"status": show_value}
        print(f"Filter download view ignored only: {show_value}")
        RedisArchivist().set_message(key, value)
        return {"success": True}

    def _forget_ignore(self):
        """delete from ta_download index"""
        video_id = self.exec_val
        print(f"{video_id}: forget from download")
        PendingInteract(video_id=video_id).delete_item()
        return {"success": True}

    def _add_single(self):
        """add single youtube_id to download queue"""
        video_id = self.exec_val
        print(f"{video_id}: add single vid to download queue")
        PendingInteract(video_id=video_id, status="pending").update_status()
        return {"success": True}

    def _delete_queue(self):
        """delete download queue"""
        status = self.exec_val
        print("deleting from download queue: " + status)
        PendingInteract(status=status).delete_by_status()
        return {"success": True}

    @staticmethod
    def _manual_import():
        """run manual import from settings page"""
        print("starting manual import")
        run_manual_import.delay()
        return {"success": True}

    @staticmethod
    def _re_embed():
        """rewrite thumbnails into media files"""
        print("start video thumbnail embed process")
        re_sync_thumbs.delay()
        return {"success": True}

    @staticmethod
    def _db_backup():
        """backup es to zip from settings page"""
        print("backing up database")
        run_backup.delay("manual")
        return {"success": True}

    def _db_restore(self):
        """restore es zip from settings page"""
        print("restoring index from backup zip")
        filename = self.exec_val
        run_restore_backup.delay(filename)
        return {"success": True}

    @staticmethod
    def _fs_rescan():
        """start file system rescan task"""
        print("start filesystem scan")
        rescan_filesystem.delay()
        return {"success": True}

    def _delete_video(self):
        """delete media file, metadata and thumb"""
        youtube_id = self.exec_val
        YoutubeVideo(youtube_id).delete_media_file()
        return {"success": True}

    def _delete_channel(self):
        """delete channel and all matching videos"""
        channel_id = self.exec_val
        YoutubeChannel(channel_id).delete_channel()
        return {"success": True}

    def _delete_playlist(self):
        """delete playlist, only metadata or incl all videos"""
        playlist_dict = self.exec_val
        playlist_id = playlist_dict["playlist-id"]
        playlist_action = playlist_dict["playlist-action"]
        print(f"{playlist_id}: delete playlist {playlist_action}")
        if playlist_action == "metadata":
            YoutubePlaylist(playlist_id).delete_metadata()
        elif playlist_action == "all":
            YoutubePlaylist(playlist_id).delete_videos_playlist()

        return {"success": True}

    def _find_playlists(self):
        """add all playlists of a channel"""
        channel_id = self.exec_val
        index_channel_playlists.delay(channel_id)
        return {"success": True}
