# 视觉参考路由

新片分析先扫描本页全部重点来源、内容模块与已有补充参考，再依文案选择需要深入的具体文件。重点来源为17个Git仓库及1个网页案例索引（2026-10-17核对），版本与许可见[motion-sources.json](motion-sources.json)。全量考虑不等于全部使用，也不要求安装整套外部Skill。用`query_motion_library.py --catalog`取得完整清单，按[导演流程](storyboard-direction.md)记录文案适配依据。

## 风格、编排与镜头来源

| 来源 | 具体读取入口 | 采用方式 |
|---|---|---|
| [xilo-opus-video](https://github.com/Kianzzz/xilo-opus-video) | `skills/xilo-opus-video/SKILL.md`；`references/plan-format.md`位于该技能目录 | 内部比较必要的构图／材料／叙事方向，以代表预览检验选择；对用户按本技能约定交统一体系的5页PDF，不强制三种风格或视频菜单 |
| [lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar) | `styles/README.md` → `styles/<slug>/STYLE.md` | 材质、光照、相机和风格识别特征；当前索引51种。历史证据优先查archive-lighttable、halftone-dossier；艺术表达查ink-wash、engraving等。先确定本片叙事再读demo |
| [mg-styles-15](https://github.com/Vincentwei1021/mg-styles-15) | `prompts/<id>.md` → `demos/<id>/`；`rubric.md` | 15种MG的识别特征、变形和运动细节。重点查08-morph、06-collage、02-line-art、03-isometric、05-cel-boil；提示词与源码是研究材料，10秒样片不是本片时长 |
| [dashi-animationstyle](https://github.com/chuspeeism/dashi-animationstyle) | `SKILL.md`、`knowledge/风格卡模板.md`；`styles/<风格>/风格卡.md` | 口播概念变可见事件，颜色／字体／质感形成风格卡。七套成套模板与研究条目分开；15–60秒是上游使用定位，不限制本片长度 |
| [huashu-art-motion](https://github.com/alchaincyf/huashu-art-motion) | `references/风格配方/INDEX.md`、`references/09-视频动画语法.md` → 指定风格卡或`动画语法/y2_vox.md`、`y6_presenter_explainer.md` | 艺术材料与9种解释语法；区分实做、研究配方和已移植组件。艺术元素本身的运动与解释动作结合 |
| [wtt-code-animation-studio](https://github.com/WaterDJiang/Wattter_openSkills/tree/main/wattter_skills/wtt-code-animation-studio) | 技能内`SKILL.md`、`references/story-and-timing.md`、`references/visual-recipes.md` | 个人非商业场景可选。借鉴从想法到可视动作的拆解、主体身份、声音与画面共用事件数据；已有定稿与录音时跳过重写／配音，衔接本技能场景数据 |
| [video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft) | `gallery/api/library.json` → `references/shots/<id>.md` → 卡中指定demo源码 | 2.5D运镜、素材卡聚焦、堆叠与空间交接。将产品页面换为实际证据素材；卡名／style-key须解析，不能仅凭名称声称复现 |
| [Herk Edit Kit](https://github.com/nateherkai/herk-edit-kit) | `.agents/skills/style-library/SKILL.md` → `style-library/GUIDE.md`、`registry.json` → 所选风格的DESIGN.md／tokens.css／style.json | 原HyperFrames Student Kit；406张草稿卡。提取贯穿主体、共享设计参数、按目的检索、文字槽位与透明叠加；适配为Remotion，不继承固定黑底、快切、强制持续运动或AIS品牌 |
| [Prompt Motion · Charts](https://prompt-motion.com/?tag=charts) | 图表分类 → 具体案例页 → 原作者／源码；本地`prompt-motion-charts/index.json`可检索 | 当前33个分类条目。已读[纸本图表](https://prompt-motion.com/ik-builds-b8bdcf)及[令牌桶机制](https://prompt-motion.com/parkerrex-1a54fe)文本；提取共享参数、状态演化与图解方法。网站不是可导入代码库，原视频未逐条观看 |

Wtt上游根README声明CC BY-NC-SA 4.0；保留来源、署名及适用许可。个人身份不会自动改变许可；本技能不额外添加禁用或逐次确认门槛。改编／分发第三方内容时保留其许可，不把同一许可套给用户所有原创成片。Dashi示例配音不在其MIT许可内；实际生产沿用用户原声。

## 内容表达与运动检查来源

具体适配与确定性时间轴规则见[内容模块](content-motion-modules.md)，支持包见[安装清单](installation-and-support.md)。

| 来源 | 具体读取入口 | 由文案触发的采用方式 |
|---|---|---|
| [iart-map-animation](https://github.com/iart-ai/map-animation-skills) | `skills/map-animation/SKILL.md` | 地点、路线、疆域、迁徙：真实坐标／GeoJSON，frame驱动地图与路径 |
| [iart-data-animation](https://github.com/iart-ai/data-animation-skills) | `skills/chart-animation/SKILL.md`、`skills/animated-infographic/SKILL.md` | 数量比较、趋势和排名：D3算几何，React绘图，同一数据驱动标记和标签 |
| [iart-explainer-video](https://github.com/iart-ai/explainer-video-skills) | `skills/diagram-animation/SKILL.md`、`skills/whiteboard-animation/SKILL.md`、`skills/isometric-animation/SKILL.md` | 因果、流程、结构：节点／边／层逐步解释，Mermaid结构稿与手绘须重套本片tokens |
| [iart-javascript-animation](https://github.com/iart-ai/javascript-animation-skills) | `skills/javascript-animation/SKILL.md` | 可程序表达的物体与事件：移植纯时间绘制函数，不启动独立播放循环 |
| [doodle-anim](https://github.com/Feitangyuan/doodle-anim) | `SKILL.md` | 人物动作解释概念：固定角色身份、骨架、步态与事件，外观服从全片风格 |
| [video-talkcraft](https://github.com/Vincentwei1021/video-talkcraft) | `SKILL.md`、`references/taxonomy.md`、`references/design-language.md` | 原声语义拍与多素材编排；可靠时码可直接复用，不强制ASR、删停顿或恢复字幕 |
| [vox-director](https://github.com/Alisa0808/vox-director) | `SKILL.md`、`references/prompt-guide.md`、`references/beat-layer.md` | 图片并置、拼贴与生成图扩展：先建立静态阅读路径，再用Remotion编排层次；不必安装其外部付费服务 |
| [pixel2motion](https://github.com/nolangz/pixel2motion) | `SKILL.md` | 标志／徽记成为动作对象：保留身份、低复杂度SVG、检查轮廓与中间态；已有矢量优先直接使用 |
| [emil-design-skills](https://github.com/emilkowalski/skills) | `skills/animate/SKILL.md`、`skills/review-animations/SKILL.md`、`skills/animation-performance/SKILL.md` | 审查运动目的、缓动、连续性和真实渲染性能；网页交互规则不无差别移入视频 |

上述新增来源已核对文本方法；缓存可读不代表已移植代码或已观看全部演示。Talkcraft采用PolyForm Noncommercial许可，其他许可以固定版本文件为准。

## 适配到本片

把来源中的设计意图落为：`source_id → 原句 → 视觉特征 → 动作起末状态 → 组件 → 证据`。记录URL、commit、具体文件、改编差异和planned／implemented／rendered／reviewed。只读文本就标文本参考，未查看成片不写“动态已看”。

Remotion是统一实现方式：外部Canvas纯时间绘制可改为frame函数，SVG路径／形变用帧采样，Three.js与Lottie接入Remotion控制。项目运行包按实际需要安装，参考源码并不自动成为可导入组件。

作者的模型分档、固定配色／镜长、持续运动配额、审批站点、营销／发布引导和自动配音不作为本技能规则。保留真正有用的风格特征和实现条件，项目的原声、字幕与素材策略优先。

## 已有补充参考

- [Remotion官方](https://github.com/remotion-dev/skills)：时间轴、媒体、转场与版本API。
- [motion-video-kit](https://github.com/echris6/motion-video-kit)：对象身份与跨镜状态接力。
- [motion-graphics-skills](https://github.com/charlie947/motion-graphics-skills)、[motion-broll](https://github.com/Barty-Bart/motion-graphics)：拼贴证据和口播落点。
- [Klik](https://github.com/t3knobox/klik-anim-skill-creation)、[iart](https://github.com/iart-ai/motion-design-skills)：观看路径与视觉导演。
- [claude-remotion-skill](https://github.com/haidrrrry/claude-remotion-skill)、[LottieFiles](https://github.com/LottieFiles/motion-design-skill)：揭示、错峰、层间编排。
- [product-launch-motion](https://github.com/AbubakrChan/product-launch-motion)、[claude-motion](https://github.com/whaleyxbt/claude-motion)：物体连续与cue表。
- [v2版式](v2-templates.md)、RVE、Scenes：按信息关系补结构。
- 旧注册线索[animate](https://github.com/cth9191/animate)、[claude-motion-design](https://github.com/howseen-ai/claude-motion-design)、[hyperframes-motion-reel](https://github.com/Sunwood-ai-labs/hyperframes-motion-reel-skill)：本轮未重新核对具体能力或组件，分析记录中保留为待核实来源；只有与文案需求相关时再核实原文，不把仓库名称当已实现效果。

检索脚本 `query_motion_library.py <关键词> --library <名称>` 返回原文件；需要复用代码时核对该文件及许可。未选来源不加入项目依赖，不载入整套说明。

Prompt Motion用`bootstrap_motion_libraries.py --library prompt-motion-charts --install-missing`建立公开案例元数据索引，不批量下载视频或复制提示词。作品归原作者，具体代码／素材许可按原出处核对。Herk旧别名hyperframes-student-kit保留兼容，新任务优先用herk-edit-kit；不要同时加载两套相同资料。
