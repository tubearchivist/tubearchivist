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
    return value.status.startsWith(dataOrigin);
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
    <p>${messageData.messages.join('<br>')}</p>
    <div class="notification-progress-bar" style="width: ${progress}%";></div>`;
    notificationDiv.appendChild(messageBox);
    if (messageData.status.startsWith('download:')) {
      animateIcons(messageData.status);
    }
  }
  if (nots > 0 && messages.length === 0) {
    location.reload();
  }

  return messages;
}

function animateIcons(status) {
  let rescanIcon = document.getElementById('rescan-icon');
  let dlIcon = document.getElementById('download-icon');
  switch (status) {
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
