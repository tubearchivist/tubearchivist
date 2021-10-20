
function sortChange(sortValue) {
    var payload = JSON.stringify({'sort_order': sortValue});
    sendPost(payload);
    setTimeout(function(){
        location.reload();
        return false;
    }, 500);
}

function isWatched(youtube_id) {
    var payload = JSON.stringify({'watched': youtube_id});
    sendPost(payload);
    var seenIcon = document.createElement('img');
    seenIcon.setAttribute('src', "/static/img/icon-seen.svg");
    seenIcon.setAttribute('alt', 'seen-icon');
    seenIcon.setAttribute('id', youtube_id);
    seenIcon.setAttribute('title', "Mark as unwatched");
    seenIcon.setAttribute('onclick', "isUnwatched(this.id)");
    seenIcon.classList = 'seen-icon';
    document.getElementById(youtube_id).replaceWith(seenIcon);
}

function isUnwatched(youtube_id) {
    var payload = JSON.stringify({'un_watched': youtube_id});
    sendPost(payload);
    var unseenIcon = document.createElement('img');
    unseenIcon.setAttribute('src', "/static/img/icon-unseen.svg");
    unseenIcon.setAttribute('alt', 'unseen-icon');
    unseenIcon.setAttribute('id', youtube_id);
    unseenIcon.setAttribute('title', "Mark as watched");
    unseenIcon.setAttribute('onclick', "isWatched(this.id)");
    unseenIcon.classList = 'unseen-icon';
    document.getElementById(youtube_id).replaceWith(unseenIcon);
}

function unsubscribe(channel_id) {
    var payload = JSON.stringify({'unsubscribe': channel_id});
    sendPost(payload);
    document.getElementById(channel_id).remove();
}

function changeView(image) {
    var sourcePage = image.getAttribute("data-origin");
    var newView = image.getAttribute("data-value");
    var payload = JSON.stringify({'change_view': sourcePage + ":" + newView});
    sendPost(payload);
    setTimeout(function(){
        location.reload();
        return false;
    }, 500);
}

function toggleCheckbox(checkbox) {
    // pass checkbox id as key and checkbox.checked as value
    var toggleId = checkbox.id;
    var toggleVal = checkbox.checked;
    var payloadDict = {};
    payloadDict[toggleId] = toggleVal;
    var payload = JSON.stringify(payloadDict);
    sendPost(payload);
    setTimeout(function(){
        var currPage = window.location.pathname;
        window.location.replace(currPage);
        return false;
    }, 500);
}

// download page buttons
function rescanPending() {
    var payload = JSON.stringify({'rescan_pending': true});
    animate('rescan-icon', 'rotate-img');
    sendPost(payload);
    setTimeout(function(){
        handleInterval();
    }, 500);
}

function dlPending() {
    var payload = JSON.stringify({'dl_pending': true});
    animate('download-icon', 'bounce-img');
    sendPost(payload);
    setTimeout(function(){
        handleInterval();
    }, 500);
}

function toIgnore(button) {
    var youtube_id = button.getAttribute('data-id');
    var payload = JSON.stringify({'ignore': youtube_id});
    sendPost(payload);
    document.getElementById('dl-' + youtube_id).remove();
}

function downloadNow(button) {
    var youtube_id = button.getAttribute('data-id');
    var payload = JSON.stringify({'dlnow': youtube_id});
    sendPost(payload);
    document.getElementById(youtube_id).remove();
    setTimeout(function(){
        handleInterval();
    }, 500);
}

function forgetIgnore(button) {
    var youtube_id = button.getAttribute('data-id');
    var payload = JSON.stringify({'forgetIgnore': youtube_id});
    sendPost(payload);
    document.getElementById("dl-" + youtube_id).remove();
}

function addSingle(button) {
    var youtube_id = button.getAttribute('data-id');
    var payload = JSON.stringify({'addSingle': youtube_id});
    sendPost(payload);
    document.getElementById("dl-" + youtube_id).remove();
    setTimeout(function(){
        handleInterval();
    }, 500);
}

function stopQueue() {
    var payload = JSON.stringify({'queue': 'stop'});
    sendPost(payload);
    document.getElementById('stop-icon').remove();
}

