package com.dobby.controller;

import android.content.*;
import android.graphics.*;
import android.view.*;
import java.util.*;

public class DobbyControllerView extends View {
    public interface Callback { void sendCommand(String c); void onConnectRequest(); void onSettingsRequest(); }
    private final Callback cb;
    private final Paint p=new Paint(3);
    private final ArrayList<Control> controls=new ArrayList<>();
    private final ArrayList<String> logs=new ArrayList<>();
    private boolean connected=false, edit=false, showLogs=true;
    private Control active=null;
    private float downX,downY,origX,origY,origW,origH;
    private boolean resize=false;
    private int speed=70;
    private final SharedPreferences prefs;

    static class Control {
        String id,label,cmd; float x,y,w,h; boolean momentary;
        Control(String i,String l,String c,float X,float Y,float W,float H,boolean m){id=i;label=l;cmd=c;x=X;y=Y;w=W;h=H;momentary=m;}
    }

    public DobbyControllerView(Context c, Callback callback){
        super(c); cb=callback; setFocusable(true);
        prefs=c.getSharedPreferences("layout",0); load();
        p.setTypeface(Typeface.create("sans",Typeface.BOLD)); setBackgroundColor(Color.rgb(8,10,13));
    }

    private void load(){
        controls.clear();
        // Natural gamepad-style layout: UP/DOWN on the left, LEFT/RIGHT side-by-side on the right.
        controls.add(new Control("up","▲","F",0.07f,0.31f,0.25f,0.25f,true));
        controls.add(new Control("down","▼","B",0.07f,0.62f,0.25f,0.25f,true));
        controls.add(new Control("left","◀","L",0.68f,0.46f,0.115f,0.25f,true));
        controls.add(new Control("right","▶","R",0.815f,0.46f,0.115f,0.25f,true));
        controls.add(new Control("aux1","AUX 1","A1",0.405f,0.28f,0.15f,0.105f,false));
        controls.add(new Control("aux2","AUX 2","A2",0.405f,0.41f,0.15f,0.105f,false));
        for(Control c:controls){
            c.x=prefs.getFloat(c.id+"x",c.x); c.y=prefs.getFloat(c.id+"y",c.y);
            c.w=prefs.getFloat(c.id+"w",c.w); c.h=prefs.getFloat(c.id+"h",c.h);
        }
        speed=prefs.getInt("speed",70);
        showLogs=prefs.getBoolean("showLogs",true);
    }
    private void save(){
        SharedPreferences.Editor e=prefs.edit();
        for(Control c:controls){e.putFloat(c.id+"x",c.x);e.putFloat(c.id+"y",c.y);e.putFloat(c.id+"w",c.w);e.putFloat(c.id+"h",c.h);}
        e.putInt("speed",speed).putBoolean("showLogs",showLogs).apply();
    }

    @Override protected void onDraw(Canvas c){
        super.onDraw(c); int W=getWidth(),H=getHeight();
        p.setStyle(Paint.Style.FILL); p.setColor(Color.rgb(9,12,16)); c.drawRect(0,0,W,H,p);
        p.setColor(Color.rgb(19,24,30)); c.drawRect(0,0,W,76,p);
        p.setColor(connected?Color.rgb(35,215,105):Color.rgb(230,65,65)); c.drawCircle(25,27,8,p);
        text(c,connected?"CONNECTED":"DISCONNECTED",44,34,19,Color.WHITE,Paint.Align.LEFT);
        text(c,"Dobby Controller",W/2,31,25,Color.WHITE,Paint.Align.CENTER);
        text(c,"PWM "+speed+"%",W-150,28,17,Color.WHITE,Paint.Align.CENTER);
        // Speed slider: maps to the original RC Controller protocol: 0-9 and q.
        p.setColor(Color.rgb(60,68,76)); c.drawRoundRect(new RectF(W-275,43,W-55,59),8,8,p);
        p.setColor(Color.rgb(0,190,255)); c.drawRoundRect(new RectF(W-275,43,W-275+220*speed/100f,59),8,8,p);
        drawHeaderButton(c,"BT",W-390,8,62,32);
        drawHeaderButton(c,"⋮",W-75,5,62,38);
        if(edit) drawHeaderButton(c,"DONE",W-150,8,62,32);

        int top=76;
        if(showLogs){
            p.setColor(Color.rgb(14,18,23)); c.drawRect(0,top,W,top+58,p);
            int start=Math.max(0,logs.size()-2); int yy=99;
            for(int i=start;i<logs.size();i++){text(c,logs.get(i),16,yy,16,Color.LTGRAY,Paint.Align.LEFT);yy+=22;}
            text(c,edit?"EDIT MODE • drag controls • bottom-right handle = resize":"",W/2,top+50,13,Color.GRAY,Paint.Align.CENTER);
        }
        for(Control q:controls) drawControl(c,q,W,H);
        text(c,"v1.1",W-15,H-8,11,Color.GRAY,Paint.Align.RIGHT);
    }

