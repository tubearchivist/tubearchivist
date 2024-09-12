'use strict';

/* globals checkMessages */

function sortChange(button) {
  let apiEndpoint = '/api/config/user/';
  let data = {};
  data[button.name] = button.value;
  apiRequest(apiEndpoint, 'POST', data);
  setTimeout(function () {
    location.reload();
  }, 500);
}

// Updates video watch status when passed a video id and it's current state (ex if the video was unwatched but you want to mark it as watched you will pass "unwatched")
function updateVideoWatchStatus(input1, videoCurrentWatchStatus) {
  let videoId;
  if (videoCurrentWatchStatus) {
    videoId = input1;
  } else if (input1.getAttribute('data-id')) {
    videoId = input1.getAttribute('data-id');
    videoCurrentWatchStatus = input1.getAttribute('data-status');
  }

  postVideoProgress(videoId, 0); // Reset video progress on watched/unwatched;
  removeProgressBar(videoId);

  let watchStatusIndicator;
  let apiEndpoint = '/api/watched/';
  if (videoCurrentWatchStatus === 'watched') {
    watchStatusIndicator = createWatchStatusIndicator(videoId, 'unwatched');
    apiRequest(apiEndpoint, 'POST', { id: videoId, is_watched: false });
  } else if (videoCurrentWatchStatus === 'unwatched') {
    watchStatusIndicator = createWatchStatusIndicator(videoId, 'watched');
    apiRequest(apiEndpoint, 'POST', { id: videoId, is_watched: true });
  }

  let watchButtons = document.getElementsByClassName('watch-button');
  for (let i = 0; i < watchButtons.length; i++) {
    if (watchButtons[i].getAttribute('data-id') === videoId) {
      watchButtons[i].outerHTML = watchStatusIndicator;
    }
  }
}

// Creates a watch status indicator when passed a video id and the videos watch status
function createWatchStatusIndicator(videoId, videoWatchStatus) {
  let seen, title;
  if (videoWatchStatus === 'watched') {
    seen = 'seen';
    title = 'Mark as unwatched';
  } else if (videoWatchStatus === 'unwatched') {
    seen = 'unseen';
    title = 'Mark as watched';
  }
  let watchStatusIndicator = `<img src="/static/img/icon-${seen}.svg" alt="${seen}-icon" data-id="${videoId}" data-status="${videoWatchStatus}" onclick="updateVideoWatchStatus(this)" class="watch-button" title="${title}">`;
  return watchStatusIndicator;
}

// Removes the progress bar when passed a video id
function removeProgressBar(videoId) {
  setProgressBar(videoId, 0, 1);
}

function isWatchedButton(button) {
  let youtube_id = button.getAttribute('data-id');
  let apiEndpoint = '/api/watched/';
  let data = { id: youtube_id, is_watched: true };
  apiRequest(apiEndpoint, 'POST', data);
  setTimeout(function () {
    location.reload();
  }, 1000);
}
function isUnwatchedButton(button) {
  let youtube_id = button.getAttribute('data-id');
  let apiEndpoint = '/api/watched/';
  let data = { id: youtube_id, is_watched: false };
  apiRequest(apiEndpoint, 'POST', data);
  setTimeout(function () {
    location.reload();
  }, 1000);
}

function subscribeStatus(subscribeButton) {
  let id = subscribeButton.getAttribute('data-id');
  let type = subscribeButton.getAttribute('data-type');
  let subscribe = Boolean(subscribeButton.getAttribute('data-subscribe'));
  let apiEndpoint;
  let data;
  if (type === 'channel') {
    apiEndpoint = '/api/channel/';
    data = { data: [{ channel_id: id, channel_subscribed: subscribe }] };
  } else if (type === 'playlist') {
    apiEndpoint = '/api/playlist/';
    data = { data: [{ playlist_id: id, playlist_subscribed: subscribe }] };
  }
  apiRequest(apiEndpoint, 'POST', data);
  let message = document.createElement('span');
  if (subscribe) {
    message.innerText = 'You are subscribed.';
  } else {
    message.innerText = 'You are unsubscribed.';
  }
  subscribeButton.replaceWith(message);
}

function changeView(image) {
  let sourcePage = image.getAttribute('data-origin');
  let newView = image.getAttribute('data-value');
  let apiEndpoint = '/api/config/user/';
  let data = {};
  data[`view_style_${sourcePage}`] = newView;
  console.log(data);
  apiRequest(apiEndpoint, 'POST', data);
  setTimeout(function () {
    location.reload();
  }, 500);
}

function changeGridItems(image) {
  let newGridItems = Number(image.getAttribute('data-value'));
  let apiEndpoint = '/api/config/user/';
  let data = { grid_items: newGridItems };
  apiRequest(apiEndpoint, 'POST', data);
  setTimeout(function () {
    location.reload();
  }, 500);
}

function toggleCheckbox(checkbox) {
  // pass checkbox id as key and checkbox.checked as value
  let apiEndpoint = '/api/config/user/';
  let data = {};
  data[checkbox.id] = checkbox.checked;
  apiRequest(apiEndpoint, 'POST', data);
  setTimeout(function () {
    let currPage = window.location.pathname;
    window.location.replace(currPage);
  }, 500);
}

// start reindex task
function reindex(button) {
  let apiEndpoint = '/api/refresh/';
  if (button.getAttribute('data-extract-videos')) {
    apiEndpoint += '?extract_videos=true';
  }
  let type = button.getAttribute('data-type');
  let id = button.getAttribute('data-id');

  let data = {};
  data[type] = [id];

  apiRequest(apiEndpoint, 'POST', data);
  let message = document.createElement('p');
  message.innerText = 'Reindex scheduled';
  document.getElementById('reindex-button').replaceWith(message);
  setTimeout(function () {
    checkMessages();
  }, 500);
}

// download page buttons
function rescanPending() {
  let apiEndpoint = '/api/task-name/update_subscribed/';
  apiRequest(apiEndpoint, 'POST');
  animate('rescan-icon', 'rotate-img');
  setTimeout(function () {
    checkMessages();
  }, 500);
}

function dlPending() {
  let apiEndpoint = '/api/task-name/download_pending/';
  apiRequest(apiEndpoint, 'POST');
  animate('download-icon', 'bounce-img');
  setTimeout(function () {
    checkMessages();
  }, 500);
}

function addToQueue(autostart = false) {
  let textArea = document.getElementById('id_vid_url');
  if (textArea.value === '') {
    return;
  }
  let toPost = { data: [{ youtube_id: textArea.value, status: 'pending' }] };
  let apiEndpoint = '/api/download/';
  if (autostart) {
    apiEndpoint = `${apiEndpoint}?autostart=true`;
  }
  apiRequest(apiEndpoint, 'POST', toPost);
  textArea.value = '';
  setTimeout(function () {
    checkMessages();
  }, 500);
  showForm();
}

//shows the video sub menu popup
function showAddToPlaylistMenu(input1) {
  let dataId, playlists, form_code, buttonId;
  dataId = input1.getAttribute('data-id');
  buttonId = input1.getAttribute('id');
  playlists = getCustomPlaylists();

  //hide the invoking button
  input1.style.visibility = 'hidden';

  //show the form
  form_code =
    '<div class="video-popup-menu"><img src="/static/img/icon-close.svg" class="video-popup-menu-close-button" title="Close menu" onclick="removeDotMenu(this, \'' +
    buttonId +
    '\')"/><h3>Add video to...</h3>';

  for (let i = 0; i < playlists.length; i++) {
    let obj = playlists[i];
    form_code +=
      '<p onclick="addToCustomPlaylist(this, \'' +
      dataId +
      "','" +
      obj.playlist_id +
      '\')"><img class="p-button" src="/static/img/icon-unseen.svg"/>' +
      obj.playlist_name +
      '</p>';
  }

  form_code += '<p><a href="/playlist">Create playlist</a></p></div>';
  input1.parentNode.parentNode.innerHTML += form_code;
}

