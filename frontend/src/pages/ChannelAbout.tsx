import { useNavigate, useOutletContext, useParams } from 'react-router-dom';
import ChannelOverview from '../components/ChannelOverview';
import { useEffect, useState } from 'react';
import loadChannelById from '../api/loader/loadChannelById';
import { ChannelResponseType } from './ChannelBase';
import Linkify from '../components/Linkify';
import deleteChannel from '../api/actions/deleteChannel';
import Routes from '../configuration/routes/RouteList';
import queueReindex, { ReindexType, ReindexTypeEnum } from '../api/actions/queueReindex';
import formatDate from '../functions/formatDates';
import PaginationDummy from '../components/PaginationDummy';
import FormattedNumber from '../components/FormattedNumber';
import { Helmet } from 'react-helmet';
import Button from '../components/Button';
import updateChannelSettings, {
  ChannelAboutConfigType,
} from '../api/actions/updateChannelSettings';

const toStringToBool = (str: string) => {
  try {
    return JSON.parse(str);
  } catch {
    return null;
  }
};

export type ChannelBaseOutletContextType = {
  isAdmin: boolean;
  currentPage: number;
  setCurrentPage: (page: number) => void;
  startNotification: boolean;
  setStartNotification: (status: boolean) => void;
};

export type OutletContextType = {
  isAdmin: boolean;
  currentPage: number;
  setCurrentPage: (page: number) => void;
};

type ChannelAboutParams = {
  channelId: string;
};