    private void drawControl(Canvas c,Control q,int W,int H){
        RectF r=new RectF(q.x*W,q.y*H,q.x*W+q.w*W,q.y*H+q.h*H);
        p.setStyle(Paint.Style.FILL); p.setColor(Color.rgb(27,36,46)); c.drawRoundRect(r,18,18,p);
        p.setStyle(Paint.Style.STROKE); p.setStrokeWidth(edit&&active==q?4:2); p.setColor(edit&&active==q?Color.rgb(0,200,255):Color.rgb(70,86,102)); c.drawRoundRect(r,18,18,p);
        float size=q.label.startsWith("AUX")?Math.max(22,r.height()*0.38f):Math.max(46,Math.min(78,r.height()*0.48f));
        text(c,q.label,r.centerX(),r.centerY()+size*0.34f,size,Color.rgb(0,200,255),Paint.Align.CENTER);
        if(edit){p.setStyle(Paint.Style.FILL);p.setColor(Color.rgb(0,200,255)); c.drawRect(r.right-18,r.bottom-18,r.right,r.bottom,p);}
    }
    private void drawHeaderButton(Canvas c,String s,float x,float y,float w,float h){p.setStyle(Paint.Style.FILL);p.setColor(Color.rgb(35,45,55));c.drawRoundRect(new RectF(x,y,x+w,y+h),10,10,p);text(c,s,x+w/2,y+h/2+6,14,Color.WHITE,Paint.Align.CENTER);}
    private void text(Canvas c,String s,float x,float y,float size,int color,Paint.Align a){p.setStyle(Paint.Style.FILL);p.setColor(color);p.setTextSize(size);p.setTextAlign(a);p.setTypeface(Typeface.create("sans",Typeface.BOLD));c.drawText(s,x,y,p);}

    private String speedCommand(int v){
        if(v<=5)return "0"; // practical minimum
        if(v>=95)return "q";
        int n=Math.max(1,Math.min(9,Math.round(v/10f)));
        return String.valueOf(n);
    }

    @Override public boolean onTouchEvent(MotionEvent e){
        float x=e.getX(),y=e.getY(); int W=getWidth(),H=getHeight();
        if(e.getAction()==MotionEvent.ACTION_DOWN){
            downX=x;downY=y;
            if(y<55 && x>W-90){cb.onSettingsRequest();return true;}
            if(y<48 && x>W-410 && x<W-315){cb.onConnectRequest();return true;}
            if(y>=38 && y<68 && x>W-290 && x<W-40){
                speed=Math.max(0,Math.min(100,(int)((x-(W-275))*100f/220f)));
                prefs.edit().putInt("speed",speed).apply(); cb.sendCommand(speedCommand(speed)); log("TX speed: "+speedCommand(speed)); invalidate(); return true;
            }
            active=null;resize=false;
            for(int i=controls.size()-1;i>=0;i--){
                Control q=controls.get(i);RectF r=new RectF(q.x*W,q.y*H,q.x*W+q.w*W,q.y*H+q.h*H);
                if(r.contains(x,y)){active=q;origX=q.x;origY=q.y;origW=q.w;origH=q.h;resize=edit&&x>r.right-30&&y>r.bottom-30;break;}
            }
            if(active!=null&&!edit&&active.momentary){cb.sendCommand(active.cmd);log("TX: "+active.cmd);invalidate();return true;}
            return active!=null;
        }
        if(e.getAction()==MotionEvent.ACTION_MOVE&&edit&&active!=null){
            float dx=(x-downX)/W,dy=(y-downY)/H;
            if(resize){active.w=Math.max(.08f,Math.min(.8f,origW+dx));active.h=Math.max(.08f,Math.min(.6f,origH+dy));}
            else{active.x=Math.max(0,Math.min(.92f,origX+dx));active.y=Math.max(.12f,Math.min(.88f,origY+dy));}
            invalidate();return true;
        }
        if(e.getAction()==MotionEvent.ACTION_UP){if(!edit&&active!=null&&active.momentary){cb.sendCommand("S");log("TX: S");invalidate();}return active!=null;}
        return true;
    }
    public void setConnected(boolean b){connected=b;invalidate();}
    public void log(String s){logs.add(s);if(logs.size()>20)logs.remove(0);invalidate();}
    public void setShowLogs(boolean b){showLogs=b;save();invalidate();}
}
