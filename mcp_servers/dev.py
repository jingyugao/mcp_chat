




import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client

class mcp_client:
    def __init__(self,sse_url:str):
        self.sse_url=sse_url
        self.inited = asyncio.Event()
        self.closing = asyncio.Event()
        self.session :ClientSession= None
        
    def connect(self):
        asyncio.create_task(self.__connect())
        return self.inited
        
    async def __connect(self):
        async with sse_client(self.sse_url) as client:
            async with ClientSession(*client) as session:
                await session.initialize()
                await asyncio.sleep(2)
                self.session = session
                self.inited.set()
                await self.closing.wait()
            
    def close(self):
        self.closing.set()

	
 
    async def list_tools(self) -> None:
        async with sse_client(self.sse_url) as client:
            async with ClientSession(*client) as session:
                await session.initialize()
                tools=await session.list_tools()
                return tools
       


async def main():
    client=mcp_client("http://127.0.0.1:9999/sse")
    client.connect()
    tools=await client.list_tools()
    print(tools)
    client.close()



if __name__=="__main__":
    asyncio.run(main())
