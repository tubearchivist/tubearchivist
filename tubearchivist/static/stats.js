// build stats for settings page

'use strict';

/* globals apiRequest */

function primaryStats() {
  let apiEndpoint = '/api/stats/primary/';
  let responseData = apiRequest(apiEndpoint, 'GET');
  let primaryBox = document.getElementById('primaryBox');
  let videoTile = buildVideoTile(responseData);
  primaryBox.appendChild(videoTile);
  let channelTile = buildChannelTile(responseData);
  primaryBox.appendChild(channelTile);
  let playlistTile = buildPlaylistTile(responseData);
  primaryBox.appendChild(playlistTile);
  let downloadTile = buildDownloadTile(responseData);
  primaryBox.appendChild(downloadTile);
}

function buildTile(titleText) {
  let tile = document.createElement('div');
  tile.classList.add('info-box-item');
  let title = document.createElement('h3');
  title.innerText = titleText;
  tile.appendChild(title);
  return tile;
}

function buildVideoTile(responseData) {
  let tile = buildTile(`Total Videos: ${responseData.videos.total || 0}`);
  let message = document.createElement('p');
  message.innerHTML = `
        videos: ${responseData.videos.videos || 0}<br>
        shorts: ${responseData.videos.shorts || 0}<br>
        streams: ${responseData.videos.streams || 0}<br>
    `;
  tile.appendChild(message);

  return tile;
}

function buildChannelTile(responseData) {
  let tile = buildTile(`Total Channels: ${responseData.channels.total || 0}`);
  let message = document.createElement('p');
  message.innerHTML = `subscribed: ${responseData.channels.sub_true || 0}`;
  tile.appendChild(message);

  return tile;
}

function buildPlaylistTile(responseData) {
  let tile = buildTile(`Total Playlists: ${responseData.playlists.total || 0}`);
  let message = document.createElement('p');
  message.innerHTML = `subscribed: ${responseData.playlists.sub_true || 0}`;
  tile.appendChild(message);

  return tile;
}

function buildDownloadTile(responseData) {
  let tile = buildTile('Downloads');
  let message = document.createElement('p');
  message.innerHTML = `
        pending: ${responseData.downloads.pending || 0}<br>
        ignored: ${responseData.downloads.ignore || 0}<br>
    `;
  tile.appendChild(message);

  return tile;
}

function buildStats() {
  primaryStats();
}

buildStats();
