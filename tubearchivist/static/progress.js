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
  if (notifications) {
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
  let messages = responseData.filter(function (value) {
    return value.group.startsWith(dataOrigin);
  }, dataOrigin);
  let notificationDiv = document.getElementById('notifications');
  let nots = notificationDiv.childElementCount;
  notificationDiv.innerHTML = '';

  for (let i = 0; i < messages.length; i++) {
    const messageData = messages[i];
    let messageBox = document.createElement('div');
    let progress = messageData?.progress * 100 || 0;
    messageBox.classList.add(messageData['level'], 'notification');
    messageBox.innerHTML = `
    <h3>${messageData.title}</h3>
    <p>${messageData.messages.join('<br>')}</p>`
    let taskControlIcons = document.createElement('div');
    taskControlIcons.classList = 'task-control-icons';
    if ('api-stop' in messageData) {
      taskControlIcons.appendChild(buildStopIcon(messageData.id));
    }
    if ('api-kill' in messageData) {
      taskControlIcons.appendChild(buildKillIcon(messageData.id));
    }
    if (taskControlIcons.hasChildNodes()) {
      messageBox.appendChild(taskControlIcons);
    }
    messageBox.innerHTML = `${messageBox.innerHTML}<div class="notification-progress-bar" style="width: ${progress}%";></div>`;
    notificationDiv.appendChild(messageBox);
    if (messageData.group.startsWith('download:')) {
      animateIcons(messageData.group);
    }
  }
  if (nots > 0 && messages.length === 0) {
    location.reload();
  }

  return messages;
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
  return stopIcon
}

function buildKillIcon(taskId) {
  let killIcon = document.createElement('img');
  killIcon.setAttribute('id', 'kill-icon');
  stopIcon.setAttribute('data', taskId);
  killIcon.setAttribute('title', 'Kill Task');
  killIcon.setAttribute('src', '/static/img/icon-close.svg');
  killIcon.setAttribute('alt', 'kill icon');
  killIcon.setAttribute('onclick', 'killTask(this)');
  return killIcon
}