//handles user action of adding a video to a custom playlist
function addToCustomPlaylist(input, video_id, playlist_id) {
  let apiEndpoint = '/api/playlist/' + playlist_id + '/';
  let data = { action: 'create', video_id: video_id };
  apiRequest(apiEndpoint, 'POST', data);

  //mark the item added in the ui
  input.firstChild.src = '/static/img/icon-seen.svg';
}

function removeDotMenu(input1, button_id) {
  //show the menu button
  document.getElementById(button_id).style.visibility = 'visible';

  //remove the form
  input1.parentNode.remove();
}

//shows the video sub menu popup on custom playlist page
function showCustomPlaylistMenu(input1, playlist_id, current_page, last_page) {
  let dataId, form_code, buttonId;
  dataId = input1.getAttribute('data-id');
  buttonId = input1.getAttribute('id');

  //hide the invoking button
  input1.style.visibility = 'hidden';

  //show the form
  form_code =
    '<div class="video-popup-menu"><img src="/static/img/icon-close.svg" class="video-popup-menu-close-button" title="Close menu" onclick="removeDotMenu(this, \'' +
    buttonId +
    '\')"/><h3>Move Video</h3>';

  form_code +=
    '<img class="move-video-button" data-id="' +
    dataId +
    '" data-context="top" onclick="moveCustomPlaylistVideo(this,\'' +
    playlist_id +
    "'," +
    current_page +
    ',' +
    last_page +
    ')" src="/static/img/icon-arrow-top.svg" title="Move to top"/>';
  form_code +=
    '<img class="move-video-button" data-id="' +
    dataId +
    '" data-context="up" onclick="moveCustomPlaylistVideo(this,\'' +
    playlist_id +
    "'," +
    current_page +
    ',' +
    last_page +
    ')" src="/static/img/icon-arrow-up.svg" title="Move up"/>';
  form_code +=
    '<img class="move-video-button" data-id="' +
    dataId +
    '" data-context="down" onclick="moveCustomPlaylistVideo(this,\'' +
    playlist_id +
    "'," +
    current_page +
    ',' +
    last_page +
    ')" src="/static/img/icon-arrow-down.svg" title="Move down"/>';
  form_code +=
    '<img class="move-video-button" data-id="' +
    dataId +
    '" data-context="bottom" onclick="moveCustomPlaylistVideo(this,\'' +
    playlist_id +
    "'," +
    current_page +
    ',' +
    last_page +
    ')" src="/static/img/icon-arrow-bottom.svg" title="Move to bottom"/>';
  form_code +=
    '<img class="move-video-button" data-id="' +
    dataId +
    '" data-context="remove" onclick="moveCustomPlaylistVideo(this,\'' +
    playlist_id +
    "'," +
    current_page +
    ',' +
    last_page +
    ')" src="/static/img/icon-remove.svg" title="Remove from playlist"/>';

  form_code += '</div>';
  input1.parentNode.parentNode.innerHTML += form_code;
}

//process custom playlist form actions
function moveCustomPlaylistVideo(input1, playlist_id, current_page, last_page) {
  let dataId, dataContext;
  dataId = input1.getAttribute('data-id');
  dataContext = input1.getAttribute('data-context');

  let apiEndpoint = '/api/playlist/' + playlist_id + '/';
  let data = { action: dataContext, video_id: dataId };
  apiRequest(apiEndpoint, 'POST', data);

  let itemDom = input1.parentElement.parentElement.parentElement;
  let listDom = itemDom.parentElement;

  if (dataContext === 'up') {
    let sibling = itemDom.previousElementSibling;
    if (sibling !== null) {
      sibling.before(itemDom);
    } else if (current_page > 1) {
      itemDom.remove();
    }
  } else if (dataContext === 'down') {
    let sibling = itemDom.nextElementSibling;
    if (sibling !== null) {
      sibling.after(itemDom);
    } else if (current_page !== last_page) {
      itemDom.remove();
    }
  } else if (dataContext === 'top') {
    let sibling = listDom.firstElementChild;
    if (sibling !== null) {
      sibling.before(itemDom);
    }
    if (current_page > 1) {
      itemDom.remove();
    }
  } else if (dataContext === 'bottom') {
    let sibling = listDom.lastElementChild;
    if (sibling !== null) {
      sibling.after(itemDom);
    }
    if (current_page !== last_page) {
      itemDom.remove();
    }
  } else if (dataContext === 'remove') {
    itemDom.remove();
  }
}

function toIgnore(button) {
  let youtube_id = button.getAttribute('data-id');
  let apiEndpoint = '/api/download/' + youtube_id + '/';
  apiRequest(apiEndpoint, 'POST', { status: 'ignore' });
  document.getElementById('dl-' + youtube_id).remove();
}

function downloadNow(button) {
  let youtube_id = button.getAttribute('data-id');
  let apiEndpoint = '/api/download/' + youtube_id + '/';
  apiRequest(apiEndpoint, 'POST', { status: 'priority' });
  document.getElementById(youtube_id).remove();
  setTimeout(function () {
    checkMessages();
  }, 500);
}

function forgetIgnore(button) {
  let youtube_id = button.getAttribute('data-id');
  let apiEndpoint = '/api/download/' + youtube_id + '/';
  apiRequest(apiEndpoint, 'DELETE');
  document.getElementById('dl-' + youtube_id).remove();
}

function addSingle(button) {
  let youtube_id = button.getAttribute('data-id');
  let apiEndpoint = '/api/download/' + youtube_id + '/';
  apiRequest(apiEndpoint, 'POST', { status: 'pending' });
  document.getElementById('dl-' + youtube_id).remove();
  setTimeout(function () {
    checkMessages();
  }, 500);
}

function deleteQueue(button) {
  let to_delete = button.getAttribute('data-id');
  let apiEndpoint = '/api/download/?filter=' + to_delete;
  apiRequest(apiEndpoint, 'DELETE');
  // clear button
  let message = document.createElement('p');
  message.innerText = 'deleting download queue: ' + to_delete;
  document.getElementById(button.id).replaceWith(message);
}

function stopTask(icon) {
  let taskId = icon.getAttribute('data');
  let apiEndpoint = `/api/task-id/${taskId}/`;
  apiRequest(apiEndpoint, 'POST', { command: 'stop' });
  icon.remove();
}

function killTask(icon) {
  let taskId = icon.getAttribute('data');
  let apiEndpoint = `/api/task-id/${taskId}/`;
  apiRequest(apiEndpoint, 'POST', { command: 'kill' });
  icon.remove();
}

// settings page buttons
function manualImport() {
  let apiEndpoint = '/api/task-name/manual_import/';
  apiRequest(apiEndpoint, 'POST');
  // clear button
  let message = document.createElement('p');
  message.innerText = 'processing import';
  let toReplace = document.getElementById('manual-import');
  toReplace.innerHTML = '';
  toReplace.appendChild(message);
  setTimeout(function () {
    location.replace('#notifications');
    checkMessages();
  }, 200);
}

function reEmbed() {
  let apiEndpoint = '/api/task-name/resync_thumbs/';
  apiRequest(apiEndpoint, 'POST');
  // clear button
  let message = document.createElement('p');
  message.innerText = 'processing thumbnails';
  let toReplace = document.getElementById('re-embed');
  toReplace.innerHTML = '';
  toReplace.appendChild(message);
  setTimeout(function () {
    location.replace('#notifications');
    checkMessages();
  }, 200);
}

