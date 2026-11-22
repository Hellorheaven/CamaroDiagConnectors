package com.camarodiag.connectors;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.zip.CRC32;
import java.util.function.LongSupplier;
import java.net.SocketTimeoutException;

/** Public discovery protocol only. No authentication or ECU commands. */
public final class BinaryDiscovery implements AutoCloseable {
    public interface Link extends AutoCloseable {
        int read(byte[] buffer,int offset,int count,int timeoutMs) throws IOException;
        void write(byte[] buffer,int timeoutMs) throws IOException;
        default void checkNoBufferedInput() throws IOException {}
        @Override void close() throws IOException;
    }
    private static final String[] EXPECTED = {
        "PONG CamaroDiagConnectors 0.1.0",
        "CAPS hs_can=disabled sw_can=disabled eeprom_read=disabled eeprom_write=disabled ecu_flash=disabled j2534=disabled",
        "STATUS mode=prototype write=disabled"
    };
    private final Link link;
    private final LongSupplier clockMs;
    private int sequence;
    private boolean closed;
    public BinaryDiscovery(Link link) { this(link, () -> System.nanoTime()/1_000_000L); }
    BinaryDiscovery(Link link,LongSupplier clockMs){
        this.link=java.util.Objects.requireNonNull(link);
        this.clockMs=java.util.Objects.requireNonNull(clockMs);
    }
    private int remaining(long since)throws IOException{
        long elapsed=clockMs.getAsLong()-since;
        if(elapsed<0||elapsed>=3000)throw new SocketTimeoutException("Discovery response deadline exceeded");
        return (int)(3000-elapsed);
    }
    private static int u(byte b) { return b&255; }
    private static long crc(byte[] data,int length) {
        CRC32 c=new CRC32(); c.update(data,0,length); return c.getValue();
    }
    private static void putCrc(byte[] data) {
        long c=crc(data,data.length-4);
        for(int i=0;i<4;i++)data[data.length-4+i]=(byte)(c>>(8*i));
    }
    private byte[] readExactly(int length,long since) throws IOException {
        byte[] data=new byte[length];
        int offset=0;
        while(offset<length) {
            int count=link.read(data,offset,length-offset,remaining(since));
            remaining(since);
            if(count<=0||count>length-offset)throw new IOException("Truncated discovery response");
            offset+=count;
        }
        return data;
    }
    private String exchange(int op) throws IOException {
        if(closed)throw new IOException("Closed discovery session");
        byte[] request={'C','D',1,(byte)op,(byte)sequence,(byte)(sequence>>8),0,0,0,0,0,0};
        putCrc(request);
        long since=clockMs.getAsLong();
        link.write(request,remaining(since));
        byte[] head=readExactly(8,since);
        if(head[0]!='C'||head[1]!='D'||head[2]!=1||u(head[3])!=op
           ||(u(head[4])|(u(head[5])<<8))!=sequence)
            throw new IOException("Unexpected discovery header");
        int length=u(head[6])|(u(head[7])<<8);
        if(length<1||length>244)throw new IOException("Invalid reply length");
        byte[] tail=readExactly(length+4,since);
        link.checkNoBufferedInput();
        remaining(since);
        byte[] combined=new byte[8+length+4];
        System.arraycopy(head,0,combined,0,8);
        System.arraycopy(tail,0,combined,8,tail.length);
        long received=0;
        for(int i=0;i<4;i++)received|=(long)u(tail[length+i])<<(8*i);
        if(received!=crc(combined,combined.length-4))throw new IOException("CRC mismatch");
        for(int i=0;i<length;i++)if(u(tail[i])<32||u(tail[i])>126)
            throw new IOException("Nonprintable reply");
        String text=new String(tail,0,length,StandardCharsets.US_ASCII);
        if(!EXPECTED[op-1].equals(text))throw new IOException("Unexpected identity or capabilities");
        sequence++;
        return text;
    }
    /** A single public discovery session, never a device authentication proof. */
    public synchronized String[] verify() throws IOException {
        if(closed||sequence!=0)throw new IOException("Fresh device session required");
        try {
            return new String[]{exchange(1),exchange(2),exchange(3)};
        } finally {
            close();
        }
    }
    @Override public synchronized void close() throws IOException {
        if(!closed){closed=true;link.close();}
    }
}
