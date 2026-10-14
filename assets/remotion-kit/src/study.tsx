import React from 'react';
import {AbsoluteFill,interpolateColors,useCurrentFrame,useVideoConfig} from 'remotion';
import {Dust,MediaCard,MonochromeLight,RevealText,SharedElement,TornMatte,TracePath,mix,phase,symmetrical} from './motion';

const ink='#e9f3ef', amber='#edb474', mint='#85e6d4';
const serif='"Microsoft YaHei", "Noto Sans SC", sans-serif';
// All artwork here is original procedural demonstration art, not historical evidence.
const Engraving: React.FC<{variant:number;frame:number}> = ({variant,frame}) => <svg viewBox="0 0 500 360" width="100%" height="100%" style={{position:'absolute',inset:0}}>
  <defs><linearGradient id={`g${variant}`} x2="1" y2="1"><stop stopColor={variant===1?'#40302a':'#16494e'}/><stop offset="1" stopColor="#08171d"/></linearGradient></defs>
  <rect width="500" height="360" fill={`url(#g${variant})`}/>
  <g transform={`translate(250 180) rotate(${variant*22+frame/180})`} fill="none" stroke={variant===1?amber:mint}>
    {[140,126,106,75,42].map((r,i)=><circle key={r} r={r} opacity={.18+i*.09} strokeWidth={i===1?2:1}/>)}
    {Array.from({length:32},(_,i)=><path key={i} d={`M ${Math.cos(i*Math.PI/16)*110} ${Math.sin(i*Math.PI/16)*110} L ${Math.cos(i*Math.PI/16)*139} ${Math.sin(i*Math.PI/16)*139}`} opacity=".28"/>)}
    <path d={variant===1?'M-110 85L0-115L112 85ZM-68 52H68M-43 15H43M-22-26H22':'M-115 54C-80-125 20 104 115-73M-115 66C-80-113 20 116 115-61'} strokeWidth="3"/>
    <circle r="8" fill={amber} stroke="none"/>
  </g>
  <path d="M28 30H80M28 30V70M472 330H420M472 330V290" fill="none" stroke="#ffffff55"/>
</svg>;

const Network:React.FC<{frame:number;fps:number}> = ({frame,fps}) => {
  const p=phase(frame,302,95);
  const spread=phase(frame,330,160);
  const retreat=phase(frame,595,72,symmetrical);
  const nodes=[{x:330,y:580,label:'素材',sub:'SOURCE'},{x:925,y:340,label:'证据',sub:'EVIDENCE'},{x:1460,y:660,label:'理解',sub:'MEANING'}];
  const paths=['M330 580 C 560 580 640 340 925 340','M925 340 C 1220 340 1220 660 1460 660'];
  return <AbsoluteFill style={{opacity:p*(1-retreat),transform:`scale(${1+retreat*.18})`,transformOrigin:'1460px 660px'}}>
    <svg width="1920" height="1080" style={{position:'absolute',inset:0}}>
      <defs><pattern id="grid" width="55" height="55" patternUnits="userSpaceOnUse"><path d="M55 0H0V55" stroke="#81ddca" strokeWidth=".8" opacity=".12" fill="none"/></pattern></defs>
      <rect x="80" y="230" width="1760" height="640" fill="url(#grid)"/>
      {paths.map((d,i)=><g key={d}><TracePath d={d} progress={phase(frame,340+i*85,110)} width={18} color={mint} opacity={.07}/><TracePath d={d} progress={phase(frame,340+i*85,110)} width={2.5} color={i?amber:mint}/></g>)}
      {nodes.map((n,i)=><g key={n.label} opacity={phase(frame,315+i*70,44)} transform={`translate(${n.x},${n.y})`}>
        <circle r={76+Math.sin(frame/fps*.7+i)*2} fill="#0a212b" stroke={i===2?amber:mint} strokeOpacity=".6"/>
        <circle r="88" fill="none" stroke={mint} strokeOpacity=".15"/>
        <circle r="39" fill="none" stroke={mint} strokeOpacity=".2" strokeDasharray="2 9" transform={`rotate(${frame/3})`}/>
        <text y="127" textAnchor="middle" fill={ink} fontSize="31" fontFamily={serif} opacity={1-phase(frame,595,42)}>{n.label}</text>
        <text y="161" textAnchor="middle" fill={mint} fontSize="15" letterSpacing="5" opacity={1-phase(frame,595,42)}>{n.sub}</text>
      </g>)}
      <g opacity={spread*.5} fill="none" stroke={mint} strokeWidth="1">
        <path d="M925 252V200H1530V335"/><path d="M330 668V815H1280"/>
        <circle cx="1530" cy="340" r="4"/><circle cx="1280" cy="815" r="4"/>
      </g>
    </svg>
    <div style={{position:'absolute',left:110,top:108,opacity:1-phase(frame,578,32)}}><RevealText frame={frame} start={325} duration={45} style={{fontSize:57,fontWeight:600}}>让线索，彼此连接。</RevealText><div style={{marginTop:18,fontSize:20,color:'#81a6a8',letterSpacing:3}}>一段画面，接住下一段叙事。</div></div>
  </AbsoluteFill>;
};

