package com.dobby.controller;

import android.content.*;
import android.graphics.*;
import android.view.*;
import java.util.*;

public class DobbyControllerView extends View {
    public interface Callback { void sendCommand(String c); void onConnectRequest(); }
    private final Callback cb;
    private final Paint p=new Paint(3);
    private final ArrayList<Control> controls=new ArrayList<>();
    private final ArrayList<String> logs=new ArrayList<>();
    private boolean connected=false, edit=false;
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
        controls.add(new Control("up","▲","F",0.07f,0.30f,0.25f,0.27f,true));
        controls.add(new Control("down","▼","B",0.07f,0.62f,0.25f,0.27f,true));
        controls.add(new Control("left","◀","L",0.69f,0.30f,0.25f,0.27f,true));
        controls.add(new Control("right","▶","R",0.69f,0.62f,0.25f,0.27f,true));
        controls.add(new Control("aux1","AUX 1","A1",0.40f,0.31f,0.16f,0.12f,false));
        controls.add(new Control("aux2","AUX 2","A2",0.40f,0.46f,0.16f,0.12f,false));
        for(Control c:controls){
            c.x=prefs.getFloat(c.id+"x",c.x); c.y=prefs.getFloat(c.id+"y",c.y);
            c.w=prefs.getFloat(c.id+"w",c.w); c.h=prefs.getFloat(c.id+"h",c.h);
        }
    }
    private void save(){
        SharedPreferences.Editor e=prefs.edit();
        for(Control c:controls){e.putFloat(c.id+"x",c.x);e.putFloat(c.id+"y",c.y);e.putFloat(c.id+"w",c.w);e.putFloat(c.id+"h",c.h);} e.apply();
    }

    @Override protected void onDraw(Canvas c){
        super.onDraw(c); int W=getWidth(),H=getHeight();
        p.setStyle(Paint.Style.FILL); p.setColor(Color.rgb(14,18,23)); c.drawRect(0,0,W,H,p);
        p.setColor(Color.rgb(20,25,31)); c.drawRect(0,0,W,72,p);
        p.setColor(connected?Color.rgb(40,200,110):Color.rgb(220,70,70)); c.drawCircle(24,27,8,p);
        text(c,connected?"CONNECTED":"DISCONNECTED",42,33,20,Color.WHITE,Paint.Align.LEFT);
        text(c,"Dobby Controller",W/2,31,22,Color.LTGRAY,Paint.Align.CENTER);
        text(c,"PWM "+speed+"%",W-145,31,18,Color.WHITE,Paint.Align.CENTER);
        text(c,edit?"EDIT MODE • drag controls • bottom-right handle = resize":"",W/2,57,13,Color.GRAY,Paint.Align.CENTER);
        p.setColor(Color.DKGRAY); c.drawRoundRect(new RectF(W-270,46,W-25,62),8,8,p);
        p.setColor(Color.rgb(0,184,255)); c.drawRoundRect(new RectF(W-270,46,W-270+245*speed/100f,62),8,8,p);
        p.setColor(Color.rgb(10,13,17)); c.drawRect(0,72,W,132,p);
        int start=Math.max(0,logs.size()-2); int yy=95;
        for(int i=start;i<logs.size();i++){text(c,logs.get(i),14,yy,12,Color.LTGRAY,Paint.Align.LEFT);yy+=18;}
        for(Control q:controls) drawControl(c,q,W,H);
        drawHeaderButton(c,"BT",W-350,8,65,32); drawHeaderButton(c,edit?"DONE":"EDIT",W-80,8,65,32);
        text(c,"v1.0",W-15,H-8,11,Color.GRAY,Paint.Align.RIGHT);
    }

    private void drawControl(Canvas c,Control q,int W,int H){
        RectF r=new RectF(q.x*W,q.y*H,q.x*W+q.w*W,q.y*H+q.h*H);
        p.setStyle(Paint.Style.FILL); p.setColor(Color.rgb(28,36,45)); c.drawRoundRect(r,18,18,p);
        p.setStyle(Paint.Style.STROKE); p.setStrokeWidth(edit&&active==q?4:2); p.setColor(edit&&active==q?Color.rgb(0,200,255):Color.rgb(65,80,95)); c.drawRoundRect(r,18,18,p);
        p.setStyle(Paint.Style.FILL); text(c,q.label,r.centerX(),r.centerY()+r.height()*0.18f,Math.max(18,r.height()*0.30f),Color.rgb(0,200,255),Paint.Align.CENTER);
        if(edit){p.setColor(Color.rgb(0,200,255)); c.drawRect(r.right-18,r.bottom-18,r.right,r.bottom,p);}
    }
    private void drawHeaderButton(Canvas c,String s,float x,float y,float w,float h){p.setColor(Color.rgb(35,45,55));c.drawRoundRect(new RectF(x,y,x+w,y+h),10,10,p);text(c,s,x+w/2,y+h/2+6,13,Color.WHITE,Paint.Align.CENTER);}
    private void text(Canvas c,String s,float x,float y,float size,int color,Paint.Align a){p.setStyle(Paint.Style.FILL);p.setColor(color);p.setTextSize(size);p.setTextAlign(a);c.drawText(s,x,y,p);}

    @Override public boolean onTouchEvent(MotionEvent e){
        float x=e.getX(),y=e.getY(); int W=getWidth(),H=getHeight();
        if(e.getAction()==MotionEvent.ACTION_DOWN){
            downX=x;downY=y;
            if(y<40 && x>W-100){edit=!edit;if(!edit)save();invalidate();return true;}
            if(y<72 && x>W-370 && x<W-285){cb.onConnectRequest();return true;}
            if(y>38 && y<70 && x>W-285){speed=Math.max(0,Math.min(100,(int)((x-(W-270))*100f/245f)));cb.sendCommand("V"+speed);invalidate();return true;}
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
            else{active.x=Math.max(0,Math.min(.92f,origX+dx));active.y=Math.max(.14f,Math.min(.88f,origY+dy));}
            invalidate();return true;
        }
        if(e.getAction()==MotionEvent.ACTION_UP){if(!edit&&active!=null&&active.momentary){cb.sendCommand("S");log("TX: S");invalidate();}return active!=null;}
        return true;
    }
    public void setConnected(boolean b){connected=b;invalidate();}
    public void log(String s){logs.add(s);if(logs.size()>20)logs.remove(0);invalidate();}
}
