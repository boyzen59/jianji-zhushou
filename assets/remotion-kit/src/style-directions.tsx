import React from 'react';
import {AbsoluteFill, Sequence, useCurrentFrame, useVideoConfig} from 'remotion';
import {mix, phase, TracePath} from './motion';

const sans = '"Microsoft YaHei", "Noto Sans SC", sans-serif';
const serif = '"SimSun", "Noto Serif SC", serif';
const ports = [{x:230,y:430},{x:510,y:260},{x:800,y:380},{x:980,y:150}];
const route = 'M230 430 C330 430 370 260 510 260 S670 390 800 380 S900 150 980 150';

/** Shared-source magnifier: local coordinates are identical to the source world. */
export const FocusLens: React.FC<{sourceId:string;clipId:string;x:number;y:number;radius:number;zoom:number;opacity?:number}> =
({sourceId,clipId,x,y,radius,zoom,opacity=1}) => <g opacity={opacity}>
  <defs><clipPath id={clipId}><circle cx={x} cy={y} r={radius}/></clipPath></defs>
  <circle cx={x+3} cy={y+10} r={radius+7} fill="#141916" opacity=".22"/>
  <g clipPath={`url(#${clipId})`}>
    <g transform={`translate(${x} ${y}) scale(${zoom}) translate(${-x} ${-y})`}>
      <use href={`#${sourceId}`}/>
    </g>
  </g>
  <circle cx={x} cy={y} r={radius} fill="none" stroke="#e4d4ac" strokeWidth="9"/>
  <circle cx={x} cy={y} r={radius+6} fill="none" stroke="#252a25" strokeWidth="2"/>
</g>;

/** Both contours have the same vertex count/order. Safe at arbitrary seek frames. */
export const morphContour = (progress:number, size=160, count=64): string =>
  Array.from({length:count},(_,i)=>{
    const a = i/count*Math.PI*2;
    const box = size/Math.max(Math.abs(Math.cos(a)),Math.abs(Math.sin(a)));
    const compass = size*(.46+.54*Math.pow(Math.abs(Math.cos(2*a)),5));
    const radius = mix(box,compass,Math.max(0,Math.min(1,progress)));
    return `${(Math.cos(a)*radius).toFixed(3)},${(Math.sin(a)*radius).toFixed(3)}`;
  }).join(' ');

const Frame: React.FC<{mode:string;dark?:boolean;children:React.ReactNode}> = ({mode,dark=false,children}) =>
  <AbsoluteFill style={{background:dark?'#0c1b28':'#eee9dc',color:dark?'#f3ead6':'#1e2a27',fontFamily:sans,overflow:'hidden'}}>
    {children}
    <div style={{position:'absolute',left:88,top:50,fontSize:19,letterSpacing:5}}>视觉机制研究 / {mode}</div>
    <div style={{position:'absolute',left:88,right:88,bottom:38,display:'flex',justifyContent:'space-between',fontSize:17,opacity:.62}}>
      <span>原创示意 · 非真实史料或地理地图</span><span>JIANJI STUDIO / 3.1</span>
    </div>
  </AbsoluteFill>;

const Harbor: React.FC<{color?:string}> = ({color='#263c35'}) => <g stroke={color} fill="none" strokeWidth="3">
  <path d="M0 110H300L265 157H48Z" fill={color}/><path d="M146 5V111M146 15L222 96H146ZM130 34L70 96H130Z" fill="#dfcfa6"/>
  {[0,1,2,3].map(i=><path key={i} d={`M${i*75-12} 178q20-12 40 0t40 0`} opacity=".55"/>)}
</g>;

