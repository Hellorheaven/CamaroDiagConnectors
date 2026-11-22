using System.Text;

namespace CamaroDiagConnectors.Windows;

internal static class SelfTests
{
    private sealed class Simulation(bool corrupt, bool wrongSequence) : Stream
    {
        private byte[] reply=[];
        private int cursor;
        internal int Commands {get;private set;}
        public override bool CanRead=>true;
        public override bool CanWrite=>true;
        public override bool CanSeek=>false;
        public override long Length=>throw new NotSupportedException();
        public override long Position {get=>throw new NotSupportedException();set=>throw new NotSupportedException();}
        public override void Flush(){}
        public override long Seek(long offset,SeekOrigin origin)=>throw new NotSupportedException();
        public override void SetLength(long value)=>throw new NotSupportedException();
        public override void Write(byte[] buffer,int offset,int count)
        {
            if(count!=12||buffer[offset+3]!=Commands+1||buffer[offset+4]!=Commands)
                throw new IOException("Invalid request");
            string[] payloads=[
              "PONG CamaroDiagConnectors 0.1.0",
              "CAPS hs_can=disabled sw_can=disabled eeprom_read=disabled eeprom_write=disabled ecu_flash=disabled j2534=disabled",
              "STATUS mode=prototype write=disabled"];
            reply=BinaryDiscovery.Encode((byte)(Commands+1),(ushort)(wrongSequence?Commands+1:Commands),
                                          Encoding.ASCII.GetBytes(payloads[Commands]));
            if(corrupt)reply[8]^=1;
            cursor=0;Commands++;
        }
        public override int Read(byte[] buffer,int offset,int count)
        {
            int n=Math.Min(3,Math.Min(count,reply.Length-cursor));
            Array.Copy(reply,cursor,buffer,offset,n);cursor+=n;return n;
        }
    }
    private static void Require(bool condition)
    {
        if(!condition)throw new Exception("Self-test assertion failed");
    }
    private static void ExpectFailure(Action action)
    {
        try{action();}
        catch(IOException){return;}
        throw new Exception("Expected protocol failure");
    }
    internal static int Run()
    {
        ConnectorTlsReferenceSelfTests.Run();
        Require(BinaryDiscovery.Crc32("123456789"u8)==0xcbf43926u);
        using(var link=new Simulation(false,false))
        {
            var client=new BinaryDiscovery(link);
            Require(client.Verify().Length==3&&link.Commands==3);
            ExpectFailure(()=>client.Verify());
        }
        foreach(var bad in new[]{(true,false),(false,true)})
        {
            using var link=new Simulation(bad.Item1,bad.Item2);
            var client=new BinaryDiscovery(link);
            ExpectFailure(()=>client.Verify());
            ExpectFailure(()=>client.Verify());
            Require(link.Commands==1);
        }
        using (var slow = new Simulation(false, false))
        {
            long ticks = 0;
            var client = new BinaryDiscovery(slow, () => ticks += 500);
            bool timeout = false;
            try { client.Verify(); }
            catch (TimeoutException) { timeout = true; }
            Require(timeout && slow.Commands == 1);
            ExpectFailure(() => client.Verify());
        }
        Console.WriteLine("Windows protocol self-tests passed (simulation).");
        return 0;
    }
}
