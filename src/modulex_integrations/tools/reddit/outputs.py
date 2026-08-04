"""Pydantic response models for the Reddit integration's @tool functions.

Reddit wraps almost everything in a ``Thing`` envelope
(``{"kind": "t3", "data": {...}}``) and listings in a ``Listing``
(``{"kind": "Listing", "data": {"children": [...], "after": ..., "before": ...}}``).
The models below hold the **unwrapped** payloads: one model per Reddit thing
kind (``t1`` comment, ``t2`` account, ``t3`` link/post, ``t4`` message,
``t5`` subreddit) plus the small result objects the write endpoints return.

Every field is optional. Reddit omits fields freely depending on the
endpoint, on whether the caller is a moderator, and on the age of the
object, so nothing here is ever asserted to be present.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "DeleteOutput",
    "EditOutput",
    "EditedThing",
    "GetCommentsOutput",
    "GetControversialOutput",
    "GetInfoOutput",
    "GetMeOutput",
    "GetMessagesOutput",
    "GetPostsOutput",
    "GetSavedOutput",
    "GetSubredditInfoOutput",
    "GetSubredditRulesOutput",
    "GetUserCommentsOutput",
    "GetUserOutput",
    "GetUserPostsOutput",
    "HideOutput",
    "HotPostsOutput",
    "ListMySubredditsOutput",
    "LockOutput",
    "MarkAllReadOutput",
    "MarkNsfwOutput",
    "MarkReadOutput",
    "ModApproveOutput",
    "ModDistinguishOutput",
    "ModRemoveOutput",
    "ModStickyOutput",
    "PostedComment",
    "RedditComment",
    "RedditMessage",
    "RedditPost",
    "RedditRule",
    "RedditSubreddit",
    "RedditUser",
    "ReplyOutput",
    "ReportOutput",
    "SaveOutput",
    "SearchOutput",
    "SearchSubredditsOutput",
    "SendMessageOutput",
    "SubmitPostOutput",
    "SubmittedPost",
    "SubscribeOutput",
    "UnhideOutput",
    "UnlockOutput",
    "UnmarkNsfwOutput",
    "UnsaveOutput",
    "VoteOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Reddit "thing" models --------------------------------------------------


class RedditPost(_Base):
    """A link/self post (``t3``), unwrapped from its Thing envelope."""

    id: str | None = None
    name: str | None = None
    title: str | None = None
    author: str | None = None
    url: str | None = None
    # Absolute permalink (``https://www.reddit.com`` + the relative path Reddit
    # returns), so the value can be opened without further assembly.
    permalink: str | None = None
    created_utc: float | None = None
    score: int | None = None
    upvote_ratio: float | None = None
    num_comments: int | None = None
    is_self: bool | None = None
    selftext: str | None = None
    thumbnail: str | None = None
    subreddit: str | None = None
    subreddit_id: str | None = None
    domain: str | None = None
    over_18: bool | None = None
    spoiler: bool | None = None
    locked: bool | None = None
    stickied: bool | None = None
    hidden: bool | None = None
    saved: bool | None = None
    # Reddit sends ``false`` when a post was never edited and an epoch
    # timestamp when it was; the boolean form degrades to ``None``.
    edited: float | None = None
    distinguished: str | None = None
    ups: int | None = None
    downs: int | None = None
    link_flair_text: str | None = None
    author_flair_text: str | None = None


class RedditComment(_Base):
    """A comment (``t1``). ``replies`` nests the same model recursively."""

    id: str | None = None
    name: str | None = None
    author: str | None = None
    body: str | None = None
    body_html: str | None = None
    created_utc: float | None = None
    score: int | None = None
    permalink: str | None = None
    parent_id: str | None = None
    link_id: str | None = None
    subreddit: str | None = None
    subreddit_id: str | None = None
    is_submitter: bool | None = None
    stickied: bool | None = None
    score_hidden: bool | None = None
    edited: float | None = None
    distinguished: str | None = None
    gilded: int | None = None
    ups: int | None = None
    downs: int | None = None
    author_flair_text: str | None = None
    link_title: str | None = None
    link_author: str | None = None
    link_url: str | None = None
    replies: list[RedditComment] = Field(default_factory=list)


RedditComment.model_rebuild()


class RedditMessage(_Base):
    """A private message or inbox item (``t4``)."""

    id: str | None = None
    name: str | None = None
    author: str | None = None
    dest: str | None = None
    subject: str | None = None
    body: str | None = None
    body_html: str | None = None
    created_utc: float | None = None
    new: bool | None = None
    was_comment: bool | None = None
    context: str | None = None
    parent_id: str | None = None
    subreddit: str | None = None
    distinguished: str | None = None


class RedditSubreddit(_Base):
    """A subreddit (``t5``)."""

    id: str | None = None
    name: str | None = None
    display_name: str | None = None
    display_name_prefixed: str | None = None
    title: str | None = None
    description: str | None = None
    public_description: str | None = None
    subscribers: int | None = None
    # Reddit spells the live-visitor count ``active_user_count`` on most
    # endpoints and ``accounts_active`` on a few older ones; both feed here.
    accounts_active: int | None = None
    created_utc: float | None = None
    over18: bool | None = None
    lang: str | None = None
    subreddit_type: str | None = None
    url: str | None = None
    icon_img: str | None = None
    community_icon: str | None = None
    banner_img: str | None = None


class RedditUser(_Base):
    """An account (``t2``)."""

    id: str | None = None
    name: str | None = None
    created_utc: float | None = None
    link_karma: int | None = None
    comment_karma: int | None = None
    total_karma: int | None = None
    awardee_karma: int | None = None
    awarder_karma: int | None = None
    is_gold: bool | None = None
    is_mod: bool | None = None
    is_employee: bool | None = None
    is_friend: bool | None = None
    has_verified_email: bool | None = None
    verified: bool | None = None
    over_18: bool | None = None
    icon_img: str | None = None


class RedditRule(_Base):
    """One subreddit rule from ``/r/<subreddit>/about/rules``."""

    short_name: str | None = None
    description: str | None = None
    description_html: str | None = None
    violation_reason: str | None = None
    kind: str | None = None
    created_utc: float | None = None
    priority: int | None = None


class SubmittedPost(_Base):
    """The thin result object ``/api/submit`` returns for a new post."""

    id: str | None = None
    name: str | None = None
    url: str | None = None
    permalink: str | None = None


class PostedComment(_Base):
    """The comment ``/api/comment`` echoes back after a successful reply."""

    id: str | None = None
    name: str | None = None
    permalink: str | None = None
    body: str | None = None


class EditedThing(_Base):
    """The post or comment ``/api/editusertext`` echoes back."""

    id: str | None = None
    name: str | None = None
    body: str | None = None
    selftext: str | None = None


# --- Shared envelopes -------------------------------------------------------


class _Result(_Base):
    """Every action answers with ``success`` plus an ``error`` on failure."""

    success: bool
    error: str | None = None


class _WriteResult(_Result):
    """Write actions add a short human-readable confirmation message."""

    message: str | None = None


class _PostListing(_Result):
    """A paginated listing of posts."""

    posts: list[RedditPost] = Field(default_factory=list)
    after: str | None = None
    before: str | None = None


class _SubredditListing(_Result):
    """A paginated listing of subreddits."""

    subreddits: list[RedditSubreddit] = Field(default_factory=list)
    after: str | None = None
    before: str | None = None


# --- Per-action outputs: reads ---------------------------------------------


class GetPostsOutput(_PostListing):
    """Posts from a subreddit under a chosen sort."""

    subreddit: str | None = None


class HotPostsOutput(_PostListing):
    """The hot posts of a subreddit."""

    subreddit: str | None = None


class GetControversialOutput(_PostListing):
    """Controversial posts from a subreddit."""

    subreddit: str | None = None


class SearchOutput(_PostListing):
    """Posts matching a search inside a subreddit."""

    subreddit: str | None = None


class GetCommentsOutput(_Result):
    """A post plus its (nested) comment tree."""

    post: RedditPost | None = None
    comments: list[RedditComment] = Field(default_factory=list)


class GetMeOutput(_Result):
    """The authenticated account."""

    user: RedditUser | None = None


class GetUserOutput(_Result):
    """A public account profile."""

    user: RedditUser | None = None


class GetMessagesOutput(_Result):
    """A page of inbox items."""

    messages: list[RedditMessage] = Field(default_factory=list)
    after: str | None = None
    before: str | None = None


class GetSubredditInfoOutput(_Result):
    """Metadata for one subreddit."""

    subreddit: RedditSubreddit | None = None


class GetSubredditRulesOutput(_Result):
    """The subreddit's own rules plus the Reddit site-wide rules."""

    rules: list[RedditRule] = Field(default_factory=list)
    site_rules: list[str] = Field(default_factory=list)


