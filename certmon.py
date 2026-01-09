import asyncio
import psycopg
import ssl

certsh_conn_str = "postgresql://guest@crt.sh:5432/certwatch"
sql_query_last = "SELECT * FROM certificate ORDER BY id DESC LIMIT 1000"
sql_query_since = "SELECT * FROM certificate c WHERE c.ID > {} ORDER BY c.ID DESC LIMIT 1000"

class CertMon:
    
    def __init__(self, callback):
        self.callback = callback
        self.running = False
        self.interval = 0.01
        self.lastid = -1
    
    async def connect(self):
        self.client = psycopg.connect(certsh_conn_str, autocommit=True)
    
    async def run(self):
        self.running = True
        cur = self.client.cursor()
        
        cur.execute(sql_query_last)
        results = cur.fetchall()
        await self.dispatch_messages(results)
        
        while self.running:
            try:
                if self.lastid == -1:
                    raise Exception("Last id was not set on initial query")
                
                query = sql_query_since.format(self.lastid)
                cur.execute(query)
                results = cur.fetchall()
                
                await self.dispatch_messages(results)
            except Exception as ex:
                print(ex)
                await asyncio.sleep(10)
        
    async def stop(self):
        self.running = False
    
    async def dispatch_messages(self, results):
        self.lastid = results[0][0]
        for result in results:
            self.dispatch_message(result)
            await asyncio.sleep(self.interval)
    
    def dispatch_message(self, entry):
        if not entry: return
        self.lastid = entry[0]
        self.callback(entry)
