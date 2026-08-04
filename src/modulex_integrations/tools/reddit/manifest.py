"""Reddit integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    CustomAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


_SUBREDDIT_PARAM = ParameterDef(
    type="string",
    description='Subreddit name, without the r/ prefix (e.g. "technology")',
    required=True,
)
_USERNAME_PARAM = ParameterDef(
    type="string",
    description='Reddit username, without the u/ prefix (e.g. "spez")',
    required=True,
)
_THING_ID_PARAM = ParameterDef(
    type="string",
    description='Thing fullname: "t3_abc123" for a post, "t1_def456" for a comment',
    required=True,
)
_POST_FULLNAME_PARAM = ParameterDef(
    type="string",
    description='Post fullname (e.g. "t3_abc123")',
    required=True,
)
_AFTER_PARAM = ParameterDef(
    type="string",
    description=(
        'Fullname cursor for the next page (e.g. "t3_abc123"), taken from a'
        " previous response"
    ),
)
_BEFORE_PARAM = ParameterDef(
    type="string",
    description='Fullname cursor for the previous page (e.g. "t3_abc123")',
)
_COUNT_PARAM = ParameterDef(
    type="integer",
    description="Number of items already seen in this listing (affects numbering only)",
)
_SHOW_PARAM = ParameterDef(
    type="string",
    description='Set to "all" to include items your account filters would normally hide',
)
_SR_DETAIL_PARAM = ParameterDef(
    type="boolean",
    description="Expand subreddit details on every item in the response",
)
_TIME_PARAM = ParameterDef(
    type="string",
    description='Time filter: "hour", "day", "week", "month", "year" or "all"',
)
_USER_SORT_PARAM = ParameterDef(
    type="string",
    description='Sort: "new" (default), "hot", "top" or "controversial"',
    default="new",
)


manifest = IntegrationManifest(
    name="reddit",
    display_name="Reddit",
    description=(
        "Read and act on Reddit: browse and search subreddits, pull comment"
        " threads, submit posts, vote, reply, edit, manage messages and saved"
        " items, and run moderator actions on communities you moderate"
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:reddit",
    app_url="https://www.reddit.com",
    categories=["Social Media", "Communication", "Content"],
    actions=[
        # --- Subreddit reads ------------------------------------------------
        ActionDefinition(
            name="get_posts",
            description=(
                "Fetch posts from a subreddit under a chosen sort (hot, new,"
                " top, rising, controversial)"
            ),
            parameters={
                "subreddit": _SUBREDDIT_PARAM,
                "sort": ParameterDef(
                    type="string",
                    description=(
                        'Sort: "hot" (default), "new", "top", "rising" or'
                        ' "controversial"'
                    ),
                    default="hot",
                ),
                "time": ParameterDef(
                    type="string",
                    description=(
                        'Time filter: "hour", "day", "week", "month", "year" or'
                        ' "all". Applies to the "top" and "controversial" sorts'
                        " only"
                    ),
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum posts to return (1-100, default 10)",
                    default=10,
                ),
                "after": _AFTER_PARAM,
                "before": _BEFORE_PARAM,
                "count": _COUNT_PARAM,
                "show": _SHOW_PARAM,
                "sr_detail": _SR_DETAIL_PARAM,
                "geo_filter": ParameterDef(
                    type="string",
                    description='Geographic filter for the "hot" sort (e.g. "GLOBAL", "US")',
                ),
            },
        ),
        ActionDefinition(
            name="hot_posts",
            description="Fetch the most popular (hot) posts from a subreddit",
            parameters={
                "subreddit": _SUBREDDIT_PARAM,
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum posts to return (1-100, default 10)",
                    default=10,
                ),
            },
        ),
        ActionDefinition(
            name="get_controversial",
            description="Fetch the most controversial posts from a subreddit",
            parameters={
                "subreddit": _SUBREDDIT_PARAM,
                "time": _TIME_PARAM,
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum posts to return (1-100, default 10)",
                    default=10,
                ),
                "after": _AFTER_PARAM,
                "before": _BEFORE_PARAM,
                "count": _COUNT_PARAM,
                "show": _SHOW_PARAM,
                "sr_detail": _SR_DETAIL_PARAM,
            },
        ),
        ActionDefinition(
            name="get_comments",
            description=(
                "Fetch a post and its comment tree, with replies nested under"
                " each comment"
            ),
            parameters={
                "subreddit": _SUBREDDIT_PARAM,
                "post_id": ParameterDef(
                    type="string",
                    description='Post id36 (e.g. "abc123") or its "t3_abc123" fullname',
                    required=True,
                ),
                "sort": ParameterDef(
                    type="string",
                    description=(
                        'Comment sort: "confidence" (best, default), "top",'
                        ' "new", "controversial", "old", "random" or "qa"'
                    ),
                    default="confidence",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum comments to return (1-100, default 50)",
                    default=50,
                ),
                "depth": ParameterDef(
                    type="integer",
                    description="Maximum depth of nested reply subtrees",
                ),
                "context": ParameterDef(
                    type="integer",
                    description=(
                        "Number of parent comments to include around a focused comment"
                    ),
                ),
                "showedits": ParameterDef(
                    type="boolean", description="Include edit information"
                ),
                "showmore": ParameterDef(
                    type="boolean",
                    description='Include "load more comments" placeholders',
                ),
                "threaded": ParameterDef(
                    type="boolean", description="Return comments threaded (nested)"
                ),
                "truncate": ParameterDef(
                    type="integer", description="Truncate the comment tree at this depth"
                ),
                "comment": ParameterDef(
                    type="string",
                    description="id36 of a single comment to focus the thread on",
                ),
            },
        ),
        ActionDefinition(
            name="search",
            description="Search for posts inside a subreddit",
            parameters={
                "subreddit": _SUBREDDIT_PARAM,
                "query": ParameterDef(
                    type="string",
                    description=(
                        "Search query. Supports field searches (title:, author:,"
                        " selftext:, flair:, site:), boolean AND/OR/NOT in caps,"
                        ' parentheses and "exact phrases"'
                    ),
                    required=True,
                ),
                "sort": ParameterDef(
                    type="string",
                    description=(
                        'Sort: "relevance" (default), "hot", "top", "new" or "comments"'
                    ),
                    default="relevance",
                ),
                "time": _TIME_PARAM,
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum results to return (1-100, default 10)",
                    default=10,
                ),
                "restrict_sr": ParameterDef(
                    type="boolean",
                    description="Restrict the search to this subreddit (default true)",
                    default=True,
                ),
                "after": _AFTER_PARAM,
                "before": _BEFORE_PARAM,
                "count": _COUNT_PARAM,
                "show": _SHOW_PARAM,
                "result_type": ParameterDef(
                    type="string",
                    description=(
                        'Result kind: "link" (posts, default), "sr" (subreddits)'
                        ' or "user"'
                    ),
                ),
                "sr_detail": _SR_DETAIL_PARAM,
            },
        ),
        ActionDefinition(
            name="get_subreddit_info",
            description=(
                "Get metadata about a subreddit: title, description, subscriber"
                " count and type"
            ),
            parameters={"subreddit": _SUBREDDIT_PARAM},
        ),
        ActionDefinition(
            name="get_subreddit_rules",
            description=(
                "Get a subreddit's own rules plus the Reddit site-wide rules that"
                " apply to it"
            ),
            parameters={"subreddit": _SUBREDDIT_PARAM},
        ),
        # --- Account + user reads -------------------------------------------
        ActionDefinition(
            name="get_me",
            description="Get the profile of the authenticated Reddit account",
            parameters={},
        ),
        ActionDefinition(
            name="get_user",
            description="Get the public profile of any Reddit user by username",
            parameters={"username": _USERNAME_PARAM},
        ),
        ActionDefinition(
            name="get_user_posts",
            description="Fetch the posts a Reddit user has submitted",
            parameters={
                "username": _USERNAME_PARAM,
                "sort": _USER_SORT_PARAM,
                "time": ParameterDef(
                    type="string",
                    description=(
                        'Time filter: "hour", "day", "week", "month", "year" or'
                        ' "all". Applies to the "top" and "controversial" sorts'
                        " only"
                    ),
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum posts to return (1-100, default 25)",
                    default=25,
                ),
                "after": _AFTER_PARAM,
                "before": _BEFORE_PARAM,
                "count": _COUNT_PARAM,
                "show": _SHOW_PARAM,
                "sr_detail": _SR_DETAIL_PARAM,
            },
        ),
        ActionDefinition(
            name="get_user_comments",
            description="Fetch the comments a Reddit user has written",
            parameters={
                "username": _USERNAME_PARAM,
                "sort": _USER_SORT_PARAM,
                "time": ParameterDef(
                    type="string",
                    description=(
                        'Time filter: "hour", "day", "week", "month", "year" or'
                        ' "all". Applies to the "top" and "controversial" sorts'
                        " only"
                    ),
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum comments to return (1-100, default 25)",
                    default=25,
                ),
                "after": _AFTER_PARAM,
                "before": _BEFORE_PARAM,
                "count": _COUNT_PARAM,
                "show": _SHOW_PARAM,
                "sr_detail": _SR_DETAIL_PARAM,
            },
        ),
        ActionDefinition(
            name="get_saved",
            description="Fetch your own saved posts and comments, split by kind",
            parameters={
                "username": ParameterDef(
                    type="string",
                    description=(
                        "Your own Reddit username — Reddit only serves saved items"
                        " for the authenticated account"
                    ),
                    required=True,
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum items to return (1-100, default 25)",
                    default=25,
                ),
                "after": _AFTER_PARAM,
                "before": _BEFORE_PARAM,
                "count": _COUNT_PARAM,
                "show": _SHOW_PARAM,
                "sr_detail": _SR_DETAIL_PARAM,
            },
        ),
        ActionDefinition(
            name="get_info",
            description="Look up posts, comments and subreddits by their thing fullnames",
            parameters={
                "thing_ids": ParameterDef(
                    type="string",
                    description=(
                        "Comma-separated thing fullnames (e.g."
                        ' "t3_abc123,t1_xyz789,t5_2qh33"). Prefixes: t1_ comment,'
                        " t3_ post, t5_ subreddit"
                    ),
                    required=True,
                ),
            },
        ),
        # --- Subreddit discovery --------------------------------------------
        ActionDefinition(
            name="search_subreddits",
            description="Search for subreddits by name and description",
            parameters={
                "query": ParameterDef(
                    type="string",
                    description="Text matched against subreddit names and descriptions",
                    required=True,
                ),
                "sort": ParameterDef(
                    type="string",
                    description='Sort: "relevance" (default) or "activity"',
                    default="relevance",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum subreddits to return (1-100, default 25)",
                    default=25,
                ),
                "after": _AFTER_PARAM,
                "before": _BEFORE_PARAM,
                "show_users": ParameterDef(
                    type="boolean", description="Also include matching user profiles"
                ),
                "sr_detail": _SR_DETAIL_PARAM,
            },
        ),
        ActionDefinition(
            name="list_my_subreddits",
            description="List the subreddits the authenticated account subscribes to",
            parameters={
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum subreddits to return (1-100, default 25)",
                    default=25,
                ),
                "after": _AFTER_PARAM,
                "before": _BEFORE_PARAM,
                "count": _COUNT_PARAM,
                "show": _SHOW_PARAM,
                "sr_detail": _SR_DETAIL_PARAM,
            },
        ),
        # --- Messages --------------------------------------------------------
        ActionDefinition(
            name="get_messages",
            description="Retrieve items from the authenticated account's inbox",
            parameters={
                "where": ParameterDef(
                    type="string",
                    description=(
                        'Folder: "inbox" (default), "unread", "sent", "messages"'
                        ' (direct only), "comments" (comment replies), "selfreply"'
                        ' or "mentions"'
                    ),
                    default="inbox",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum messages to return (1-100, default 25)",
                    default=25,
                ),
                "after": _AFTER_PARAM,
                "before": _BEFORE_PARAM,
                "mark": ParameterDef(
                    type="boolean", description="Mark the fetched messages as read"
                ),
                "count": _COUNT_PARAM,
                "show": _SHOW_PARAM,
            },
        ),
        ActionDefinition(
            name="send_message",
            description="Send a private message to a Reddit user or subreddit",
            parameters={
                "to": ParameterDef(
                    type="string",
                    description=(
                        'Recipient username (e.g. "spez") or subreddit (e.g. "/r/python")'
                    ),
                    required=True,
                ),
                "subject": ParameterDef(
                    type="string",
                    description="Message subject (max 100 characters)",
                    required=True,
                ),
                "text": ParameterDef(
                    type="string",
                    description="Message body in Reddit markdown",
                    required=True,
                ),
                "from_sr": ParameterDef(
                    type="string",
                    description=(
                        "Send as modmail from this subreddit (requires mod mail"
                        " permission)"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="mark_read",
            description="Mark one or more inbox messages as read",
            parameters={
                "thing_ids": ParameterDef(
                    type="string",
                    description=(
                        'Comma-separated message fullnames (e.g. "t4_abc123,t4_def456")'
                    ),
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="mark_all_read",
            description="Mark every message in the inbox as read",
            parameters={},
        ),
        # --- Content writes ---------------------------------------------------
        ActionDefinition(
            name="submit_post",
            description="Submit a new text or link post to a subreddit",
            parameters={
                "subreddit": _SUBREDDIT_PARAM,
                "title": ParameterDef(
                    type="string",
                    description="Post title (max 300 characters)",
                    required=True,
                ),
                "text": ParameterDef(
                    type="string",
                    description=(
                        "Body of a self post, in Reddit markdown. Mutually"
                        " exclusive with url"
                    ),
                ),
                "url": ParameterDef(
                    type="string",
                    description="Target of a link post. Mutually exclusive with text",
                ),
                "nsfw": ParameterDef(type="boolean", description="Mark the post NSFW"),
                "spoiler": ParameterDef(
                    type="boolean", description="Mark the post a spoiler"
                ),
                "send_replies": ParameterDef(
                    type="boolean",
                    description="Send reply notifications to the inbox (default true)",
                ),
                "flair_id": ParameterDef(
                    type="string", description="Flair template UUID (max 36 characters)"
                ),
                "flair_text": ParameterDef(
                    type="string", description="Flair text (max 64 characters)"
                ),
                "collection_id": ParameterDef(
                    type="string", description="Collection UUID to add the new post to"
                ),
            },
        ),
        ActionDefinition(
            name="reply",
            description="Post a comment in reply to a Reddit post or comment",
            parameters={
                "parent_id": ParameterDef(
                    type="string",
                    description=(
                        'Thing fullname being replied to: "t3_abc123" for a post,'
                        ' "t1_def456" for a comment'
                    ),
                    required=True,
                ),
                "text": ParameterDef(
                    type="string",
                    description="Reply body in Reddit markdown",
                    required=True,
                ),
                "return_rtjson": ParameterDef(
                    type="boolean",
                    description="Return the reply as Rich Text JSON instead of markdown",
                ),
            },
        ),
        ActionDefinition(
            name="edit",
            description="Replace the body of your own Reddit post or comment",
            parameters={
                "thing_id": _THING_ID_PARAM,
                "text": ParameterDef(
                    type="string",
                    description="Replacement body in Reddit markdown",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="delete",
            description="Delete your own Reddit post or comment",
            parameters={"thing_id": _THING_ID_PARAM},
        ),
        ActionDefinition(
            name="vote",
            description="Upvote, downvote or clear your vote on a Reddit post or comment",
            parameters={
                "thing_id": _THING_ID_PARAM,
                "direction": ParameterDef(
                    type="integer",
                    description="1 to upvote, 0 to clear the vote, -1 to downvote",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="save",
            description="Save a Reddit post or comment to your saved items",
            parameters={
                "thing_id": _THING_ID_PARAM,
                "category": ParameterDef(
                    type="string",
                    description="Saved-items category (a Reddit Premium feature)",
                ),
            },
        ),
        ActionDefinition(
            name="unsave",
            description="Remove a Reddit post or comment from your saved items",
            parameters={"thing_id": _THING_ID_PARAM},
        ),
        ActionDefinition(
            name="subscribe",
            description="Subscribe to or unsubscribe from a subreddit",
            parameters={
                "subreddit": _SUBREDDIT_PARAM,
                "action": ParameterDef(
                    type="string",
                    description='"sub" to subscribe (default) or "unsub" to unsubscribe',
                    default="sub",
                ),
            },
        ),
        ActionDefinition(
            name="report",
            description="Report a Reddit post or comment to the subreddit moderators",
            parameters={
                "thing_id": _THING_ID_PARAM,
                "reason": ParameterDef(
                    type="string",
                    description=(
                        "Subreddit rule the content violates (max 100 characters)"
                    ),
                ),
                "other_reason": ParameterDef(
                    type="string", description="Free-form reason (max 100 characters)"
                ),
            },
        ),
        ActionDefinition(
            name="hide",
            description="Hide one or more posts from your own listings",
            parameters={
                "thing_ids": ParameterDef(
                    type="string",
                    description=(
                        'Comma-separated post fullnames (e.g. "t3_abc123,t3_def456")'
                    ),
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="unhide",
            description="Unhide one or more previously hidden posts",
            parameters={
                "thing_ids": ParameterDef(
                    type="string",
                    description=(
                        'Comma-separated post fullnames (e.g. "t3_abc123,t3_def456")'
                    ),
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="marknsfw",
            description="Mark a post NSFW",
            parameters={"thing_id": _POST_FULLNAME_PARAM},
        ),
        ActionDefinition(
            name="unmarknsfw",
            description="Remove the NSFW mark from a post",
            parameters={"thing_id": _POST_FULLNAME_PARAM},
        ),
        # --- Moderator actions ------------------------------------------------
        ActionDefinition(
            name="mod_approve",
            description=(
                "Approve a reported or removed post or comment. Requires"
                " moderator rights on the subreddit"
            ),
            parameters={"thing_id": _THING_ID_PARAM},
        ),
        ActionDefinition(
            name="mod_remove",
            description=(
                "Remove a post or comment, optionally as spam. Requires moderator"
                " rights on the subreddit"
            ),
            parameters={
                "thing_id": _THING_ID_PARAM,
                "spam": ParameterDef(
                    type="boolean",
                    description="Also train the subreddit spam filter on this item",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="mod_distinguish",
            description=(
                "Add or remove a moderator/admin badge on a post or comment."
                " Requires moderator rights on the subreddit"
            ),
            parameters={
                "thing_id": _THING_ID_PARAM,
                "how": ParameterDef(
                    type="string",
                    description=(
                        '"yes" for a moderator badge (default), "no" to remove it,'
                        ' "admin" or "special"'
                    ),
                    default="yes",
                ),
                "sticky": ParameterDef(
                    type="boolean",
                    description=(
                        "Also sticky the comment to the top of the thread"
                        " (comments only)"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="lock",
            description=(
                "Lock a post or comment so no new replies can be posted. Requires"
                " moderator rights on the subreddit"
            ),
            parameters={"thing_id": _THING_ID_PARAM},
        ),
        ActionDefinition(
            name="unlock",
            description=(
                "Unlock a previously locked post or comment. Requires moderator"
                " rights on the subreddit"
            ),
            parameters={"thing_id": _THING_ID_PARAM},
        ),
        ActionDefinition(
            name="mod_sticky",
            description=(
                "Sticky or unsticky a post at the top of a subreddit. Requires"
                " moderator rights on the subreddit"
            ),
            parameters={
                "thing_id": _POST_FULLNAME_PARAM,
                "state": ParameterDef(
                    type="boolean",
                    description="True to sticky the post (default), false to unsticky it",
                    default=True,
                ),
                "num": ParameterDef(
                    type="integer",
                    description=(
                        "Sticky slot 1-4 (1 is the top slot); only used when stickying"
                    ),
                ),
            },
        ),
    ],
    auth_schemas=[
        CustomAuthSchema(
            display_name="Reddit Script App",
            description=(
                "Authenticate with a Reddit script app and the account it runs"
                " as. Four static values, no browser redirect and no consent"
                " screen."
            ),
            setup_instructions=[
                (
                    "Sign in as the account the integration should act as and open "
                    "https://www.reddit.com/prefs/apps."
                ),
                (
                    "Click 'create another app...', choose the 'script' type, give it "
                    "a name, and set the redirect uri to http://localhost:8080 "
                    "(unused by this flow but required by the form)."
                ),
                (
                    "Copy the client ID — the string under the app name, just below "
                    "'personal use script' — and the secret."
                ),
                (
                    "Enter the username and password of that same account. A script "
                    "app can only authenticate accounts listed as its developers."
                ),
                (
                    "Disable two-factor authentication on that account: Reddit's "
                    "password grant cannot complete a 2FA challenge."
                ),
                (
                    "Optionally set a User-Agent. The default is "
                    "'python:modulex.reddit:v1.0.0 (by /u/<account>)'; Reddit "
                    "requires a unique, descriptive one and throttles generic "
                    "agents hard."
                ),
            ],
            setup_environment_variables=[
                EnvVar(
                    name="REDDIT_CLIENT_ID",
                    display_name="Client ID",
                    description=(
                        "The app ID shown under the app name on the Reddit app"
                        " preferences page"
                    ),
                    required=True,
                    sensitive=False,
                    sample_format="p-jcoLKBynTLew",
                    about_url="https://www.reddit.com/prefs/apps",
                ),
                EnvVar(
                    name="REDDIT_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="The app secret shown next to 'secret' on the same page",
                    required=True,
                    sensitive=True,
                    sample_format="gko_LXELoV07ZBNUXrvWZfzE3aI",
                    about_url="https://www.reddit.com/prefs/apps",
                ),
                EnvVar(
                    name="REDDIT_BOT_USERNAME",
                    display_name="Reddit Username",
                    description=(
                        "Username of the account the app acts as. It must be listed"
                        " as a developer of the script app."
                    ),
                    required=True,
                    sensitive=False,
                    sample_format="my_reddit_bot",
                    about_url="https://www.reddit.com/prefs/apps",
                ),
                EnvVar(
                    name="REDDIT_BOT_PASSWORD",
                    display_name="Reddit Password",
                    description=(
                        "Password of that account. Two-factor authentication must be"
                        " disabled — the password grant cannot answer a 2FA challenge."
                    ),
                    required=True,
                    sensitive=True,
                    sample_format="correct-horse-battery-staple",
                    about_url="https://www.reddit.com/prefs/apps",
                ),
                EnvVar(
                    name="REDDIT_USER_AGENT",
                    display_name="User Agent",
                    description=(
                        "Overrides the User-Agent sent with every request. Reddit"
                        " requires a unique, descriptive value and applies much"
                        " lower rate limits to generic ones. Recommended shape:"
                        " <platform>:<app id>:<version> (by /u/<username>)"
                    ),
                    required=False,
                    sensitive=False,
                    sample_format="python:my-reddit-bot:v1.0.0 (by /u/my_reddit_bot)",
                    about_url="https://support.reddithelp.com/hc/en-us/articles/16160319875092",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://www.reddit.com/api/v1/access_token",
                method="POST",
                # Reachability check only. Minting a token requires posting the
                # client secret with HTTP Basic auth plus the account password,
                # which the runtime cannot assemble from a static endpoint
                # definition, so the credential is truly validated on the first
                # action call. An unauthenticated POST answers 401, which is the
                # documented "endpoint is up" response.
                success_indicators=SuccessIndicators(status_codes=[200, 401]),
                cost_level="free",
                description=(
                    "Reachability check against the Reddit token endpoint."
                    " Credentials are validated when an action first mints a token."
                ),
            ),
        ),
    ],
)
