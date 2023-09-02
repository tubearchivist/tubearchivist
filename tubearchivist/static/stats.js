// build stats for settings page

'use strict';

/* globals apiRequest */

function primaryStats() {
  let apiEndpoint = '/api/stats/primary/';
  let responseData = apiRequest(apiEndpoint, 'GET');
  let primaryBox = document.getElementById('primaryBox');
  clearLoading(primaryBox);
  let videoTile = buildVideoTile(responseData);
  primaryBox.appendChild(videoTile);
  let channelTile = buildChannelTile(responseData);
  primaryBox.appendChild(channelTile);
  let playlistTile = buildPlaylistTile(responseData);
  primaryBox.appendChild(playlistTile);
  let downloadTile = buildDownloadTile(responseData);
  primaryBox.appendChild(downloadTile);
}

function clearLoading(dashBox) {
  dashBox.querySelector('#loading').remove();
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

function watchStats() {
  let apiEndpoint = '/api/stats/watch/';
  let responseData = apiRequest(apiEndpoint, 'GET');
  let watchBox = document.getElementById('watchBox');
  clearLoading(watchBox);

  for (const property in responseData) {
    let tile = buildWatchTile(property, responseData[property]);
    watchBox.appendChild(tile);
  }
}

function buildWatchTile(title, watchDetail) {
  let tile = buildTile(`Total ${title}`);
  let message = document.createElement('p');
  message.innerHTML = `
    ${watchDetail.items} Videos<br>
    ${watchDetail.duration} Seconds<br>
    ${watchDetail.duration_str} Playback
  `;
  if (watchDetail.progress) {
    message.innerHTML += `<br>${Number(watchDetail.progress * 100).toFixed(2)}%`;
  }
  tile.appendChild(message);
  return tile;
}

function downloadHist() {
  let apiEndpoint = '/api/stats/downloadhist/';
  let responseData = apiRequest(apiEndpoint, 'GET');
  let histBox = document.getElementById('downHistBox');
  clearLoading(histBox);
  if (responseData.length === 0) {
    let tile = buildTile('No recent downloads');
    histBox.appendChild(tile);
    return;
  }

  for (let i = 0; i < responseData.length; i++) {
    const dailyStat = responseData[i];
    let tile = buildDailyStat(dailyStat);
    histBox.appendChild(tile);
  }
}

function buildDailyStat(dailyStat) {
  let tile = buildTile(dailyStat.date);
  let message = document.createElement('p');
  message.innerText = `new videos: ${dailyStat.count}`;
  tile.appendChild(message);
  return tile;
}

function biggestChannel() {
  let apiEndpoint = '/api/stats/biggestchannels/';
  let responseData = apiRequest(apiEndpoint, 'GET');
  let tBody = document.getElementById('biggestChannelTable');
  for (let i = 0; i < responseData.length; i++) {
    const channelData = responseData[i];
    let tableRow = buildChannelRow(channelData);
    tBody.appendChild(tableRow);
  }
}

function buildChannelRow(channelData) {
  let tableRow = document.createElement('tr');
  tableRow.innerHTML = `
    <td><a href="/channel/${channelData.id}/">${channelData.name}</a></td>
    <td>${channelData.doc_count}</td>
    <td>${channelData.duration_str}</td>
    <td>${humanFileSize(channelData.media_size)}</td>
  `;
  return tableRow;
}

function humanFileSize(size) {
  let i = size === 0 ? 0 : Math.floor(Math.log(size) / Math.log(1024));
  return (size / Math.pow(1024, i)).toFixed(1) * 1 + ' ' + ['B', 'kB', 'MB', 'GB', 'TB'][i];
}

async function buildStats() {
  primaryStats();
  watchStats();
  downloadHist();
  biggestChannel();
}

document.addEventListener('DOMContentLoaded', () => {
  window.requestAnimationFrame(() => {
    buildStats();
  });
});
