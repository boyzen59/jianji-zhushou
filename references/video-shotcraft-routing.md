# 版式与动效路由

版式来自文案结构和 [v2 模板](v2-templates.md)；主动作来自用户采用的 VIDEO SHOTCRAFT 规则。三套動效源码和 v2 完整源码留在外部缓存，按需读取实际模块，不复制整套默认主题进成片。

## 比例与记录

- Remotion 镜数 / 全部镜数 >75%。
- 每个有主程序化动效的分镜只计一次：Shotcraft 镜数 / 全部动效镜数为 85%–100%，RVE＋Scenes / 同一分母为 0%–10%，其余为原生/自定义。
- 三者之和为 100%；不能同时取 100% Shotcraft 和 10% 补充库。静态/纯素材镜不凑动效占比。
- v2 是版式来源，与动效来源分开记录。使用 v2 时间线排版＋Shotcraft 年代推进时，前者记 layout，后者记 motion；仅抄 v2 动画不能冒算 Shotcraft。
- 保留来源模块及实际实现路径；按源码或明确实现规则使用才记为实际调用。

## 语义候选

| 文案需要 | Shotcraft 候选 |
|---|---|
| 宏观世界、版图 | dataviz-landscape-open、crane-rise-reveal |
| 章节重点、聚焦概念 | spotlight-hero-card、morph-from-primitive |
| 要点推进、关键词传递 | beat-step-list-theme-cycle、word-relay-filmstrip |
| 标题建立与层级变化 | typewriter-moves、title-demote-to-label、text-as-mask |
| 数字、统计图表 | odometer-digit-roll、chart-live-moves |
| 路线、轮廓、时间演进 | draw-svg-trace、timeline-travel |
| 多源汇合、关系中枢 | bezier-source-converge-merge、integration-hub-map |
| 文档、卡片归类 | canvas-materialize-moves、doc-park-left-pill-deal、card-stack、deck-deal-flyin |
| 图像细节、证据展开 | graze-face-tour、page-waterfall-wall、page-turn-transitions |
| 多层结构、面板解释 | depth-layer-moves、panel-grid-moves、value-stagger-gradient、wall-reveal-moves |
| 信息迁移、对象延续 | paper-plane-messenger、line-carry-transition、circle-match-iris、mosaic-reframe |
| 对比与并行叙事 | quad-split-parallel-scenes、card-flip-reveal |
| 强转折、短暂强调 | crash-zoom-punch、fracture、scan-bracket-sweep、speed-ramp-freeze |

候选不是封闭白名单。通过查询脚本查实际模块，按当前文案选最贴切动作；RVE/Scenes 用于补足主库不适合的结构。
每镜以一个主解释动作组织注意力，辅助动作按需。普通相邻镜头的主动作与卡片结构不重复；换名字、文字、颜色或速度不算实质差异。重复信息优先合并或保持为同一镜，不靠多写镜头凑比例。
固定章节卡在不同章节边界复用是例外，每个边界只播一次；章节重点卡不能替换固定过渡。片尾不默认加入品牌按钮、点赞图标或无关UI。
