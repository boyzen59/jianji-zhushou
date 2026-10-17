# jianji-zhushou 3.0

中文文案驱动的视觉导演与 Remotion 制作技能。覆盖风格、地图、数据图表、解释动画、手绘、拼贴和标志动作，包含按需参考检索、录制与文字审阅工具。

显示名称为 `jianji-zhushou 3.0`，调用 `$jianji-zhushou`。安装目录为 `~/.codex/skills/jianji-zhushou/`。入口：[SKILL.md](SKILL.md)。

安装时先看[支持清单](references/installation-and-support.md)：Python版本、Node／Remotion、功能库及会调用的技能。运行`scripts/check_installation.py --project-root <制作目录> --feature all`查看缺项；需要一次补齐时用`scripts/setup_support.py --project-root <制作目录> --feature all --install --with-references`。依赖安装到制作工程，不放入技能目录。

创作硬约束：先完整分析文案；分析时全量参考能力目录、执行时按文案选用；全片坚持唯一风格卡与共享tokens。自主糅合图、表、拼贴、图解与生成图扩展，不硬套模板或追求效果配额。风格选择直接交5页视觉PDF；已定风格沿用。按请求完成计划、审阅、局部动画或成片，不要求每次都跑完整流程。

- [制作默认值](references/production-defaults.md)：原声、10秒AI视频、真人、字幕区、文字校对。
- [内容模块](references/content-motion-modules.md)：按文案糅合地图、数据、图解、手绘、同步、拼贴与标志动作。
- [参考路由](references/motion-reference-index.md)：原有来源及iart子库、Talkcraft、Doodle、Vox、Pixel2Motion与Emil的具体入口。
- [Remotion制作](references/remotion-production.md)：随附基础组件与工程使用方法。
- [官方指导依据](references/maintenance-basis.md)：本次精简依据、适用范围。

外部项目按原许可证使用；wtt纳入个人非商业使用参考，保留来源与许可说明。通用包不携带示例配音或私人项目。可选旧版式与第三方资料的原许可证继续保留。