export const MotionStudy:React.FC = () => {
  const f=useCurrentFrame();const {fps}=useVideoConfig();
  const into=phase(f,245,83,symmetrical);
  const finale=phase(f,650,62,symmetrical);
  const titleOpacity=1-phase(f,212,35);
  return <AbsoluteFill style={{background:'#08161d',color:ink,fontFamily:serif,overflow:'hidden'}}>
    <MonochromeLight frame={f} fps={fps} intensity={mix(.65,.9,finale)} color={interpolateColors(f,[580,680],['#3ccfb9','#d39b66'])}/>
    <Dust frame={f} fps={fps}/>
    <div style={{position:'absolute',left:-270,top:-420,width:1220,height:1220,borderRadius:'50%',border:'1px solid #72bfb219',transform:`rotate(${f/20}deg)`}}><div style={{position:'absolute',inset:30,border:'1px dashed #72bfb217',borderRadius:'50%'}}/></div>
    <div style={{position:'absolute',left:112,top:145,opacity:titleOpacity}}>
      <div style={{color:mint,fontSize:19,letterSpacing:8,marginBottom:35}}>NARRATIVE / MOTION</div>
      <div style={{fontWeight:650,fontSize:89,lineHeight:1.27}}>从散落的素材，<br/><span style={{color:amber}}>到连贯的故事。</span></div>
      <RevealText frame={f} start={38} duration={45} style={{fontSize:25,color:'#9ab2b6',marginTop:42}}>画面有层次，镜头有来处。</RevealText>
      <svg width="360" height="140" style={{marginTop:35}}><TracePath d="M0 30H170Q210 30 235 70T330 95" progress={phase(f,70,100)} color={mint}/><circle cx="330" cy="95" r="5" fill={mint} opacity={phase(f,150,24)}/></svg>
    </div>
    {[0,1,2].map((i)=>{
      const entry=phase(f,-22+i*12,86);
      const away=phase(f,224+i*7,55,symmetrical);
      const x=[925,1200,1100][i], y=[183,365,620][i];
      return <div key={i} style={{position:'absolute',left:mix(2100,x,entry)+away*(i===1?500:-600),top:y+Math.sin(f/180+i)*6,width:450,height:315,opacity:1-into,transform:`rotate(${[-8,8,-4][i]}deg) scale(${1-away*.4})`}}><MediaCard rotateY={[-9,11,-5][i]}><Engraving variant={i} frame={f}/><div style={{position:'absolute',left:22,bottom:20,fontSize:17,letterSpacing:4,color:'#ffffffa0'}}>{['观察','关联','转化'][i]}</div></MediaCard></div>;
    })}
    <Network frame={f} fps={fps}/>
    {/* One actor persists through BOTH scene boundaries; curves match the drawn routes. */}
    <SharedElement frame={f} keys={[
      {at:0,x:1140,y:334,width:18,height:18,radius:9},
      {at:220,x:1140,y:334,width:18,height:18,radius:9},
      {at:274,x:1450,y:60,width:240,height:240,radius:120},
      {at:332,x:312,y:562,width:36,height:36,radius:18},
      {at:364,x:322,y:572,width:16,height:16,radius:8,controlOut:{x:552,y:572}},
      {at:445,x:917,y:332,width:16,height:16,radius:8,controlIn:{x:632,y:332},controlOut:{x:1212,y:332}},
      {at:555,x:1452,y:652,width:16,height:16,radius:8,controlIn:{x:1212,y:652}},
      {at:610,x:1452,y:652,width:16,height:16,radius:8},
      {at:708,x:1330,y:350,width:430,height:430,radius:215},
      {at:959,x:1330,y:350,width:430,height:430,radius:215}
    ]} style={{background:`radial-gradient(circle at 30% 30%,#fff3d4,${amber} 22%,#866540 100%)`,boxShadow:'0 0 65px #e0ab6350',opacity:f<224?.2:1}}/>
    <AbsoluteFill style={{opacity:finale,transform:`translateY(${(1-finale)*70}px)`}}>
      <div style={{position:'absolute',left:110,top:180,color:amber,fontSize:18,letterSpacing:8}}>STORY FIRST. MOTION WITH PURPOSE.</div>
      <div style={{position:'absolute',left:107,top:260,fontWeight:700,fontSize:115,lineHeight:1.24}}>每一次动效，<br/>都让<span style={{color:amber}}>故事</span>更进一步。</div>
      <div style={{position:'absolute',left:112,top:646,width:1030,height:126,transform:`rotate(${mix(-3,-1,finale)}deg)`}}><TornMatte width={1030} height={126} seed="narrative-paper"/><div style={{position:'relative',padding:'36px 43px',color:'#233b3d',fontSize:28,letterSpacing:2}}>以文案为核心 · 让证据、空间与镜头共同叙事</div></div>
      <svg width="1920" height="1080" style={{position:'absolute',inset:0,pointerEvents:'none'}}><g transform={`translate(1545 565) rotate(${(f-650)/5})`} fill="none" stroke={amber}><ellipse rx="252" ry="325" strokeOpacity=".35"/><ellipse rx="330" ry="135" transform="rotate(24)" strokeOpacity=".5"/><circle r="283" strokeOpacity=".18" strokeDasharray="2 12"/></g></svg>
    </AbsoluteFill>
    <div style={{position:'absolute',left:110,right:110,bottom:55,display:'flex',justifyContent:'space-between',alignItems:'center',fontSize:15,color:'#829a9f',letterSpacing:3}}><span>REMOTION MOTION STUDY</span><span>机制演示 · 非项目成片</span></div>
    <div style={{position:'absolute',bottom:0,left:0,height:3,width:`${f/959*100}%`,background:`linear-gradient(90deg,${mint},${amber})`}}/>
  </AbsoluteFill>;
};
