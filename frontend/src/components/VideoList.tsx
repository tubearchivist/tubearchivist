import { ViewStylesEnum, ViewStylesType } from '../configuration/constants/ViewStyle';
import { VideoType } from '../pages/Home';
import VideoListItem from './VideoListItem';
import VideoListItemTable from './VideoListItemTable';

type VideoListProps = {
  videoList: VideoType[] | undefined;
  viewStyle: ViewStylesType;
  playlistId?: string;
  showReorderButton?: boolean;
  refreshVideoList: (refresh: boolean) => void;
};

const VideoList = ({
  videoList,
  viewStyle,
  playlistId,
  showReorderButton = false,
  refreshVideoList,
}: VideoListProps) => {
  if (!videoList || videoList.length === 0) {
    return <p>No videos found.</p>;
  }

  if (viewStyle === ViewStylesEnum.Table) {
    return <VideoListItemTable videoList={videoList} viewStyle={viewStyle} />;
  }

  return (
    <>
      {videoList.map(video => {
        return (
          <VideoListItem
            key={video.youtube_id}
            video={video}
            viewStyle={viewStyle}
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
