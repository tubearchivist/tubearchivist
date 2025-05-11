import { useSearchParams } from 'react-router-dom';
import { useEffect, useState } from 'react';
import loadSearch, { SearchResultsType } from '../api/loader/loadSearch';
import VideoList from '../components/VideoList';
import ChannelList from '../components/ChannelList';
import PlaylistList from '../components/PlaylistList';
import SubtitleList from '../components/SubtitleList';
import { ViewStylesEnum } from '../configuration/constants/ViewStyle';
import EmbeddableVideoPlayer from '../components/EmbeddableVideoPlayer';
import SearchExampleQueries from '../components/SearchExampleQueries';
import { useUserConfigStore } from '../stores/UserConfigStore';
import { ApiResponseType } from '../functions/APIClient';

const EmptySearchResponse: ApiResponseType<SearchResultsType> = {
  data: {
    results: {
      video_results: [],
      channel_results: [],
      playlist_results: [],
      fulltext_results: [],
    },
    queryType: 'simple',
  },
  error: undefined,
  status: 200,
};

const Search = () => {
  const { userConfig } = useUserConfigStore();
  const [searchParams] = useSearchParams();
  const videoId = searchParams.get('videoId');

  const viewVideos = userConfig.view_style_home;
  const viewChannels = userConfig.view_style_channel;
  const viewPlaylists = userConfig.view_style_playlist;
  const gridItems = userConfig.grid_items || 3;

  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState<string>('');
  const [searchResults, setSearchResults] = useState<ApiResponseType<SearchResultsType>>();

  const [refresh, setRefresh] = useState(false);

  const { data: searchResultsData } = searchResults ?? {};

  const videoList = searchResultsData?.results.video_results;
  const channelList = searchResultsData?.results.channel_results;
  const playlistList = searchResultsData?.results.playlist_results;
  const fulltextList = searchResultsData?.results.fulltext_results;
  const queryType = searchResultsData?.queryType;

  const hasSearchQuery = searchTerm.length > 0;
  const hasVideos = Number(videoList?.length) > 0;
  const hasChannels = Number(channelList?.length) > 0;
  const hasPlaylist = Number(playlistList?.length) > 0;
  const hasFulltext = Number(fulltextList?.length) > 0;

  const isSimpleQuery = queryType === 'simple';
  const isVideoQuery = queryType === 'video' || isSimpleQuery;
  const isChannelQuery = queryType === 'channel' || isSimpleQuery;
  const isPlaylistQuery = queryType === 'playlist' || isSimpleQuery;
  const isFullTextQuery = queryType === 'full' || isSimpleQuery;

  const isGridView = viewVideos === ViewStylesEnum.Grid;
  const gridView = isGridView ? `boxed-${gridItems}` : '';
  const gridViewGrid = isGridView ? `grid-${gridItems}` : '';

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm);
    }, 300);

    return () => {
      clearTimeout(handler);
    };
  }, [searchTerm]);

  useEffect(() => {
    if (debouncedSearchTerm.trim() !== '') {
      fetchResults(debouncedSearchTerm);
    } else {
      setSearchResults(EmptySearchResponse);
    }
  }, [debouncedSearchTerm, refresh, videoId]);

  const fetchResults = async (searchQuery: string) => {
    const searchResults = await loadSearch(searchQuery);

    setSearchResults(searchResults);
    setRefresh(false);
  };

  return (
    <>
      <title>TubeArchivist</title>

      <EmbeddableVideoPlayer videoId={videoId} />

      <div className={`boxed-content ${gridView}`}>
        <div className="title-bar">
          <h1>Search your Archive</h1>
        </div>
        <div className="multi-search-box">
          <div>
            <input
              type="text"
              autoFocus
              autoComplete="off"
              value={searchTerm}
              onChange={event => {
                setSearchTerm(event.currentTarget.value);
              }}
              onKeyDown={event => {
                if (event.key === 'Enter') {
                  fetchResults(searchTerm);
                }
              }}
            />
          </div>
        </div>
        <div id="multi-search-results">
          {hasSearchQuery && isVideoQuery && (
            <div className="multi-search-result">
              <h2>Video Results</h2>
              <div id="video-results" className={`video-list ${viewVideos} ${gridViewGrid}`}>
                <VideoList
                  videoList={videoList}
                  viewLayout={viewVideos}
                  refreshVideoList={setRefresh}
                />
              </div>
            </div>
          )}

          {hasSearchQuery && isChannelQuery && (
            <div className="multi-search-result">
              <h2>Channel Results</h2>
              <div id="channel-results" className={`channel-list ${viewChannels} ${gridViewGrid}`}>
                <ChannelList channelList={channelList} refreshChannelList={setRefresh} />
              </div>
            </div>
          )}

          {hasSearchQuery && isPlaylistQuery && (
            <div className="multi-search-result">
              <h2>Playlist Results</h2>
              <div
                id="playlist-results"
                className={`playlist-list ${viewPlaylists} ${gridViewGrid}`}
              >
                <PlaylistList playlistList={playlistList} setRefresh={setRefresh} />
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
