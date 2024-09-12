/**
 * Handle multi channel notifications
 *
 */

'use strict';

/* globals apiRequest animate */

checkMessages();

// start to look for messages
function checkMessages() {
  let notifications = document.getElementById('notifications');
  if (notifications && notifications.childNodes.length === 0) {
    let dataOrigin = notifications.getAttribute('data');
    getMessages(dataOrigin);
  }
}

function getMessages(dataOrigin) {
  let apiEndpoint = '/api/notification/';
  let responseData = apiRequest(apiEndpoint, 'GET');
  let messages = buildMessage(responseData, dataOrigin);
  if (messages.length > 0) {
    // restart itself
    setTimeout(() => getMessages(dataOrigin), 500);
  }
}

function buildMessage(responseData, dataOrigin) {
  // filter relevant messages
  let messages;
  if (dataOrigin) {
    messages = responseData.filter(function (value) {
      return dataOrigin.split(' ').includes(value.group.split(':')[0]);
    }, dataOrigin);
  } else {
    messages = responseData;
  }

  let notifications = document.getElementById('notifications');
  let currentNotifications = notifications.childElementCount;

  for (let i = 0; i < messages.length; i++) {
    const messageData = messages[i];
    if (!document.getElementById(messageData.id)) {
      let messageBox = buildPlainBox(messageData);
      notifications.appendChild(messageBox);
    }
    updateMessageBox(messageData);
    if (messageData.group.startsWith('download:')) {
      animateIcons(messageData.group);
    }
  }
  clearNotifications(responseData);
  if (currentNotifications > 0 && messages.length === 0) {
    location.replace(location.href);
  }
  return messages;
}

function buildPlainBox(messageData) {
  let messageBox = document.createElement('div');
  messageBox.classList.add(messageData.level, 'notification');
  messageBox.id = messageData.id;
  messageBox.innerHTML = `
  <h3></h3>
  <p></p>
  <div class="task-control-icons"></div>
  <div class="notification-progress-bar"></div>`;
  return messageBox;
}

function updateMessageBox(messageData) {
  let messageBox = document.getElementById(messageData.id);
  let children = messageBox.children;
  children[0].textContent = messageData.title;
  children[1].innerHTML = messageData.messages.join('<br>');
  if (
    !messageBox.querySelector('#stop-icon') &&
    messageData['api_stop'] &&
    messageData.command !== 'STOP'
  ) {
    children[2].appendChild(buildStopIcon(messageData.id));
  }
  if (messageData.progress) {
    children[3].style.width = `${messageData.progress * 100 || 0}%`;
  }
}

function animateIcons(group) {
  let rescanIcon = document.getElementById('rescan-icon');
  let dlIcon = document.getElementById('download-icon');
  switch (group) {
    case 'download:scan':
      if (rescanIcon && !rescanIcon.classList.contains('rotate-img')) {
        animate('rescan-icon', 'rotate-img');
      }
      break;

    case 'download:run':
      if (dlIcon && !dlIcon.classList.contains('bounce-img')) {
        animate('download-icon', 'bounce-img');
      }
      break;

    default:
      break;
  }
}

function buildStopIcon(taskId) {
  let stopIcon = document.createElement('img');
  stopIcon.setAttribute('id', 'stop-icon');
  stopIcon.setAttribute('data', taskId);
  stopIcon.setAttribute('title', 'Stop Task');
  stopIcon.setAttribute('src', '/static/img/icon-stop.svg');
  stopIcon.setAttribute('alt', 'stop icon');
  stopIcon.setAttribute('onclick', 'stopTask(this)');
  return stopIcon;
}

function buildKillIcon(taskId) {
  let killIcon = document.createElement('img');
  killIcon.setAttribute('id', 'kill-icon');
  killIcon.setAttribute('data', taskId);
  killIcon.setAttribute('title', 'Kill Task');
  killIcon.setAttribute('src', '/static/img/icon-close.svg');
  killIcon.setAttribute('alt', 'kill icon');
  killIcon.setAttribute('onclick', 'killTask(this)');
  return killIcon;
}

function clearNotifications(responseData) {
  let allIds = Array.from(responseData, x => x.id);
  let allBoxes = document.getElementsByClassName('notification');
  for (let i = 0; i < allBoxes.length; i++) {
    const notificationBox = allBoxes[i];
    if (!allIds.includes(notificationBox.id)) {
      notificationBox.remove();
    }
  }
}