function dbBackup() {
  let apiEndpoint = '/api/backup/';
  apiRequest(apiEndpoint, 'POST');
  // clear button
  let message = document.createElement('p');
  message.innerText = 'backing up archive';
  let toReplace = document.getElementById('db-backup');
  toReplace.innerHTML = '';
  toReplace.appendChild(message);
  setTimeout(function () {
    location.replace('#notifications');
    checkMessages();
  }, 200);
}

function dbRestore(button) {
  let fileName = button.getAttribute('data-id');
  let apiEndpoint = `/api/backup/${fileName}/`;
  apiRequest(apiEndpoint, 'POST');
  // clear backup row
  let message = document.createElement('p');
  message.innerText = 'restoring from backup';
  let toReplace = document.getElementById(fileName);
  toReplace.innerHTML = '';
  toReplace.appendChild(message);
  setTimeout(function () {
    location.replace('#notifications');
    checkMessages();
  }, 200);
}

function fsRescan() {
  let apiEndpoint = '/api/task-name/rescan_filesystem/';
  apiRequest(apiEndpoint, 'POST');
  // clear button
  let message = document.createElement('p');
  message.innerText = 'File system scan in progress';
  let toReplace = document.getElementById('fs-rescan');
  toReplace.innerHTML = '';
  toReplace.appendChild(message);
  setTimeout(function () {
    location.replace('#notifications');
    checkMessages();
  }, 200);
}

function resetToken() {
  let apiEndpoint = '/api/token/';
  let result = apiRequest(apiEndpoint, 'DELETE');
  if (result && result.success) {
    let message = document.createElement('p');
    message.innerText = 'Token revoked';
    document.getElementById('text-reveal').replaceWith(message);
  } else {
    console.error('unable to revoke token');
  }
}

// restore from snapshot
function restoreSnapshot(snapshotId) {
  console.log('restore ' + snapshotId);
  let apiEndpoint = '/api/snapshot/' + snapshotId + '/';
  apiRequest(apiEndpoint, 'POST');
  let message = document.createElement('p');
  message.innerText = 'Snapshot restore started';
  document.getElementById(snapshotId).parentElement.replaceWith(message);
}

function createSnapshot() {
  console.log('create snapshot now');
  let apiEndpoint = '/api/snapshot/';
  apiRequest(apiEndpoint, 'POST');
  let message = document.createElement('span');
  message.innerText = 'Snapshot in progress';
  document.getElementById('createButton').replaceWith(message);
}

function deleteNotificationUrl(button) {
  console.log('delete notification url');
  let apiEndpoint = '/api/schedule/notification/';
  let data = {
    task_name: button.dataset.task,
    url: button.dataset.url,
  };
  apiRequest(apiEndpoint, 'DELETE', data);
  button.parentElement.remove();
}

function deleteSchedule(button) {
  console.log('delete schedule');
  let apiEndpoint = '/api/schedule/';
  let data = { task_name: button.dataset.schedule };
  apiRequest(apiEndpoint, 'DELETE', data);
  let message = document.createElement('span');
  message.innerText = 'False';
  message.classList.add('settings-current');
  button.parentElement.replaceWith(message);
}

// delete from file system
function deleteConfirm() {
  let to_show = document.getElementById('delete-button');
  document.getElementById('delete-item').style.display = 'none';
  to_show.style.display = 'block';
}

function deleteVideo(button) {
  let to_delete = button.getAttribute('data-id');
  let to_ignore = button.getAttribute('data-ignore');
  let to_redirect = button.getAttribute('data-redirect');
  let apiDeleteEndpoint = '/api/video/' + to_delete + '/';
  apiRequest(apiDeleteEndpoint, 'DELETE');

  if (to_ignore !== null) {
    let apiIgnoreEndpoint = '/api/download/' + to_delete + '/';
    apiRequest(apiIgnoreEndpoint, 'POST', { status: 'ignore-force' });
  }

  setTimeout(function () {
    let redirect = '/channel/' + to_redirect;
    window.location.replace(redirect);
  }, 1000);
}

function deleteChannel(button) {
  let to_delete = button.getAttribute('data-id');
  let apiEndpoint = '/api/channel/' + to_delete + '/';
  apiRequest(apiEndpoint, 'DELETE');
  setTimeout(function () {
    window.location.replace('/channel/');
  }, 1000);
}

function deletePlaylist(button) {
  let playlist_id = button.getAttribute('data-id');
  let playlist_action = button.getAttribute('data-action');
  let apiEndpoint = `/api/playlist/${playlist_id}/`;
  if (playlist_action === 'delete-videos') {
    apiEndpoint += '?delete-videos=true';
  }
  apiRequest(apiEndpoint, 'DELETE');
  setTimeout(function () {
    window.location.replace('/playlist/');
  }, 1000);
}

function cancelDelete() {
  document.getElementById('delete-button').style.display = 'none';
  document.getElementById('delete-item').style.display = 'block';
}

// get seconds from hh:mm:ss.ms timestamp
function getSeconds(timestamp) {
  let elements = timestamp.split(':', 3);
  let secs = parseInt(elements[0]) * 60 * 60 + parseInt(elements[1]) * 60 + parseFloat(elements[2]);
  return secs;
}

// player
let sponsorBlock = [];
function createPlayer(button) {
  let videoId = button.getAttribute('data-id');
  let videoPosition = button.getAttribute('data-position');
  let videoData = getVideoData(videoId);

  let sponsorBlockElements = '';
  if (videoData.data.sponsorblock && videoData.data.sponsorblock.is_enabled) {
    sponsorBlock = videoData.data.sponsorblock;
    if (sponsorBlock.segments.length === 0) {
      sponsorBlockElements = `
            <div class="sponsorblock" id="sponsorblock">
                <h4>This video doesn't have any sponsor segments added. To add a segment go to <u><a href="https://www.youtube.com/watch?v=${videoId}">this video on Youtube</a></u> and add a segment using the <u><a href="https://sponsor.ajay.app/">SponsorBlock</a></u> extension.</h4>
            </div>
            `;
    } else {
      if (sponsorBlock.has_unlocked) {
        sponsorBlockElements = `
                <div class="sponsorblock" id="sponsorblock">
                    <h4>This video has unlocked sponsor segments. Go to <u><a href="https://www.youtube.com/watch?v=${videoId}">this video on YouTube</a></u> and vote on the segments using the <u><a href="https://sponsor.ajay.app/">SponsorBlock</a></u> extension.</h4>
                </div>
                `;
      }
    }
  } else {
    sponsorBlock = null;
  }
  let videoProgress;
  if (videoPosition) {
    videoProgress = getSeconds(videoPosition);
  } else {
    videoProgress = getVideoProgress(videoId).position;
  }
  let videoName = videoData.data.title;

  let videoTag = createVideoTag(videoData, videoProgress, true);

  let playlist = '';
  let videoPlaylists = videoData.data.playlist; // Array of playlists the video is in
  if (typeof videoPlaylists !== 'undefined') {
    let subbedPlaylists = getSubbedPlaylists(videoPlaylists); // Array of playlist the video is in that are subscribed
    if (subbedPlaylists.length !== 0) {
      let playlistData = getPlaylistData(subbedPlaylists[0]); // Playlist data for first subscribed playlist
      let playlistId = playlistData.playlist_id;
      let playlistName = playlistData.playlist_name;
      playlist = `<h5><a href="/playlist/${playlistId}/">${playlistName}</a></h5>`;
    }
  }

  let videoViews = formatNumbers(videoData.data.stats.view_count);

  let channelId = videoData.data.channel.channel_id;
  let channelName = videoData.data.channel.channel_name;

  removePlayer();

  // If cast integration is enabled create cast button
  let castButton = '';
  if (videoData.config.enable_cast) {
    castButton = `<google-cast-launcher id="castbutton"></google-cast-launcher>`;
  }

  // Watched indicator
  let watchStatusIndicator;
  if (videoData.data.player.watched) {
    watchStatusIndicator = createWatchStatusIndicator(videoId, 'watched');
  } else {
    watchStatusIndicator = createWatchStatusIndicator(videoId, 'unwatched');
  }

  let playerStats = `<div class="thumb-icon player-stats"><img src="/static/img/icon-eye.svg" alt="views icon"><span>${videoViews}</span>`;
  if (videoData.data.stats.like_count) {
    let likes = formatNumbers(videoData.data.stats.like_count);
    playerStats += `<span>|</span><img src="/static/img/icon-thumb.svg" alt="thumbs-up"><span>${likes}</span>`;
  }
  if (videoData.data.stats.dislike_count && videoData.config.downloads.integrate_ryd) {
    let dislikes = formatNumbers(videoData.data.stats.dislike_count);
    playerStats += `<span>|</span><img class="dislike" src="/static/img/icon-thumb.svg" alt="thumbs-down"><span>${dislikes}</span>`;
  }
  playerStats += '</div>';

  const markup = `
    <div class="video-player" data-id="${videoId}">
        <div class="video-modal"><span class="video-modal-text"></span></div>
        ${videoTag}
        <div class="notifications" id="notifications"></div>
        ${sponsorBlockElements}
        <div class="player-title boxed-content">
            <img class="close-button" src="/static/img/icon-close.svg" alt="close-icon" data="${videoId}" onclick="removePlayer()" title="Close player">
            ${watchStatusIndicator}
            ${castButton}
            ${playerStats}
            <div class="player-channel-playlist">
                <h3><a href="/channel/${channelId}/">${channelName}</a></h3>
                ${playlist}
            </div>
            <a href="/video/${videoId}/"><h2 id="video-title">${videoName}</h2></a>
        </div>
    </div>
    `;
  const divPlayer = document.getElementById('player');
  divPlayer.innerHTML = markup;
  recordTextTrackChanges();
}