export const ArchiveDirection: React.FC = () => {
  const f=useCurrentFrame(), {fps}=useVideoConfig();
  const focus=phase(f,.9*fps,1.3*fps);
  const camera=phase(f,0,4*fps);
  return <Frame mode="01 · 档案灯台">
    <div style={{position:'absolute',left:88,top:196,width:510}}>
      <div style={{fontSize:21,letterSpacing:8,color:'#9b4b36'}}>从证据，到关系</div>
      <div style={{fontFamily:serif,fontSize:80,lineHeight:1.3,marginTop:38}}>一条航线<br/>连接了什么？</div>
      <div style={{width:76,height:5,background:'#ae4933',margin:'42px 0'}}/>
      <div style={{fontSize:27,lineHeight:1.85,opacity:.72}}>先看完整图景，<br/>再靠近那个关键细节。</div>
      <div style={{fontSize:18,marginTop:90,letterSpacing:3}}>纸本 · 同源放大 · 关系揭示</div>
    </div>
    <svg width="1920" height="1080" style={{position:'absolute',inset:0}}>
      <defs>
        <pattern id="paper-grid" width="32" height="32" patternUnits="userSpaceOnUse"><path d="M32 0H0V32" fill="none" stroke="#697b67" strokeWidth=".5" opacity=".2"/></pattern>
        <radialGradient id="table-light"><stop stopColor="#fff6cf" stopOpacity=".7"/><stop offset="1" stopColor="#b8ab87" stopOpacity="0"/></radialGradient>
      </defs>
      <g transform={`translate(620 190) rotate(${mix(-5,-2,camera)} 560 350) scale(${mix(.94,1,camera)})`}>
        <rect x="16" y="20" width="1130" height="680" rx="3" fill="#302f23" opacity=".16"/>
        <g id="archive-world">
          <rect width="1130" height="680" fill="#ddd6ba"/>
          <rect x="18" y="18" width="1094" height="644" fill="url(#paper-grid)" stroke="#a39c7a"/>
          {Array.from({length:13},(_,i)=><path key={i} d={`M0 ${110+i*26} C180 ${i*20-40} 270 ${600-i*22} 440 ${570-i*20} S670 ${120+i*16} 790 ${140+i*17} S940 ${700-i*30} 1130 ${450+i*20}`} fill="none" stroke="#8d997a" opacity=".35" strokeWidth="1.3"/>)}
          <text x="48" y="66" fontFamily={serif} fontSize="28" fill="#344438">航路关系 / 示意图</text>
          <TracePath d={route} progress={phase(f,.2*fps,2*fps)} color="#aa412d" width={3}/>
          {ports.map((p,i)=><g key={i} transform={`translate(${p.x} ${p.y})`} opacity={phase(f,(.25+i*.3)*fps,.6*fps)}>
            <circle r="16" fill="#ddd6ba" stroke="#a7422d" strokeWidth="2"/><circle r="5" fill="#a7422d"/>
            <text x="24" y="8" fontFamily={sans} fontSize="22" fill="#263c35">{['出发','交换','汇聚','延伸'][i]}</text>
          </g>)}
          <g transform="translate(735 450) scale(.65)"><Harbor/></g>
          <text x="48" y="618" fontFamily={sans} fontSize="17" fill="#6e765f">不是两点之间的一根线，而是流动的开始。</text>
          <rect width="1130" height="680" fill="url(#table-light)"/>
        </g>
        <FocusLens sourceId="archive-world" clipId="archive-lens" x={mix(380,510,focus)} y={mix(400,260,focus)} radius={134} zoom={1.8} opacity={focus}/>
        <g opacity={phase(f,2.4*fps,.6*fps)}>
          <path d="M630 185L815 72H1030" fill="none" stroke="#942c23" strokeWidth="2"/>
          <rect x="806" y="32" width="238" height="42" fill="#942c23"/>
          <text x="825" y="61" fill="#fff0d8" fontFamily={sans} fontSize="22">把注意力交给证据</text>
        </g>
      </g>
    </svg>
  </Frame>;
};

export const MorphDirection: React.FC = () => {
  const f=useCurrentFrame(), {fps}=useVideoConfig();
  const p=phase(f,.9*fps,1.7*fps);
  const expand=phase(f,2.3*fps,1.5*fps);
  return <Frame mode="02 · 图形变形">
    <div style={{position:'absolute',left:90,top:178,fontSize:24,letterSpacing:6,color:'#b4432c'}}>让概念真的发生</div>
    <div style={{position:'absolute',left:82,top:247,fontSize:113,fontWeight:800,lineHeight:1.15,letterSpacing:-3}}>货物流动。<br/><span style={{color:'#bb432c'}}>世界相连。</span></div>
    <div style={{position:'absolute',left:90,top:576,fontSize:28,lineHeight:1.9,opacity:.72}}>一件货物，成为一个节点。<br/>一次交换，长出一张网络。</div>
    <div style={{position:'absolute',left:90,top:866,fontSize:18,letterSpacing:4}}>等拓扑形变 / 身份延续 / 有因果的动作</div>
    <svg width="1920" height="1080">
      <defs><pattern id="morph-grid" width="48" height="48" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.5" fill="#344b40" opacity=".17"/></pattern></defs>
      <rect x="835" y="160" width="985" height="740" fill="url(#morph-grid)"/>
      <circle cx="1310" cy="520" r="285" fill="none" stroke="#bec3b4" strokeWidth="1"/>
      <circle cx="1310" cy="520" r="220" fill="none" stroke="#bec3b4" strokeWidth="1" strokeDasharray="3 14"/>
      {[[-280,-180],[300,-180],[300,200],[-280,200]].map(([x,y],i)=><g key={i}>
        <TracePath d={`M1310 520Q${1310+x*.3} ${520+y} ${1310+x} ${520+y}`} progress={phase(f,(2+i*.15)*fps,1.5*fps)} color="#af432f" width={3}/>
        <g transform={`translate(${1310+x} ${520+y}) scale(${phase(f,(2.7+i*.15)*fps,.65*fps)})`}>
          <circle r="44" fill="#1d3930"/><circle r="10" fill="#eee9dc"/>
          <text y="83" textAnchor="middle" fontFamily={sans} fontSize="22" fill="#1d3930">{['货物','信息','人群','城市'][i]}</text>
        </g>
      </g>)}
      <g transform={`translate(1310 520) rotate(${mix(-12,0,p)}) scale(${mix(1,.78,expand)})`}>
        <polygon points={morphContour(p)} fill="#be432c"/>
        <polygon points={morphContour(p,.64*160)} fill="none" stroke="#efbd91" strokeWidth="1.5"/>
        <circle r={mix(4,26,p)} fill="#eee9dc"/>
      </g>
      <text x="1310" y="861" textAnchor="middle" fontFamily={sans} fontSize="19" letterSpacing="5" fill="#526452">同一个形状 · 不同的意义</text>
    </svg>
  </Frame>;
};

