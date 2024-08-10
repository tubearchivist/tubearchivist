import { useLoaderData, useSearchParams } from 'react-router-dom';
import { UserMeType } from '../api/actions/updateUserConfig';
import { useEffect, useState } from 'react';
import { VideoType, ViewLayoutType } from './Home';
import loadSearch from '../api/loader/loadSearch';
import { PlaylistType } from './Playlist';
import { ChannelType } from './Channels';
import VideoList from '../components/VideoList';
import ChannelList from '../components/ChannelList';
import PlaylistList from '../components/PlaylistList';
import SubtitleList from '../components/SubtitleList';
import { ViewStyles } from '../configuration/constants/ViewStyle';
import EmbeddableVideoPlayer from '../components/EmbeddableVideoPlayer';
import { Helmet } from 'react-helmet';
import SearchExampleQueries from '../components/SearchExampleQueries';

const EmptySearchResponse: SearchResultsType = {
  results: {
    video_results: [],
    channel_results: [],
    playlist_results: [],
    fulltext_results: [],
  },
  queryType: 'simple',
};

type SearchResultType = {
  video_results: VideoType[];
  channel_results: ChannelType[];
  playlist_results: PlaylistType[];
  fulltext_results: [];
};

type SearchResultsType = {
  results: SearchResultType;
  queryType: string;
};

type SearchLoaderDataType = {
  userConfig: UserMeType;
};

const Search = () => {
  const { userConfig } = useLoaderData() as SearchLoaderDataType;
  const [searchParams] = useSearchParams();
  const videoId = searchParams.get('videoId');
  const userMeConfig = userConfig.config;

  const view = (userMeConfig.view_style_home || ViewStyles.grid) as ViewLayoutType;
  const gridItems = userMeConfig.grid_items || 3;

  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResultsType>();

  const [refresh, setRefresh] = useState(false);

  const videoList = searchResults?.results.video_results;
  const channelList = searchResults?.results.channel_results;
  const playlistList = searchResults?.results.playlist_results;
  const fulltextList = searchResults?.results.fulltext_results;
  const queryType = searchResults?.queryType;
  const showEmbeddedVideo = videoId !== null;

  const hasSearchQuery = searchQuery.length > 0;
  const hasVideos = Number(videoList?.length) > 0;
  const hasChannels = Number(channelList?.length) > 0;
  const hasPlaylist = Number(playlistList?.length) > 0;
  const hasFulltext = Number(fulltextList?.length) > 0;

  const isSimpleQuery = queryType === 'simple';
  const isVideoQuery = queryType === 'video' || isSimpleQuery;
  const isChannelQuery = queryType === 'channel' || isSimpleQuery;
  const isPlaylistQuery = queryType === 'playlist' || isSimpleQuery;
  const isFullTextQuery = queryType === 'full' || isSimpleQuery;

  const isGridView = view === ViewStyles.grid;
  const gridView = isGridView ? `boxed-${gridItems}` : '';
  const gridViewGrid = isGridView ? `grid-${gridItems}` : '';

  useEffect(() => {
    (async () => {
      if (!hasSearchQuery) {
        setSearchResults(EmptySearchResponse);

        return;
      }

      const searchResults = await loadSearch(searchQuery);

      setSearchResults(searchResults);
      setRefresh(false);
    })();
  }, [searchQuery, refresh, hasSearchQuery]);

  return (
    <>
      <Helmet>
        <title>TubeArchivist</title>
      </Helmet>
      {showEmbeddedVideo && <EmbeddableVideoPlayer videoId={videoId} />}
      <div className={`boxed-content ${gridView}`}>
        <div className="title-bar">
          <h1>Search your Archive</h1>
        </div>
        <div className="multi-search-box">
          <div>
            <input
              type="text"
              name="searchInput"
              autoComplete="off"
              value={searchQuery}
              onChange={event => {
                setSearchQuery(event.target.value);
              }}
            />
          </div>
        </div>
        <div id="multi-search-results">
          {hasSearchQuery && isVideoQuery && (
            <div className="multi-search-result">
              <h2>Video Results</h2>
              <div id="video-results" className={`video-list ${view} ${gridViewGrid}`}>
                <VideoList videoList={videoList} viewLayout={view} refreshVideoList={setRefresh} />
              </div>
            </div>
          )}

          {hasSearchQuery && isChannelQuery && (
            <div className="multi-search-result">
              <h2>Channel Results</h2>
              <div id="channel-results" className={`channel-list ${view} ${gridViewGrid}`}>
                <ChannelList
                  channelList={channelList}
                  viewLayout={view}
                  refreshChannelList={setRefresh}
                />
              </div>
            </div>
          )}

          {hasSearchQuery && isPlaylistQuery && (
            <div className="multi-search-result">
              <h2>Playlist Results</h2>
              <div id="playlist-results" className={`playlist-list ${view} ${gridViewGrid}`}>
                <PlaylistList
                  playlistList={playlistList}
                  viewLayout={view}
                  setRefresh={setRefresh}
                />
              </div>
            </div>
          )}

          {hasSearchQuery && isFullTextQuery && (
            <div className="multi-search-result">
              <h2>Fulltext Results</h2>
              <div id="fulltext-results" className="video-list list">
                <SubtitleList subtitleList={fulltextList} />
              </div>
            </div>
          )}
        </div>

        {!hasVideos && !hasChannels && !hasPlaylist && !hasFulltext && <SearchExampleQueries />}
      </div>
    </>
  );
};

export default Search;
