import iconClose from '/img/icon-close.svg';
import iconArrowTop from '/img/icon-arrow-top.svg';
import iconArrowUp from '/img/icon-arrow-up.svg';
import iconArrowDown from '/img/icon-arrow-down.svg';
import iconArrowBottom from '/img/icon-arrow-bottom.svg';
import iconRemove from '/img/icon-remove.svg';
import updateCustomPlaylist from '../api/actions/updateCustomPlaylist';

type MoveVideoMenuProps = {
  playlistId?: string;
  videoId: string;
  setCloseMenu: (status: boolean) => void;
  setRefresh: (status: boolean) => void;
};

const MoveVideoMenu = ({ playlistId, videoId, setCloseMenu, setRefresh }: MoveVideoMenuProps) => {
  if (playlistId === undefined) {
    return [];
  }

  return (
    <>
      <div className="video-popup-menu">
        <img
          src={iconClose}
          className="video-popup-menu-close-button"
          title="Close menu"
          onClick={() => setCloseMenu(true)}
        />
        <h3>Move Video</h3>

        <img
          className="move-video-button"
          data-context="top"
          onClick={async () => {
            await updateCustomPlaylist('top', playlistId, videoId);

            setRefresh(true);
          }}
          src={iconArrowTop}
          title="Move to top"
        />
        <img
          className="move-video-button"
          data-context="up"
          onClick={async () => {
            await updateCustomPlaylist('up', playlistId, videoId);

            setRefresh(true);
          }}
          src={iconArrowUp}
          title="Move up"
        />
        <img
          className="move-video-button"
          data-context="down"
          onClick={async () => {
            await updateCustomPlaylist('down', playlistId, videoId);

            setRefresh(true);
          }}
          src={iconArrowDown}
          title="Move down"
        />

        <img
          className="move-video-button"
          data-context="bottom"
          onClick={async () => {
            await updateCustomPlaylist('bottom', playlistId, videoId);

            setRefresh(true);
          }}
          src={iconArrowBottom}
          title="Move to bottom"
        />

        <img
          className="move-video-button"
          data-context="remove"
          onClick={async () => {
            await updateCustomPlaylist('remove', playlistId, videoId);

            setRefresh(true);
          }}
          src={iconRemove}
          title="Remove from playlist"
        />
      </div>
    </>
  );
};

export default MoveVideoMenu;
