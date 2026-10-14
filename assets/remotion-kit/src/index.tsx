import React from 'react';
import {Composition, registerRoot} from 'remotion';
import {MotionStudy} from './study';

const Root = () => <Composition id="MotionStudy" component={MotionStudy} width={1920} height={1080} fps={60} durationInFrames={960}/>;
registerRoot(Root);
