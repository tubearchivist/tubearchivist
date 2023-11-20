// build stats for settings page

'use strict';

/* globals apiRequest */

function primaryStats() {
  let apiVideoEndpoint = '/api/stats/video/';
  let responseData = apiRequest(apiVideoEndpoint, 'GET');

  let activeBox = document.getElementById('activeBox');
  clearLoading(activeBox);

  let totalTile = buildTotalVideoTile(responseData);
  activeBox.appendChild(totalTile);
  let activeTile = buildActiveVideoTile(responseData);
  activeBox.appendChild(activeTile);
  let inActiveTile = buildInActiveVideoTile(responseData);
  activeBox.appendChild(inActiveTile);

  let videoTypeBox = document.getElementById('videoTypeBox');
  clearLoading(videoTypeBox);

  let videosTypeTile = buildVideosTypeTile(responseData);
  videoTypeBox.appendChild(videosTypeTile);
  let shortsTypeTile = buildShortsTypeTile(responseData);
  videoTypeBox.appendChild(shortsTypeTile);
  let streamsTypeTile = buildStreamsTypeTile(responseData);
  videoTypeBox.appendChild(streamsTypeTile);
}

function secondaryStats() {
  let apiChannelEndpoint = '/api/stats/channel/';
  let channelResponseData = apiRequest(apiChannelEndpoint, 'GET');
  let secondaryBox = document.getElementById('secondaryBox');
  clearLoading(secondaryBox);
  let channelTile = buildChannelTile(channelResponseData);
  secondaryBox.appendChild(channelTile);

  let apiPlaylistEndpoint = '/api/stats/playlist/';
  let playlistResponseData = apiRequest(apiPlaylistEndpoint, 'GET');
  let playlistTile = buildPlaylistTile(playlistResponseData);
  secondaryBox.appendChild(playlistTile);

  let apiDownloadEndpoint = '/api/stats/download/';
  let downloadResponseData = apiRequest(apiDownloadEndpoint, 'GET');
  let downloadTile = buildDownloadTile(downloadResponseData);
  secondaryBox.appendChild(downloadTile);
}

function buildTotalVideoTile(responseData) {
  const totalCount = responseData.doc_count || 0;
  const totalSize = humanFileSize(responseData.media_size || 0);
  const content = {
    Videos: `${totalCount}`,
    'Media Size': `${totalSize}`,
    Duration: responseData.duration_str,
  };
  const tile = buildTile('All: ');
  const table = buildTileContenTable(content, 2);
  tile.appendChild(table);
  return tile;
}

function buildActiveVideoTile(responseData) {
  const activeCount = responseData?.active_true?.doc_count || 0;
  const activeSize = humanFileSize(responseData?.active_true?.media_size || 0);
  const duration = responseData?.active_true?.duration_str || 'NA';
  const content = {
    Videos: `${activeCount}`,
    'Media Size': `${activeSize}`,
    Duration: duration,
  };
  const tile = buildTile('Active: ');
  const table = buildTileContenTable(content, 2);
  tile.appendChild(table);
  return tile;
}

function buildInActiveVideoTile(responseData) {
  const inActiveCount = responseData?.active_false?.doc_count || 0;
  const inActiveSize = humanFileSize(responseData?.active_false?.media_size || 0);
  const duration = responseData?.active_false?.duration_str || 'NA';
  const content = {
    Videos: `${inActiveCount}`,
    'Media Size': `${inActiveSize}`,
    Duration: duration,
  };
  const tile = buildTile('Inactive: ');
  const table = buildTileContenTable(content, 2);
  tile.appendChild(table);
  return tile;
}

function buildVideosTypeTile(responseData) {
  const videosCount = responseData?.type_videos?.doc_count || 0;
  const videosSize = humanFileSize(responseData?.type_videos?.media_size || 0);
  const duration = responseData?.type_videos?.duration_str || 'NA';
  const content = {
    Videos: `${videosCount}`,
    'Media Size': `${videosSize}`,
    Duration: duration,
  };
  const tile = buildTile('Regular Videos: ');
  const table = buildTileContenTable(content, 2);
  tile.appendChild(table);
  return tile;
}