// Add video tag to video page when passed a video id, function loaded on page load `video.html (115-117)`
function insertVideoTag(videoData, videoProgress) {
  let videoTag = createVideoTag(videoData, videoProgress);
  let videoMain = document.querySelector('.video-main');
  videoMain.innerHTML += videoTag;
}

// Generates a video tag with subtitles when passed videoData and videoProgress.
function createVideoTag(videoData, videoProgress, autoplay = false) {
  let videoId = videoData.data.youtube_id;
  let videoUrl = videoData.data.media_url;
  let videoThumbUrl = videoData.data.vid_thumb_url;
  let subtitles = '';
  let videoSubtitles = videoData.data.subtitles; // Array of subtitles
  if (typeof videoSubtitles !== 'undefined' && videoData.config.downloads.subtitle) {
    for (let i = 0; i < videoSubtitles.length; i++) {
      let label = videoSubtitles[i].name;
      if (videoSubtitles[i].source === 'auto') {
        label += ' - auto';
      }
      subtitles += `<track label="${label}" kind="subtitles" srclang="${videoSubtitles[i].lang}" src="${videoSubtitles[i].media_url}">`;
    }
  }

  let videoTag = `
    <video poster="${videoThumbUrl}" onvolumechange="onVolumeChange(this)" onloadstart="this.volume=getPlayerVolume()" ontimeupdate="onVideoProgress()" onpause="onVideoPause()" onended="onVideoEnded()" ${
    autoplay ? 'autoplay' : ''
  } controls width="100%" playsinline id="video-item">
        <source src="${videoUrl}#t=${videoProgress}" type="video/mp4" id="video-source" videoid="${videoId}">
        ${subtitles}
    </video>
    `;
  return videoTag;
}

function onVolumeChange(videoTag) {
  localStorage.setItem('playerVolume', videoTag.volume);
}

function getPlayerVolume() {
  return localStorage.getItem('playerVolume') ?? 1;
}

// Gets video tag
function getVideoPlayer() {
  let videoElement = document.getElementById('video-item');
  return videoElement;
}

// Gets the video source tag
function getVideoPlayerVideoSource() {
  let videoPlayerVideoSource = document.getElementById('video-source');
  return videoPlayerVideoSource;
}

// Gets the current progress of the video currently in the player
function getVideoPlayerCurrentTime() {
  let videoElement = getVideoPlayer();
  if (videoElement != null) {
    return videoElement.currentTime;
  }
}

// Gets the video id of the video currently in the player
function getVideoPlayerVideoId() {
  let videoPlayerVideoSource = getVideoPlayerVideoSource();
  if (videoPlayerVideoSource != null) {
    return videoPlayerVideoSource.getAttribute('videoid');
  }
}

// Gets the duration of the video currently in the player
function getVideoPlayerDuration() {
  let videoElement = getVideoPlayer();
  if (videoElement != null) {
    return videoElement.duration;
  }
}

// Gets current watch status of video based on watch button
function getVideoPlayerWatchStatus() {
  let videoId = getVideoPlayerVideoId();
  let watched = false;

  let watchButtons = document.getElementsByClassName('watch-button');
  for (let i = 0; i < watchButtons.length; i++) {
    if (
      watchButtons[i].getAttribute('data-id') === videoId &&
      watchButtons[i].getAttribute('data-status') === 'watched'
    ) {
      watched = true;
    }
  }
  return watched;
}

// Runs on video playback, marks video as watched if video gets to 90% or higher, sends position to api, SB skipping
function onVideoProgress() {
  let videoId = getVideoPlayerVideoId();
  let currentTime = getVideoPlayerCurrentTime();
  let duration = getVideoPlayerDuration();
  let videoElement = getVideoPlayer();
  let notificationsElement = document.getElementById('notifications');
  if (sponsorBlock && sponsorBlock.segments) {
    for (let i in sponsorBlock.segments) {
      if (
        currentTime >= sponsorBlock.segments[i].segment[0] &&
        currentTime <= sponsorBlock.segments[i].segment[0] + 0.3
      ) {
        videoElement.currentTime = sponsorBlock.segments[i].segment[1];
        let notificationElement = document.getElementById(
          'notification-' + sponsorBlock.segments[i].UUID
        );
        if (!notificationElement) {
          notificationsElement.innerHTML += `<h3 id="notification-${
            sponsorBlock.segments[i].UUID
          }">Skipped sponsor segment from ${formatTime(
            sponsorBlock.segments[i].segment[0]
          )} to ${formatTime(sponsorBlock.segments[i].segment[1])}.</h3>`;
        }
      }
      if (currentTime > sponsorBlock.segments[i].segment[1] + 10) {
        let notificationsElementUUID = document.getElementById(
          'notification-' + sponsorBlock.segments[i].UUID
        );
        if (notificationsElementUUID) {
          notificationsElementUUID.outerHTML = '';
        }
      }
    }
  }
  if (currentTime < 10) return;
  if ((currentTime % 10).toFixed(1) <= 0.2) {
    // Check progress every 10 seconds or else progress is checked a few times a second
    postVideoProgress(videoId, currentTime);
    if (!getVideoPlayerWatchStatus()) {
      // Check if video is already marked as watched
      if (watchedThreshold(currentTime, duration)) {
        updateVideoWatchStatus(videoId, 'unwatched');
      }
    }
  }
}

// Runs on video end, marks video as watched
function onVideoEnded() {
  let videoId = getVideoPlayerVideoId();
  if (!getVideoPlayerWatchStatus()) {
    // Check if video is already marked as watched
    updateVideoWatchStatus(videoId, 'unwatched');
  }
  for (let i in sponsorBlock.segments) {
    let notificationsElementUUID = document.getElementById(
      'notification-' + sponsorBlock.segments[i].UUID
    );
    if (notificationsElementUUID) {
      notificationsElementUUID.outerHTML = '';
    }
  }
}

