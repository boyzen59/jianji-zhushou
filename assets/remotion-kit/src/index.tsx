import React from 'react';
import {Composition, registerRoot} from 'remotion';
import {MotionStudy} from './study';
import {ArchiveDirection, MorphDirection, DepthDirection, StyleDirections} from './style-directions';

const Root = () => <>
  <Composition id="MotionStudy" component={MotionStudy} width={1920} height={1080} fps={60} durationInFrames={960}/>
  <Composition id="StyleDirections" component={StyleDirections} width={1920} height={1080} fps={30} durationInFrames={540}/>
  <Composition id="ArchiveDirection" component={ArchiveDirection} width={1920} height={1080} fps={30} durationInFrames={180}/>
  <Composition id="MorphDirection" component={MorphDirection} width={1920} height={1080} fps={30} durationInFrames={180}/>
  <Composition id="DepthDirection" component={DepthDirection} width={1920} height={1080} fps={30} durationInFrames={180}/>
</>;
registerRoot(Root);
