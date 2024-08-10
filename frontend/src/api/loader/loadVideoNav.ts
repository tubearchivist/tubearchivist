import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import isDevEnvironment from '../../functions/isDevEnvironment';

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
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/video/${youtubeVideoId}/nav/`, {
    headers: defaultHeaders,
    credentials: getFetchCredentials(),
  });

  const videoNav = await response.json();

  if (isDevEnvironment()) {
    console.log('loadVideoNav', videoNav);
  }

  return videoNav;
};

export default loadVideoNav;