function watchedThreshold(currentTime, duration) {
  let watched = false;
  if (duration <= 1800) {
    // If video is less than 30 min
    if (currentTime / duration >= 0.9) {
      // Mark as watched at 90%
      watched = true;
    }
  } else {
    // If video is more than 30 min
    if (currentTime >= duration - 120) {
      // Mark as watched if there is two minutes left
      watched = true;
    }
  }
  return watched;
}

// Runs on video pause. Sends current position.
function onVideoPause() {
  let videoId = getVideoPlayerVideoId();
  let currentTime = getVideoPlayerCurrentTime();
  if (currentTime < 10) return;
  postVideoProgress(videoId, currentTime);
}

// Format numbers for frontend
function formatNumbers(number) {
  let numberUnformatted = parseFloat(number);
  let numberFormatted;
  if (numberUnformatted > 999999999) {
    numberFormatted = (numberUnformatted / 1000000000).toFixed(1).toString() + 'B';
  } else if (numberUnformatted > 999999) {
    numberFormatted = (numberUnformatted / 1000000).toFixed(1).toString() + 'M';
  } else if (numberUnformatted > 999) {
    numberFormatted = (numberUnformatted / 1000).toFixed(1).toString() + 'K';
  } else {
    numberFormatted = numberUnformatted;
  }
  return numberFormatted;
}

// Formats times in seconds for frontend
function formatTime(time) {
  let hoursUnformatted = time / 3600;
  let minutesUnformatted = (time % 3600) / 60;
  let secondsUnformatted = time % 60;

  let hoursFormatted = Math.trunc(hoursUnformatted);
  let minutesFormatted;
  if (minutesUnformatted < 10 && hoursFormatted > 0) {
    minutesFormatted = '0' + Math.trunc(minutesUnformatted);
  } else {
    minutesFormatted = Math.trunc(minutesUnformatted);
  }
  let secondsFormatted;
  if (secondsUnformatted < 10) {
    secondsFormatted = '0' + Math.trunc(secondsUnformatted);
  } else {
    secondsFormatted = Math.trunc(secondsUnformatted);
  }

  let timeUnformatted = '';
  if (hoursFormatted > 0) {
    timeUnformatted = hoursFormatted + ':';
  }
  let timeFormatted = timeUnformatted.concat(minutesFormatted, ':', secondsFormatted);
  return timeFormatted;
}

// Gets video data when passed video ID
function getVideoData(videoId) {
  let apiEndpoint = '/api/video/' + videoId + '/';
  let videoData = apiRequest(apiEndpoint, 'GET');
  return videoData;
}

// Gets channel data when passed channel ID
function getChannelData(channelId) {
  let apiEndpoint = '/api/channel/' + channelId + '/';
  let channelData = apiRequest(apiEndpoint, 'GET');
  return channelData.data;
}

// Gets playlist data when passed playlist ID
function getPlaylistData(playlistId) {
  let apiEndpoint = '/api/playlist/' + playlistId + '/';
  let playlistData = apiRequest(apiEndpoint, 'GET');
  return playlistData.data;
}

// Gets custom playlists
function getCustomPlaylists() {
  let apiEndpoint = '/api/playlist/?playlist_type=custom';
  let playlistData = apiRequest(apiEndpoint, 'GET');
  return playlistData.data;
}

// Get video progress data when passed video ID
function getVideoProgress(videoId) {
  let apiEndpoint = '/api/video/' + videoId + '/progress/';
  let videoProgress = apiRequest(apiEndpoint, 'GET');
  return videoProgress;
}

// Given an array of playlist ids it returns an array of subbed playlist ids from that list
function getSubbedPlaylists(videoPlaylists) {
  let subbedPlaylists = [];
  for (let i = 0; i < videoPlaylists.length; i++) {
    if (getPlaylistData(videoPlaylists[i]).playlist_subscribed) {
      subbedPlaylists.push(videoPlaylists[i]);
    }
  }
  return subbedPlaylists;
}

// Send video position when given video id and progress in seconds
function postVideoProgress(videoId, videoProgress) {
  let apiEndpoint = '/api/video/' + videoId + '/progress/';
  let duartion = getVideoPlayerDuration();
  if (!isNaN(videoProgress) && duartion !== 'undefined') {
    let data = {
      position: videoProgress,
    };
    if (videoProgress === 0) {
      apiRequest(apiEndpoint, 'DELETE');
      // console.log("Deleting Video Progress for Video ID: " + videoId + ", Progress: " + videoProgress);
    } else if (!getVideoPlayerWatchStatus()) {
      apiRequest(apiEndpoint, 'POST', data);
      // console.log("Saving Video Progress for Video ID: " + videoId + ", Progress: " + videoProgress);
    }
  }
}

// Send sponsor segment when given video id and and timestamps
function postSponsorSegment(videoId, startTime, endTime) {
  let apiEndpoint = '/api/video/' + videoId + '/sponsor/';
  let data = {
    segment: {
      startTime: startTime,
      endTime: endTime,
    },
  };
  apiRequest(apiEndpoint, 'POST', data);
}

// Send sponsor segment when given video id and and timestamps
function postSponsorSegmentVote(videoId, uuid, vote) {
  let apiEndpoint = '/api/video/' + videoId + '/sponsor/';
  let data = {
    vote: {
      uuid: uuid,
      yourVote: vote,
    },
  };
  apiRequest(apiEndpoint, 'POST', data);
}

function handleCookieValidate() {
  document.getElementById('cookieButton').remove();
  let cookieMessageElement = document.getElementById('cookieMessage');
  cookieMessageElement.innerHTML = `<span>Processing.</span>`;
  let response = postCookieValidate();
  if (response.cookie_validated === true) {
    cookieMessageElement.innerHTML = `<span>The cookie file is valid.</span>`;
  } else {
    cookieMessageElement.innerHTML = `<span class="danger-zone">Warning, the cookie file is invalid.</span>`;
  }
}

// Check youtube cookie settings
function postCookieValidate() {
  let apiEndpoint = '/api/cookie/';
  return apiRequest(apiEndpoint, 'POST');
}

// Makes api requests when passed an endpoint and method ("GET", "POST", "DELETE")
function apiRequest(apiEndpoint, method, data) {
  const xhttp = new XMLHttpRequest();
  let sessionToken = getCookie('sessionid');
  xhttp.open(method, apiEndpoint, false);
  xhttp.setRequestHeader('X-CSRFToken', getCookie('csrftoken')); // Used for video progress POST requests
  xhttp.setRequestHeader('Authorization', 'Token ' + sessionToken);
  xhttp.setRequestHeader('Content-Type', 'application/json');
  xhttp.send(JSON.stringify(data));
  if (xhttp.status === 404) {
    return false;
  } else {
    return JSON.parse(xhttp.responseText);
  }
}

// Gets origin URL
function getURL() {
  return window.location.origin;
}

function removePlayer() {
  let currentTime = getVideoPlayerCurrentTime();
  let duration = getVideoPlayerDuration();
  let videoId = getVideoPlayerVideoId();
  postVideoProgress(videoId, currentTime);
  setProgressBar(videoId, currentTime, duration);
  let playerElement = document.getElementById('player');
  if (playerElement.hasChildNodes()) {
    let youtubeId = playerElement.childNodes[1].getAttribute('data-id');
    let playedStatus = document.createDocumentFragment();
    let playedBox = document.getElementById(youtubeId);
    if (playedBox) {
      playedStatus.appendChild(playedBox);
    }
    playerElement.innerHTML = '';
    // append played status
    let videoInfo = document.getElementById('video-info-' + youtubeId);
    if (videoInfo) {
      videoInfo.insertBefore(playedStatus, videoInfo.firstChild);
    }
  }
}

