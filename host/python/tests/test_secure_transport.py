import concurrent.futures
import shutil
import socket
import ssl
import subprocess
import tempfile
import unittest
from pathlib import Path

from camarodiagconnectors.secure_transport import client_context, server_context, connect, accept

@unittest.skipUnless(shutil.which("openssl") and ssl.HAS_TLSv1_3,
                     "OpenSSL command and TLS 1.3 required")
class SecureTransportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.root=Path(cls.tmp.name)
        def openssl(*args):
            subprocess.run(["openssl",*args],cwd=cls.root,check=True,
                           stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=30)
        for name in ("host-ca","device-ca","foreign-ca"):
            openssl("req","-x509","-newkey","rsa:2048","-nodes","-days","1",
                    "-subj","/CN="+name,"-keyout",name+".key","-out",name+".crt",
                    "-addext","basicConstraints=critical,CA:TRUE",
                    "-addext","keyUsage=critical,keyCertSign,cRLSign")
        for name,ca,usage in (("connector","device-ca","serverAuth"),
                              ("host","host-ca","clientAuth"),
                              ("foreign","foreign-ca","clientAuth")):
            openssl("req","-newkey","rsa:2048","-nodes","-subj","/CN="+name,
                    "-keyout",name+".key","-out",name+".csr")
            ext=cls.root/(name+".ext")
            ext.write_text("basicConstraints=CA:FALSE\nextendedKeyUsage="+usage+
                           "\nkeyUsage=digitalSignature\nsubjectAltName=DNS:"+name+"\n")
            openssl("x509","-req","-in",name+".csr","-CA",ca+".crt",
                    "-CAkey",ca+".key","-CAcreateserial","-days","1",
                    "-extfile",ext.name,"-out",name+".crt")
    def server(self):
        p=self.root
        return server_context(ca_file=p/"host-ca.crt",cert_file=p/"connector.crt",key_file=p/"connector.key")
    def client(self,who="host"):
        p=self.root
        return client_context(ca_file=p/"device-ca.crt",cert_file=p/(who+".crt"),key_file=p/(who+".key"))
    def exchange(self,client,server,name="connector",expect_success=True):
        a,b=socket.socketpair()
        with a,b,concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            a.settimeout(3); b.settimeout(3)
            def worker():
                with accept(server,a) as stream:
                    self.assertEqual(stream.recv(1),b"P")
                    stream.sendall(b"Q")
            future=pool.submit(worker)
            try:
                with connect(client,b,name) as stream:
                    stream.sendall(b"P")
                    self.assertEqual(stream.recv(1),b"Q")
                future.result(timeout=5)
                if not expect_success:
                    self.fail("Unauthorized TLS session succeeded")
            except (ssl.SSLError,OSError,ValueError) as exc:
                if expect_success:
                    raise
                with self.assertRaises((ssl.SSLError,OSError,ValueError)):
                    future.result(timeout=5)
    def test_mutual_auth(self):
        self.exchange(self.client(),self.server())
    def test_wrong_device_identity(self):
        self.exchange(self.client(),self.server(),"wrong",False)
    def test_untrusted_host_certificate(self):
        self.exchange(self.client("foreign"),self.server(),expect_success=False)
    def test_missing_host_certificate(self):
        ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.minimum_version=ctx.maximum_version=ssl.TLSVersion.TLSv1_3
        ctx.load_verify_locations(cafile=self.root/"device-ca.crt")
        ctx.set_alpn_protocols(["camarodiag-discovery/1"])
        self.exchange(ctx,self.server(),expect_success=False)
    def test_wrong_alpn(self):
        ctx=self.client()
        ctx.set_alpn_protocols(["other/1"])
        self.exchange(ctx,self.server(),expect_success=False)
    def test_refuse_downgrade_configuration(self):
        ctx=self.client()
        ctx.minimum_version=ssl.TLSVersion.TLSv1_2
        with socket.socket() as sock, self.assertRaises(ValueError):
            connect(ctx,sock,"connector")
