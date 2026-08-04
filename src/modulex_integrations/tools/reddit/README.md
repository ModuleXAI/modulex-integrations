# Reddit

Read and act on Reddit through the official Data API (`oauth.reddit.com`): browse and search subreddits, pull comment threads, submit posts, vote, reply, edit, manage messages and saved items, and run moderator actions on communities you moderate.

## Authentication

### Reddit Script App

A script app is Reddit's server-to-server credential: four static values, no browser redirect and no consent screen. It is bound to one Reddit account, which is what makes the write and moderator actions possible — a user-less token can only read.

- Sign in as the account the integration should act as and open <https://www.reddit.com/prefs/apps>.
- Click **create another app...**, choose the **script** type, name it, and set the redirect uri to `http://localhost:8080` (unused by this flow but required by the form).
- Copy the **client ID** (the string under the app name, just below `personal use script`) and the **secret**.
- Required credential settings:
  - `REDDIT_CLIENT_ID` — the app ID from the app preferences page
  - `REDDIT_CLIENT_SECRET` — the app secret from the same page
  - `REDDIT_BOT_USERNAME` — username of the account the app acts as; it must be listed as a developer of the script app
  - `REDDIT_BOT_PASSWORD` — that account's password
- Optional credential setting:
  - `REDDIT_USER_AGENT` — overrides the `User-Agent` header. The default is `python:modulex.reddit:v1.0.0 (by /u/<account>)`.

Each call first exchanges the credential set for a short-lived bearer token (`POST https://www.reddit.com/api/v1/access_token` with HTTP Basic `client_id:client_secret` and `grant_type=password`), then calls `https://oauth.reddit.com` with `Authorization: bearer <token>`. Nothing is cached between invocations, so every action is stateless: expect two HTTP round trips per call.

Two constraints are worth knowing before you configure a credential:

- **Two-factor authentication must be off** on the acting account. The password grant has no way to answer a 2FA challenge, and Reddit rejects the token request outright.
- **The `User-Agent` matters.** Reddit's API rules require a unique, descriptive agent in the shape `<platform>:<app id>:<version> (by /u/<username>)` and apply drastically reduced rate limits to generic ones. The default folds the account name in so it is unique per credential; override it if you want your own app identifier.

## Tools

| name | description | required params |
| --- | --- | --- |
| `get_posts` | Posts from a subreddit under a chosen sort (hot, new, top, rising, controversial) | `subreddit` |
| `hot_posts` | The hot posts of a subreddit | `subreddit` |
| `get_controversial` | The most controversial posts of a subreddit | `subreddit` |
| `get_comments` | A post plus its comment tree, replies nested under each comment | `subreddit`, `post_id` |
| `search` | Search posts inside a subreddit | `subreddit`, `query` |
| `get_subreddit_info` | Subreddit metadata: title, description, subscribers, type | `subreddit` |
| `get_subreddit_rules` | A subreddit's own rules plus the site-wide rules | `subreddit` |
| `get_me` | The authenticated account's profile | |
| `get_user` | Any user's public profile | `username` |
| `get_user_posts` | Posts a user has submitted | `username` |
| `get_user_comments` | Comments a user has written | `username` |
| `get_saved` | Your own saved posts and comments, split by kind | `username` |
| `get_info` | Look up posts/comments/subreddits by thing fullname | `thing_ids` |
| `search_subreddits` | Search subreddits by name and description | `query` |
| `list_my_subreddits` | Subreddits the account subscribes to | |
| `get_messages` | Inbox items from a chosen folder | |
| `send_message` | Send a private message to a user or subreddit | `to`, `subject`, `text` |
| `mark_read` | Mark specific inbox items read | `thing_ids` |
| `mark_all_read` | Mark the whole inbox read | |
| `submit_post` | Submit a text or link post | `subreddit`, `title` |
| `reply` | Comment in reply to a post or comment | `parent_id`, `text` |
| `edit` | Replace the body of your own post or comment | `thing_id`, `text` |
| `delete` | Delete your own post or comment | `thing_id` |
| `vote` | Upvote, downvote or clear a vote | `thing_id`, `direction` |
| `save` | Save a post or comment | `thing_id` |
| `unsave` | Unsave a post or comment | `thing_id` |
| `subscribe` | Subscribe to or unsubscribe from a subreddit | `subreddit` |
| `report` | Report a post or comment to the moderators | `thing_id` |
| `hide` | Hide posts from your listings | `thing_ids` |
| `unhide` | Unhide previously hidden posts | `thing_ids` |
| `marknsfw` | Mark a post NSFW | `thing_id` |
| `unmarknsfw` | Remove the NSFW mark from a post | `thing_id` |
| `mod_approve` | Approve a reported or removed item (moderator) | `thing_id` |
| `mod_remove` | Remove an item, optionally as spam (moderator) | `thing_id` |
| `mod_distinguish` | Add/remove a moderator or admin badge (moderator) | `thing_id` |
| `lock` | Lock an item against new replies (moderator) | `thing_id` |
| `unlock` | Unlock a locked item (moderator) | `thing_id` |
| `mod_sticky` | Sticky or unsticky a post (moderator) | `thing_id` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved credential.

Reddit identifies objects by *fullname* — a kind prefix plus a base-36 id: `t1_` comment, `t2_` account, `t3_` post, `t4_` message, `t5_` subreddit. Anything named `thing_id`/`thing_ids` takes fullnames; `get_comments.post_id` accepts either the bare id36 (`abc123`) or the `t3_abc123` form. Permalinks come back absolute (`https://www.reddit.com/...`) rather than as the site-relative paths the API returns.

The six moderator tools (`mod_approve`, `mod_remove`, `mod_distinguish`, `mod_sticky`, `lock`, `unlock`) act on subreddits the account moderates. Called anywhere else they return `success=false` with Reddit's HTTP 403 — a permission outcome, not a configuration error.

## Limits & Quotas

- **Rate limits**: 100 queries per minute per OAuth client ID on the free tier, averaged over a 10-minute window. Budget two calls per action (token mint + API call). A generic or missing `User-Agent` gets a much lower limit.
- **Pagination**: listings are cursor-based. Pass `after`/`before` (thing fullnames) and read the `after`/`before` the response carries; `limit` is capped at 100 per page and over-large values are clamped rather than rejected.
- **Comment depth**: `get_comments` nests replies up to 32 levels. Reddit itself truncates deep threads with "load more" placeholders, which are dropped rather than followed — use `comment` plus `context` to walk into a specific subtree.
- **Write throttles**: new or low-karma accounts are rate-limited on submissions and comments. Reddit reports these inside an HTTP 200 as `RATELIMIT` in the response's `errors` array; they surface as `success=false` with the code and message.
- **Token lifetime**: bearer tokens are short-lived and minted per invocation, so nothing goes stale between calls.
- **Error model**: non-2xx responses, rejected credentials, `errors`-array write failures and malformed bodies are all returned as `success=false` + `error` rather than raised. Response values are type-coerced on the way into the models, so a field arriving with an unexpected type degrades to `null` instead of failing the call.

## Maintainer

ModuleX core team.
