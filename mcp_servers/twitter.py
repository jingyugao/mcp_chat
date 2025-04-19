import asyncio
import os
from re import T
from typing import Any, List, Optional
import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel
from dotenv import load_dotenv

# Initialize FastMCP server
mcp = FastMCP("twitter")

# Load environment variables
load_dotenv()

# Get API key from environment variables
api_key = os.getenv("TWITTER_API_KEY")
if not api_key:
    raise ValueError(
        "TWITTER_API_KEY environment variable is not set. "
        "Please create a .env file with your Twitter API key. "
        "See .env.example for reference."
    )

api_base = "https://api.twitterapi.io/twitter"


class TwitterUser(BaseModel):
    type: Optional[str] = None
    userName: Optional[str] = None
    url: Optional[str] = None
    id: Optional[str] = None
    name: Optional[str] = None
    isBlueVerified: Optional[bool] = None
    profilePicture: Optional[str] = None
    coverPicture: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    followers: Optional[int] = None
    following: Optional[int] = None
    canDm: Optional[bool] = None
    createdAt: Optional[str] = None
    fastFollowersCount: Optional[int] = None
    favouritesCount: Optional[int] = None
    hasCustomTimelines: Optional[bool] = None
    isTranslator: Optional[bool] = None
    mediaCount: Optional[int] = None
    statusesCount: Optional[int] = None
    withheldInCountries: Optional[List[str]] = None
    affiliatesHighlightedLabel: Optional[dict] = None
    possiblySensitive: Optional[bool] = None
    pinnedTweetIds: Optional[List[str]] = None
    isAutomated: Optional[bool] = None
    automatedBy: Optional[str] = None
    unavailable: Optional[bool] = None
    message: Optional[str] = None
    unavailableReason: Optional[str] = None


class TwitterUserResponse(BaseModel):
    data: Optional[TwitterUser] = None
    status: Optional[str] = None
    msg: Optional[str] = None


class Hashtag(BaseModel):
    indices: Optional[List[int]] = None
    text: Optional[str] = None


class UrlEntity(BaseModel):
    display_url: Optional[str] = None
    expanded_url: Optional[str] = None
    indices: Optional[List[int]] = None
    url: Optional[str] = None


class UserMention(BaseModel):
    id_str: Optional[str] = None
    name: Optional[str] = None
    screen_name: Optional[str] = None


class TweetEntities(BaseModel):
    hashtags: Optional[List[Hashtag]] = None
    urls: Optional[List[UrlEntity]] = None
    user_mentions: Optional[List[UserMention]] = None


class Tweet(BaseModel):
    type: Optional[str] = None
    id: Optional[str] = None
    url: Optional[str] = None
    text: Optional[str] = None
    source: Optional[str] = None
    retweetCount: Optional[int] = None
    replyCount: Optional[int] = None
    likeCount: Optional[int] = None
    quoteCount: Optional[int] = None
    viewCount: Optional[int] = None
    createdAt: Optional[str] = None
    lang: Optional[str] = None
    bookmarkCount: Optional[int] = None
    isReply: Optional[bool] = None
    inReplyToId: Optional[str] = None
    conversationId: Optional[str] = None
    inReplyToUserId: Optional[str] = None
    inReplyToUsername: Optional[str] = None
    author: Optional[TwitterUser] = None
    entities: Optional[TweetEntities] = None
    quoted_tweet: Optional[dict] = None
    retweeted_tweet: Optional[dict] = None


class TweetsResponse(BaseModel):
    tweets: Optional[List[Tweet]] = None
    has_next_page: Optional[bool] = None
    next_cursor: Optional[str] = None
    status: Optional[str] = None
    message: Optional[str] = None


@mcp.tool("search_user_by_name")
async def search_user_by_name(name: str) -> TwitterUser:
    url = f"{api_base}/user/info"
    headers = {"X-API-Key": api_key}
    querystring = {"userName": name}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        response_data = response.json()
        # 使用 model_validate 并关闭严格验证
        return TwitterUserResponse(**response_data).data


@mcp.resource("resource://twitter/user/{user_id}/latest_tweets")
async def get_user_latest_tweets(user_id: str) -> List[Tweet]:
    url = f"{api_base}/user/last_tweets"
    headers = {"X-API-Key": api_key}
    querystring = {"userId": user_id}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        response_data = response.json()
        with open("response_data.json", "w") as f:
            pass
            # f.write(str(response.content))
        # 使用 model_validate 并关闭严格验证
        return TweetsResponse(**response_data).tweets


if __name__ == "__main__":
    # Example usage
    async def main():
        try:
            # Test user search
            user = await search_user_by_name("realDonaldTrump")
            if user is None:
                print("User not found")
                return

            print(f"User found: {user.userName}, {user.id}")
            # Test getting latest tweets
            tweets = await get_user_latest_tweets(user.id)
            print(f"Found {len(tweets)} tweets")

        except Exception as e:
            print(f"Error: {e}")

    asyncio.run(main())
