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

function buildVideoTile(responseData) {
  let tile = buildTile(`Video types: `);

  const total = responseData.videos.total || 0;
  const videos = responseData.videos.videos || 0;
  const shorts = responseData.videos.shorts || 0;
  const streams = responseData.videos.streams || 0;

  const content = {
    Videos: `${videos}/${total}`,
    Shorts: `${shorts}/${total}`,
    Streams: `${streams}/${total}`,
  };

  const table = buildTileContenTable(content, 3);

  tile.appendChild(table);

  return tile;
}

function buildChannelTile(responseData) {
  let tile = buildTile(`Channels: `);

  const total = responseData.channels.total || 0;
  const subscribed = responseData.channels.sub_true || 0;

  const content = {
    Subscribed: `${subscribed}/${total}`,
  };

  const table = buildTileContenTable(content, 3);

  tile.appendChild(table);

  return tile;
}

function buildPlaylistTile(responseData) {
  let tile = buildTile(`Playlists:`);

  const total = responseData.playlists.total || 0;
  const subscribed = responseData.playlists.sub_true || 0;

  const content = {
    Subscribed: `${subscribed}/${total}`,
  };

  const table = buildTileContenTable(content, 3);

  tile.appendChild(table);

  return tile;
}

function buildDownloadTile(responseData) {
  let tile = buildTile('Downloads');

  const pending = responseData.downloads.pending || 0;
  const ignored = responseData.downloads.ignore || 0;

  const content = {
    Pending: pending,
    Ignored: ignored,
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

  const { total, watched, unwatched } = responseData;

  let firstCard = buildWatchTile('total', total);
  watchBox.appendChild(firstCard);

  let secondCard = buildWatchTile('watched', watched);
  watchBox.appendChild(secondCard);

  let thirdCard = buildWatchTile('unwatched', unwatched);
  watchBox.appendChild(thirdCard);
}

function capitalizeFirstLetter(string) {
  // source: https://stackoverflow.com/a/1026087
  return string.charAt(0).toUpperCase() + string.slice(1);
}

function buildWatchTile(title, watchDetail) {
  const items = watchDetail.items || 0;
  const duration = watchDetail.duration || 0;
  const duration_str = watchDetail.duration_str || 0;
  const hasProgess = !!watchDetail.progress;
  const progress = Number(watchDetail.progress * 100).toFixed(2);

  let titleCapizalized = capitalizeFirstLetter(title);

  if (hasProgess) {
    titleCapizalized = `${progress}% ` + titleCapizalized;
  }

  let tile = buildTile(titleCapizalized);

  const content = {
    Videos: items,
    Seconds: duration,
    Playback: duration_str,
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

  message.innerText = 
  `+${dailyStat.count} ${text}
  ${humanFileSize(dailyStat.media_size)}`;

  tile.appendChild(message);
  return tile;
}

function humanFileSize(size) {
  let i = size === 0 ? 0 : Math.floor(Math.log(size) / Math.log(1024));
  return (size / Math.pow(1024, i)).toFixed(1) * 1 + ' ' + ['B', 'kB', 'MB', 'GB', 'TB'][i];
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

function biggestChannel() {
  addBiggestChannelByDocCount();
  addBiggestChannelByDuration();
  addBiggestChannelByMediaSize();
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
