# Remotion制作与验收

## 工程

新工程把 `assets/remotion-kit/` 复制到独立制作目录；有锁文件用 `npm ci`，已有工程直接适配组件。所有Remotion包保持同一版本，核对实际API后再采用上游代码。生产素材和字体建立本地映射并等待加载，渲染不依赖实时网络。

基础演示 `MotionStudy` 为1920×1080／60fps／16秒／无声；仅演示机制。真实项目须实现Master Composition、场景与独立媒体轨，并记录入口和参数。现有 `build_render_plan.py` 读取project.json及04_spec/video-spec.json，scene.start/end用连续母版秒数。

`npm run typecheck` 检查类型；`npm run studio` 预览；`npm run render:demo` 渲基础演示。只做文字任务时不安装或渲演示；新视觉组件用代表静帧／短试片验证，不重渲无关全片。

## 时间与媒体

frame/fps是唯一时钟。区分母版帧和Sequence局部帧；状态纯计算，固定随机种子。Canvas每帧复位并重建，累积模拟先预计算再采样。Three.js与Lottie读取同一时间，不运行独立动画循环。新程序化组件比较不同seek顺序下的相同帧。

原声、AI视频、真人、图片与文字独立轨；换文字或全屏收窗不重置媒体。项目策略读[默认值](production-defaults.md)。字幕安全区由实际布局避让，不能仅在JSON声明。

转场重叠只计算一次。TransitionSeries会缩短相邻序列的并集；固定母版预算也可用全局Sequence中的mask／共享对象转场。相邻媒体在淡化区间仍有可播放源帧；不能同时透明闪底。细节见[连续性](playback-continuity.md)。

## 从参考到可用组件

地图、数据、图解、手绘、口播同步、拼贴与标志动作按[内容模块](content-motion-modules.md)路由；相应支持按[安装清单](installation-and-support.md)补齐。D3／Rough／Mermaid提供运算或SVG，不引入独立播放时钟。

保留参考机制的关键形态／速度关系，并按本句阅读量改编。Canvas／WebGL上游实现移植后验证乱序采样；依赖、纹理与字体同步到制作工程。复用代码保留上游许可和改动说明。

基础组件：SharedElement、MediaCard、TracePath、TornMatte、MonochromeLight、Dust、RevealText。配方中的水墨、真实3D、图表等需按项目补实现。CSS blur只能标近似；真实运动模糊按当前Remotion版本验证，避免快门采样跨硬切污染。

3.1另附`src/style-directions.tsx`：FocusLens同源坐标放大、morphContour等拓扑轮廓插值，以及三个原创方向样片。Composition为ArchiveDirection、MorphDirection、DepthDirection（各6秒）或StyleDirections（三段合计18秒），1920×1080／30fps／无声。示范的港口、航线和文案均非历史证据；这是机制起点，不是所有影片的固定模板。

`npx remotion render src/index.tsx StyleDirections out/style-directions.mp4 --codec=h264 --muted --color-space=bt709`。追溯与实测范围见工程的`style-directions-usage.json`。

## 画面检验与完成

1. 结构：`validate_storyboard.py`查原句关联、连续帧段、媒体窗口和声明策略；不证明审美或实际像素。
2. 静帧：选关键动作前中后、落定、转场中帧，看中文、证据、遮挡、边缘、安全区及所选风格识别特征。
3. 动态：看包含复杂交接的连续代表片段，检查速度、注意力、原声落点、黑闪／跳帧。全片成片任务还检查全片叙事与音轨；只有连续帧采样能力时明确检查范围，不能冒称实时播放。
4. 修复：按影响排序记录时间码、可见缺陷、改法和复检结果；严重缺陷清除且请求的完成标准满足后交付，不无限追求自评分。
5. 输出：核对总帧数、规格、音轨及实际可见媒体使用表。按真实指纹续跑，输出报告未做的检查。

`verify_master_media.py --width W --height H --fps FPS --audio none/required/either --expected-frames N`用于H.264 High／Rec.709 MP4技术检查，参数来自项目，旧1440p60静音默认不限制其他交付。

重滤镜、粒子、3D先用真实镜头测耗时，静态纹理可缓存。长片顺序分段，资源不足先降低并发；预览规格和正式规格分别记录。最终交本次要求的文件、可复跑源码／锁文件、分镜／风格与采用记录；有待检查项就准确注明。
