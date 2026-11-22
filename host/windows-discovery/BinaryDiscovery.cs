using System.Buffers.Binary;
using System.Text;

namespace CamaroDiagConnectors.Windows;

internal sealed class BinaryDiscovery(Stream stream, Func<long>? clockMs = null)
{
    private bool used;
    private const int ReplyBudgetMs = 3000;
    private readonly Func<long> now = clockMs ?? (() => Environment.TickCount64);
    private static readonly string[] Expected =
    [
        "PONG CamaroDiagConnectors 0.1.0",
        "CAPS hs_can=disabled sw_can=disabled eeprom_read=disabled eeprom_write=disabled ecu_flash=disabled j2534=disabled",
        "STATUS mode=prototype write=disabled"
    ];

    internal static uint Crc32(ReadOnlySpan<byte> bytes)
    {
        uint crc = 0xffffffff;
        foreach (var value in bytes)
        {
            crc ^= value;
            for (int i=0;i<8;i++)
                crc = (crc >> 1) ^ ((crc & 1) != 0 ? 0xedb88320u : 0u);
        }
        return crc ^ 0xffffffff;
    }

    internal static byte[] Encode(byte op, ushort seq, ReadOnlySpan<byte> payload)
    {
        if (op is < 1 or > 3 || payload.Length > 4096)
            throw new ArgumentException("Invalid discovery frame");
        var buffer = new byte[payload.Length+12];
        buffer[0]=(byte)'C'; buffer[1]=(byte)'D'; buffer[2]=1; buffer[3]=op;
        BinaryPrimitives.WriteUInt16LittleEndian(buffer.AsSpan(4),seq);
        BinaryPrimitives.WriteUInt16LittleEndian(buffer.AsSpan(6),(ushort)payload.Length);
        payload.CopyTo(buffer.AsSpan(8));
        BinaryPrimitives.WriteUInt32LittleEndian(buffer.AsSpan(buffer.Length-4),Crc32(buffer.AsSpan(0,buffer.Length-4)));
        return buffer;
    }

    private int Remaining(long since)
    {
        long elapsed = now() - since;
        if (elapsed < 0 || elapsed >= ReplyBudgetMs)
            throw new TimeoutException("Discovery response deadline exceeded");
        return ReplyBudgetMs - (int)elapsed;
    }

    private void ReadBounded(Span<byte> buffer, long since)
    {
        while (!buffer.IsEmpty)
        {
            int remaining = Remaining(since);
            if (stream.CanTimeout)
                stream.ReadTimeout = remaining;
            int count = stream.Read(buffer);
            if (count <= 0 || count > buffer.Length)
                throw new IOException("Incomplete discovery reply");
            Remaining(since);
            buffer = buffer[count..];
        }
    }

    private string Exchange(byte op, ushort seq)
    {
        long since = now();
        if (stream.CanTimeout)
            stream.WriteTimeout = Remaining(since);
        stream.Write(Encode(op,seq,ReadOnlySpan<byte>.Empty));
        stream.Flush();
        Span<byte> header=stackalloc byte[8];
        ReadBounded(header, since);
        if (header[0]!='C'||header[1]!='D'||header[2]!=1||header[3]!=op||
            BinaryPrimitives.ReadUInt16LittleEndian(header[4..])!=seq)
            throw new IOException("Unexpected discovery response");
        var length=BinaryPrimitives.ReadUInt16LittleEndian(header[6..]);
        if(length is < 1 or > 244) throw new IOException("Invalid discovery length");
        var frame=new byte[length+12];
        header.CopyTo(frame);
        ReadBounded(frame.AsSpan(8), since);
        if(BinaryPrimitives.ReadUInt32LittleEndian(frame.AsSpan(length+8))!=Crc32(frame.AsSpan(0,length+8)))
            throw new IOException("Invalid discovery CRC");
        for (int i=8;i<length+8;i++)
            if(frame[i] is < 32 or > 126)throw new IOException("Nonprintable discovery response");
        var text=Encoding.ASCII.GetString(frame,8,length);
        if(text!=Expected[op-1])throw new IOException("Unexpected identity, capabilities or status");
        return text;
    }

    internal string[] Verify()
    {
        if(used)throw new IOException("Fresh prototype session required");
        used=true; // one attempt only, even on failure
        return [Exchange(1,0),Exchange(2,1),Exchange(3,2)];
    }
}
