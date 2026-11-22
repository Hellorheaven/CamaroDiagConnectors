package com.camarodiag.connectors;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.zip.CRC32;

public final class BinaryDiscoveryTest {
    private static final String[] REPLIES={
      "PONG CamaroDiagConnectors 0.1.0",
      "CAPS hs_can=disabled sw_can=disabled eeprom_read=disabled eeprom_write=disabled ecu_flash=disabled j2534=disabled",
      "STATUS mode=prototype write=disabled"};
    private static final class Sim implements BinaryDiscovery.Link {
        byte[] pending;
        int cursor,commands;
        boolean corrupt,wrongSequence,closed,trailing;
        @Override public void write(byte[] data,int timeoutMs) throws IOException {
            if(data.length!=12||data[3]!=commands+1||data[4]!=commands)
                throw new IOException("Invalid request");
            int op=data[3];
            byte[] text=REPLIES[op-1].getBytes(StandardCharsets.US_ASCII);
            pending=new byte[text.length+12];
            System.arraycopy(data,0,pending,0,8);
            if(wrongSequence)pending[4]++;
            pending[6]=(byte)text.length;
            System.arraycopy(text,0,pending,8,text.length);
            CRC32 crc=new CRC32();crc.update(pending,0,pending.length-4);
            for(int i=0;i<4;i++)pending[pending.length-4+i]=(byte)(crc.getValue()>>(8*i));
            if(corrupt)pending[8]^=1;
            if(trailing)pending=java.util.Arrays.copyOf(pending,pending.length+1);
            cursor=0;commands++;
        }
        @Override public int read(byte[] b,int off,int count,int timeoutMs){
            int len=Math.min(3,Math.min(count,pending.length-cursor));
            System.arraycopy(pending,cursor,b,off,len);cursor+=len;return len;
        }
        @Override public void checkNoBufferedInput()throws IOException{
            if(cursor!=pending.length)throw new IOException("Unexpected buffered data");
        }
        @Override public void close(){closed=true;}
    }
    public static void main(String[] args)throws Exception{
        Sim slow=new Sim();
        long[] ticks={0};
        try(BinaryDiscovery d=new BinaryDiscovery(slow,()->ticks[0]+=500)){
            try {d.verify();throw new AssertionError("Late response accepted");}
            catch(java.net.SocketTimeoutException expected){assert slow.closed&&slow.commands==1;}
        }
        Sim ok=new Sim();
        try(BinaryDiscovery d=new BinaryDiscovery(ok)){
            assert d.verify().length==3;
            assert ok.commands==3&&ok.closed;
            try {d.verify();throw new AssertionError("Reused closed session");}
            catch(IOException expected){}
        }
        for(int i=0;i<3;i++){
            Sim broken=new Sim();broken.corrupt=i==0;broken.wrongSequence=i==1;broken.trailing=i==2;
            try(BinaryDiscovery d=new BinaryDiscovery(broken)){
                try {d.verify();throw new AssertionError("Accepted invalid response");}
                catch(IOException expected){assert broken.closed&&broken.commands==1;}
            }
        }
    }
}