const ChannelAbout = () => {
  const { channelId } = useParams() as ChannelAboutParams;
  const { isAdmin, setStartNotification } = useOutletContext() as ChannelBaseOutletContextType;
  const navigate = useNavigate();

  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [descriptionExpanded, setDescriptionExpanded] = useState(false);
  const [reindex, setReindex] = useState(false);
  const [refresh, setRefresh] = useState(true);

  const [channelResponse, setChannelResponse] = useState<ChannelResponseType>();
  const [channelConfig, setChannelConfig] = useState<ChannelAboutConfigType>();

  const [downloadFormat, setDownloadFormat] = useState(channelConfig?.download_format);
  const [autoDeleteAfter, setAutoDeleteAfter] = useState(channelConfig?.autodelete_days);
  const [indexPlaylists, setIndexPlaylists] = useState(
    channelConfig?.index_playlists ? 'true' : 'false',
  );
  const [enableSponsorblock, setEnableSponsorblock] = useState(
    channelConfig?.integrate_sponsorblock,
  );
  const [pageSizeVideo, setPageSizeVideo] = useState(channelConfig?.subscriptions_channel_size);
  const [pageSizeStreams, setPageSizeStreams] = useState(
    channelConfig?.subscriptions_live_channel_size,
  );
  const [pageSizeShorts, setPageSizeShorts] = useState(
    channelConfig?.subscriptions_shorts_channel_size,
  );

  const channel = channelResponse?.data;

  const channelOverwrites = channel?.channel_overwrites;

  const handleSubmit = async (event: { preventDefault: () => void }) => {
    event.preventDefault();

    await updateChannelSettings(channelId, {
      index_playlists: toStringToBool(indexPlaylists),
      download_format: downloadFormat,
      autodelete_days: autoDeleteAfter,
      integrate_sponsorblock: enableSponsorblock,
      subscriptions_channel_size: pageSizeVideo,
      subscriptions_live_channel_size: pageSizeStreams,
      subscriptions_shorts_channel_size: pageSizeShorts,
    });

    setRefresh(true);
  };

  useEffect(() => {
    (async () => {
      if (refresh) {
        const channelResponse = await loadChannelById(channelId);

        setChannelResponse(channelResponse);
        setChannelConfig(channelResponse?.data?.channel_overwrites);
        console.log('channel_overwrites', channelResponse?.data);
        console.log('channel_overwrites', channelResponse?.data?.channel_overwrites);
        console.log('channel_overwrites', '--------');
        setRefresh(false);
      }
    })();
  }, [refresh, channelId]);

  if (!channel) {
    return 'Channel not found!';
  }

  return (
    <>
      <Helmet>
        <title>TA | Channel: About {channel.channel_name}</title>
      </Helmet>
      <div className="boxed-content">
        <div className="info-box info-box-3">
          <ChannelOverview
            channelId={channel.channel_id}
            channelname={channel.channel_name}
            channelSubs={channel.channel_subs}
            channelSubscribed={channel.channel_subscribed}
            showSubscribeButton={true}
            isUserAdmin={isAdmin}
            setRefresh={setRefresh}
          />

          <div className="info-box-item">
            <div>
              <p>Last refreshed: {formatDate(channel.channel_last_refresh)}</p>
              {channel.channel_active && (
                <p>
                  Youtube:{' '}
                  <a href={`https://www.youtube.com/channel/${channel.channel_id}`} target="_blank">
                    Active
                  </a>
                </p>
              )}
              {!channel.channel_active && <p>Youtube: Deactivated</p>}
            </div>
          </div>

          <div className="info-box-item">
            <div>
              {channel.channel_views > 0 && (
                <FormattedNumber text="Channel views:" number={channel.channel_views} />
              )}

              {isAdmin && (
                <>
                  <div className="button-box">
                    {!showDeleteConfirm && (
                      <Button
                        label="Delete Channel"
                        id="delete-item"
                        onClick={() => setShowDeleteConfirm(!showDeleteConfirm)}
                      />
                    )}

                    {showDeleteConfirm && (
                      <div className="delete-confirm" id="delete-button">
                        <span>Delete {channel.channel_name} including all videos? </span>
                        <Button
                          label="Delete"
                          className="danger-button"
                          onClick={async () => {
                            await deleteChannel(channelId);
                            navigate(Routes.Channels);
                          }}
                        />{' '}
                        <Button
                          label="Cancel"
                          onClick={() => setShowDeleteConfirm(!showDeleteConfirm)}
                        />
                      </div>
                    )}
                  </div>
                  {reindex && <p>Reindex scheduled</p>}
                  {!reindex && (
                    <div id="reindex-button" className="button-box">
                      <Button
                        label="Reindex"
                        title={`Reindex Channel ${channel.channel_name}`}
                        onClick={async () => {
                          await queueReindex(channelId, ReindexTypeEnum.channel as ReindexType);

                          setReindex(true);
                          setStartNotification(true);
                        }}
                      />{' '}
                      <Button
                        label="Reindex Videos"
                        title={`Reindex Videos of ${channel.channel_name}`}
                        onClick={async () => {
                          await queueReindex(
                            channelId,
                            ReindexTypeEnum.channel as ReindexType,
                            true,
                          );

                          setReindex(true);
                          setStartNotification(true);
                        }}
                      />
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>

        {channel.channel_description && (
          <div className="description-box">
            <p
              id={descriptionExpanded ? 'text-expand-expanded' : 'text-expand'}
              className="description-text"
            >
              <Linkify>{channel.channel_description}</Linkify>
            </p>

            <Button
              label="Show more"
              id="text-expand-button"
              onClick={() => setDescriptionExpanded(!descriptionExpanded)}
            />
          </div>
        )}

        {channel.channel_tags && (
          <div className="description-box">
            <div className="video-tag-box">
              {channel.channel_tags.map(tag => {
                return (
                  <span key={tag} className="video-tag">
                    {tag}
                  </span>
                );
              })}
            </div>
          </div>
        )}

        {isAdmin && (
          <div id="overwrite-form" className="info-box">
            <div className="info-box-item">
              <h2>Customize {channel.channel_name}</h2>
              <form className="overwrite-form" onSubmit={handleSubmit}>
                <div className="overwrite-form-item">
                  <p>
                    Download format:{' '}
                    <span className="settings-current">
                      {channelOverwrites?.download_format || 'False'}
                    </span>
                  </p>
                  <input
                    type="text"
                    name="download_format"
                    id="id_download_format"
                    onChange={event => {
                      const value = event.currentTarget.value;

                      setDownloadFormat(value);
                    }}
                  />
                  <Button
                    label="Reset"
                    onClick={() => {
                      setDownloadFormat(false);
                    }}
                  />
                  <br />
                </div>
                <div className="overwrite-form-item">
                  <p>
                    Auto delete watched videos after x days:{' '}
                    <span className="settings-current">
                      {channelOverwrites?.autodelete_days || 'False'}
                    </span>
                  </p>
                  <input
                    type="number"
                    name="autodelete_days"
                    id="id_autodelete_days"
                    onChange={event => {
                      const value = Number(event.currentTarget.value);

                      if (value === 0) {
                        setAutoDeleteAfter(false);
                      } else {
                        setAutoDeleteAfter(Number(value));
                      }
                    }}
                  />

                  <br />
                </div>

                <div className="overwrite-form-item">
                  <p>
                    Index playlists:{' '}
                    <span className="settings-current">
                      {JSON.stringify(channelOverwrites?.index_playlists)}
                    </span>
                  </p>

                  <select
                    name="index_playlists"
                    id="id_index_playlists"
                    value={indexPlaylists}
                    onChange={event => {
                      const value = event.currentTarget.value;

                      setIndexPlaylists(value);
                    }}
                  >
                    <option value="null">-- change playlist index --</option>
                    <option value="false">Disable playlist index</option>
                    <option value="true">Enable playlist index</option>
                  </select>

                  <br />
                </div>

                <div className="overwrite-form-item">
                  <p>
                    Enable{' '}
                    <a href="https://sponsor.ajay.app/" target="_blank">
                      SponsorBlock
                    </a>
                    :{' '}
                    <span className="settings-current">
                      {JSON.stringify(channelOverwrites?.integrate_sponsorblock)}
                    </span>
                  </p>
                  <select
                    name="integrate_sponsorblock"
                    id="id_integrate_sponsorblock"
                    value={enableSponsorblock?.toString() || ''}
                    onChange={event => {
                      const value = event.currentTarget.value;

                      if (value !== '') {
                        setEnableSponsorblock(JSON.parse(value));
                      } else {
                        setEnableSponsorblock(undefined);
                      }
                    }}
                  >
                    <option value="">-- change sponsorblock integrations</option>
                    <option value="false">disable sponsorblock integration</option>
                    <option value="true">enable sponsorblock integration</option>
                    <option value="null">unset sponsorblock integration</option>
                  </select>
                </div>
                <h3>Page Size Overrides</h3>
                <br />
                <p>
                  Disable standard videos, shorts, or streams for this channel by setting their page
                  size to 0 (zero).
                </p>
                <br />
                <p>Disable page size overwrite for channel by setting to negative value.</p>
                <br />
                <div className="overwrite-form-item">
                  <p>
                    YouTube page size:{' '}
                    <span className="settings-current">
                      {channelOverwrites?.subscriptions_channel_size || 'False'}
                    </span>
                  </p>
                  <i>
                    Videos to scan to find new items for the <b>Rescan subscriptions</b> task, max
                    recommended 50.
                  </i>
                  <br />
                  <input
                    type="number"
                    name="channel_size"
                    id="id_channel_size"
                    onChange={event => {
                      setPageSizeVideo(Number(event.currentTarget.value));
                    }}
                  />
                  <br />
                </div>
                <div className="overwrite-form-item">
                  <p>
                    YouTube Live page size:{' '}
                    <span className="settings-current">
                      {channelOverwrites?.subscriptions_live_channel_size || 'False'}
                    </span>
                  </p>
                  <i>
                    Live Videos to scan to find new items for the <b>Rescan subscriptions</b> task,
                    max recommended 50.
                  </i>
                  <br />
                  <input
                    type="number"
                    name="live_channel_size"
                    id="id_live_channel_size"
                    onChange={event => {
                      setPageSizeStreams(Number(event.currentTarget.value));
                    }}
                  />
                  <br />
                </div>
                <div className="overwrite-form-item">
                  <p>
                    YouTube Shorts page size:{' '}
                    <span className="settings-current">
                      {channelOverwrites?.subscriptions_shorts_channel_size || 'False'}
                    </span>
                  </p>
                  <i>
                    Shorts Videos to scan to find new items for the <b>Rescan subscriptions</b>{' '}
                    task, max recommended 50.
                  </i>
                  <br />
                  <input
                    type="number"
                    name="shorts_channel_size"
                    id="id_shorts_channel_size"
                    onChange={event => {
                      setPageSizeShorts(Number(event.currentTarget.value));
                    }}
                  />
                </div>
                <br />

                <Button type="submit" label="Save Channel Overwrites" />
              </form>
            </div>
          </div>
        )}
      </div>

      <PaginationDummy />
    </>
  );
};

export default ChannelAbout;
