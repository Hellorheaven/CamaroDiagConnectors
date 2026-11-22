"""Host-side reference TLS 1.3 transport, for isolated simulation only.

Use independently provisioned trust anchors and unique endpoint certificates.
No automatic trust, fallback, or application data before handshake succeeds.
This is not the USB/ESP32 implementation, and does not authorize ECU access.
"""
import ssl
import hashlib
import hmac
import re

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

def _pins(values):
    # An empty set means deny all. Never trust all CA-issued certificates
    # merely because an operator has removed the last authorized endpoint.
    if isinstance(values, (str, bytes)):
        raise ValueError("Provide an explicit collection of certificate fingerprints")
    result = tuple(values)
    if not result or any(not isinstance(v, str) or not re.fullmatch(r"[0-9a-f]{64}", v) for v in result):
        raise ValueError("Provisioned SHA-256 certificate fingerprints required")
    return result

def _wrap(context, stream, *, allowed_peer_sha256, expected_name=None, server=False):
    pins = _pins(allowed_peer_sha256)
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
        if wrapped.session_reused:
            raise ssl.SSLError("Resumed sessions are not accepted by this prototype")
        peer = wrapped.getpeercert(binary_form=True)
        if not peer:
            raise ssl.SSLError("Peer certificate missing")
        fingerprint = hashlib.sha256(peer).hexdigest()
        if not any(hmac.compare_digest(fingerprint, pin) for pin in pins):
            raise ssl.SSLError("Peer is not present in the local authorization registry")
        return wrapped
    except BaseException:
        wrapped.close()
        raise

def connect(context, stream, expected_name, *, device_sha256):
    return _wrap(context, stream, expected_name=expected_name,
                 allowed_peer_sha256=(device_sha256,))

def accept(context, stream, *, allowed_host_sha256):
    # Registry snapshot is supplied locally for every new session. Removing a
    # fingerprint denies future sessions, even for an otherwise trusted CA.
    # Active session revocation and roles are not implemented here.
    return _wrap(context, stream, server=True,
                 allowed_peer_sha256=allowed_host_sha256)
