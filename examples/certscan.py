import asyncio
from cryptography import x509
from certmon import CertMon

FLAG_CN = x509.oid.NameOID.COMMON_NAME

def x509_decode(cert_binary):
    return x509.load_der_x509_certificate(cert_binary)

def x509_getdomain(cert):
    cn = cert.subject.get_attributes_for_oid(FLAG_CN)
    return cn[0].value

async def callback(entry):
    cert = x509_decode(entry.binary)
    domain = x509_getdomain(cert)
    print(entry.id, domain)

async def main():
    mon = CertMon(callback)
    await mon.connect()
    await mon.start()

if __name__ == '__main__':
    asyncio.run(main())
