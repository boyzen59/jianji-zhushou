# 按文案选择动效模块

这是本技能的执行路由。先读完整文案，再把每段的新理解映射到可见对象、关系或变化。可以混合下列模块；共用项目色彩、字体、材料、对象身份和运动曲线。现有5页风格选择方式不变。

本表与完整[参考目录](motion-reference-index.md)在新片分析时全部纳入候选视野，再按文案决定采用、不采用或待核实。不是在表里轮流选效果，也不因缺少可选安装包而提前排除合适表达。覆盖记录和进入制作条件见[导演流程](storyboard-direction.md)。

| 文案在做什么 | 优先入口与具体资料 | 落到Remotion的方式 |
|---|---|---|
| 说明地点、迁徙、贸易、疆域 | iart-map-animation：`skills/map-animation/SKILL.md` | 用有来源的GeoJSON／坐标构造SVG地图，投影、路线与区域强调由frame驱动。历史疆界使用对应时期数据；镜头动作不改变地理关系 |
| 比较数量、趋势、规模 | iart-data-animation：chart-animation、animated-infographic | D3计算尺度／轴／路径，React绘制；数值、图形和标签使用同一采样值。排名改变时保留对象ID；标单位、时间和出处 |
| 解释流程、因果、组成 | iart-explainer-video：diagram-animation、whiteboard-animation、isometric-animation | 从原句生成节点／边／层数据；按解释次序揭示。Mermaid可起结构稿，正式SVG按项目tokens重排；拆层保持连线、基准及阅读停留 |
| 让抽象概念由人物演出来 | doodle-anim；iart-javascript-animation | 角色ID、骨架、步态、表情和事件分开；Canvas在每帧重建，姿态=f(frame/fps)，固定seed。移植绘制函数，不运行独立播放循环 |
| 原录音关键词触发多素材动作 | video-talkcraft：taxonomy、design-language | 先按素材类型、再按语义拍选配方；对齐已有录音，把cue写回本技能场景数据。沿用全局媒体时钟、真人和字幕策略，文字换页不重启视频 |
| 用图片／史料并置论点 | vox-director：prompt-guide、beat-layer | 先完成静态层级与观看路径，再做抠图、遮罩和对象接力。内置GPT生图可补原创插图；原史料保留原图层，重建／示意另标，文字不烧进背景 |
| 标志、徽记、图标成为转场对象 | pixel2motion：SKILL.md | 先保留原图形身份，再得到低复杂度、语义分组的SVG；检查拟合与轮廓中间态，用路径／mask／共享对象制作动效。现有SVG优先直接编辑 |
| 运动生硬、装饰抢注意力或渲染慢 | emil-design-skills：animate、review-animations、animation-performance | 检查目的、曲线、方向、遮挡与运动连续性；用实际渲染时间和画面定位问题。网页的触控／hover规则只在真实UI镜头需要时采用 |

## 进入工程

1. 在项目风格卡登记共用tokens与已经决定的视觉方向。
2. 每镜在现有narrative_intent／reference_uses中说明表现形式为何适合该句；共用参考只登记一次，镜头记录差异。
3. 选中模块后读具体原文和所选代码；用 `query_motion_library.py "<关键词>" --feature maps` 等命令缩小检索。功能与安装支持的名称见[安装清单](installation-and-support.md)。
4. 将方法适配为本工程组件，登记原文件、commit、改编与验证证据。参考可读、源码适配、样片通过分别记录。
5. 检查关键帧、转场中帧及连续片段；需要正式成片时完成实际音画检查。

## 三个代码库怎样使用

- **D3 7.9.0**：只负责数据运算、投影和布局。动画不用D3独立timer／transition；力导向布局先固定seed、停止计时器并预计算，再按frame采样。
- **Rough.js 4.6.6**：手绘线、圈注和填充；每个对象有固定seed。若刻意使用boil，按秒量化线条变化，避免每帧重新随机导致闪烁。
- **Mermaid 12.2.0**：把关系起稿为SVG。统一字体与颜色，给需运动的节点和边稳定ID；复杂布局可改写为React/SVG，不把独立网页播放当视频时间线。

这些是可用的安装基线，新项目通过lockfile固定。已有项目保留验证过的版本，选用不同API时先适配，不因参考版本而整体降级。

## 适配边界

原稿、原录音和本技能项目策略优先。上述来源的固定片长、快切配额、自动删停顿、默认字幕、强制苹果风、每镜边框、先审批样镜、营销文字及默认外部API不成为通用规则。Vox的拼贴方法用现有图像工具与Remotion落实，Atlas Cloud／Fish Audio不是本技能安装必需项。录音对齐不足才启用ASR；已有可靠时间戳直接复用。

代码源按原许可保留来源；不额外添加个人使用禁用流程。未提供可直接适配的组件时先实现并验证相关镜头，不把文档缓存称为已移植代码。
