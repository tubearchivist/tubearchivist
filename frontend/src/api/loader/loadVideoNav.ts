import APIClient from '../../functions/APIClient';

export type VideoNavResponseType = {
  playlist_meta: {
    current_idx: number;
    playlist_id: string;
    playlist_name: string;
    playlist_channel: string;
  };
  playlist_previous: {
    youtube_id: string;
    title: string;
    uploader: string;
    idx: number;
    downloaded: boolean;
    vid_thumb: string;
  };
  playlist_next: {
    youtube_id: string;
    title: string;
    uploader: string;
    idx: number;
    downloaded: boolean;
    vid_thumb: string;
  };
};

const loadVideoNav = async (youtubeVideoId: string): Promise<VideoNavResponseType[]> => {
  return APIClient(`/api/video/${youtubeVideoId}/nav/`);
};

export default loadVideoNav;