class GetUserPostsOutput(_PostListing):
    """Posts submitted by a user."""


class GetUserCommentsOutput(_Result):
    """Comments written by a user."""

    comments: list[RedditComment] = Field(default_factory=list)
    after: str | None = None
    before: str | None = None


class GetSavedOutput(_Result):
    """Saved posts and comments, split by thing kind."""

    posts: list[RedditPost] = Field(default_factory=list)
    comments: list[RedditComment] = Field(default_factory=list)
    after: str | None = None
    before: str | None = None


class GetInfoOutput(_Result):
    """Things looked up by fullname, split by kind."""

    posts: list[RedditPost] = Field(default_factory=list)
    comments: list[RedditComment] = Field(default_factory=list)
    subreddits: list[RedditSubreddit] = Field(default_factory=list)


class SearchSubredditsOutput(_SubredditListing):
    """Subreddits matching a query."""


class ListMySubredditsOutput(_SubredditListing):
    """Subreddits the authenticated account subscribes to."""


# --- Per-action outputs: writes --------------------------------------------


class SubmitPostOutput(_WriteResult):
    """Result of submitting a new post."""

    post: SubmittedPost | None = None


class ReplyOutput(_WriteResult):
    """Result of replying to a post or comment."""

    comment: PostedComment | None = None


