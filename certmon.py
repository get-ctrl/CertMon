import asyncio
import psycopg
import ssl
import sys

CONN_STR_CRTSH = "postgresql://guest@crt.sh:5432/certwatch"
QUERY_STR_LAST = "SELECT * FROM certificate c ORDER BY c.ID DESC LIMIT 1000"
QUERY_STR_SINCE = "SELECT * FROM certificate c WHERE c.ID > {} ORDER BY c.ID ASC LIMIT 2000"

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class CertEntry:
    
    def __init__(self, entry):
        if not entry: return
        if len(entry) < 3: return
        self.id = entry[0]
        self.binary = entry[2]

class CertMon:
    
    def __init__(self, callback):
        self.callback = callback
        self.running = False
        self.lastid = -1
        self.request_interval = 1
        self.return_interval = 0.03
        self.max_pages = 4
        self.pages = asyncio.Queue(maxsize = self.max_pages)
        self.conn = None
        self.request_task = None
        self.verbose = False
    
    async def connect(self):
        try:
            self.conn = await psycopg.AsyncConnection.connect(CONN_STR_CRTSH, autocommit=True, prepare_threshold=None)
            await asyncio.sleep(1)
            if self.verbose: print("connected")
        except Exception as ex:
            print("Connect", ex)
    
    async def disconnect(self):
        if not self.conn: return
        try:
            await self.conn.close()
            await asyncio.sleep(1)
            if self.verbose: print("disconnected")
        except Exception as ex:
            print("Disconnect", ex)
    
    async def reconnect(self):
        await self.disconnect()
        await self.connect()
        if self.verbose: print("reconnected")
    
    async def query(self, query_str):
        async with self.conn.cursor() as cur:
            await cur.execute(query_str)
            return await cur.fetchall()
    
    async def query_latest(self):
        if self.pages.full(): return
        results = await self.query(QUERY_STR_LAST)
        results.reverse()
        await self.page_results(results)
    
    async def query_since(self):
        if self.pages.full(): return
        query_str = QUERY_STR_SINCE.format(self.lastid)
        results = await self.query(query_str)
        await self.page_results(results)
    
    async def page_results(self, results):
        if not results: return
        reslen = len(results)
        self.lastid = results[reslen - 1][0]
        await self.pages.put(results)
        if self.verbose: print("paged", str(reslen))
    
    async def dispatch(self, page):
        for entry in page:
            try:
                wrapped = CertEntry(entry)
                await self.callback(wrapped)
                #await self.callback(CertEntry(entry))
            except Exception as ex:
                print("Callback", ex)
            await asyncio.sleep(self.return_interval)
        if self.verbose: print("dispatched", str(len(page)))
    
    async def request_loop(self):
        await self.query_latest()
        while self.running:
            await asyncio.sleep(self.request_interval)
            try:
                await self.query_since()
            except Exception as ex:
                print("Request", ex)
                await self.reconnect()
    
    async def return_loop(self):
        while self.running:
            if self.pages.empty():
                await asyncio.sleep(1)
                continue
            page = await self.pages.get()
            await self.dispatch(page)
            if self.verbose: print("Dispatched", str(len(page)))
    
    async def start(self):
        self.running = True
        self.request_task = asyncio.create_task(self.request_loop())
        try:
            await self.return_loop()
        finally:
            self.request_task.cancel()
        
    async def stop(self):
        self.running = False
        if self.request_task: self.request_task.cancel()
        await self.disconnect()
