import { Link } from 'react-router-dom';
import Routes from '../configuration/routes/RouteList';
import { VideoType } from '../pages/Home';
import { ViewStylesType } from '../configuration/constants/ViewStyle';
import humanFileSize from '../functions/humanFileSize';
import { FileSizeUnits } from '../api/actions/updateUserConfig';
import { useUserConfigStore } from '../stores/UserConfigStore';
import { useVideoSelectionStore } from '../stores/VideoSelectionStore';
import iconChecked from '/img/icon-seen.svg';
import iconUnchecked from '/img/icon-unseen.svg';

const StreamsTypeEmun = {
  Video: 'video',
  Audio: 'audio',
};

type VideoListItemProps = {
  videoList: VideoType[] | undefined;
  viewStyle: ViewStylesType;
};

const VideoListItemTable = ({ videoList, viewStyle }: VideoListItemProps) => {
  const { userConfig } = useUserConfigStore();
  const { showSelection, selectedVideoIds, removeVideoId, appendVideoId } =
    useVideoSelectionStore();

  const useSiUnits = userConfig.file_size_unit === FileSizeUnits.Metric;

  let pageIds: string[] = [];
  if (videoList) {
    pageIds = videoList.map(video => video.youtube_id);
  }

  const anySelected = pageIds.some(id => selectedVideoIds.includes(id));

  const handleToggleAllCheck = () => {
    if (anySelected) {
      pageIds.forEach(id => removeVideoId(id));
    } else {
      pageIds.forEach(id => appendVideoId(id));
    }
  };

  return (
    <div className={`video-item ${viewStyle}`}>
      <table>
        <thead>
          <tr>
            {showSelection && (
              <th>
                <img
                  src={anySelected ? iconChecked : iconUnchecked}
                  className="video-item-select"
                  onClick={handleToggleAllCheck}
                />
              </th>
            )}
            <th>Title</th>
            <th>Channel</th>
            <th>Type</th>
            <th>Resolution</th>
            <th>Media size</th>
            <th>Video codec</th>
            <th>Video bitrate</th>
            <th>Audio codec</th>
            <th>Audio bitrate</th>
          </tr>
        </thead>

        <tbody>
          {videoList?.map(({ youtube_id, title, channel, vid_type, media_size, streams }) => {
            const videoStream = streams?.find(s => s.type === StreamsTypeEmun.Video);
            const audioStream = streams?.find(s => s.type === StreamsTypeEmun.Audio);

            return (
              <tr key={youtube_id}>
                {showSelection && (
                  <td>
                    <img
                      src={selectedVideoIds.includes(youtube_id) ? iconChecked : iconUnchecked}
                      className="video-item-select"
                      onClick={() =>
                        selectedVideoIds.includes(youtube_id)
                          ? removeVideoId(youtube_id)
                          : appendVideoId(youtube_id)
                      }
                    />
                  </td>
                )}
                <td className="no-nowrap title">
                  <Link to={Routes.Video(youtube_id)}>{title}</Link>
                </td>
                <td className="no-nowrap">
                  <Link to={Routes.Channel(channel.channel_id)}>{channel.channel_name}</Link>
                </td>
                <td>{vid_type}</td>
                <td>{`${videoStream?.width || '-'}x${videoStream?.height || '-'}`}</td>
                <td>{humanFileSize(media_size, useSiUnits)}</td>
                <td>{videoStream?.codec || '-'}</td>
                <td>{humanFileSize(videoStream?.bitrate || 0, useSiUnits)}</td>
                <td>{audioStream?.codec || '-'}</td>
                <td>{humanFileSize(audioStream?.bitrate || 0, useSiUnits)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default VideoListItemTable;
