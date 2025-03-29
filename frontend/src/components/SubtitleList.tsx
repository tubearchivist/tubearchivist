import { Link, useSearchParams } from 'react-router-dom';
import Routes from '../configuration/routes/RouteList';
import iconPlay from '/img/icon-play.svg';
import Linkify from './Linkify';
import VideoThumbnail from './VideoThumbail';

type SubtitleListType = {
  subtitle_index: number;
  subtitle_line: string;
  subtitle_start: string;
  subtitle_fragment_id: string;
  subtitle_end: string;
  youtube_id: string;
  title: string;
  subtitle_channel: string;
  subtitle_channel_id: string;
  subtitle_last_refresh: number;
  subtitle_lang: string;
  subtitle_source: string;
  vid_thumb_url: string;
  _index: string;
  _score: number;
};

type SubtitleListProps = {
  subtitleList: SubtitleListType[] | undefined;
};

const stripNanoSecs = (time: string) => {
  return time.split('.').shift();
};

const SubtitleList = ({ subtitleList }: SubtitleListProps) => {
  const [, setSearchParams] = useSearchParams();

  if (!subtitleList || subtitleList.length === 0) {
    return <p>No fulltext results found.</p>;
  }

  return (
    <>
      {subtitleList.map(subtitle => {
        return (
          <div className="video-item list">
            <a
              onClick={() => {
                setSearchParams(params => {
                  params.set('videoId', subtitle.youtube_id);
                  params.set('t', stripNanoSecs(subtitle.subtitle_start) || '00:00:00');

                  return params;
                });
              }}
            >
              <div className="video-thumb-wrap list">
                <div className="video-thumb">
                  <VideoThumbnail videoThumbUrl={subtitle.vid_thumb_url} />
                </div>
                <div className="video-play">
                  <img src={iconPlay} alt="play-icon" />
                </div>
              </div>
            </a>
            <div className="video-desc list">
              <div>
                <Link to={Routes.Channel(subtitle.subtitle_channel_id)}>
                  <h3>{subtitle.subtitle_channel}</h3>
                </Link>
                <Link
                  className="video-more"
                  to={Routes.VideoAtTimestamp(
                    subtitle.youtube_id,
                    stripNanoSecs(subtitle.subtitle_start) || '00:00:00',
                  )}
                >
                  <h2>{subtitle.title}</h2>
                </Link>
              </div>
              <p>
                {stripNanoSecs(subtitle.subtitle_start)} - {stripNanoSecs(subtitle.subtitle_end)}
              </p>
              <p>
                <Linkify ignoreLineBreak>{subtitle.subtitle_line}</Linkify>
              </p>
              <span className="settings-current">Score: {subtitle._score}</span>
            </div>
          </div>
        );
      })}
    </>
  );
};

export default SubtitleList;
