<h2>CertMon</h2>
<span>Provides a simple crt.sh certificate scanner using a callback system. Allows continuous scanning of crt.sh's certificate transparency records.</span>
<hr/>
<h3>Requirements</h3>
<span>asyncio, psycopg, psycopg-binary</span>
<hr/>
<h3>Example</h3>

```py
import asyncio
from certmon import CertMon

async def callback(entry):
    cert_id = entry[0]
    cert_binary = entry[2]
    print(cert_id)

async def main():
    mon = CertMon(callback)
    await mon.connect()
    await mon.start()

if __name__ == '__main__':
    asyncio.run(main())
```
