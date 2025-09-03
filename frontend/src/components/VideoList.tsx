import { ViewStylesEnum, ViewStylesType } from '../configuration/constants/ViewStyle';
import { VideoType } from '../pages/Home';
import VideoListItem from './VideoListItem';
import VideoListItemTable from './VideoListItemTable';
import LoadingIndicator from './LoadingIndicator';

type VideoListProps = {
  videoList: VideoType[] | undefined;
  viewStyle: ViewStylesType;
  playlistId?: string;
  showReorderButton?: boolean;
  allowInlinePlay?: boolean;
  refreshVideoList: (refresh: boolean) => void;
};

const VideoList = ({
  videoList,
  viewStyle,
  playlistId,
  showReorderButton = false,
  allowInlinePlay = true,
  refreshVideoList,
}: VideoListProps) => {
  if (!videoList) {
    return <LoadingIndicator />;
  }
  if (videoList.length === 0) {
    return <h2>No videos found...</h2>;
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
            allowInlinePlay={allowInlinePlay}
            refreshVideoList={refreshVideoList}
          />
        );
      })}
    </>
  );
};

export default VideoList;
