# 用户收录动效参考的选用

核查日期：2026-10-14。这里是设计分镜和动效时的首要参考索引，不是安装任务清单。文案决定讲什么，参考帮助决定如何表现。先查下表相关具体文件，再把机制、取舍及实际实现记录进分镜；已缓存的资料可直接读。当前集成的是经过筛选的工作方法和本Skill原创Remotion组件，不意味着所有外部引擎/样片已安装或测试。

## 优先进入设计工作的来源

| 来源与读取位置 | 适用阶段与借鉴点 | 在本工作流中怎样使用 |
|---|---|---|
| [remotion-dev/skills](https://github.com/remotion-dev/skills)，skills/remotion-markup/{timing,transitions,motion-blur,3d}.md | 实现、时间轴、媒体和随机访问 | 当前版本API为准；统一frame，核对转场重叠与时长；不继承默认字幕 |
| [huashu-art-motion](https://github.com/alchaincyf/huashu-art-motion)，references/动画语法/y2_vox.md、y6_presenter_explainer.md、镜头表模板.md | 解说分镜、艺术材质、具象动作、讲解员与图形互动 | 把画面里的“物与动作”及拼贴/绘制机制移植成帧驱动SVG/Canvas；不采用其独立渲染器、角色素材与每镜字数/时长硬限制 |
| [motion-video-kit](https://github.com/echris6/motion-video-kit)，business-motion-film/references/motion-grammar.md、quality-bar.md | 前后镜的对象延续、构图层级、结果检查 | 设计同一对象的状态接力与因果变化；把短广告的强度调到中文长解说；不继承商业CTA或静止秒数阈值 |
| [motion-graphics-skills](https://github.com/charlie947/motion-graphics-skills)，skills/{vox-explainer,motion-effects,reference-to-motion}/SKILL.md | 拼贴、视觉参考拆解、图形状态变化 | 学习实物/证据组织、形变和素材揭示；用Remotion重写，不强制网点、禁用光效或8秒循环 |
| [motion-graphics](https://github.com/Barty-Bart/motion-graphics)，skills/motion-broll/SKILL.md | 口播与补充画面同步 | 每段选择关键词落点、全屏/局部/真人留场；保留已有音轨；不强制鼠标UI、“一形永不切”或尾帧冻结 |
| [claude-remotion-skill](https://github.com/haidrrrry/claude-remotion-skill)，remotion-motion-graphics/references/motion-patterns.md | Remotion组件、错峰、揭示、图层处理 | 取适配组件机制并实测；不继承“每图Ken Burns、每元素呼吸、禁止所有线性运动” |
| [klik-anim-skill-creation](https://github.com/t3knobox/klik-anim-skill-creation)，klik-anim/SKILL.md、klik-cam/SKILL.md | 注意力、镜头强度、运动与阅读安排 | 将观看路径、速度峰值、焦平面和主体避让写成镜头字段；不复制整套全局限制或宣称其代码已获复用许可 |
| [iart-ai/motion-design-skills](https://github.com/iart-ai/motion-design-skills)，skills/{motion-art-direction,shot-composition,color-motion}/SKILL.md | 视觉导演、构图、色彩和运动主次 | 建项目风格令牌与能量曲线；不把单一缓动/唯一高潮等偏好变成全片硬规则 |
| [LottieFiles/motion-design-skill](https://github.com/LottieFiles/motion-design-skill)，skills/motion-design/director/{choreography,decision-framework}.md | 主体和辅助动作编排 | 建立动作优先级、错峰及层间速度差；Lottie是可选资产，由Remotion控制播放 |
| [product-launch-motion](https://github.com/AbubakrChan/product-launch-motion)，SKILL.md、references/technique.md | 物体状态连续、运动细节、视觉高潮 | 借鉴容器与内容分别编排、快出慢入等机制；去掉作者私人工程、产品鼠标操作、音乐优先与强制不切镜 |
| [claude-motion](https://github.com/whaleyxbt/claude-motion)，.claude/skills/motion-design 与 review-loop | 统一事件时间表、动效自查、音效cue | 画面、音效和检查共用cue；声音按需要，渲染只用Remotion |

## 有条件借鉴，先移植再使用

| 来源 | 保留用途 | 不进入主流程的部分 |
|---|---|---|
| [cth9191/animate](https://github.com/cth9191/animate) | 剪纸/网点/手绘材质、风格帧比较、物体变形衔接 | 单Canvas播放器、独立录制引擎、层层等待批准 |
| [hyperframes-motion-reel-skill](https://github.com/Sunwood-ai-labs/hyperframes-motion-reel-skill) | 跨镜形态链、高潮层级、事件网格 | HyperFrames执行、固定BPM、音乐覆盖口播 |
| [claude-motion-design](https://github.com/howseen-ai/claude-motion-design) | 确定性、对象交接、转场中帧检验 | HTML/Playwright生产渲染器、逐帧复制他人作品 |
| [hyperframes-student-kit](https://github.com/nateherkai/hyperframes-student-kit) | 按语义查参考卡、贯穿母题、素材审核 | 卡片是草稿不是验收成品；不移入整套引擎和默认字幕 |
| [GSAP](https://github.com/greensock/GSAP)、[Motion](https://github.com/motiondivision/motion)、[motion-dev-animations-skill](https://github.com/199-biotechnologies/motion-dev-animations-skill) | 缓动、状态变形和轨迹思路 | 网页hover/scroll和自主动画时钟；实现优先Remotion原生，必要适配亦须逐帧可seek |
| [lottie-web](https://github.com/airbnb/lottie-web) | 有合适授权的现成矢量动画 | 用@remotion/lottie接入，不直接autoplay；装播放器不等于有可用资产 |
| [pixel2motion](https://github.com/nolangz/pixel2motion) | 用户确有图标/徽记时，分语义SVG、先核对轮廓再动画 | 不把历史照片全转SVG；不复制未核实许可的代码或品牌标志 |
| [lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar) | 按当前叙事挑选电影材质、镜头风格与技术说明 | 默认重新编故事、TTS、Canvas/WebGL独立成片管线 |
| [PDoomVideo](https://github.com/JohnHeibel/PDoomVideo) | 程序绘制、按时间求帧的结构案例 | 音乐MV剧情、歌词、角色与p5渲染管线 |
| [digitalsamba/claude-code-video-toolkit](https://github.com/digitalsamba/claude-code-video-toolkit) | Remotion工程组织、场景审阅与品牌配置思路 | 云GPU/配音/模型API/整套全局安装，不因参考项目而替换用户录音 |

## 检索来源和暂不集成项

- [awesome-motion-design-agent-skills](https://github.com/frankxai/awesome-motion-design-agent-skills)、[opus-video-prompts](https://github.com/joeseesun/opus-video-prompts)、[awesome-opus5-5-videos](https://github.com/yihui-dev/awesome-opus5-5-videos)、[Prompt Motion](https://prompt-motion.com/?tag=charts)：仅用于找到具体案例。索引、提示词和网站不是已就绪组件；本次Prompt Motion页面读取失败，不能声称已经学习其图表代码。
- [Remotion](https://github.com/remotion-dev/remotion)是生产框架；[HyperFrames](https://github.com/heygen-com/hyperframes)是另一框架，只研究设计，不装作本片第二引擎。
- [video-talkcraft](https://github.com/Vincentwei1021/video-talkcraft)：叙事对齐很相关，但当前LICENSE为PolyForm Noncommercial并要求商业使用事先授权；本次不复制/封装其工具或配方。口播对齐由本Skill自有规则及其他已核实来源实现，制作不依赖该项目。
- [OpenMontage](https://github.com/calesthio/OpenMontage)、[hypit](https://github.com/hypit-ai/hypit)、[FireRed-OpenStoryline](https://github.com/FireRedTeam/FireRed-OpenStoryline)：整体视频工作台/编排系统，本次不嵌套另一整套生产流程。
- [chengfeng-videocut-skills](https://github.com/Agentchengfeng/chengfeng-videocut-skills)、[narrator-ai-cli-skill](https://github.com/NarratorAI-Studio/narrator-ai-cli-skill)：剪口播/解说工具链，不是增强当前Remotion动效的必需模块；已有稿和音轨时不接入自动重写、剪音轨或配音流程。
- comfyui-mcp存在多个同名仓库；可在确有素材修复任务且已有兼容服务时另选接入，本次无具体图像修复输入，不加入动画必需依赖。
- ux-ui-agent-skills、oh-my-design、jev-skill存在同名/泛设计项目；awesome-scientific-skills是科研技能索引，均未证明对本次历史视频动效有直接收益，不装入主流程。
- draw-with-code、wise-motion、ge0-sleuth、prompt-master及没有owner的“4.lottie”“5.skills”：截至核查未唯一确认与收录描述相符的项目，不编造仓库或接口。以后有准确链接再评估。
- 搜索未找到可确认为“小lin说官方动效Skill”的仓库。huashu中可核实的“讲解员式财经科普”语法是相近参考，非官方授权或复刻模板；借鉴讲解员/数字/证据互动，保留用户自己的内容和形象。

## 六份Word如何进入制作

- 口播风格提示词：吸收拼贴、手绘线条揭示、数量实体化、绘画过程和参考参数拆解；把p5时间循环/MediaRecorder改成Remotion帧函数。文档称01–07，但实际只见01–06，不补造缺失模块。
- 动效特点与“20个开源项目”合集：去重后按上表核实；后者实际列出9项，不按标题虚构剩余条目，也不以星数评质量。
- 单彩渐变提示词：转换为“单色域调色 → 局部体积光/放射 → 动感模糊收束”的可选视觉研究。剪映0–100参数不是CSS/Remotion单位，需重标定并验画，不能称1:1等效。
- 高级动效开场：吸收底层真实素材、信息辅助层、主动画层，以及素材卡空间关系、大字图形化和形态衔接；原文末尾截断，不补写其未给出的步骤。
- 其他收录：只有能帮助当前文案且来源明确者进入工作流，其余保留核查结果。

## 使用记录

每项使用记录 source_url、source_path/commit（可获取时）、参考机制、适配说明、实现文件、许可证/资产条件及 planned/implemented/rendered/reviewed。当前参考方法可离线从本Skill继续使用；复用第三方代码时读取当前原文与许可，保留必要署名。不同项目能合用的是方法与帧组件，不是互相冲突的全局指令。
