using System.Net.Security;
using System.Security.Authentication;
using System.Security.Cryptography;
using System.Security.Cryptography.X509Certificates;

namespace CamaroDiagConnectors.Windows;

/// <summary>Isolated TLS 1.3 IP reference. No USB or vehicle command, no bridge listener.
/// Trust anchors and client identities must be locally provisioned.</summary>
internal sealed class ConnectorTlsReference
{
    internal const string Alpn = "camarodiag-discovery/1";
    private readonly string deviceName;
    private readonly byte[] devicePin;
    private readonly byte[] hostPin;

    internal ConnectorTlsReference(string name, string deviceSha256, string hostSha256)
    {
        if (string.IsNullOrWhiteSpace(name) || name != name.Trim())
            throw new ArgumentException("Provisioned connector name required");
        deviceName = name;
        devicePin = DecodePin(deviceSha256);
        hostPin = DecodePin(hostSha256);
    }

    private static byte[] DecodePin(string value)
    {
        if (value.Length != 64 || value.Any(c => !(c is >= '0' and <= '9' or >= 'a' and <= 'f')))
            throw new ArgumentException("Explicit lowercase certificate SHA-256 required");
        return Convert.FromHexString(value);
    }

    private static void CheckPin(byte[] expected, byte[]? der)
    {
        if (der is null || der.Length == 0 ||
            !CryptographicOperations.FixedTimeEquals(expected, SHA256.HashData(der)))
            throw new AuthenticationException("Unprovisioned connector or host certificate");
    }

    // Post-handshake policy only, never a replacement for chain or name validation.
    internal void CheckNegotiatedIdentity(SslProtocols protocol, string alpn,
        bool mutual, byte[]? remoteDer, byte[]? localDer)
    {
        if (protocol != SslProtocols.Tls13 || alpn != Alpn || !mutual)
            throw new AuthenticationException("Unexpected connector TLS protocol or missing mutual authentication");
        CheckPin(devicePin, remoteDer);
        CheckPin(hostPin, localDer);
    }

    internal async Task<SslStream> AuthenticateIsolatedStreamAsync(Stream transport,
        X509Certificate2 deviceCa, X509Certificate2 localCertificate, CancellationToken cancellationToken = default)
    {
        // Caller owns the stream until this method is invoked. Once wrapped,
        // the TLS stream owns it; any failure closes it without application I/O.
        var tls = new SslStream(transport, leaveInnerStreamOpen: false);
        try
        {
            if (!localCertificate.HasPrivateKey)
                throw new AuthenticationException("Local client private key required");
            CheckPin(hostPin, localCertificate.RawData);
            if (!deviceCa.Extensions.OfType<X509BasicConstraintsExtension>().Any(e => e.CertificateAuthority))
                throw new AuthenticationException("Dedicated device CA required");

            var policy = new X509ChainPolicy
            {
                TrustMode = X509ChainTrustMode.CustomRootTrust,
                RevocationMode = X509RevocationMode.NoCheck, // offline reference: exact local pin registry
                VerificationFlags = X509VerificationFlags.NoFlag,
                DisableCertificateDownloads = true
            };
            policy.CustomTrustStore.Add(deviceCa);
            policy.ApplicationPolicy.Add(new Oid("1.3.6.1.5.5.7.3.1")); // serverAuth
            var options = new SslClientAuthenticationOptions
            {
                TargetHost = deviceName,
                ClientCertificates = new X509CertificateCollection { localCertificate },
                CertificateChainPolicy = policy,
                EnabledSslProtocols = SslProtocols.Tls13,
                ApplicationProtocols = [new SslApplicationProtocol(Alpn)],
                AllowRenegotiation = false,
                AllowTlsResume = false
            };
            using var deadline = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
            deadline.CancelAfter(TimeSpan.FromSeconds(3));
            await tls.AuthenticateAsClientAsync(options, deadline.Token).ConfigureAwait(false);
            CheckNegotiatedIdentity(tls.SslProtocol, tls.NegotiatedApplicationProtocol.ToString(),
                tls.IsMutuallyAuthenticated, tls.RemoteCertificate?.GetRawCertData(),
                tls.LocalCertificate?.GetRawCertData());
            return tls;
        }
        catch
        {
            await tls.DisposeAsync().ConfigureAwait(false);
            throw;
        }
    }
}
