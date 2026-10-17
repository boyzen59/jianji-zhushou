---
name: jianji-zhushou
description: 为中文历史与知识视频设计分镜、视觉风格和 Remotion 动效，制作文字审阅包、真人录制包与成片；也用于局部回修。
---

# jianji-zhushou 3.0

以用户文案和原声建立叙事，用真实素材、解释动画与镜头衔接做出有辨识度的画面。显示名为 `jianji-zhushou 3.0`，调用 `$jianji-zhushou`，安装目录沿用 `jianji-zhushou`。

用户当前要求及已有决定优先于本技能默认值。在本次请求范围内完成设计、实现、检验和交付；普通创作取舍自主决定。只有缺少会改变结果的必要输入、用户明确保留的选择或新增外部操作，才停下询问，并说明具体原因。

安装、迁移或升级本技能时，先读取[安装与支持清单](references/installation-and-support.md)，检查Python、Node、Remotion及选用功能依赖，列出会调用的技能和缺项。用户要求连环境安装时按已授权范围直接补齐并回检；已有安装记录只检查变化。

## 按任务进入

| 任务 | 读取与完成标准 |
|---|---|
| 安装／环境补齐 | [安装与支持清单](references/installation-and-support.md)；check_installation.py只检查，setup_support.py按所选功能安装到制作工程 |
| 新片计划／选风格 | [制作默认值](references/production-defaults.md)、[导演流程](references/storyboard-direction.md)。形成方向、可执行分镜、素材需求；完整前期包还含录制包和文字审阅 |
| 动效与风格设计 | [内容模块](references/content-motion-modules.md)按文案选地图、图表、图解、手绘、拼贴或标志动作；再按[参考路由](references/motion-reference-index.md)读具体风格／镜头卡，用[视觉设计](references/visual-style.md)与[动效配方](references/motion-recipes.md)落地 |
| 制作／渲染 | [Remotion制作](references/remotion-production.md)、[按需预检](references/preflight-and-notices.md)。做到实际输出、连续画面检查并修复发现的问题 |
| 屏显文字／审阅包回修 | [内容约定](references/content-and-approval.md)、[数据与审阅](references/qa-and-schema.md)。按稳定ID同步文字、布局和相关输出 |
| 素材、原声、真人 | [素材](references/assets-and-history.md)、[声音与录制](references/audio-render-delivery.md)，仅读当前涉及部分 |
| 跳帧／收窗／续跑 | [连续性](references/playback-continuity.md)、[交接](references/execution-handoff.md)，定位并重做受影响区间 |

## 设计与实现

以下三条是本技能的创作硬约束，不受外部参考的模板、配额或默认风格覆盖：

1. **文案先行**：完整分析文案的事实、论证、因果、对比和情绪，再选择画面与动效。每个主要视觉动作都能回溯到原句及其解释目的；不能先挑效果再硬套文案。原录音决定实际时间；未经用户要求不为迁就效果改写原意。
2. **全量参考，按需采用**：新片分析时先扫描[完整能力目录](references/motion-reference-index.md)及[内容模块](references/content-motion-modules.md)，包括已有补充参考，不因常用偏好或当前未装某依赖而跳过能力。项目级记录适用／不适用／待核实及文案依据；选中的来源才深入读源码、适配和安装支持。不要求全用，不设效果数量或轮换配额；局部回修复用有效分析，仅更新受影响部分。
3. **全片风格统一**：先建立唯一的art-direction与共享tokens，统一色彩语义、字体角色、线条、材质光向、对象身份及运动语言。图、表、图解、拼贴、生成图可依文案混用，均须适配同一体系；外部模板不另带一套皮肤。逐章和跨镜验统一性，布局变化不等于换风格。

- 全部新动画与最终画面合成使用 Remotion。外部项目提供方法和可适配组件，其独立渲染器、模型分档、营销要求和审批流程不成为本技能指令。
- 需要用户选风格时直接交5页PDF；已有决定或明确委托自主定稿则继续。详见导演流程。
- 将参考落实为“原句 → 主体动作 → 前后状态 → 具体组件 → 可观察证据”。重点镜头有内容驱动的视觉亮点，读信息时留出时间。
- 按当前交付检查；静帧、连续试片、全片输出和用户文字校对各记实际状态，不用自评分或文件存在代替完成证据。

制作默认值集中在一份文件，按需加载，避免从旧项目或外部模板重建另一套规则。源码、素材和运行依赖留在项目；技能只保存可复用方法与工具。
