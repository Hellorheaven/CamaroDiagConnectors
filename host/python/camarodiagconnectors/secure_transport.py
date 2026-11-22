"""Host-side reference TLS 1.3 transport, for isolated simulation only.

Use independently provisioned trust anchors and unique endpoint certificates.
No automatic trust, fallback, or application data before handshake succeeds.
This is not the USB/ESP32 implementation, and does not authorize ECU access.
"""
import ssl

def client_context(*, ca_file, cert_file, key_file):
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_3
    ctx.maximum_version = ssl.TLSVersion.TLSv1_3
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.check_hostname = True
    ctx.load_verify_locations(cafile=ca_file)
    ctx.load_cert_chain(certfile=cert_file, keyfile=key_file)
    ctx.options |= ssl.OP_NO_COMPRESSION
    ctx.set_alpn_protocols(["camarodiag-discovery/1"])
    return ctx

def server_context(*, ca_file, cert_file, key_file):
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_3
    ctx.maximum_version = ssl.TLSVersion.TLSv1_3
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.load_verify_locations(cafile=ca_file)
    ctx.load_cert_chain(certfile=cert_file, keyfile=key_file)
    ctx.options |= ssl.OP_NO_COMPRESSION
    ctx.num_tickets = 0
    ctx.set_alpn_protocols(["camarodiag-discovery/1"])
    return ctx

def _wrap(context, stream, *, expected_name=None, server=False):
    if not server and (not isinstance(expected_name, str) or not expected_name.strip()):
        raise ValueError("Provisioned connector identity required")
    if context.minimum_version != ssl.TLSVersion.TLSv1_3 or context.maximum_version != ssl.TLSVersion.TLSv1_3:
        raise ValueError("TLS 1.3 required")
    if context.verify_mode != ssl.CERT_REQUIRED or (not server and not context.check_hostname):
        raise ValueError("Mutual certificate verification required")
    wrapped = context.wrap_socket(stream, server_side=server,
                                  server_hostname=None if server else expected_name)
    try:
        if wrapped.version() != "TLSv1.3" or wrapped.selected_alpn_protocol() != "camarodiag-discovery/1":
            raise ssl.SSLError("Unexpected TLS application protocol")
        if not wrapped.getpeercert():
            raise ssl.SSLError("Peer certificate missing")
        return wrapped
    except BaseException:
        wrapped.close()
        raise

def connect(context, stream, expected_name):
    return _wrap(context, stream, expected_name=expected_name)

def accept(context, stream):
    # Trust anchor must be dedicated to authorized host identities.
    # Application roles and individual revocation still need implementation.
    return _wrap(context, stream, server=True)
