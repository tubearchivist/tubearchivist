import getApiUrl from '../configuration/getApiUrl';
import defaultPlaylistThumbnail from '/img/default-playlist-thumb.jpg';

type PlaylistThumbnailProps = {
  playlistId: string;
  playlistThumbnail: string | undefined;
};

const PlaylistThumbnail = ({ playlistId, playlistThumbnail }: PlaylistThumbnailProps) => {
  let src = `${getApiUrl()}${playlistThumbnail}`;

  if (playlistThumbnail === undefined) {
    src = defaultPlaylistThumbnail;
  }

  return (
    <img
      src={src}
      alt={`${playlistId}-thumbnail`}
      onError={({ currentTarget }) => {
        currentTarget.onerror = null; // prevents looping
        currentTarget.src = defaultPlaylistThumbnail;
      }}
    />
  );
};

export default PlaylistThumbnail;
