import { VideoType, ViewLayoutType } from '../pages/Home';
import VideoListItem from './VideoListItem';

type VideoListProps = {
  videoList: VideoType[] | undefined;
  viewLayout: ViewLayoutType;
  playlistId?: string;
  showReorderButton?: boolean;
  refreshVideoList: (refresh: boolean) => void;
};

const VideoList = ({
  videoList,
  viewLayout,
  playlistId,
  showReorderButton = false,
  refreshVideoList,
}: VideoListProps) => {
  if (!videoList || videoList.length === 0) {
    return <p>No videos found.</p>;
  }

  return (
    <>
      {videoList.map(video => {
        return (
          <VideoListItem
            key={video.youtube_id}
            video={video}
            viewLayout={viewLayout}
            playlistId={playlistId}
            showReorderButton={showReorderButton}
            refreshVideoList={refreshVideoList}
          />
        );
      })}
    </>
  );
};

export default VideoList;
