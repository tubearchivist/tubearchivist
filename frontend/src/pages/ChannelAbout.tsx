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
import Button from '../components/Button';
import updateChannelOverwrites from '../api/actions/updateChannelOverwrite';
import useIsAdmin from '../functions/useIsAdmin';
import InputConfig from '../components/InputConfig';
import ToggleConfig from '../components/ToggleConfig';
import { useUserConfigStore } from '../stores/UserConfigStore';

export type ChannelBaseOutletContextType = {
  currentPage: number;
  setCurrentPage: (page: number) => void;
  startNotification: boolean;
  setStartNotification: (status: boolean) => void;
};

export type OutletContextType = {
  currentPage: number;
  setCurrentPage: (page: number) => void;
};

type ChannelAboutParams = {
  channelId: string;
};

const ChannelAbout = () => {
  const { channelId } = useParams() as ChannelAboutParams;
  const { userConfig } = useUserConfigStore();
  const { setStartNotification } = useOutletContext() as ChannelBaseOutletContextType;
  const navigate = useNavigate();
  const isAdmin = useIsAdmin();

  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [descriptionExpanded, setDescriptionExpanded] = useState(false);
  const [reindex, setReindex] = useState(false);
  const [refresh, setRefresh] = useState(true);

  const [channelResponse, setChannelResponse] = useState<ChannelResponseType>();

  const [downloadFormat, setDownloadFormat] = useState<string | null>(null);
  const [autoDeleteAfter, setAutoDeleteAfter] = useState<number | null>(null);
  const [indexPlaylists, setIndexPlaylists] = useState(false);
  const [enableSponsorblock, setEnableSponsorblock] = useState<boolean | null>(null);
  const [pageSizeVideo, setPageSizeVideo] = useState<number | null>(null);
  const [pageSizeShorts, setPageSizeShorts] = useState<number | null>(null);
  const [pageSizeStreams, setPageSizeStreams] = useState<number | null>(null);

  const channel = channelResponse?.data;

  useEffect(() => {
    (async () => {
      if (refresh) {
        const channelResponse = await loadChannelById(channelId);

        setChannelResponse(channelResponse);
        setDownloadFormat(channelResponse?.data?.channel_overwrites?.download_format ?? null);
        setAutoDeleteAfter(channelResponse?.data?.channel_overwrites?.autodelete_days ?? null);
        setIndexPlaylists(channelResponse?.data?.channel_overwrites?.index_playlists ?? null);
        setEnableSponsorblock(
          channelResponse?.data?.channel_overwrites?.integrate_sponsorblock ?? null,
        );
        setPageSizeVideo(
          channelResponse?.data?.channel_overwrites?.subscriptions_channel_size ?? null,
        );
        setPageSizeShorts(
          channelResponse?.data?.channel_overwrites?.subscriptions_shorts_channel_size ?? null,
        );
        setPageSizeStreams(
          channelResponse?.data?.channel_overwrites?.subscriptions_live_channel_size ?? null,
        );

        setRefresh(false);
      }
    })();
  }, [refresh, channelId]);

  const handleUpdateConfig = async (
    configKey: string,
    configValue: string | boolean | number | null,
  ) => {
    if (!channel) return;
    await updateChannelOverwrites(channel.channel_id, configKey, configValue);
    setRefresh(true);
  };

  const handleToggleSponsorBlock = async (isEnabled: boolean) => {
    if (isEnabled) {
      setEnableSponsorblock(true);
      await handleUpdateConfig('integrate_sponsorblock', false);
    } else {
      await handleUpdateConfig('integrate_sponsorblock', null);
      setEnableSponsorblock(null);
    }
  };

  if (!channel) {
    return 'Channel not found!';
  }

  return (
    <>
      <title>{`TA | Channel: About ${channel.channel_name}`}</title>
      <div className="boxed-content">
        <div className="info-box info-box-3">
          <ChannelOverview
            channelId={channel.channel_id}
            channelname={channel.channel_name}
            channelSubs={channel.channel_subs}
            channelSubscribed={channel.channel_subscribed}
            channelThumbUrl={channel.channel_thumb_url}
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
                      <div className="delete-confirm">
                        <span>Delete {channel.channel_name} including all videos? </span>

                        <Button
                          label="Delete"
                          className="danger-button"
                          onClick={async () => {
                            await deleteChannel(channelId);
                            navigate(Routes.Channels);
                          }}
                        />

                        <Button
                          label="Cancel"
                          onClick={() => setShowDeleteConfirm(!showDeleteConfirm)}
                        />
                      </div>
                    )}
                  </div>
                  <br></br>
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
          <div className="info-box">
            <div className="info-box-item">
              <h2>Channel Customization</h2>
              {userConfig.config.show_help_text && (
                <div className="help-text">
                  <ul>
                    <li>Overwrite the download format over the format set globally.</li>
                    <li>Autodelete watched after x days overwrites the global setting.</li>
                    <li>
                      Indexing playlists indexes all playlists from that channel.
                      <ul>
                        <li>
                          Only activate that for channels you care about the playlists. This is
                          slow.
                        </li>
                        <li>
                          More details{' '}
                          <a target="_blank" href="https://docs.tubearchivist.com/channels/#about">
                            here
                          </a>
                          .
                        </li>
                      </ul>
                    </li>
                    <li>
                      Once you click on <i>Configure</i>, this will activate sponsorblock settings.
                    </li>
                  </ul>
                </div>
              )}
              <div className="settings-box-wrapper">
                <div>
                  <p>Download Format</p>
                </div>
                <InputConfig
                  type="text"
                  name="download_format"
                  value={downloadFormat}
                  setValue={setDownloadFormat}
                  oldValue={channel.channel_overwrites?.download_format ?? null}
                  updateCallback={handleUpdateConfig}
                />
              </div>
              <div className="settings-box-wrapper">
                <div>
                  <p>
                    <span className="danger-zone">Danger Zone</span>: Auto delete watched
                  </p>
                </div>
                <InputConfig
                  type="number"
                  name="autodelete_days"
                  value={autoDeleteAfter}
                  setValue={setAutoDeleteAfter}
                  oldValue={channel.channel_overwrites?.autodelete_days ?? null}
                  updateCallback={handleUpdateConfig}
                />
              </div>
              <div className="settings-box-wrapper">
                <div>
                  <p>Index playlists</p>
                </div>
                <ToggleConfig
                  name="index_playlists"
                  value={indexPlaylists}
                  updateCallback={handleUpdateConfig}
                />
              </div>
              <div className="settings-box-wrapper">
                <div>
                  <p>
                    Overwrite{' '}
                    <a href="https://sponsor.ajay.app/" target="_blank">
                      SponsorBlock
                    </a>
                  </p>
                </div>
                <div>
                  {enableSponsorblock !== null ? (
                    <ToggleConfig
                      name="integrate_sponsorblock"
                      value={enableSponsorblock}
                      updateCallback={handleUpdateConfig}
                      resetCallback={handleToggleSponsorBlock}
                    />
                  ) : (
                    <button onClick={() => handleToggleSponsorBlock(true)}>Configure</button>
                  )}
                </div>
              </div>
            </div>
            <div className="info-box-item">
              <h2>Page Size Overrides</h2>
              {userConfig.config.show_help_text && (
                <div className="help-text">
                  <p>
                    Disable standard videos, shorts, or streams for this channel by setting their
                    page size to 0 (zero).
                  </p>
                </div>
              )}
              <div className="settings-box-wrapper">
                <div>
                  <p>Videos page size</p>
                </div>
                <InputConfig
                  type="number"
                  name="subscriptions_channel_size"
                  value={pageSizeVideo}
                  setValue={setPageSizeVideo}
                  oldValue={channel.channel_overwrites?.subscriptions_channel_size ?? null}
                  updateCallback={handleUpdateConfig}
                />
              </div>
              <div className="settings-box-wrapper">
                <div>
                  <p>Shorts page size</p>
                </div>
                <InputConfig
                  type="number"
                  name="subscriptions_shorts_channel_size"
                  value={pageSizeShorts}
                  setValue={setPageSizeShorts}
                  oldValue={channel.channel_overwrites?.subscriptions_shorts_channel_size ?? null}
                  updateCallback={handleUpdateConfig}
                />
              </div>
              <div className="settings-box-wrapper">
                <div>
                  <p>Live streams page size</p>
                </div>
                <InputConfig
                  type="number"
                  name="subscriptions_live_channel_size"
                  value={pageSizeStreams}
                  setValue={setPageSizeStreams}
                  oldValue={channel.channel_overwrites?.subscriptions_live_channel_size ?? null}
                  updateCallback={handleUpdateConfig}
                />
              </div>
            </div>
          </div>
        )}
      </div>

      <PaginationDummy />
    </>
  );
};

export default ChannelAbout;
