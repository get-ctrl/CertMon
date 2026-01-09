import asyncio
import psycopg
import ssl

certsh_conn_str = "postgresql://guest@crt.sh:5432/certwatch"
sql_query_last = "SELECT * FROM certificate c ORDER BY c.ID DESC LIMIT 8000"
sql_query_since = "SELECT * FROM certificate c WHERE c.ID > {} ORDER BY c.ID DESC LIMIT 8000"

class CertMon:
    
    def __init__(self, callback):
        self.callback = callback
        self.running = False
        self.lastid = -1
        self.interval = 0.01
    
    async def connect(self):
        self.client = psycopg.connect(certsh_conn_str, autocommit=True, prepare_threshhold=None)
        self.cur = self.client.cursor()
    
    async def disconnect(self):
        self.client.close()
    
    async def query(self, query_str):
        self.cur.execute(query_str)
        results = self.cur.fetchall()
        for entry in results:
            self.lastid = entry[0]
            await self.callback(entry)
            await asyncio.sleep(self.interval)
    
    async def start(self):
        self.running = True
        await self.query(sql_query_last)
        while self.running:
            try:
                query_str = sql_query_since.format(self.lastid)
                await self.query(query_str)
            except Exception as ex:
                print(ex)
                await self.disconnect()
                await asyncio.sleep(5)
                await self.connect()
        
    async def stop(self):
        await self.disconnect()
        self.running = False