function buildShortsTypeTile(responseData) {
  const shortsCount = responseData?.type_shorts?.doc_count || 0;
  const shortsSize = humanFileSize(responseData?.type_shorts?.media_size || 0);
  const duration = responseData?.type_shorts?.duration_str || 'NA';
  const content = {
    Videos: `${shortsCount}`,
    'Media Size': `${shortsSize}`,
    Duration: duration,
  };
  const tile = buildTile('Shorts: ');
  const table = buildTileContenTable(content, 2);
  tile.appendChild(table);
  return tile;
}

function buildStreamsTypeTile(responseData) {
  const streamsCount = responseData?.type_streams?.doc_count || 0;
  const streamsSize = humanFileSize(responseData?.type_streams?.media_size || 0);
  const duration = responseData?.type_streams?.duration_str || 'NA';
  const content = {
    Videos: `${streamsCount}`,
    'Media Size': `${streamsSize}`,
    Duration: duration,
  };
  const tile = buildTile('Streams: ');
  const table = buildTileContenTable(content, 2);
  tile.appendChild(table);
  return tile;
}

function buildChannelTile(responseData) {
  let tile = buildTile('Channels: ');
  const total = responseData.doc_count || 0;
  const subscribed = responseData.subscribed_true || 0;
  const active = responseData.active_true || 0;
  const content = {
    Subscribed: subscribed,
    Active: active,
    Total: total,
  };
  const table = buildTileContenTable(content, 3);
  tile.appendChild(table);

  return tile;
}

function buildPlaylistTile(responseData) {
  let tile = buildTile('Playlists: ');
  const total = responseData.doc_count || 0;
  const subscribed = responseData.subscribed_true || 0;
  const active = responseData.active_true || 0;
  const content = {
    Subscribed: subscribed,
    Active: active,
    Total: total,
  };
  const table = buildTileContenTable(content, 2);
  tile.appendChild(table);

  return tile;
}

function buildDownloadTile(responseData) {
  const pendingTotal = responseData.pending || 0;
  let tile = buildTile(`Downloads Pending: ${pendingTotal}`);
  const pendingVideos = responseData.pending_videos || 0;
  const pendingShorts = responseData.pending_shorts || 0;
  const pendingStreams = responseData.pending_streams || 0;
  const content = {
    Videos: pendingVideos,
    Shorts: pendingShorts,
    Streams: pendingStreams,
  };
  const table = buildTileContenTable(content, 3);
  tile.appendChild(table);

  return tile;
}

function watchStats() {
  let apiEndpoint = '/api/stats/watch/';
  let responseData = apiRequest(apiEndpoint, 'GET');
  let watchBox = document.getElementById('watchBox');
  clearLoading(watchBox);

  let watchedTile = buildWatchTile('watched', responseData.watched);
  watchBox.appendChild(watchedTile);

  let unwatchedTile = buildWatchTile('unwatched', responseData.unwatched);
  watchBox.appendChild(unwatchedTile);
}

function buildWatchTile(title, watchDetail) {
  const items = watchDetail?.items ?? 0;
  const duration = watchDetail?.duration ?? 0;
  const duration_str = watchDetail?.duration_str ?? '0s';
  const hasProgess = !!watchDetail?.progress;
  const progress = (Number(watchDetail?.progress) * 100).toFixed(2) ?? '0';

  let titleCapizalized = capitalizeFirstLetter(title);

  if (hasProgess) {
    titleCapizalized = `${progress}% ` + titleCapizalized;
  }

  let tile = buildTile(titleCapizalized);

  const content = {
    Videos: items,
    Seconds: duration,
    Duration: duration_str,
  };

  const table = buildTileContenTable(content, 3);

  tile.appendChild(table);

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
  const isExactlyOne = dailyStat.count === 1;

  let text = 'Videos';
  if (isExactlyOne) {
    text = 'Video';
  }

  message.innerText = `+${dailyStat.count} ${text}
  ${humanFileSize(dailyStat.media_size)}`;

  tile.appendChild(message);
  return tile;
}

function buildChannelRow(id, name, value) {
  let tableRow = document.createElement('tr');

  tableRow.innerHTML = `
    <td class="agg-channel-name"><a href="/channel/${id}/">${name}</a></td>
    <td class="agg-channel-right-align">${value}</td>
  `;

  return tableRow;
}

