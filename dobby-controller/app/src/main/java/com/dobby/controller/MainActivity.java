package com.dobby.controller;

import android.Manifest;
import android.app.*;
import android.bluetooth.*;
import android.content.*;
import android.content.pm.PackageManager;
import android.os.*;
import android.view.*;
import java.io.*;
import java.util.*;

public class MainActivity extends Activity implements DobbyControllerView.Callback {
    private DobbyControllerView controller;
    private BluetoothAdapter bt;
    private BluetoothSocket socket;
    private OutputStream out;
    private BufferedReader reader;
    private Thread rxThread;
    private final UUID SPP = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB");
    private static final int REQ_BT=44;

    @Override public void onCreate(Bundle b) {
        super.onCreate(b);
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN, WindowManager.LayoutParams.FLAG_FULLSCREEN);
        controller = new DobbyControllerView(this, this);
        setContentView(controller);
        requestBluetoothPermissions();
    }

    private void requestBluetoothPermissions() {
        if (Build.VERSION.SDK_INT >= 31 &&
            (checkSelfPermission(Manifest.permission.BLUETOOTH_CONNECT)!=PackageManager.PERMISSION_GRANTED ||
             checkSelfPermission(Manifest.permission.BLUETOOTH_SCAN)!=PackageManager.PERMISSION_GRANTED)) {
            requestPermissions(new String[]{Manifest.permission.BLUETOOTH_CONNECT, Manifest.permission.BLUETOOTH_SCAN}, REQ_BT);
        } else initBluetooth();
    }

    @Override public void onRequestPermissionsResult(int r,String[] p,int[] g){
        super.onRequestPermissionsResult(r,p,g);
        if(r==REQ_BT) initBluetooth();
    }

    private void initBluetooth() {
        BluetoothManager bm=(BluetoothManager)getSystemService(BLUETOOTH_SERVICE);
        bt=bm.getAdapter();
        if(bt==null){ controller.log("Bluetooth not available"); return; }
        if(!bt.isEnabled()) startActivityForResult(new Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE), 45);
    }

    @Override public void onConnectRequest() {
        if(bt==null){ initBluetooth(); return; }
        if(Build.VERSION.SDK_INT>=31 && checkSelfPermission(Manifest.permission.BLUETOOTH_CONNECT)!=PackageManager.PERMISSION_GRANTED){
            requestBluetoothPermissions(); return;
        }
        Set<BluetoothDevice> paired=bt.getBondedDevices();
        if(paired.isEmpty()){ controller.log("No paired Bluetooth devices"); return; }
        final BluetoothDevice[] devices=paired.toArray(new BluetoothDevice[0]);
        String[] names=new String[devices.length];
        for(int i=0;i<devices.length;i++) names[i]=devices[i].getName()+"\n"+devices[i].getAddress();
        new AlertDialog.Builder(this).setTitle("Select Dobby / ESP32")
            .setItems(names,(d,which)->connect(devices[which])).setNegativeButton("Cancel",null).show();
    }

    private void connect(BluetoothDevice device) {
        controller.log("Connecting to "+device.getName()+"...");
        new Thread(()->{
            try {
                if(socket!=null) try{socket.close();}catch(Exception ignored){}
                socket=device.createRfcommSocketToServiceRecord(SPP);
                socket.connect();
                out=socket.getOutputStream();
                reader=new BufferedReader(new InputStreamReader(socket.getInputStream()));
                runOnUiThread(()->{controller.setConnected(true); controller.log("Connected to "+device.getName());});
                rxThread=new Thread(()->{
                    try{
                        String line;
                        while((line=reader.readLine())!=null){
                            final String s=line;
                            runOnUiThread(()->controller.log("ESP32: "+s));
                        }
                    }catch(Exception e){ runOnUiThread(()->controller.log("RX ended: "+e.getMessage())); }
                });
                rxThread.start();
            }catch(Exception e){
                runOnUiThread(()->{controller.setConnected(false); controller.log("BT error: "+e.getMessage());});
            }
        }).start();
    }

    @Override public void sendCommand(String command) {
        if(out==null){ controller.log("Not connected: "+command); return; }
        try { out.write((command+"\n").getBytes("UTF-8")); out.flush(); }
        catch(Exception e){ controller.log("TX error: "+e.getMessage()); }
    }

    @Override protected void onDestroy(){
        if(out!=null) try{out.close();}catch(Exception ignored){}
        if(socket!=null) try{socket.close();}catch(Exception ignored){}
        super.onDestroy();
    }
}
