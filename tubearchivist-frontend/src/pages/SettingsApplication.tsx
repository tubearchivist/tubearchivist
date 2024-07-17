import { useEffect, useState } from 'react';
import loadSnapshots from '../api/loader/loadSnapshots';
import Notifications from '../components/Notifications';
import PaginationDummy from '../components/PaginationDummy';
import SettingsNavigation from '../components/SettingsNavigation';
import restoreSnapshot from '../api/actions/restoreSnapshot';
import queueSnapshot from '../api/actions/queueSnapshot';
import updateCookie from '../api/actions/updateCookie';
import deleteApiToken from '../api/actions/deleteApiToken';
import { Helmet } from 'react-helmet';
import Button from '../components/Button';

type SnapshotType = {
  id: string;
  state: string;
  es_version: string;
  start_date: string;
  end_date: string;
  end_stamp: number;
  duration_s: number;
};

type SnapshotListType = {
  next_exec: number;
  next_exec_str: string;
  expire_after: string;
  snapshots?: SnapshotType[];
};

type SettingsApplicationReponses = {
  snapshots?: SnapshotListType;
};

const SettingsApplication = () => {
  // Subscriptions
  const [videoPageSize, setVideoPageSize] = useState(0);
  const [livePageSize, setLivePageSize] = useState(0);
  const [shortPageSize, setShortPageSize] = useState(0);
  const [isAutostart, setIsAutostart] = useState(false);

  // Downloads
  const [currentDownloadSpeed, setCurrentDownloadSpeed] = useState(0);
  const [currentThrottledRate, setCurrentThrottledRate] = useState(0);
  const [currentScrapingSleep, setCurrentScrapingSleep] = useState(0);
  const [currentAutodelete, setCurrentAutodelete] = useState(0);

  // Download Format
  const [downloadsFormat, setDownloadsFormat] = useState('');
  const [downloadsFormatSort, setDownloadsFormatSort] = useState('');
  const [downloadsExtractorLang, setDownloadsExtractorLang] = useState('');
  const [embedMetadata, setEmbedMetadata] = useState(false);
  const [embedThumbnail, setEmbedThumbnail] = useState(false);

  // Subtitles
  const [subtitleLang, setSubtitleLang] = useState('');
  const [subtitleSource, setSubtitleSource] = useState('');
  const [indexSubtitles, setIndexSubtitles] = useState(false);

  // Comments
  const [commentsMax, setCommentsMax] = useState('');
  const [commentsSort, setCommentsSort] = useState('');

  // Cookie
  const [cookieImport, setCookieImport] = useState(false);
  const [validatingCookie, setValidatingCookie] = useState(false);
  const [cookieResponse, setCookieResponse] = useState({});

  // Integrations
  const [showApiToken, setShowApiToken] = useState(false);
  const [downloadDislikes, setDownloadDislikes] = useState(false);
  const [enableSponsorBlock, setEnableSponsorBlock] = useState(false);
  const [resetTokenResponse, setResetTokenResponse] = useState({});

  // Snapshots
  const [enableSnapshots, setEnableSnapshots] = useState(false);
  const [isSnapshotQueued, setIsSnapshotQueued] = useState(false);
  const [restoringSnapshot, setRestoringSnapshot] = useState(false);

  const [response, setResponse] = useState<SettingsApplicationReponses>({
    snapshots: undefined,
  });

  const snapshots = response?.snapshots;

  const config = {
    api_token: '<token>',
    subscriptions: {
      channel_size: 69,
      live_channel_size: 69,
      shorts_channel_size: 69,
      auto_start: false,
    },
    downloads: {
      limit_speed: false,
      sleep_interval: 3,
      autodelete_days: false,
      format: false,
      format_sort: false,
      add_metadata: false,
      add_thumbnail: false,
      subtitle: false,
      subtitle_source: false,
      subtitle_index: false,
      comment_max: false,
      comment_sort: 'top',
      cookie_import: false,
      throttledratelimit: false,
      extractor_lang: false,
      integrate_ryd: false,
      integrate_sponsorblock: false,
    },
    application: {
      enable_snapshot: true,
    },
  };

  useEffect(() => {
    (async () => {
      const snapshotResponse = await loadSnapshots();

      setResponse({
        snapshots: snapshotResponse,
      });
    })();
  }, []);

  return (
    <>
      <Helmet>
        <title>TA | Application Settings</title>
      </Helmet>
      <div className="boxed-content">
        <SettingsNavigation />
        <Notifications pageName={'all'} />

        <div className="title-bar">
          <h1>Application Configurations</h1>
        </div>
        <form
          name="application-update"
          onSubmit={event => {
            event.preventDefault();
          }}
        >
          <div className="settings-group">
            <h2 id="subscriptions">Subscriptions</h2>
            <p>Disable shorts or streams by setting their page size to 0 (zero).</p>

            <div className="settings-item">
              <p>
                YouTube page size:{' '}
                <span className="settings-current">{config.subscriptions.channel_size}</span>
              </p>
              <i>
                Videos to scan to find new items for the <b>Rescan subscriptions</b> task, max
                recommended 50.
              </i>
              <br />
              <input
                type="number"
                name="subscriptions_channel_size"
                min="1"
                id="id_subscriptions_channel_size"
                onChange={event => {
                  setVideoPageSize(Number(event.target.value));
                }}
              />
            </div>

            <div className="settings-item">
              <p>
                YouTube Live page size:{' '}
                <span className="settings-current">{config.subscriptions.live_channel_size}</span>
              </p>
              <i>
                Live Videos to scan to find new items for the <b>Rescan subscriptions</b> task, max
                recommended 50.
              </i>
              <br />
              <input
                type="number"
                name="subscriptions_live_channel_size"
                min="0"
                id="id_subscriptions_live_channel_size"
                onChange={event => {
                  setLivePageSize(Number(event.target.value));
                }}
              />
            </div>

            <div className="settings-item">
              <p>
                YouTube Shorts page size:{' '}
                <span className="settings-current">{config.subscriptions.shorts_channel_size}</span>
              </p>
              <i>
                Shorts Videos to scan to find new items for the <b>Rescan subscriptions</b> task,
                max recommended 50.
              </i>
              <br />
              <input
                type="number"
                name="subscriptions_shorts_channel_size"
                min="0"
                id="id_subscriptions_shorts_channel_size"
                onChange={event => {
                  setShortPageSize(Number(event.target.value));
                }}
              />
            </div>

            <div className="settings-item">
              <p>
                Auto start download from your subscriptions:{' '}
                <span className="settings-current">{config.subscriptions.auto_start}</span>
              </p>
              <i>
                Enable this will automatically start and prioritize videos from your subscriptions.
              </i>
              <br />
              <select
                name="subscriptions_auto_start"
                id="id_subscriptions_auto_start"
                defaultValue=""
                onChange={event => {
                  setIsAutostart(event.target.value === 'true');
                }}
              >
                <option value="">-- change subscription autostart --</option>
                <option value="false">disable auto start</option>
                <option value="true">enable auto start</option>
              </select>
            </div>
          </div>
          <div className="settings-group">
            <h2 id="downloads">Downloads</h2>

            <div className="settings-item">
              <p>
                Current download speed limit in KB/s:{' '}
                <span className="settings-current">{config.downloads.limit_speed}</span>
              </p>
              <i>
                Limit download speed. 0 (zero) to deactivate, e.g. 1000 (1MB/s). Speeds are in KB/s.
                Setting takes effect on new download jobs or application restart.
              </i>
              <br />
              <input
                type="number"
                name="downloads_limit_speed"
                id="id_downloads_limit_speed"
                onChange={event => {
                  setCurrentDownloadSpeed(Number(event.target.value));
                }}
              />
            </div>

            <div className="settings-item">
              <p>
                Current throttled rate limit in KB/s:{' '}
                <span className="settings-current">{config.downloads.throttledratelimit}</span>
              </p>
              <i>
                Download will restart if speeds drop below specified amount. 0 (zero) to deactivate,
                e.g. 100. Speeds are in KB/s.
              </i>
              <br />
              <input
                type="number"
                name="downloads_throttledratelimit"
                id="id_downloads_throttledratelimit"
                onChange={event => {
                  setCurrentThrottledRate(Number(event.target.value));
                }}
              />
            </div>

            <div className="settings-item">
              <p>
                Current scraping sleep interval:{' '}
                <span className="settings-current">{config.downloads.sleep_interval}</span>
              </p>
              <i>
                Seconds to sleep between calls to YouTube. Might be necessary to avoid throttling.
                Recommended 3.
              </i>
              <br />
              <input
                type="number"
                name="downloads_sleep_interval"
                id="id_downloads_sleep_interval"
                onChange={event => {
                  setCurrentScrapingSleep(Number(event.target.value));
                }}
              />
            </div>

            <div className="settings-item">
              <p>
                <span className="danger-zone">Danger Zone</span>: Current auto delete watched
                videos: <span className="settings-current">{config.downloads.autodelete_days}</span>
              </p>
              <i>Auto delete watched videos after x days, 0 (zero) to deactivate:</i>
              <br />
              <input
                type="number"
                name="downloads_autodelete_days"
                id="id_downloads_autodelete_days"
                onChange={event => {
                  setCurrentAutodelete(Number(event.target.value));
                }}
              />
            </div>
          </div>
          <div className="settings-group">
            <h2 id="format">Download Format</h2>

            <div className="settings-item">
              <p>
                Limit video and audio quality format for yt-dlp.
                <br />
                Currently: <span className="settings-current">{config.downloads.format}</span>
              </p>
              <p>Example configurations:</p>
              <ul>
                <li>
                  <span className="settings-current">
                    bestvideo[height{'<='}720]+bestaudio/best[height{'<='}720]
                  </span>
                  : best audio and max video height of 720p.
                </li>
                <li>
                  <span className="settings-current">
                    bestvideo[height{'<='}1080]+bestaudio/best[height{'<='}1080]
                  </span>
                  : best audio and max video height of 1080p.
                </li>
                <li>
                  <span className="settings-current">
                    bestvideo[height{'<='}
                    1080][vcodec*=avc1]+bestaudio[acodec*=mp4a]/mp4
                  </span>
                  : Max 1080p video height with iOS compatible video and audio codecs.
                </li>
                <li>
                  <span className="settings-current">0</span>: deactivate and download the best
                  quality possible as decided by yt-dlp.
                </li>
              </ul>
              <i>
                Make sure your custom format gets merged into a single file. Check out the{' '}
                <a href="https://github.com/yt-dlp/yt-dlp#format-selection" target="_blank">
                  documentation
                </a>{' '}
                for valid configurations.
              </i>
              <br />
              <input
                type="text"
                name="downloads_format"
                id="id_downloads_format"
                onChange={event => {
                  setDownloadsFormat(event.target.value);
                }}
              />
              <br />
            </div>

            <div className="settings-item">
              <p>
                Force sort order to have precedence over all yt-dlp fields.
                <br />
                Currently: <span className="settings-current">{config.downloads.format_sort}</span>
              </p>
              <p>Example configurations:</p>
              <ul>
                <li>
                  <span className="settings-current">res,codec:av1</span>: prefer AV1 over all other
                  video codecs.
                </li>
                <li>
                  <span className="settings-current">0</span>: deactivate and keep the default as
                  decided by yt-dlp.
                </li>
              </ul>
              <i>
                Not all codecs are supported by all browsers. The default value ensures best
                compatibility. Check out the{' '}
                <a href="https://github.com/yt-dlp/yt-dlp#sorting-formats" target="_blank">
                  documentation
                </a>{' '}
                for valid configurations.
              </i>
              <br />
              <input
                type="text"
                name="downloads_format_sort"
                id="id_downloads_format_sort"
                onChange={event => {
                  setDownloadsFormatSort(event.target.value);
                }}
              />
              <br />
            </div>

            <div className="settings-item">
              <p>
                Prefer translated metadata language:{' '}
                <span className="settings-current">{config.downloads.extractor_lang}</span>
              </p>
              <i>
                This will change the language this video gets indexed as. That will only be
                available if the uploader provides translations. Add as two letter ISO language
                code, check the{' '}
                <a href="https://github.com/yt-dlp/yt-dlp#youtube" target="_blank">
                  documentation
                </a>{' '}
                which languages are available.
              </i>
              <br />
              <input
                type="text"
                name="downloads_extractor_lang"
                id="id_downloads_extractor_lang"
                onChange={event => {
                  setDownloadsExtractorLang(event.target.value);
                }}
              />
            </div>

            <div className="settings-item">
              <p>
                Current metadata embed setting:{' '}
                <span className="settings-current">{config.downloads.add_metadata}</span>
              </p>
              <i>Metadata is not embedded into the downloaded files by default.</i>
              <br />
              <select
                name="downloads_add_metadata"
                id="id_downloads_add_metadata"
                defaultValue=""
                onChange={event => {
                  setEmbedMetadata(event.target.value === 'true');
                }}
              >
                <option value="">-- change metadata embed --</option>
                <option value="false">don't embed metadata</option>
                <option value="true">embed metadata</option>
              </select>
            </div>

            <div className="settings-item">
              <p>
                Current thumbnail embed setting:{' '}
                <span className="settings-current">{config.downloads.add_thumbnail}</span>
              </p>
              <i>Embed thumbnail into the mediafile.</i>
              <br />
              <select
                name="downloads_add_thumbnail"
                id="id_downloads_add_thumbnail"
                defaultValue=""
                onChange={event => {
                  setEmbedThumbnail(event.target.value === 'true');
                }}
              >
                <option value="">-- change thumbnail embed --</option>
                <option value="false">don't embed thumbnail</option>
                <option value="true">embed thumbnail</option>
              </select>
            </div>
          </div>

          <div className="settings-group">
            <h2 id="format">Subtitles</h2>
            <div className="settings-item">
              <p>
                Subtitles download setting:{' '}
                <span className="settings-current">{config.downloads.subtitle}</span>
                <br />
                <i>
                  Choose which subtitles to download, add comma separated language codes,
                  <br />
                  e.g. <span className="settings-current">en, de, zh-Hans</span>
                </i>
                <br />
                <input
                  type="text"
                  name="downloads_subtitle"
                  id="id_downloads_subtitle"
                  onChange={event => {
                    setSubtitleLang(event.target.value);
                  }}
                />
              </p>
            </div>
            <div className="settings-item">
              <p>
                Subtitle source settings:{' '}
                <span className="settings-current">{config.downloads.subtitle_source}</span>
              </p>
              <i>Download only user generated, or also less accurate auto generated subtitles.</i>
              <br />
              <select
                name="downloads_subtitle_source"
                id="id_downloads_subtitle_source"
                defaultValue=""
                onChange={event => {
                  setSubtitleSource(event.target.value);
                }}
              >
                <option value="">-- change subtitle source settings</option>
                <option value="user">only download user created</option>
                <option value="auto">also download auto generated</option>
              </select>
            </div>
            <div className="settings-item">
              <p>
                Index and make subtitles searchable:{' '}
                <span className="settings-current">{config.downloads.subtitle_index}</span>
              </p>
              <i>Store subtitle lines in Elasticsearch. Not recommended for low-end hardware.</i>
              <br />
              <select
                name="downloads_subtitle_index"
                id="id_downloads_subtitle_index"
                defaultValue=""
                onChange={event => {
                  setIndexSubtitles(event.target.value === 'true');
                }}
              >
                <option value="">-- change subtitle index settings --</option>
                <option value="false">disable subtitle index</option>
                <option value="true">enable subtitle index</option>
              </select>
            </div>
          </div>

          <div className="settings-group">
            <h2 id="comments">Comments</h2>
            <div className="settings-item">
              <p>
                Download and index comments:{' '}
                <span className="settings-current">{config.downloads.comment_max}</span>
                <br />
                <i>
                  Follow the yt-dlp max_comments documentation,{' '}
                  <a href="https://github.com/yt-dlp/yt-dlp#youtube" target="_blank">
                    max-comments,max-parents,max-replies,max-replies-per-thread
                  </a>
                  :
                </i>
                <br />
                <p>Example configurations:</p>
                <ul>
                  <li>
                    <span className="settings-current">all,100,all,30</span>: Get 100 max-parents
                    and 30 max-replies-per-thread.
                  </li>
                  <li>
                    <span className="settings-current">1000,all,all,50</span>: Get a total of 1000
                    comments over all, 50 replies per thread.
                  </li>
                </ul>
                <input
                  type="text"
                  name="downloads_comment_max"
                  id="id_downloads_comment_max"
                  value={commentsMax}
                  onChange={event => {
                    setCommentsMax(event.target.value);
                  }}
                />
              </p>
            </div>
            <div className="settings-item">
              <p>
                Selected comment sort method:{' '}
                <span className="settings-current">{config.downloads.comment_sort}</span>
                <br />
                <i>Select how many comments and threads to download:</i>
                <br />
                <select
                  name="downloads_comment_sort"
                  id="id_downloads_comment_sort"
                  defaultValue=""
                  onChange={event => {
                    setCommentsSort(event.target.value);
                  }}
                >
                  <option value="">-- change comments sort settings --</option>
                  <option value="top">sort comments by top</option>
                  <option value="new">sort comments by new</option>
                </select>
              </p>
            </div>
          </div>

          <div className="settings-group">
            <h2 id="format">Cookie</h2>
            <div className="settings-item">
              <p>
                Import YouTube cookie:{' '}
                <span className="settings-current">{config.downloads.cookie_import}</span>
                <br />
              </p>
              <p>
                For automatic cookie import use <b>Tube Archivist Companion</b>{' '}
                <a href="https://github.com/tubearchivist/browser-extension" target="_blank">
                  browser extension
                </a>
                .
              </p>
              <i>
                For manual cookie import, place your cookie file named{' '}
                <span className="settings-current">cookies.google.txt</span> in{' '}
                <span className="settings-current">cache/import</span> before enabling. Instructions
                in the{' '}
                <a
                  href="https://docs.tubearchivist.com/settings/application/#cookie"
                  target="_blank"
                >
                  Wiki.
                </a>
              </i>
              <br />
              <select
                name="downloads_cookie_import"
                id="id_downloads_cookie_import"
                defaultValue=""
                onChange={event => {
                  setCookieImport(event.target.value === 'true');
                }}
              >
                <option value="">-- change cookie settings</option>
                <option value="false">remove cookie</option>
                <option value="true">import cookie</option>
              </select>
              <br />
              {validatingCookie && <span>Processing.</span>}
              {validatingCookie && cookieResponse?.cookie_validated && (
                <span>The cookie file is valid.</span>
              )}
              {validatingCookie && !cookieResponse?.cookie_validated && (
                <span className="danger-zone">Warning, the cookie file is invalid.</span>
              )}
              {!validatingCookie && (
                <>
                  {config.downloads.cookie_import && (
                    <div id="cookieMessage">
                      <Button
                        id="cookieButton"
                        label="Validate Cookie File"
                        type="button"
                        onClick={async () => {
                          setValidatingCookie(true);
                          const response = await updateCookie();
                          setCookieResponse(response);
                        }}
                      />
                    </div>
                  )}
                </>
              )}
            </div>
          </div>

          <div className="settings-group">
            <h2 id="integrations">Integrations</h2>
            <div className="settings-item">
              <p>
                API token:{' '}
                <Button
                  id="text-reveal-button"
                  label="Show"
                  type="button"
                  onClick={() => {
                    setShowApiToken(!showApiToken);
                  }}
                />
              </p>
              {resetTokenResponse && resetTokenResponse?.success && <p>Token revoked</p>}
              {showApiToken && !resetTokenResponse?.success && (
                <div className="description-text">
                  <p>{config.api_token}</p>
                  <Button
                    className="danger-button"
                    label="Revoke"
                    type="button"
                    onClick={async () => {
                      const response = await deleteApiToken();
                      setResetTokenResponse(response);
                    }}
                  />
                </div>
              )}
            </div>

            <div className="settings-item">
              <p>
                Integrate with{' '}
                <a href="https://returnyoutubedislike.com/" target="_blank">
                  returnyoutubedislike.com
                </a>{' '}
                to get dislikes and average ratings back:{' '}
                <span className="settings-current">{config.downloads.integrate_ryd}</span>
              </p>
              <i>
                Before activating that, make sure you have a scraping sleep interval of at least 3
                secs set to avoid ratelimiting issues.
              </i>
              <br />
              <select
                name="downloads_integrate_ryd"
                id="id_downloads_integrate_ryd"
                defaultValue=""
                onChange={event => {
                  setDownloadDislikes(event.target.value === 'true');
                }}
              >
                <option value="">-- change ryd integrations</option>
                <option value="false">disable ryd integration</option>
                <option value="true">enable ryd integration</option>
              </select>
            </div>

            <div className="settings-item">
              <p>
                Integrate with{' '}
                <a href="https://sponsor.ajay.app/" target="_blank">
                  SponsorBlock
                </a>{' '}
                to get sponsored timestamps:{' '}
                <span className="settings-current">{config.downloads.integrate_sponsorblock}</span>
              </p>
              <i>
                Before activating that, make sure you have a scraping sleep interval of at least 3
                secs set to avoid ratelimiting issues.
              </i>
              <br />
              <select
                name="downloads_integrate_sponsorblock"
                id="id_downloads_integrate_sponsorblock"
                defaultValue=""
                onChange={event => {
                  setEnableSponsorBlock(event.target.value === 'true');
                }}
              >
                <option value="">-- change sponsorblock integrations</option>
                <option value="false">disable sponsorblock integration</option>
                <option value="true">enable sponsorblock integration</option>
              </select>
            </div>
          </div>

          <div className="settings-group">
            <h2 id="snapshots">Snapshots</h2>
            <div className="settings-item">
              <p>
                Current system snapshot:{' '}
                <span className="settings-current">{config.application.enable_snapshot}</span>
              </p>
              <i>
                Automatically create daily deduplicated snapshots of the index, stored in
                Elasticsearch. Read first before activating:{' '}
                <a
                  target="_blank"
                  href="https://docs.tubearchivist.com/settings/application/#snapshots"
                >
                  Wiki
                </a>
                .
              </i>
              <br />
              <select
                name="application_enable_snapshot"
                id="id_application_enable_snapshot"
                defaultValue=""
                onChange={event => {
                  setEnableSnapshots(event.target.value === 'true');
                }}
              >
                <option value="">-- change snapshot settings --</option>
                <option value="false">disable system snapshots</option>
                <option value="true">enable system snapshots</option>
              </select>
            </div>

            <div>
              {snapshots && (
                <>
                  <p>
                    Create next snapshot:{' '}
                    <span className="settings-current">{snapshots.next_exec_str}</span>, snapshots
                    expire after <span className="settings-current">{snapshots.expire_after}</span>
                    . <br />
                    {isSnapshotQueued && <span>Snapshot in progress</span>}
                    {!isSnapshotQueued && (
                      <Button
                        label="Create snapshot now"
                        id="createButton"
                        onClick={async () => {
                          setIsSnapshotQueued(true);
                          await queueSnapshot();
                        }}
                      />
                    )}
                  </p>
                  <br />
                  {restoringSnapshot && <p>Snapshot restore started</p>}
                  {!restoringSnapshot &&
                    snapshots.snapshots &&
                    snapshots.snapshots.map((snapshot, index) => {
                      return (
                        <p key={index}>
                          <Button
                            label="Restore"
                            onClick={async () => {
                              setRestoringSnapshot(true);
                              await restoreSnapshot(snapshot.id);
                            }}
                          />{' '}
                          Snapshot created on:{' '}
                          <span className="settings-current">{snapshot.start_date}</span>, took{' '}
                          <span className="settings-current">{snapshot.duration_s}s</span> to
                          create. State: <i>{snapshot.state}</i>
                        </p>
                      );
                    })}
                </>
              )}
            </div>
          </div>

          <Button
            type="submit"
            name="application-settings"
            label="Update Application Configurations"
          />
        </form>
      </div>

      <PaginationDummy />
    </>
  );
};

export default SettingsApplication;