function addBiggestChannelByDocCount() {
  let tBody = document.getElementById('biggestChannelTableVideos');

  let apiEndpoint = '/api/stats/biggestchannels/?order=doc_count';
  const responseData = apiRequest(apiEndpoint, 'GET');

  for (let i = 0; i < responseData.length; i++) {
    const { id, name, doc_count } = responseData[i];

    let tableRow = buildChannelRow(id, name, doc_count);

    tBody.appendChild(tableRow);
  }
}

function addBiggestChannelByDuration() {
  const tBody = document.getElementById('biggestChannelTableDuration');

  let apiEndpoint = '/api/stats/biggestchannels/?order=duration';
  const responseData = apiRequest(apiEndpoint, 'GET');

  for (let i = 0; i < responseData.length; i++) {
    const { id, name, duration_str } = responseData[i];

    let tableRow = buildChannelRow(id, name, duration_str);

    tBody.appendChild(tableRow);
  }
}

function addBiggestChannelByMediaSize() {
  let tBody = document.getElementById('biggestChannelTableMediaSize');

  let apiEndpoint = '/api/stats/biggestchannels/?order=media_size';
  const responseData = apiRequest(apiEndpoint, 'GET');

  for (let i = 0; i < responseData.length; i++) {
    const { id, name, media_size } = responseData[i];

    let tableRow = buildChannelRow(id, name, humanFileSize(media_size));

    tBody.appendChild(tableRow);
  }
}

function clearLoading(dashBox) {
  dashBox.querySelector('#loading').remove();
}

function capitalizeFirstLetter(string) {
  // source: https://stackoverflow.com/a/1026087
  return string.charAt(0).toUpperCase() + string.slice(1);
}

function humanFileSize(size) {
  let i = size === 0 ? 0 : Math.floor(Math.log(size) / Math.log(1024));
  return (size / Math.pow(1024, i)).toFixed(1) * 1 + ' ' + ['B', 'kB', 'MB', 'GB', 'TB'][i];
}

function buildTile(titleText) {
  let tile = document.createElement('div');
  tile.classList.add('info-box-item');

  let title = document.createElement('h3');

  title.innerText = titleText;
  tile.appendChild(title);

  return tile;
}

function buildTileContenTable(content, rowsWanted) {
  let contentEntries = Object.entries(content);

  const nbsp = '\u00A0'; // No-Break Space https://www.compart.com/en/unicode/U+00A0

  // Do not add spacing rows when on mobile device
  const isMobile = window.matchMedia('(max-width: 600px)');
  if (!isMobile.matches) {
    if (contentEntries.length < rowsWanted) {
      const rowsToAdd = rowsWanted - contentEntries.length;

      for (let i = 0; i < rowsToAdd; i++) {
        contentEntries.push([nbsp, nbsp]);
      }
    }
  }

  const table = document.createElement('table');
  table.classList.add('agg-channel-table');
  const tableBody = document.createElement('tbody');

  for (const [key, value] of contentEntries) {
    const row = document.createElement('tr');

    const leftCell = document.createElement('td');
    leftCell.classList.add('agg-channel-name');

    // Do not add ":" when its a spacing entry
    const keyText = key === nbsp ? key : `${key}: `;
    const leftText = document.createTextNode(keyText);
    leftCell.appendChild(leftText);

    const rightCell = document.createElement('td');
    rightCell.classList.add('agg-channel-right-align');

    const rightText = document.createTextNode(value);
    rightCell.appendChild(rightText);

    row.appendChild(leftCell);
    row.appendChild(rightCell);

    tableBody.appendChild(row);
  }

  table.appendChild(tableBody);

  return table;
}

function biggestChannel() {
  addBiggestChannelByDocCount();
  addBiggestChannelByDuration();
  addBiggestChannelByMediaSize();
}

async function buildStats() {
  primaryStats();
  secondaryStats();
  watchStats();
  downloadHist();
  biggestChannel();
}

document.addEventListener('DOMContentLoaded', () => {
  window.requestAnimationFrame(() => {
    buildStats();
  });
});
