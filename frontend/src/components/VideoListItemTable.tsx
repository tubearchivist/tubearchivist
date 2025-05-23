import { Link } from 'react-router-dom';
import Routes from '../configuration/routes/RouteList';
import { VideoType } from '../pages/Home';
import { ViewStylesType } from '../configuration/constants/ViewStyle';
import humanFileSize from '../functions/humanFileSize';
import { FileSizeUnits } from '../api/actions/updateUserConfig';
import { useUserConfigStore } from '../stores/UserConfigStore';

type VideoListItemProps = {
  videoList: VideoType[] | undefined;
  viewStyle: ViewStylesType;
};

const VideoListItemTable = ({ videoList, viewStyle }: VideoListItemProps) => {
  const { userConfig } = useUserConfigStore();

  const useSiUnits = userConfig.file_size_unit === FileSizeUnits.Metric;

  return (
    <div className={`video-item ${viewStyle}`}>
      <table>
        <thead>
          <tr>
            <th>Channel</th>
            <th>Title</th>
            <th>Type</th>
            <th>Width</th>
            <th>Height</th>
            <th>Media size</th>
            <th>Video codec</th>
            <th>Video bitrate</th>
            <th>Audio codec</th>
            <th>Audio bitrate</th>
          </tr>
        </thead>

        <tbody>
          {videoList?.map(({ youtube_id, title, channel, vid_type, media_size, streams }) => {
            const [videoStream, audioStream] = streams;

            return (
              <tr key={youtube_id}>
                <td>
                  <Link to={Routes.Channel(channel.channel_id)}>{channel.channel_name}</Link>
                </td>
                <td>
                  <Link to={Routes.Video(youtube_id)}>{title}</Link>
                </td>
                <td>{vid_type}</td>
                <td>{videoStream.width}</td>
                <td>{videoStream.height}</td>
                <td>{humanFileSize(media_size, useSiUnits)}</td>
                <td>{videoStream.codec}</td>
                <td>{humanFileSize(videoStream.bitrate, useSiUnits)}</td>
                <td>{audioStream.codec}</td>
                <td>{humanFileSize(audioStream.bitrate, useSiUnits)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default VideoListItemTable;
