import React from 'react';
import {Easing, Img, interpolate, random} from 'remotion';

export const smooth = Easing.bezier(0.22, 1, 0.36, 1);
export const symmetrical = Easing.bezier(0.76, 0, 0.24, 1);
export const unit = (x: number) => Math.max(0, Math.min(1, x));
export const phase = (frame: number, start: number, length: number, ease = smooth) =>
  length <= 0 ? Number(frame >= start) : ease(unit((frame - start) / length));
export const mix = (a: number, b: number, p: number) => a + (b - a) * p;

export type Pose = {x: number; y: number; width: number; height: number; rotate?: number; radius?: number; opacity?: number};
export type Point = {x: number; y: number};
export type PoseKey = Pose & {at: number; controlOut?: Point; controlIn?: Point};
export const cubicPoint = (a:Point,b:Point,c:Point,d:Point,t:number): Point => {
  const q=1-t;
  return {x:q*q*q*a.x+3*q*q*t*b.x+3*q*t*t*c.x+t*t*t*d.x,y:q*q*q*a.y+3*q*q*t*b.y+3*q*t*t*c.y+t*t*t*d.y};
};
export const poseAt = (frame: number, keys: PoseKey[]): Pose => {
  if (!keys.length) throw new Error('poseAt requires at least one key');
  if (keys.some((k, i) => i > 0 && k.at <= keys[i - 1].at)) throw new Error('Pose keys must increase');
  const aIndex = Math.max(0, keys.findIndex(k => k.at > frame) - 1);
  if (frame <= keys[0].at) return keys[0];
  if (frame >= keys[keys.length - 1].at) return keys[keys.length - 1];
  const a = keys[aIndex], b = keys[aIndex + 1];
  const p = phase(frame, a.at, b.at - a.at, symmetrical);
  const pos=a.controlOut && b.controlIn ? cubicPoint(a,a.controlOut,b.controlIn,b,p) : {x:mix(a.x,b.x,p),y:mix(a.y,b.y,p)};
  return {...pos, width: mix(a.width,b.width,p), height: mix(a.height,b.height,p), rotate: mix(a.rotate ?? 0,b.rotate ?? 0,p), radius: mix(a.radius ?? 0,b.radius ?? 0,p), opacity: mix(a.opacity ?? 1,b.opacity ?? 1,p)};
};

/** Caller supplies GLOBAL frame, keeping an actor alive across text/scene changes. */
export const SharedElement: React.FC<{frame: number; keys: PoseKey[]; children?: React.ReactNode; style?: React.CSSProperties}> = ({frame,keys,children,style}) => {
  const p = poseAt(frame,keys);
  return <div style={{position:'absolute',left:p.x,top:p.y,width:p.width,height:p.height,borderRadius:p.radius,opacity:p.opacity ?? 1,transform:`rotate(${p.rotate ?? 0}deg)`,transformOrigin:'center',...style}}>{children}</div>;
};

export const MediaCard: React.FC<{children?: React.ReactNode; src?: string; color?: string; rotateY?: number; style?: React.CSSProperties}> = ({children,src,color='#122f38',rotateY=0,style}) => <div style={{position:'relative',width:'100%',height:'100%',overflow:'hidden',borderRadius:22,background:color,border:'1px solid #ffffff26',boxShadow:'0 38px 85px #0008, inset 0 1px 0 #ffffff30',transform:`perspective(1500px) rotateY(${rotateY}deg)`,...style}}>{src ? <Img src={src} style={{width:'100%',height:'100%',objectFit:'cover'}}/> : null}{children}</div>;

/** Normalized SVG path length makes tracing independent of path geometry. */
export const TracePath: React.FC<{d: string; progress: number; color?: string; width?: number; opacity?: number}> = ({d,progress,color='#75e2d1',width=3,opacity=1}) => <path d={d} fill="none" stroke={color} strokeWidth={width} strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1-unit(progress)} opacity={opacity}/>;

/** Static deterministic torn outline, recomputed safely in any frame order. */
export const tornOutline = (width: number, height: number, seed: string, amplitude=7) => {
  const points: string[] = [];
  const point=(x:number,y:number) => points.push(`${x.toFixed(2)},${y.toFixed(2)}`);
  const n=36;
  for(let i=0;i<=n;i++) point(i*width/n,random(`${seed}:top:${i}`)*amplitude);
  for(let i=0;i<=n;i++) point(width-random(`${seed}:right:${i}`)*amplitude,i*height/n);
  for(let i=n;i>=0;i--) point(i*width/n,height-random(`${seed}:bottom:${i}`)*amplitude);
  for(let i=n;i>=0;i--) point(random(`${seed}:left:${i}`)*amplitude,i*height/n);
  return points.join(' ');
};
export const TornMatte: React.FC<{width:number;height:number;seed:string;color?:string}> = ({width,height,seed,color='#efe5cc'}) => <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" style={{position:'absolute',inset:0}}><polygon points={tornOutline(width,height,seed)} fill={color}/><polygon points={tornOutline(width-16,height-16,`${seed}:inside`,4)} transform="translate(8 8)" fill="none" stroke="#b9a98b" strokeWidth="1" opacity=".55"/></svg>;

/** Stylized light fields, not a physically accurate Tyndall or shutter simulation. */
export const MonochromeLight: React.FC<{frame:number;fps:number;color?:string;intensity?:number}> = ({frame,fps,color='#51ddcc',intensity=.8}) => {
  const t=frame/fps;
  return <div style={{position:'absolute',inset:0,overflow:'hidden',pointerEvents:'none',opacity:intensity}}>
    <div style={{position:'absolute',inset:'-65%',background:`conic-gradient(from ${t*6}deg at 50% 50%, transparent 0deg, ${color}66 16deg, transparent 28deg, transparent 155deg, ${color}30 174deg, transparent 195deg)`,filter:'blur(42px)',transform:`translate(${Math.sin(t*.2)*3}%, -9%)`,mixBlendMode:'screen'}}/>
    <div style={{position:'absolute',inset:0,background:`radial-gradient(ellipse at ${62+Math.sin(t*.2)*12}% 32%,${color}25,transparent 60%)`}}/>
  </div>;
};

/** Cheap depth particles: fixed identity, closed-form positions, no accumulated time. */
export const Dust: React.FC<{frame:number;fps:number;count?:number;color?:string}> = ({frame,fps,count=60,color='#eacda6'}) => <>{Array.from({length:count},(_,i)=>{
  const t=frame/fps;
  const x=random(`dust:x:${i}`)*100, y=random(`dust:y:${i}`)*100;
  const r=1+random(`dust:r:${i}`)*2;
  return <div key={i} style={{position:'absolute',left:`${x+Math.sin(t*.25+i)*.5}%`,top:`${y+Math.cos(t*.18+i)*.8}%`,width:r,height:r,borderRadius:'50%',background:color,opacity:.08+random(`dust:o:${i}`)*.2}}/>;
})}</>;

export const RevealText: React.FC<{frame:number;start:number;duration:number;children:React.ReactNode;style?:React.CSSProperties}> = ({frame,start,duration,children,style}) => {
  const p=phase(frame,start,duration);
  return <div style={{overflow:'hidden',...style}}><div style={{transform:`translateY(${(1-p)*110}%)`,opacity:unit(p*2)}}>{children}</div></div>;
};

export const exposure = (frame:number,start:number,end:number) => interpolate(frame,[start,start+8,end-8,end],[0,1,1,0],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
