import asyncio
from re import T
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

# Initialize FastMCP server
mcp = FastMCP("twitter", host="127.0.0.1", port=9999)


class Tweet(BaseModel):
    content: str
    author: str
    created_at: str


@mcp.resource("resource://twitter/{user_name}/last_tweets")
async def get_last_tweets(user_name: str):
    """Get the last tweets from Twitter.
    Args:
            user_name: The name of the user to get the tweets from
    """

    return [Tweet(content="Hello, world!", author="John Doe", created_at="2021-01-01")]


@mcp.resource("resource://translate/supported_languages")
async def get_supported_languages():
    """Get the supported languages for translation.
    
    return: list of supported languages
    """
    return ["en", "zh"]


@mcp.tool()
async def translate(language: str, text: str):
    """Translate text to a given language.
    Args:
            language: The language to translate to
            text: The text to translate
    """
    return f"translated {text} to {language}"

@mcp.prompt()
async def translate_user_tweets(user_name: str,language: str):
    """Translate a user's tweets to a given language.
    Args:
            user_name: The name of the user to translate the tweets of
            language: The language to translate to
    """
    tweets = await get_last_tweets(user_name)
    return [
        {
            "role": "user",
            "content": f"Translate the following tweets to {language}: {tweets}",
        }
    ]


if __name__ == "__main__":
    resources = asyncio.run(mcp.list_resource_templates())
    for resource in resources:
        print(resource.description,resource.name,resource.uriTemplate)

    resources = asyncio.run(mcp.list_resources())
    for resource in resources:
        print(resource.description,resource.name,resource.uri)

    # Initialize and run the server
    mcp.run(transport="sse")
