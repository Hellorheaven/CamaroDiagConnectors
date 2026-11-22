package com.camarodiag.connectors;

import android.hardware.usb.UsbConstants;
import android.hardware.usb.UsbDevice;
import android.hardware.usb.UsbDeviceConnection;
import android.hardware.usb.UsbEndpoint;
import android.hardware.usb.UsbInterface;
import android.hardware.usb.UsbManager;
import java.io.IOException;

/** USB Host CDC discovery for an explicitly selected isolated prototype.
 * Call off the UI thread, after Android USB permission has been granted.
 * No vendor-specific USB protocol, target access or cryptographic identity.
 */
public final class UsbDiscovery {
    private UsbDiscovery() {}
    public static String[] verify(UsbManager manager, UsbDevice selected,
                                  int controlId,int dataId) throws IOException {
        if(!manager.hasPermission(selected))throw new IOException("USB permission required");
        UsbInterface control=null,data=null;
        for(int i=0;i<selected.getInterfaceCount();i++){
            UsbInterface candidate=selected.getInterface(i);
            if(candidate.getId()==controlId && candidate.getInterfaceClass()==UsbConstants.USB_CLASS_COMM){
                if(control!=null)throw new IOException("Ambiguous CDC control");
                control=candidate;
            }
            if(candidate.getId()==dataId && candidate.getInterfaceClass()==UsbConstants.USB_CLASS_CDC_DATA){
                if(data!=null)throw new IOException("Ambiguous CDC data");
                data=candidate;
            }
        }
        if(control==null||data==null||controlId==dataId)throw new IOException("CDC interface not supported");
        UsbEndpoint in=null,out=null;
        for(int i=0;i<data.getEndpointCount();i++){
            UsbEndpoint e=data.getEndpoint(i);
            if(e.getType()!=UsbConstants.USB_ENDPOINT_XFER_BULK)continue;
            if(e.getDirection()==UsbConstants.USB_DIR_IN){
                if(in!=null)throw new IOException("Ambiguous bulk input");
                in=e;
            }else{
                if(out!=null)throw new IOException("Ambiguous bulk output");
                out=e;
            }
        }
        if(in==null||out==null)throw new IOException("Missing CDC endpoints");
        UsbDeviceConnection conn=manager.openDevice(selected);
        if(conn==null)throw new IOException("Cannot open USB device");
        boolean c=false,d=false;
        try{
            c=conn.claimInterface(control,false);
            if(!c)throw new IOException("Cannot claim control interface");
            d=conn.claimInterface(data,false);
            if(!d)throw new IOException("Cannot claim data interface");
            byte[] line={(byte)0x00,(byte)0xc2,1,0,0,0,8}; // 115200 8N1
            if(conn.controlTransfer(0x21,0x20,0,controlId,line,7,1000)!=7)
                throw new IOException("CDC line coding rejected");
            if(conn.controlTransfer(0x21,0x22,1,controlId,null,0,1000)!=0)
                throw new IOException("CDC control state rejected");
            final UsbEndpoint input=in,output=out;
            // USB bulk transfers are packet-based. Read into a sufficiently
            // large buffer to retain a whole small response, not just its header.
            BinaryDiscovery.Link link=new BinaryDiscovery.Link(){
                private final byte[] pending=new byte[4096];
                private int cursor=0,limit=0;
                @Override public int read(byte[] b,int off,int count,int timeoutMs) throws IOException{
                    if(cursor==limit){
                        limit=conn.bulkTransfer(input,pending,pending.length,Math.min(timeoutMs,1500));
                        cursor=0;
                        if(limit<=0)throw new IOException("USB disconnected or timed out");
                    }
                    int n=Math.min(count,limit-cursor);
                    System.arraycopy(pending,cursor,b,off,n);cursor+=n;return n;
                }
                @Override public void write(byte[] b,int timeoutMs)throws IOException{
                    checkNoBufferedInput();
                    if(conn.bulkTransfer(output,b,b.length,Math.min(timeoutMs,1500))!=b.length)
                        throw new IOException("USB short write or timeout");
                }
                @Override public void checkNoBufferedInput()throws IOException{
                    if(cursor!=limit)throw new IOException("Unexpected buffered USB data");
                }
                @Override public void close(){} // outer owner releases claimed interfaces
            };
            try(BinaryDiscovery discovery=new BinaryDiscovery(link)){return discovery.verify();}
        } finally {
            if(d)conn.releaseInterface(data);
            if(c)conn.releaseInterface(control);
            conn.close();
        }
    }
}