// Sets the progress bar when passed a video id, video progress and video duration
function setProgressBar(videoId, currentTime, duration) {
  let progressBarWidth = (currentTime / duration) * 100 + '%';
  let progressBars = document.getElementsByClassName('video-progress-bar');
  for (let i = 0; i < progressBars.length; i++) {
    if (progressBars[i].id === 'progress-' + videoId) {
      if (!getVideoPlayerWatchStatus()) {
        progressBars[i].style.width = progressBarWidth;
      } else {
        progressBars[i].style.width = '0%';
      }
    }
  }

  // progressBar = document.getElementById("progress-" + videoId);
}

// multi search form
let searchTimeout = null;
let searchHttpRequest = null;
function searchMulti(query) {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(function () {
    if (query.length > 0) {
      if (searchHttpRequest) {
        searchHttpRequest.abort();
      }
      searchHttpRequest = new XMLHttpRequest();
      searchHttpRequest.onreadystatechange = function () {
        if (searchHttpRequest.readyState === 4) {
          const response = JSON.parse(searchHttpRequest.response);
          populateMultiSearchResults(response.results, response.queryType);
        }
      };
      searchHttpRequest.open('GET', `/api/search/?query=${query}`, true);
      searchHttpRequest.setRequestHeader('X-CSRFToken', getCookie('csrftoken'));
      searchHttpRequest.setRequestHeader('Content-type', 'application/json');
      searchHttpRequest.send();
    } else {
      if (searchHttpRequest) {
        searchHttpRequest.abort();
        searchHttpRequest = null;
      }
      // show the placeholder container and hide the results container
      document.getElementById('multi-search-results').style.display = 'none';
      document.getElementById('multi-search-results-placeholder').style.display = 'block';
    }
  }, 500);
}

function getViewDefaults(view) {
  let defaultView = document.getElementById('id_' + view).value;
  return defaultView;
}

function populateMultiSearchResults(allResults, queryType) {
  // show the results container and hide the placeholder container
  document.getElementById('multi-search-results').style.display = 'block';
  document.getElementById('multi-search-results-placeholder').style.display = 'none';
  // videos
  let defaultVideo = getViewDefaults('home');
  let allVideos = allResults.video_results;
  let videoBox = document.getElementById('video-results');
  videoBox.innerHTML = '';
  videoBox.parentElement.style.display = 'block';
  if (allVideos.length > 0) {
    for (let index = 0; index < allVideos.length; index++) {
      const video = allVideos[index];
      const videoDiv = createVideo(video, defaultVideo);
      videoBox.appendChild(videoDiv);
    }
  } else {
    if (queryType === 'simple' || queryType === 'video') {
      videoBox.innerHTML = '<p>No videos found.</p>';
    } else {
      videoBox.parentElement.style.display = 'none';
    }
  }
  // channels
  let defaultChannel = getViewDefaults('channel');
  let allChannels = allResults.channel_results;
  let channelBox = document.getElementById('channel-results');
  channelBox.innerHTML = '';
  channelBox.parentElement.style.display = 'block';
  if (allChannels.length > 0) {
    for (let index = 0; index < allChannels.length; index++) {
      const channel = allChannels[index];
      const channelDiv = createChannel(channel, defaultChannel);
      channelBox.appendChild(channelDiv);
    }
  } else {
    if (queryType === 'simple' || queryType === 'channel') {
      channelBox.innerHTML = '<p>No channels found.</p>';
    } else {
      channelBox.parentElement.style.display = 'none';
    }
  }
  // playlists
  let defaultPlaylist = getViewDefaults('playlist');
  let allPlaylists = allResults.playlist_results;
  let playlistBox = document.getElementById('playlist-results');
  playlistBox.innerHTML = '';
  playlistBox.parentElement.style.display = 'block';
  if (allPlaylists.length > 0) {
    for (let index = 0; index < allPlaylists.length; index++) {
      const playlist = allPlaylists[index];
      const playlistDiv = createPlaylist(playlist, defaultPlaylist);
      playlistBox.appendChild(playlistDiv);
    }
  } else {
    if (queryType === 'simple' || queryType === 'playlist') {
      playlistBox.innerHTML = '<p>No playlists found.</p>';
    } else {
      playlistBox.parentElement.style.display = 'none';
    }
  }
  // fulltext
  let allFullText = allResults.fulltext_results;
  let fullTextBox = document.getElementById('fulltext-results');
  fullTextBox.innerHTML = '';
  fullTextBox.parentElement.style.display = 'block';
  if (allFullText.length > 0) {
    for (let i = 0; i < allFullText.length; i++) {
      const fullText = allFullText[i];
      if ('subtitle_line' in fullText) {
        const fullTextDiv = createFulltext(fullText);
        fullTextBox.appendChild(fullTextDiv);
      }
    }
  } else {
    if (queryType === 'simple' || queryType === 'full') {
      fullTextBox.innerHTML = '<p>No fulltext items found.</p>';
    } else {
      fullTextBox.parentElement.style.display = 'none';
    }
  }
}

function createVideo(video, viewStyle) {
  // create video item div from template
  const videoId = video.youtube_id;
  // const mediaUrl = video.media_url;
  // const thumbUrl = '/cache/' + video.vid_thumb_url;
  const videoTitle = video.title;
  const videoPublished = video.published;
  const videoDuration = video.player.duration_str;
  let watchStatusIndicator;
  if (video.player.watched) {
    watchStatusIndicator = createWatchStatusIndicator(videoId, 'watched');
  } else {
    watchStatusIndicator = createWatchStatusIndicator(videoId, 'unwatched');
  }
  const channelId = video.channel.channel_id;
  const channelName = video.channel.channel_name;
  // build markup
  const markup = `
    <a href="#player" data-id="${videoId}" onclick="createPlayer(this)">
        <div class="video-thumb-wrap ${viewStyle}">
            <div class="video-thumb">
                <img src="${video.vid_thumb_url}" alt="video-thumb">
            </div>
            <div class="video-play">
                <img src="/static/img/icon-play.svg" alt="play-icon">
            </div>
        </div>
    </a>
    <div class="video-desc ${viewStyle}">
        <div class="video-desc-player" id="video-info-${videoId}">
                ${watchStatusIndicator}
            <span>${videoPublished} | ${videoDuration}</span>
        </div>
        <div>
            <a href="/channel/${channelId}/"><h3>${channelName}</h3></a>
            <a class="video-more" href="/video/${videoId}/"><h2>${videoTitle}</h2></a>
        </div>
    </div>
    `;
  const videoDiv = document.createElement('div');
  videoDiv.setAttribute('class', 'video-item ' + viewStyle);
  videoDiv.innerHTML = markup;
  return videoDiv;
}

function createChannel(channel, viewStyle) {
  // create channel item div from template
  const channelId = channel.channel_id;
  const channelName = channel.channel_name;
  const channelSubs = channel.channel_subs;
  const channelLastRefresh = channel.channel_last_refresh;
  let button;
  if (channel.channel_subscribed) {
    button = `<button class="unsubscribe" type="button" data-id="${channelId}" data-subscribe="" data-type="channel" onclick="subscribeStatus(this)" title="Unsubscribe from ${channelName}">Unsubscribe</button>`;
  } else {
    button = `<button type="button" data-id="${channelId}" data-subscribe="true" data-type="channel" onclick="subscribeStatus(this)" title="Subscribe to ${channelName}">Subscribe</button>`;
  }
  // build markup
  const markup = `
    <div class="channel-banner ${viewStyle}">
        <a href="/channel/${channelId}/">
            <img src="/cache/channels/${channelId}_banner.jpg" alt="${channelId}-banner">
        </a>
    </div>
    <div class="info-box info-box-2 ${viewStyle}">
        <div class="info-box-item">
            <div class="round-img">
                <a href="/channel/${channelId}/">
                    <img src="/cache/channels/${channelId}_thumb.jpg" alt="channel-thumb">
                </a>
            </div>
            <div>
                <h3><a href="/channel/${channelId}/">${channelName}</a></h3>
                <p>Subscribers: ${channelSubs}</p>
            </div>
        </div>
        <div class="info-box-item">
            <div>
                <p>Last refreshed: ${channelLastRefresh}</p>
                ${button}
            </div>
        </div>
    </div>
    `;
  const channelDiv = document.createElement('div');
  channelDiv.setAttribute('class', 'channel-item ' + viewStyle);
  channelDiv.innerHTML = markup;
  return channelDiv;
}