class EditOutput(_WriteResult):
    """Result of editing your own post or comment."""

    thing: EditedThing | None = None


class VoteOutput(_WriteResult):
    """Result of casting or clearing a vote."""


class SaveOutput(_WriteResult):
    """Result of saving a post or comment."""


class UnsaveOutput(_WriteResult):
    """Result of unsaving a post or comment."""


class DeleteOutput(_WriteResult):
    """Result of deleting your own post or comment."""


class SubscribeOutput(_WriteResult):
    """Result of subscribing to or unsubscribing from a subreddit."""


class SendMessageOutput(_WriteResult):
    """Result of sending a private message."""


class ReportOutput(_WriteResult):
    """Result of reporting a post or comment."""


class HideOutput(_WriteResult):
    """Result of hiding posts."""


class UnhideOutput(_WriteResult):
    """Result of unhiding posts."""


class MarkNsfwOutput(_WriteResult):
    """Result of marking a post NSFW."""


class UnmarkNsfwOutput(_WriteResult):
    """Result of removing the NSFW mark from a post."""


class MarkReadOutput(_WriteResult):
    """Result of marking specific inbox items read."""


class MarkAllReadOutput(_WriteResult):
    """Result of marking the whole inbox read."""


class ModApproveOutput(_WriteResult):
    """Result of a moderator approval."""


class ModRemoveOutput(_WriteResult):
    """Result of a moderator removal."""


class ModDistinguishOutput(_WriteResult):
    """Result of distinguishing or un-distinguishing an item."""


class LockOutput(_WriteResult):
    """Result of locking a post or comment."""


class UnlockOutput(_WriteResult):
    """Result of unlocking a post or comment."""


class ModStickyOutput(_WriteResult):
    """Result of stickying or unstickying a post."""