export const DepthDirection: React.FC = () => {
  const f=useCurrentFrame(), {fps}=useVideoConfig();
  const camera=phase(f,0,3.8*fps);
  return <Frame mode="03 · 纵深运镜" dark>
    <div style={{position:'absolute',inset:0,background:'radial-gradient(ellipse at 70% 25%,#254448 0,transparent 62%)'}}/>
    <div style={{position:'absolute',left:90,top:196,width:610}}>
      <div style={{fontSize:23,color:'#d6b875',letterSpacing:7}}>把信息变成可穿行的空间</div>
      <div style={{fontFamily:serif,fontSize:110,lineHeight:1.25,marginTop:34}}>从一个港口<br/>到一张网络</div>
      <div style={{fontSize:28,opacity:.7,lineHeight:1.9,marginTop:43}}>镜头向前，关系展开。<br/>画面停住，让理解跟上。</div>
      <div style={{height:2,background:'#d6b875',width:90,marginTop:55}}/>
    </div>
    <div style={{position:'absolute',left:770,top:160,width:1030,height:720,perspective:1700}}>
      <div style={{position:'absolute',inset:0,transformStyle:'preserve-3d',transform:`rotateX(${mix(18,7,camera)}deg) rotateY(${mix(-25,-12,camera)}deg) translateZ(${mix(-170,0,camera)}px)`}}>
        {[0,1,2].map(i=>{
          const entry=phase(f,(.2+i*.35)*fps,1.3*fps);
          const w=770,h=430;
          return <div key={i} style={{position:'absolute',left:90+i*40,top:220-i*75,width:w,height:h,
            border:'1px solid #c3b68166',background:i===2?'#182f36':'#11232d',boxShadow:'0 40px 90px #0006',
            opacity:entry,transform:`translateY(${(1-entry)*160}px) translateZ(${i*110-220}px)`,overflow:'hidden'}}>
            <svg width={w} height={h}>
              {Array.from({length:12},(_,j)=><path key={j} d={`M0 ${55+j*29}Q280 ${j*16} 430 ${100+j*23}T770 ${10+j*35}`} stroke="#678d83" fill="none" opacity=".22"/>)}
              {i===2?<g transform="translate(225 90) scale(.95)"><Harbor color="#d7bb78"/></g>:
              <g>{[0,1,2,3].map(j=><circle key={j} cx={100+j*160} cy={180+Math.sin(j)*60} r="12" fill="#a3c6ad"/>)}<TracePath d="M100 180Q340 80 580 190" progress={entry} color="#b5c69d" width={2}/></g>}
              <text x="38" y="52" fill="#d7bb78" fontSize="16" letterSpacing="5" fontFamily={sans}>{['航路 / ROUTE','关系 / NETWORK','港口 / HARBOR'][i]}</text>
              <text x="38" y="388" fill="#c8d5c9" fontSize="21" fontFamily={sans}>{['沿线建立联系','交换带来汇聚','在这里，流动开始'][i]}</text>
            </svg>
          </div>;
        })}
      </div>
    </div>
  </Frame>;
};

export const StyleDirections: React.FC = () => {
  const {fps}=useVideoConfig();
  return <><Sequence durationInFrames={6*fps}><ArchiveDirection/></Sequence>
    <Sequence from={6*fps} durationInFrames={6*fps}><MorphDirection/></Sequence>
    <Sequence from={12*fps} durationInFrames={6*fps}><DepthDirection/></Sequence></>;
};