function createPlaylist(playlist, viewStyle) {
  // create playlist item div from template
  const playlistId = playlist.playlist_id;
  const playlistName = playlist.playlist_name;
  const playlistChannelId = playlist.playlist_channel_id;
  const playlistChannel = playlist.playlist_channel;
  const playlistLastRefresh = playlist.playlist_last_refresh;
  let button;
  if (playlist.playlist_subscribed) {
    button = `<button class="unsubscribe" type="button" data-id="${playlistId}" data-subscribe="" data-type="playlist" onclick="subscribeStatus(this)" title="Unsubscribe from ${playlistName}">Unsubscribe</button>`;
  } else {
    button = `<button type="button" data-id="${playlistId}" data-subscribe="true" data-type="playlist" onclick="subscribeStatus(this)" title="Subscribe to ${playlistName}">Subscribe</button>`;
  }
  const markup = `
    <div class="playlist-thumbnail">
        <a href="/playlist/${playlistId}/">
            <img src="/cache/playlists/${playlistId}.jpg" alt="${playlistId}-thumbnail">
        </a>
    </div>
    <div class="playlist-desc ${viewStyle}">
        <a href="/channel/${playlistChannelId}/"><h3>${playlistChannel}</h3></a>
        <a href="/playlist/${playlistId}/"><h2>${playlistName}</h2></a>
        <p>Last refreshed: ${playlistLastRefresh}</p>
        ${button}
    </div>
    `;
  const playlistDiv = document.createElement('div');
  playlistDiv.setAttribute('class', 'playlist-item ' + viewStyle);
  playlistDiv.innerHTML = markup;
  return playlistDiv;
}

function createFulltext(fullText) {
  const videoId = fullText.youtube_id;
  const subtitle_start = fullText.subtitle_start.split('.')[0];
  const subtitle_end = fullText.subtitle_end.split('.')[0];
  const markup = `
    <a href="#player" data-id="${videoId}" data-position="${subtitle_start}" onclick="createPlayer(this)">
        <div class="video-thumb-wrap list">
            <div class="video-thumb">
                <img src="${fullText.vid_thumb_url}" alt="video-thumb">
            </div>
            <div class="video-play">
                <img src="/static/img/icon-play.svg" alt="play-icon">
            </div>
        </div>
    </a>
    <div class="video-desc list">
        <div>
          <a href="/channel/${fullText.subtitle_channel_id}/"><h3>${fullText.subtitle_channel}</h3></a>
          <a class="video-more" href="/video/${videoId}/?t=${subtitle_start}"><h2>${fullText.title}</h2></a>
        </div>
        <p>${subtitle_start} - ${subtitle_end}</p>
        <p>${fullText.subtitle_line}</p>
        <span class="settings-current">Score: ${fullText._score}</span>
    </div>
    `;
  const fullTextDiv = document.createElement('div');
  fullTextDiv.setAttribute('class', 'video-item list');
  fullTextDiv.innerHTML = markup;
  return fullTextDiv;
}

function getComments(videoId) {
  let apiEndpoint = '/api/video/' + videoId + '/comment/';
  let response = apiRequest(apiEndpoint, 'GET');
  let allComments = response.data;

  writeComments(allComments);
}

function writeComments(allComments) {
  let commentsListBox = document.getElementById('comments-list');
  for (let i = 0; i < allComments.length; i++) {
    const rootComment = allComments[i];

    let commentBox = createCommentBox(rootComment, true);

    // add replies to commentBox
    if (rootComment.comment_replies) {
      let commentReplyBox = document.createElement('div');
      commentReplyBox.setAttribute('class', 'comments-replies');
      commentReplyBox.setAttribute('id', rootComment.comment_id + '-replies');
      let totalReplies = rootComment.comment_replies.length;
      if (totalReplies > 0) {
        let replyButton = createReplyButton(rootComment.comment_id + '-replies', totalReplies);
        commentBox.appendChild(replyButton);
      }
      for (let j = 0; j < totalReplies; j++) {
        const commentReply = rootComment.comment_replies[j];
        let commentReplyDiv = createCommentBox(commentReply, false);
        commentReplyBox.appendChild(commentReplyDiv);
      }
      if (totalReplies > 0) {
        commentBox.appendChild(commentReplyBox);
      }
    }
    commentsListBox.appendChild(commentBox);
  }
}

function createReplyButton(replyId, totalReplies) {
  let replyButton = document.createElement('button');
  replyButton.innerHTML = `<span id="toggle-icon">▼</span> ${totalReplies} replies`;
  replyButton.setAttribute('data-id', replyId);
  replyButton.setAttribute('onclick', 'toggleCommentReplies(this)');
  return replyButton;
}

function toggleCommentReplies(button) {
  let commentReplyId = button.getAttribute('data-id');
  let state = document.getElementById(commentReplyId).style.display;

  if (state === 'none' || state === '') {
    document.getElementById(commentReplyId).style.display = 'block';
    button.querySelector('#toggle-icon').innerHTML = '▲';
  } else {
    document.getElementById(commentReplyId).style.display = 'none';
    button.querySelector('#toggle-icon').innerHTML = '▼';
  }
}

function createCommentBox(comment, isRoot) {
  let commentBox = document.createElement('div');
  commentBox.setAttribute('class', 'comment-box');

  let commentClass;
  if (isRoot) {
    commentClass = 'root-comment';
  } else {
    commentClass = 'reply-comment';
  }

  commentBox.classList.add = commentClass;

  let commentAuthor = document.createElement('h3');
  commentAuthor.innerText = comment.comment_author;
  if (comment.comment_author_is_uploader) {
    commentAuthor.setAttribute('class', 'comment-highlight');
  }
  commentBox.appendChild(commentAuthor);

  let commentText = document.createElement('p');
  commentText.innerText = comment.comment_text;
  commentBox.appendChild(commentText);

  const spacer = '<span class="space-carrot">|</span>';
  let commentMeta = document.createElement('div');
  commentMeta.setAttribute('class', 'comment-meta');

  commentMeta.innerHTML = `<span>${comment.comment_time_text}</span>`;

  if (comment.comment_likecount > 0) {
    let numberFormatted = formatNumbers(comment.comment_likecount);
    commentMeta.innerHTML += `${spacer}<span class="thumb-icon"><img src="/static/img/icon-thumb.svg"> ${numberFormatted}</span>`;
  }

  if (comment.comment_is_favorited) {
    commentMeta.innerHTML += `${spacer}<span class="comment-like"><img src="/static/img/icon-heart.svg"></span>`;
  }

  commentBox.appendChild(commentMeta);

  return commentBox;
}

function getSimilarVideos(videoId) {
  let apiEndpoint = '/api/video/' + videoId + '/similar/';
  let response = apiRequest(apiEndpoint, 'GET');
  if (!response) {
    populateEmpty();
    return;
  }
  let allSimilar = response.data;
  if (allSimilar.length > 0) {
    populateSimilar(allSimilar);
  }
}

