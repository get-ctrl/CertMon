import asyncio
import psycopg
import ssl
import sys

CONN_STR_CRTSH = "postgresql://guest@crt.sh:5432/certwatch"
QUERY_STR_LAST = "SELECT * FROM certificate c ORDER BY c.ID DESC LIMIT 1000"
QUERY_STR_SINCE = "SELECT * FROM certificate c WHERE c.ID > {} ORDER BY c.ID ASC LIMIT 1000"

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class CertMon:
    
    def __init__(self, callback):
        self.callback = callback
        self.running = False
        self.lastid = -1
        self.interval = 0.01
    
    async def connect(self):
        self.conn = await psycopg.AsyncConnection.connect(CONN_STR_CRTSH, autocommit=True, prepare_threshold=None)
        self.cur = self.conn.cursor()
    
    async def disconnect(self):
        if self.conn: self.conn.close()
    
    async def reconnect(self):
        await self.disconnect()
        await asyncio.sleep(5)
        await self.connect()
    
    async def query(self, query_str):
        await self.cur.execute(query_str)
        return await self.cur.fetchall()
    
    async def query_latest(self):
        results = await self.query(QUERY_STR_LAST)
        results.reverse()
        await self.dispatch(results)
    
    async def query_since(self):
        query_str = QUERY_STR_SINCE.format(self.lastid)
        results = await self.query(query_str)
        await self.dispatch(results)
    
    async def dispatch(self, results):
        for entry in results:
            await self.callback(entry)
            entry_id = entry[0]
            self.lastid = entry_id
            await asyncio.sleep(self.interval)
    
    async def start(self):
        self.running = True
        await self.query_latest()
        while self.running:
            try:
                await self.query_since()
            except Exception as ex:
                print(ex)
                await self.reconnect()
        
    async def stop(self):
        self.running = False
        await self.disconnect()