function killQueue() {
    var payload = JSON.stringify({'queue': 'kill'});
    sendPost(payload);
    document.getElementById('kill-icon').remove();
}

// settings page buttons
function manualImport() {
    var payload = JSON.stringify({'manual-import': true});
    sendPost(payload);
    // clear button
    var message = document.createElement('p');
    message.innerText = 'processing import';
    var toReplace = document.getElementById('manual-import');
    toReplace.innerHTML = '';
    toReplace.appendChild(message);
}

function dbBackup() {
    var payload = JSON.stringify({'db-backup': true});
    sendPost(payload)
    // clear button
    var message = document.createElement('p');
    message.innerText = 'backing up archive';
    var toReplace = document.getElementById('db-backup');
    toReplace.innerHTML = '';
    toReplace.appendChild(message);
}

function dbRestore() {
    var payload = JSON.stringify({'db-restore': true});
    sendPost(payload);
    // clear button
    var message = document.createElement('p');
    message.innerText = 'restoring from backup';
    var toReplace = document.getElementById('db-restore');
    toReplace.innerHTML = '';
    toReplace.appendChild(message);
}

function fsRescan() {
    var payload = JSON.stringify({'fs-rescan': true});
    sendPost(payload);
    // clear button
    var message = document.createElement('p');
    message.innerText = 'File system scan in progress';
    var toReplace = document.getElementById('fs-rescan');
    toReplace.innerHTML = '';
    toReplace.appendChild(message);
}

// delete from file system
function deleteConfirm() {
    to_show = document.getElementById("delete-button");
    document.getElementById("delete-item").style.display = 'none';
    to_show.style.display = "block";
}

function deleteVideo(button) {
    var to_delete = button.getAttribute("data-id");
    var to_redirect = button.getAttribute("data-redirect");
    var payload = JSON.stringify({"delete-video": to_delete});
    sendPost(payload);
    setTimeout(function(){
        var redirect = "/channel/" + to_redirect;
        window.location.replace(redirect);
        return false;
    }, 1000);
}

function deleteChannel(button) {
    var to_delete = button.getAttribute("data-id");
    var payload = JSON.stringify({"delete-channel": to_delete});
    sendPost(payload);
    setTimeout(function(){
        window.location.replace("/channel/");
        return false;
    }, 1000);
}

function cancelDelete() {
    document.getElementById("delete-button").style.display = 'none';
    document.getElementById("delete-item").style.display = 'block';
}

// player
function createPlayer(button) {
    var mediaUrl = button.getAttribute('data-src');
    var mediaThumb = button.getAttribute('data-thumb');
    var mediaTitle = button.getAttribute('data-title');
    var mediaChannel = button.getAttribute('data-channel');
    var dataId = button.getAttribute('data-id');
    // get watched status
    var playedStatus = document.createDocumentFragment();
    playedStatus.appendChild(document.getElementById(dataId));
    // create player
    removePlayer();
    var playerElement = document.getElementById('player');
    playerElement.setAttribute('data-id', dataId);
    // playerElement.innerHTML = '';
    var videoPlayer = document.createElement('video');
    videoPlayer.setAttribute('src', mediaUrl);
    videoPlayer.setAttribute('controls', true);
    videoPlayer.setAttribute('autoplay', true);
    videoPlayer.setAttribute('width', '100%');
    videoPlayer.setAttribute('playsinline', true);
    videoPlayer.setAttribute('poster', mediaThumb);
    playerElement.appendChild(videoPlayer);
    // title bar
    var titleBar = document.createElement('div');
    titleBar.className = 'player-title';
    // close
    var closeButton = document.createElement('img');
    closeButton.className = 'close-button';
    closeButton.setAttribute('src', "/static/img/icon-close.svg");
    closeButton.setAttribute('alt', 'close-icon');
    closeButton.setAttribute('data', dataId);
    closeButton.setAttribute('onclick', "removePlayer()");
    closeButton.setAttribute('title', 'Close player');
    titleBar.appendChild(closeButton);
    // played
    titleBar.appendChild(playedStatus);
    playerElement.appendChild(titleBar);
    // title
    var videoTitle = document.createElement('p');
    videoTitle.innerText = mediaTitle;
    titleBar.appendChild(videoTitle);
    var videoChannel = document.createElement('p');
    videoChannel.innerText = mediaChannel
    titleBar.appendChild(videoChannel);
    // button
    var videoButton = document.createElement('button');
    videoButton.innerText = 'Details';
    videoButton.setAttribute('onclick', "window.location.href='/video/" + dataId + "/';");
    titleBar.appendChild(videoButton);
}

