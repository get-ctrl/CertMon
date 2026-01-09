import os
import asyncio
from certmon import CertMon
from pathlib import Path

appdata_path = Path(os.getenv("APPDATA"))
certsave_path = Path(appdata_path / "CertSave")

if not os.path.exists(certsave_path):
    os.mkdir(certsave_path)

def callback(entry):
    cert_id = entry[0]
    cert = entry[2]
    
    if not cert:
        return
    
    file_name = str(cert_id) + ".der"
    file_path = Path(certsave_path / file_name)
    
    with open (file_path, "wb") as cert_file:
        cert_file.write(entry[2])
        print(file_path)

async def main():
    mon = CertMon(callback)
    await mon.connect()
    await mon.run()

if __name__ == '__main__':
    asyncio.run(main())
