# 版式与动效路由

版式来自文案结构和 [v2 模板](v2-templates.md)；主动作来自用户采用的 VIDEO SHOTCRAFT 规则。三套動效源码和 v2 完整源码留在外部缓存，按需读取实际模块，不复制整套默认主题进成片。

## 主题化实现与记录

先复用已批准模板和实际动效。按解释需要增补运动，落定时回到原卡片/人像/图片几何；不以新增特效为由重新排版。布局与动作分别记录layout来源、主配方、demo源文件、实现路径和渲染状态。项目有占比目标时在项目配置中统计；不把一次项目的比例强加到所有视频。

非AI视频镜优先选合适的Shotcraft配方；RVE/Scenes补充其不足。图像横推、缓移、放大与卡片/关系线动效配合，但不同配方应保留可观察的不同运动语法。AI视频保持原运动，卡片稳定或短入场，不持续套静态图视差/翻页。

图片整段运动与分论点独立分组按[播放连续性](playback-continuity.md)执行；项目禁用的版式和定格效果优先于下方候选表。

先定位实际配方卡和demo，再移植所需模块；去掉原品牌、UI、假数据和主题。只写效果名、下载缓存或静态PDF不算运行。可用短样片验证新动作，已经批准且输入未变的镜头不用重复制作。相邻动作避免机械重复，但不能为去重改掉锁定版式；固定章卡允许跨不同边界复用。

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