function removePlayer() {
    var playerElement = document.getElementById('player');
    if (playerElement.hasChildNodes()) {
        var youtubeId = playerElement.getAttribute('data-id');
        var playedStatus = document.createDocumentFragment();
        playedStatus.appendChild(document.getElementById(youtubeId));
        playerElement.innerHTML = '';
        // append played status
        var videoInfo = document.getElementById('video-info-' + youtubeId);
        videoInfo.insertBefore(playedStatus, videoInfo.firstChild);
    };
}

// searching channels
function searchChannels(query) {
    var searchResultBox = document.getElementById('resultBox');
    searchResultBox.innerHTML = '';
    if (query.length > 1) {
        var payload = JSON.stringify({'channel-search': query})
        sendSearchAsYouType(payload);
    };
}


function populateChannelResults(allResults) {
    var searchResultBox = document.getElementById('resultBox');
    for (let i = 0; i < allResults.length; i++) {
        var singleResult = allResults[i];
        var source = singleResult['source'];
        var channelName = source['channel_name'];
        var channelId = source['channel_id'];
        var optionElement = document.createElement('option');
        optionElement.value = channelName;
        optionElement.setAttribute('data', channelId);
        searchResultBox.appendChild(optionElement);
    };
}

function channelRedirect(){
    var response = document.getElementById('resultBox');
    var firstChild = response.firstChild
    if (firstChild) {
        var redirectId = firstChild.getAttribute('data');
        location = '/channel/' + redirectId;
    };
    return false;
}


function sendSearchAsYouType(payload) {
    var http = new XMLHttpRequest();
    http.onreadystatechange = function() {
        if (http.readyState === 4) {
            allResults = JSON.parse(http.response)['results'];
            populateChannelResults(allResults);
        };
    };
    http.open("POST", "/process/", true);
    http.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
    http.setRequestHeader("Content-type", "application/json");
    http.send(payload);
}


// generic
function sendPost(payload) {
    var http = new XMLHttpRequest();
    http.open("POST", "/process/", true);
    http.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
    http.setRequestHeader("Content-type", "application/json");
    http.send(payload);
}


function getCookie(c_name) {
    if (document.cookie.length > 0) {
        c_start = document.cookie.indexOf(c_name + "=");
        if (c_start != -1) {
            c_start = c_start + c_name.length + 1;
            c_end = document.cookie.indexOf(";", c_start);
            if (c_end == -1) c_end = document.cookie.length;
            return unescape(document.cookie.substring(c_start,c_end));
        };
    };
    return "";
}


// animations
function textReveal() {
    var textBox = document.getElementById('text-reveal');
    var button = document.getElementById('text-reveal-button');
    var textBoxHeight = textBox.style.height;
    if (textBoxHeight === 'unset') {
        textBox.style.height = '0px';
        button.innerText = 'Show';
    } else {
        textBox.style.height = 'unset';
        button.innerText = 'Hide';
    };
}

function showSearch() {
    var searchBox = document.getElementById('search-box');
    var displayStyle = searchBox.style.display
    if (displayStyle === "") {
        searchBox.style.display = 'block';
    } else {
        searchBox.style.display = "";
    }
    var inputBox = document.getElementById('searchInput');
    inputBox.focus();
}

function showForm() {
    var formElement = document.getElementById('hidden-form');
    var displayStyle = formElement.style.display
    if (displayStyle === "") {
        formElement.style.display = 'block';
        animate('add-icon', 'pulse-img');
    } else {
        formElement.style.display = "";
    }
}

function animate(elementId, animationClass) {
    var toAnimate = document.getElementById(elementId);
    if (toAnimate.className !== animationClass) {
        toAnimate.className = animationClass;
    }
}
