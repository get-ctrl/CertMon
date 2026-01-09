import asyncio
#import ssl

from cryptography import x509

from certmon import CertMon

FLAG_CN = x509.oid.NameOID.COMMON_NAME
FLAG_SAN = x509.SubjectAlternativeName
FLAG_DNS = x509.DNSName

def x509_decode(cert_binary):
    return x509.load_der_x509_certificate(cert_binary)

def x509_get_subjectNames(cert):
    domains = []
    try:
        cn = cert.subject.get_attributes_for_oid(FLAG_CN)
        san = cert.extensions.get_extension_for_class(FLAG_SAN)
        if cn: domains.append(cn[0].value)
        for name in san.value.get_values_for_type(FLAG_DNS):
            domains.append(name)
    except:
        pass
    return domains

async def callback(entry):
    cert = x509_decode(entry[2])
    domains = x509_get_subjectNames(cert)
    print(str(entry[0]) + " " + ", ".join(domains))

async def main():
    mon = CertMon(callback)
    await mon.connect()
    await mon.start()

if __name__ == '__main__':
    asyncio.run(main())
