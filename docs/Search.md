# Search Page
Accessible at `/search/` of your **Tube Archivist**, search your archive for Videos, Channels and Playlists - or even full text search throughout your indexed subtitles.

Just start typing to start a **simple** search *or* **start your query with a primary keyword** to search for a specific type and narrow down the result with secondary keywords. Secondary keywords can be in any order. Use *yes* or *no* for boolean values.

- This will return 30 results per query, pagination is not implemented yet.
- All your queries are case insensitive and are normalized to lowercase.
- All your queries are analyzed for the english language, this means *singular*, *plural* and word variations like *-ing*, *-ed*, *-able* etc are treated as synonyms.
- Keyword value parsing begins with the `keyword:` name all the way until the end of query or the next keyword, e.g. in `video:learn python channel:corey`, the keyword `video` has value `learn python`.
- Fuzzy search is activated for all your searches by default. This can catch typos in your queries or in the matching documents with one to two letters difference, depending on the query length. You can configure fuzziness with the secondary keyword `fuzzy:`, e.g:
  - `fuzzy:0` or `fuzzy:no`: Deactivate fuzzy matching.
  - `fuzzy:1`: Set fuzziness to one letter difference.
  - `fuzzy:2`: Set fuzziness to two letters difference.
- All text searches are ranked, meaning the better a match the higher ranked the result. Unless otherwise stated, queries with multiple words are processed with the `and` operator, meaning all words need to match so each word will narrow down the result.

## Simple
Start your query without a keyword to make a simple query (primary keyword `simple:` is implied). This will search in *video titles*, *channel names* and *playlist titles* and will return matching videos, channels and playlists. Keyword searches will return more results in a particular category due to the fact that more fields are searched for matches. Simple queries do not have any secondary keywords.

## Video
Start your query with the **primary keyword** `video:` to search for videos only. This will search through the *video titles*, *tags* and *category* fields. Narrow your search down with secondary keywords:
- `channel:` search for videos matching the channel name.
- `active:` is a boolean value, to search for videos that are still active on youtube or that are not active any more.

**Example**:
- `video:learn python channel:corey schafer active:yes`: This will return all videos with the term *Learn Python* from the channel *Corey Schafer* that are still *Active* on YouTube.
- `video: channel:tom scott active:no`: Note the omitted term after the primary key, this will show all videos from the channel *Tom Scott* that are no longer active on YouTube.

## Channel
Start with the `channel:` **primary keyword** to search for channels matching your query. This will search through the *channel name* and *channel description* fields. Narrow your search down with secondary keywords:
- `subscribed:` is a boolean value, search for channels that you are subscribed to or not.
- `active:` is a boolean value, to search for channels that are still active on YouTube or that are no longer active.

**Example**:
- `channel:linux subscribed:yes`: Search for channels with the term *Linux* that you are subscribed to.
- `channel: active:no`: Note the omitted term after the primary key, this will return all channels that are no longer active on YouTube.

## Playlist
Start your query with the **primary keyword** `playlist:` to search for playlists only. This will search through the *playlist title* and *playlist description* fields. Narrow down your search with these secondary keywords:
- `subscribed`: is a boolean value, search for playlists that you are subscribed to or not.
- `active:` is a boolean value, to search for playlists that are still active on YouTube or that are no longer active.

**Example**:
- `playlist:backend engineering subscribed:yes`: Search for playlists about *Backend Engineering* that you are subscribed to.
- `playlist: active:yes subscribed:yes`: Note the omitted primary search term, this will return all playlists active on YouTube that you are subscribed to.
- `playlist:html css active:yes`: Search for playlists containing *HTML CSS* that are still active on YouTube.

## Full
Start a full text search by beginning your query with the **primary keyword** `full:`. This will search through your indexed Subtitles showing segments with possible matches. This will only show any results if you have activated *subtitle download and index* on the settings page. The operator for full text searches is `or` meaning when searching for multiple words not all words need to match, but additional words will change the ranking of the result, the more words match and the better they match, the higher ranked the result. The matching words will get highlighted in the text preview.

Clicking the play button on the thumbnail will open the inplace player at the timestamp from where the segment starts. Same when clicking the video title, this will open the video page and put the player at the segment timestamp. This will overwrite any previous playback position.

Narrow down your search with these secondary keywords:
- `lang`: Search for matches only within a language. Use the same two letter ISO country code as you have set on the settings page.
- `source`: Can either be *auto* to search through auto generated subtitles only or *user* to search through user uploaded subtitles only.

**Example**:
- `full:contribute to open source lang:en` search for subtitle segments matching with the words *Contribute to Open Source* in the language *en*.
- `full:flight simulator cockpit source:user` to search for the words *Flight Simulator Cockpit* from *user* uploaded subtitle segments.
