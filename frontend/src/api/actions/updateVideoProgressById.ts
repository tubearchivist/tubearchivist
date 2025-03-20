import APIClient from '../../functions/APIClient';

type VideoProgressResponseType = {
  watched: boolean;
  duration: number;
  duration_str: string;
  watched_date: number;
  position: number;
  youtube_id: string;
};

type VideoProgressProp = {
  youtubeId: string;
  currentProgress: number;
};

const updateVideoProgressById = async ({ youtubeId, currentProgress }: VideoProgressProp) => {
  return APIClient<VideoProgressResponseType>(`/api/video/${youtubeId}/progress/`, {
    method: 'POST',
    body: { position: currentProgress },
  });
};

export default updateVideoProgressById;
