# Remotion 统一制作与验证

全部新动画及最终合成用Remotion。参考项目帮助设计，不接管工作流。接口以实际安装版本与[官方文档](https://www.remotion.dev/docs)为准；`assets/remotion-kit/`是本次原创、可运行的组件起点，项目可直接扩展，不限定使用比例。

## 工程入口

开始制作计划先执行[开工缺项提醒](preflight-and-notices.md)。Remotion能运行与参考已补齐分别检查：不能用编译成功掩盖缺少Shotcraft/其他参考或插件；先提醒用户处理，再按回应推进。

新项目可复制`assets/remotion-kit`到项目的独立制作目录，运行`npm ci`（已有锁文件）或`npm install`，再`npm run typecheck`、`npm run studio`、`npm run render:demo`。依赖装在项目，不在Skill目录。已有Remotion工程优先接入组件和场景数据，不覆盖其锁文件或源码。演示Composition为MotionStudy，1920×1080/60fps/960帧/无音轨；程序绘制内容非史料，仅展示机制。演示使用Windows微软雅黑；跨机需选择已有授权且包含中文字形的本地字体再验画，模板不包含第三方字体文件。

组件包演示的是机制，不是通用一键全片渲染器。制作真实视频时，按分镜建立Master Composition、场景与独立媒体层；需要现有`build_render_plan.py`时输出`project.json`和`04_spec/video-spec.json`，scene的start/end为连续母版秒数。实际工程入口、Composition ID和参数写入交接。

所有Remotion包锁在同一版本。升级不是让旧模板运行的默认办法，先核实已有项目版本。官方参考代码可能比本机更新，使用前编译验证。

## 时间和确定性

- 所有变化来自`useCurrentFrame()`、`useVideoConfig()`以及显式的全局/局部起点。frame/fps是唯一时钟；`Sequence`中的frame是局部帧，要与母版帧明确转换。
- 状态以frame纯计算；不用`Date.now`、未固定seed的随机数、CSS animation/transition、setInterval、requestAnimationFrame或独立GSAP/Motion时钟推动动画。
- Canvas每帧清空并从固定事件表重建该时刻，随机访问结果与顺序播放一致。需要累积物理模拟时先确定性预计算，再按frame采样。
- Three.js动画读取Remotion frame，禁止独立useFrame累计delta。Lottie使用`@remotion/lottie`；SVG描边、形变、粒子同样受frame控制。
- 中文字体本地化并等待加载。生产素材先建立稳定本地映射，渲染过程中不依赖实时网络。图片解码、字体和异步数据的准备通过Remotion等待机制管理。

## 原声与镜头共存

用户录音是时长权威；文案是叙事权威；时间戳是定位资料。图片/真人/AI视频/文字各自独立轨，不因文字换页重播源视频。

`TransitionSeries`会使相邻段重叠，不能将已经确定的总时长再减一次。可在固定全局Sequence窗口内自绘mask/共享对象转场；若用TransitionSeries，明确重叠计入方式。crossfade后媒体可播放范围仍要覆盖每一帧。官方说明：[TransitionSeries](https://www.remotion.dev/docs/transitions/transitionseries)。

生成画面的落点跟随说出的概念，音乐节拍用于细化；不为卡点改写原声。句级SRT不等于逐词数据。保留源入点、素材母版起点及预挂载区间，详见playback-continuity.md。

## 性能与画质

用真实镜头测试较重的粒子、SVG滤镜、模糊和3D。纸纹/笔触等不变部分可缓存，保留全局采样一致性。景深和光晕不要糊住证据；运动模糊只在相应层和运动窗口启用。

Remotion当前支持多种[motion blur](https://www.remotion.dev/docs/motion-blur)实现，接口和浏览器能力随版本变化。先验证再采用；CSS高斯模糊/拖影只标为近似。不要跨硬切混合前后镜的快门样本。

GPU编码、浏览器合成和滤镜加速分开检查。生产段顺序执行，并发从低值实测提高，资源不足先降低并发，不擅自降交付规格或删素材。

## 验证：技术与审美分别成立

1. **分镜检查**：每镜原句对应、主要参考、具体机制、前后接力、时间与素材均明确。`scripts/validate_storyboard.py`检查结构和帧区间，不宣称能评审审美。
2. **构图检查**：开头、关键动作前中后、落定和转场中间帧；看中文字形、重叠、边缘、证据、人物遮挡和来源真实性。
3. **动态检查**：至少一段连续的代表片段，含复杂素材交接；核对速度、注意力、强弱、黑闪/跳帧和原声落点。只看静帧不能认证节奏。
4. **可复现检查**：对新Canvas/WebGL/程序化组件，将同一frame按不同seek顺序生成并比较；分段输出和整段参考在接缝一致。
5. **完整制作**：按输入/代码指纹续跑；正式输出核验总帧数、音轨、规格和素材实际可见清单。`verify_master_media.py --width W --height H --fps FPS --audio none/required/either --expected-frames N`按当前规格检查H.264 High/Rec.709 MP4；不把其旧1440p60静音默认当全片限制。其他编码规格按实际交付单检查。只能以实际输出宣称完成。

视觉评审问：动作是否让文案更容易理解？素材是否相互接住？是否有鲜明但不妨碍阅读的亮点？层次、材质和镜头是否精细？有没有只是“每图推近+标题弹出”的长段？发现问题回修具体镜头并重看。

未来交付含原源码/配置、当前锁文件、实际渲染入口、分镜与参考采用记录、需要的音轨/录制包，以及本次用户指定的成片或审阅格式。未经动态观察的输出标“渲染完成，动态审阅待做”，不宣称达到某频道或顶尖YouTube质量。