function populateSimilar(allSimilar) {
  let similarBox = document.getElementById('similar-videos');
  for (let i = 0; i < allSimilar.length; i++) {
    const similarRaw = allSimilar[i];
    let similarDiv = createVideo(similarRaw, 'grid');
    similarBox.appendChild(similarDiv);
  }
}

function populateEmpty() {
  let similarBox = document.getElementById('similar-videos');
  let emptyMessage = document.createElement('p');
  emptyMessage.innerText = 'No similar videos found.';
  similarBox.appendChild(emptyMessage);
}

// generic

function getCookie(c_name) {
  if (document.cookie.length > 0) {
    let c_start = document.cookie.indexOf(c_name + '=');
    if (c_start !== -1) {
      c_start = c_start + c_name.length + 1;
      let c_end = document.cookie.indexOf(';', c_start);
      if (c_end === -1) c_end = document.cookie.length;
      return unescape(document.cookie.substring(c_start, c_end));
    }
  }
  return '';
}

// animations

function textReveal(button) {
  let revealBox = button.parentElement.parentElement;
  let textBox = revealBox.querySelector('#text-reveal');
  let textBoxHeight = textBox.style.height;
  if (textBoxHeight === 'unset') {
    textBox.style.height = '0px';
    button.innerText = 'Show';
  } else {
    textBox.style.height = 'unset';
    button.innerText = 'Hide';
  }
}

function textExpand() {
  let textBox = document.getElementById('text-expand');
  let button = document.getElementById('text-expand-button');
  let style = window.getComputedStyle(textBox);
  if (style.webkitLineClamp === 'none') {
    textBox.style['-webkit-line-clamp'] = '4';
    button.innerText = 'Show more';
  } else {
    textBox.style['-webkit-line-clamp'] = 'unset';
    button.innerText = 'Show less';
  }
}

// hide "show more" button if all text is already visible
function textExpandButtonVisibilityUpdate() {
  let textBox = document.getElementById('text-expand');
  let button = document.getElementById('text-expand-button');
  if (!textBox || !button) return;

  let styles = window.getComputedStyle(textBox);
  let textBoxLineClamp = styles.webkitLineClamp;
  if (textBoxLineClamp === 'unset') return; // text box is in revealed state

  if (textBox.offsetHeight < textBox.scrollHeight || textBox.offsetWidth < textBox.scrollWidth) {
    // the element has an overflow, show read more button
    button.style.display = 'inline-block';
  } else {
    // the element doesn't have overflow
    button.style.display = 'none';
  }
}

document.addEventListener('readystatechange', textExpandButtonVisibilityUpdate);
window.addEventListener('resize', textExpandButtonVisibilityUpdate);

function showForm(id) {
  let id2 = id === undefined ? 'hidden-form' : id;
  let formElement = document.getElementById(id2);
  let displayStyle = formElement.style.display;
  if (displayStyle === '') {
    formElement.style.display = 'block';
  } else {
    formElement.style.display = '';
  }
  animate('animate-icon', 'pulse-img');
}

function channelFilterDownload(value) {
  if (value === 'all') {
    window.location = '/downloads/';
  } else {
    window.location.search = '?channel=' + value;
  }
}

function showOverwrite() {
  let overwriteDiv = document.getElementById('overwrite-form');
  if (overwriteDiv.classList.contains('hidden-overwrite')) {
    overwriteDiv.classList.remove('hidden-overwrite');
  } else {
    overwriteDiv.classList.add('hidden-overwrite');
  }
}

function animate(elementId, animationClass) {
  let toAnimate = document.getElementById(elementId);
  if (toAnimate.className !== animationClass) {
    toAnimate.className = animationClass;
  } else {
    toAnimate.classList.remove(animationClass);
  }
}

// keep track of changes to the subtitles list made with the native UI
// needed so that when toggling subtitles with the shortcut we go to the last selected one, not the first one
addEventListener('DOMContentLoaded', recordTextTrackChanges);

let lastSeenTextTrack = 0;
function recordTextTrackChanges() {
  let player = getVideoPlayer();
  if (player == null) {
    return;
  }
  player.textTracks.addEventListener('change', () => {
    let active = [...player.textTracks].findIndex(x => x.mode === 'showing');
    if (active !== -1) {
      lastSeenTextTrack = active;
    }
  });
}

// keyboard shortcuts for the video player
// need useCapture so we can prevent events from reaching the player
document.addEventListener('keydown', doShortcut, true);

let modalHideTimeout = -1;
function showModal(html, duration) {
  let modal = document.querySelector('.video-modal-text');
  modal.innerHTML = html;
  modal.style.display = 'initial';
  clearTimeout(modalHideTimeout);
  modalHideTimeout = setTimeout(() => {
    modal.style.display = 'none';
  }, duration);
}

let videoSpeeds = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5, 2.75, 3];
function doShortcut(e) {
  if (!(e.target instanceof HTMLElement)) {
    return;
  }
  let target = e.target;
  let targetName = target.nodeName.toLowerCase();
  if (
    targetName === 'textarea' ||
    targetName === 'input' ||
    targetName === 'select' ||
    target.isContentEditable
  ) {
    return;
  }
  if (e.altKey || e.ctrlKey || e.metaKey) {
    return;
  }
  let player = getVideoPlayer();
  if (player == null) {
    // not on the video page
    return;
  }
  switch (e.key) {
    case 'c': {
      // toggle captions
      let tracks = [...player.textTracks];
      if (tracks.length === 0) {
        break;
      }
      let active = tracks.find(x => x.mode === 'showing');
      if (active != null) {
        active.mode = 'disabled';
      } else {
        tracks[lastSeenTextTrack].mode = 'showing';
      }
      break;
    }
    case 'm': {
      player.muted = !player.muted;
      break;
    }
    case 'f': {
      e.preventDefault();
      if (document.fullscreenElement === null) {
        player.requestFullscreen().catch(e => {
          console.error(e);
          showModal('Unable to enter fullscreen', 3000);
        });
      } else {
        document.exitFullscreen().catch(e => {
          console.error(e);
          showModal('Unable to exit fullscreen', 3000);
        });
      }
      break;
    }
    case 'ArrowLeft': {
      e.preventDefault();
      showModal('- 5 seconds', 500);
      player.currentTime -= 5;
      break;
    }
    case 'ArrowRight': {
      e.preventDefault();
      showModal('+ 5 seconds', 500);
      player.currentTime += 5;
      break;
    }
    case '<':
    case '>': {
      // change speed
      let currentSpeedIdx = videoSpeeds.findIndex(s => s >= player.playbackRate);
      if (currentSpeedIdx === -1) {
        // handle the case where the user manually set the speed above our max speed
        currentSpeedIdx = videoSpeeds.length - 1;
      }
      let newSpeedIdx =
        e.key === '<'
          ? Math.max(0, currentSpeedIdx - 1)
          : Math.min(videoSpeeds.length - 1, currentSpeedIdx + 1);
      let newSpeed = videoSpeeds[newSpeedIdx];
      player.playbackRate = newSpeed;
      showModal(newSpeed + 'x', 500);
      break;
    }
    case ' ': {
      e.preventDefault();
      if (player.paused) {
        player.play();
      } else {
        player.pause();
      }
      break;
    }
    case '?': {
      showModal(
        `
                <table style="margin: auto; background: rgba(0,0,0,.5)"><tbody>
                <tr><td>Show help</td><td>?</td>
                <tr><td>Toggle mute</td><td>m</td>
                <tr><td>Toggle fullscreen</td><td>f</td>
                <tr><td>Toggle subtitles (if available)</td><td>c</td>
                <tr><td>Increase speed</td><td>&gt;</td>
                <tr><td>Decrease speed</td><td>&lt;</td>
                <tr><td>Back 5 seconds</td><td>←</td>
                <tr><td>Forward 5 seconds</td><td>→</td>
            `,
        3000
      );
      break;
    }
  }
}
