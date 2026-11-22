using System.Security.Authentication;
using System.Security.Cryptography;

namespace CamaroDiagConnectors.Windows;

internal static class ConnectorTlsReferenceSelfTests
{
    internal static void Run()
    {
        static string Pin(byte[] bytes) => Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();
        static void MustReject(Action action)
        {
            try { action(); }
            catch (AuthenticationException) { return; }
            throw new InvalidOperationException("TLS reference accepted invalid negotiated identity");
        }

        // Synthetic byte strings for pin policy only, not certificates or secrets.
        byte[] device = [1, 2, 3], host = [4, 5, 6];
        var reference = new ConnectorTlsReference("connector", Pin(device), Pin(host));
        reference.CheckNegotiatedIdentity(SslProtocols.Tls13, ConnectorTlsReference.Alpn, true, device, host);
        MustReject(() => reference.CheckNegotiatedIdentity(SslProtocols.Tls12, ConnectorTlsReference.Alpn, true, device, host));
        MustReject(() => reference.CheckNegotiatedIdentity(SslProtocols.Tls13, "other/1", true, device, host));
        MustReject(() => reference.CheckNegotiatedIdentity(SslProtocols.Tls13, ConnectorTlsReference.Alpn, false, device, host));
        MustReject(() => reference.CheckNegotiatedIdentity(SslProtocols.Tls13, ConnectorTlsReference.Alpn, true, host, device));
        MustReject(() => reference.CheckNegotiatedIdentity(SslProtocols.Tls13, ConnectorTlsReference.Alpn, true, null, host));
        MustReject(() => reference.CheckNegotiatedIdentity(SslProtocols.Tls13, ConnectorTlsReference.Alpn, true, device, null));
        bool invalid = false;
        try { _ = new ConnectorTlsReference("connector", "bad", Pin(host)); }
        catch (ArgumentException) { invalid = true; }
        if (!invalid) throw new InvalidOperationException("Malformed certificate digest accepted");
    }
}
