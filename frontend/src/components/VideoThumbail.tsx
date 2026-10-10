import getApiUrl from '../configuration/getApiUrl';
import defaultVideoThumb from '/img/default-video-thumb.jpg';

type VideoThumbailProps = {
  videoThumbUrl: string | undefined | null;
};

const VideoThumbnail = ({ videoThumbUrl }: VideoThumbailProps) => {
  let src = `${getApiUrl()}${videoThumbUrl}`;

  if (videoThumbUrl === undefined || videoThumbUrl === null) {
    src = defaultVideoThumb;
  }

  return (
    <img
      src={src}
      alt="video_thumb"
      onError={({ currentTarget }) => {
        currentTarget.onerror = null; // prevents looping
        currentTarget.src = defaultVideoThumb;
      }}
    />
  );
};

export default VideoThumbnail;
