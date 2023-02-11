/**
 * Handle multi channel notifications
 *
 */

'use strict';

checkMessages();

// page map to notification status
const messageTypes = {
  download: ['message:download', 'message:add', 'message:rescan', 'message:playlistscan'],
  channel: ['message:subchannel'],
  channel_id: ['message:playlistscan'],
  playlist: ['message:subplaylist'],
  setting: ['message:setting'],
};

// start to look for messages
function checkMessages() {
  let notifications = document.getElementById('notifications');
  if (notifications) {
    let dataOrigin = notifications.getAttribute('data');
    getMessages(dataOrigin);
  }
}

// get messages for page on timer
function getMessages(dataOrigin) {
  fetch('/progress/')
    .then(response => response.json())
    .then(responseData => {
      const messages = buildMessage(responseData, dataOrigin);
      if (messages.length > 0) {
        // restart itself
        setTimeout(() => getMessages(dataOrigin), 500);
      }
    });
}

// make div for all messages, return relevant
function buildMessage(responseData, dataOrigin) {
  // filter relevan messages
  let allMessages = responseData['messages'];
  let messages = allMessages.filter(function (value) {
    return messageTypes[dataOrigin].includes(value['status']);
  }, dataOrigin);
  // build divs
  let notificationDiv = document.getElementById('notifications');
  let nots = notificationDiv.childElementCount;
  notificationDiv.innerHTML = '';
  for (let i = 0; i < messages.length; i++) {
    let messageData = messages[i];
    let messageStatus = messageData['status'];
    let messageBox = document.createElement('div');
    let title = document.createElement('h3');
    title.innerHTML = messageData['title'];
    let message = document.createElement('p');
    message.innerHTML = messageData['message'];
    messageBox.appendChild(title);
    messageBox.appendChild(message);
    messageBox.classList.add(messageData['level'], 'notification');
    notificationDiv.appendChild(messageBox);
    if (messageStatus === 'message:download') {
      checkDownloadIcons();
    }
  }
  // reload page when no more notifications
  if (nots > 0 && messages.length === 0) {
    location.reload();
  }
  return messages;
}

// check if download icons are needed
function checkDownloadIcons() {
  let iconBox = document.getElementById('downloadControl');
  if (iconBox.childElementCount === 0) {
    let downloadIcons = buildDownloadIcons();
    iconBox.appendChild(downloadIcons);
  }
}

// add dl control icons
function buildDownloadIcons() {
  let downloadIcons = document.createElement('div');
  downloadIcons.classList = 'dl-control-icons';
  // stop icon
  let stopIcon = document.createElement('img');
  stopIcon.setAttribute('id', 'stop-icon');
  stopIcon.setAttribute('title', 'Stop Download Queue');
  stopIcon.setAttribute('src', '/static/img/icon-stop.svg');
  stopIcon.setAttribute('alt', 'stop icon');
  stopIcon.setAttribute('onclick', 'stopQueue()');
  // kill icon
  let killIcon = document.createElement('img');
  killIcon.setAttribute('id', 'kill-icon');
  killIcon.setAttribute('title', 'Kill Download Queue');
  killIcon.setAttribute('src', '/static/img/icon-close.svg');
  killIcon.setAttribute('alt', 'kill icon');
  killIcon.setAttribute('onclick', 'killQueue()');
  // stich together
  downloadIcons.appendChild(stopIcon);
  downloadIcons.appendChild(killIcon);
  return downloadIcons;
}
