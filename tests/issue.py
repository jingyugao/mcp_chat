import asyncio
from typing import Any
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("twitter", host="127.0.0.1", port=9999)

@mcp.resource("resource://${file_name}/content")
async def get_file_content(file_name: str):
    """Get the File Content
    """

    return "Hello, world!"


@mcp.resource("resource://files")
async def get_file_list():
    """Get the list of files in the directory.
    return: list of file names
    """
    return ["1.txt","2.txt"]


if __name__ == "__main__":
    resource_templates = asyncio.run(mcp.list_resource_templates())
    print(resource_templates[0].description) # Get the File Content
    print(resource_templates[0]) # Get the File Content

    resources = asyncio.run(mcp.list_resources())
    print(resources[0].description) # None


