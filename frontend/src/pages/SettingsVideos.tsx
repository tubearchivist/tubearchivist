import { useEffect, useState } from 'react';
import SettingsNavigation from '../components/SettingsNavigation';
import { ApiResponseType } from '../functions/APIClient';
import loadVideoListByFilter, {
  SortByEnum,
  SortByType,
  SortOrderEnum,
  SortOrderType,
  VideoListByFilterResponseType,
  WatchTypes,
  WatchTypesEnum,
} from '../api/loader/loadVideoListByPage';
import { Link, useOutletContext } from 'react-router-dom';
import { OutletContextType } from './Base';
import Pagination from '../components/Pagination';
import humanFileSize from '../functions/humanFileSize';
import { useUserConfigStore } from '../stores/UserConfigStore';
import { FileSizeUnits } from '../api/actions/updateUserConfig';
import Routes from '../configuration/routes/RouteList';

const SettingsVideos = () => {
  const { userConfig } = useUserConfigStore();
  const { currentPage, setCurrentPage } = useOutletContext() as OutletContextType;

  const [refreshVideoList, setRefreshVideoList] = useState(false);
  const [watchedState, setWatchedState] = useState<WatchTypes>('unwatched');
  const [sortBy, setSortBy] = useState<SortByType>('mediasize');
  const [sortOrder, setSortOrder] = useState<SortOrderType>('desc');

  const [videoResponse, setVideoReponse] =
    useState<ApiResponseType<VideoListByFilterResponseType>>();

  const { data: videoResponseData } = videoResponse ?? {};

  useEffect(() => {
    (async () => {
      const videos = await loadVideoListByFilter({
        page: currentPage,
        watch: watchedState,
        sort: sortBy,
        order: sortOrder,
      });

      setVideoReponse(videos);

      setRefreshVideoList(false);
    })();
  }, [refreshVideoList, currentPage, watchedState, sortBy, sortOrder]);

  const videoList = videoResponseData?.data;
  const pagination = videoResponseData?.paginate;
  const hasVideos = videoResponseData?.data?.length !== 0;

  const useSiUnits = userConfig.file_size_unit === FileSizeUnits.Metric;

  const toggleSortOrder = () => {
    if (sortOrder === 'asc') {
      setSortOrder('desc');
    } else {
      setSortOrder('asc');
    }
  };

  const onHeaderClicked = (header: SortByType) => {
    if (sortBy === header) {
      toggleSortOrder();
    } else {
      setSortBy(header);
    }
  };

  return (
    <>
      <title>TA | Videos</title>
      <div className="boxed-content">
        <SettingsNavigation />

        <div className="title-bar">
          <h1>Video details</h1>
        </div>

        <div className="settings-group video-details">
          <p>
            Show watched:{' '}
            <select
              id="id_watchedstate"
              value={watchedState}
              onChange={event => {
                setWatchedState(event.currentTarget.value as WatchTypes);
              }}
            >
              {Object.entries(WatchTypesEnum).map(([key, value]) => {
                return (
                  <option key={key} value={value}>
                    {key}
                  </option>
                );
              })}
            </select>
            <br />
            Sort by:
            <select
              name="sort_by"
              id="sort"
              value={sortBy}
              onChange={event => {
                setSortBy(event.currentTarget.value as SortByType);
              }}
            >
              {Object.entries(SortByEnum).map(([key, value]) => {
                return <option value={value}>{key}</option>;
              })}
            </select>
            <select
              name="sort_order"
              id="sort-order"
              value={sortOrder}
              onChange={event => {
                setSortOrder(event.currentTarget.value as SortOrderType);
              }}
            >
              {Object.entries(SortOrderEnum).map(([key, value]) => {
                return <option value={value}>{key}</option>;
              })}
            </select>
          </p>
          {!hasVideos && <p>No videos found</p>}

          {hasVideos && (
            <table>
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

              <thead>
                <tr>
                  <th>Channel name</th>
                  <th>Video title</th>
                  <th>Type</th>
                  <th>
                    <a
                      onClick={() => {
                        onHeaderClicked('width');
                      }}
                    >
                      <div>Width</div>
                    </a>
                  </th>
                  <th>
                    <a
                      onClick={() => {
                        onHeaderClicked('height');
                      }}
                    >
                      Height
                    </a>
                  </th>
                  <th>
                    <a
                      onClick={() => {
                        onHeaderClicked('mediasize');
                      }}
                    >
                      Media size
                    </a>
                  </th>
                  <th>Video codec</th>
                  <th>Video bitrate</th>
                  <th>Audio codec</th>
                  <th>Audio bitrate</th>
                </tr>
              </thead>
            </table>
          )}
        </div>

        {pagination && (
          <div className="boxed-content">
            <Pagination pagination={pagination} setPage={setCurrentPage} />
          </div>
        )}
      </div>
    </>
  );
};

export default SettingsVideos;
