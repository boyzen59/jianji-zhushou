# v2 模板：筛选后的历史视频版式

来源：[feicaiclub/video-spec-builder](https://github.com/feicaiclub/video-spec-builder)，用户的 [v2.pdf](../assets/reference/v2.pdf) 为 48 页组件设计参考。它是排版/组件规范 PDF，不是可直接编辑的 PPTX；本 Skill 将可用结构编入下表，供分镜及程序化视频选用。

## 调用方式

1. 按文案的关系类型选下表版式，在场景记录 layout ID 和 PDF 页。
2. 用查询脚本找到外部 video-spec-builder 源码的函数和文件；只读所需组件，提取结构。
3. 用 [card.css](../assets/templates/card.css) 的历史样式或等效实现覆盖容器；字段由场景数据提供。
4. 动画按 video-shotcraft 路由实现，记录真实 motion 来源。上游 JSX 多为展示代码，有页面包装和运行时依赖；移植目标片段后需要编译，不能把“缓存已下载”说成“已完成镜头”。
5. 审阅将结构重建为PPT原生对象，图片单独放置；保留参考PDF，新的PDF仅按用户明确请求另出。

数据与视觉约束统一见SKILL.md；不把原模板主题、示例值或入场方式一并继承。

目录不是刚性轮换表。结构有帮助就用，内容不适合可自由设计。下表合并 v2 的重复光谱/迷你图条目，并删除与当前历史剪辑无关的技术 UI。

## 可用结构索引

源文件均相对外部缓存的 `video-spec-builder/Full Code/sections/`。

| 版式 ID | v2 页 | 用途与需提供的真实内容 | 源文件 |
|---|---:|---|---|
| keyword-sticker | 5 | 独立关键词强调；概念词与解释，不跟读整句旁白 | aroll.jsx |
| concept-card | 6 | 一项制度/术语定义；标题、解释、必要出处 | aroll.jsx |
| flow-chart | 7 | 顺序步骤；节点和依赖方向 | broll-structure.jsx |
| pyramid | 8 | 统治层级；各层名称和关系 | broll-structure.jsx |
| funnel | 8 | 征募/筛选；阶段及有出处的数量 | broll-structure.jsx |
| concentric | 9 | 核心与外围；包含范围 | broll-structure.jsx |
| node-graph | 9 | 势力/制度关联；节点及已知关系 | broll-structure.jsx |
| spectrum | 10、20 | 两种制度间的定位；两极及定位依据，不虚构精确数值 | broll-abstract.jsx |
| big-type | 15 | 主论点重申；一句有效结论，不附章节时长标签 | broll-hero.jsx |
| big-number | 16 | 单项关键数字；值、单位、口径、来源 | broll-hero.jsx |
| pull-quote | 16 | 有来源的历史引文；原义与出处 | broll-hero.jsx |
| inversion-flash | 17 | 短暂修辞转折；仅内容需要时低频采用 | broll-hero.jsx |
| analogy | 18 | 陌生制度与熟悉概念类比；相似点及适用边界 | broll-abstract.jsx |
| black-box | 19 | 机制内部未知；已知输入、输出及不确定性 | broll-abstract.jsx |
| equation | 19 | 因素组合；关系明确的组成项，定性示意须标明 | broll-abstract.jsx |
| iceberg | 20 | 表面现象与深层成因；无比例数据则不用 10%/90% | broll-abstract.jsx |
| versus | 21 | 两种制度对照；相同维度的两组信息 | broll-abstract.jsx |
| line | 22 | 随时间变化；真实时点和值 | broll-charts.jsx |
| multi-line | 23 | 多组趋势；一致单位和口径 | broll-charts.jsx |
| bar | 23 | 分类数量；分类与值 | broll-charts.jsx |
| h-bar | 24 | 排名；有依据的条目和值 | broll-charts.jsx |
| stacked | 24 | 总量构成随时间变化；可加总数据 | broll-charts.jsx |
| area | 25 | 累积趋势；避免把存量/流量混算 | broll-charts.jsx |
| donut | 25 | 整体构成；分母及比例 | broll-charts.jsx |
| scatter | 26 | 分布与相关；真实样本及双轴意义 | broll-charts.jsx |
| heatmap | 26 | 二维强度；行列维度、数值及图例 | broll-charts.jsx |
| gauge | 27 | 有明确量程的指标；值和范围 | broll-charts.jsx |
| sparkline | 14、27 | 多指标概览；每项值及趋势 | broll-charts.jsx |
| sankey | 28 | 税收/资源流向；满足总量关系的数据 | broll-charts.jsx |
| complex | 29 | 较长流程；真实环节与重点，移除假延迟和时码装饰 | broll-flows.jsx |
| branching | 30 | 两路决策；条件和结果 | broll-flows.jsx |
| decision-tree | 30 | 多层判断；有根据的分支 | broll-flows.jsx |
| state-machine | 31 | 制度/事件状态变化；状态和触发事件 | broll-flows.jsx |
| sequence | 31 | 多方交互时序；主体、动作、顺序 | broll-flows.jsx |
| swimlane | 32 | 多主体分工；责任归属与交接 | broll-flows.jsx |
| fork-join | 32 | 多路行动后汇合；分流和汇合条件 | broll-flows.jsx |
| loop | 33 | 循环机制；反馈关系和终止条件 | broll-flows.jsx |
| tree | 34 | 谱系与分类；父子关系 | broll-structures2.jsx |
| mind-map | 35 | 主论点展开；有依据的分支 | broll-structures2.jsx |
| matrix-2x2 | 35 | 双维度定位；轴定义与分类依据 | broll-structures2.jsx |
| venn | 36 | 群体交集；真实集合关系 | broll-structures2.jsx |
| layered-stack | 36 | 制度层次；层名与联系 | broll-structures2.jsx |
| hub-spoke | 37 | 中央与地方；中心和连接对象 | broll-structures2.jsx |
| grid-map | 37 | 示意分布；图例和示意性质，不冒充地理疆域图 | broll-structures2.jsx |
| compare-table | 38 | 多方逐维对比；各方同口径资料 | broll-thinking.jsx |
| swot | 39 | 条件分析；用文稿支持优势/弱点/机会/威胁 | broll-thinking.jsx |
| fishbone | 39 | 多因素成因；问题及证据支持的原因 | broll-thinking.jsx |
| timeline-row | 40 | 历史演进；年代、事件，时间间距与轴说明一致 | broll-thinking.jsx |
| gantt | 40 | 多事件持续期对照；真实起止日期 | broll-thinking.jsx |
| kanban | 41 | 事件按状态分类；仅正文确有这种状态关系时使用 | broll-thinking.jsx |
| card-grid | 41 | 多项要点/人物/史料概览；每项新信息 | broll-thinking.jsx |
| source-citation | 47 | 史料出处说明；书名/作者/年代/页码，可融合进侧栏 | 按 PDF 结构在 concept-card 中实现 |

图标系统（42–43 页）只吸收统一线宽、对齐与语义图标用法；不强制 48 个图标或指定现代科技图标。普通图片/史料大图版式由 visual-style.md 补充。

## 排除与覆盖

- 删除 v2 第 4 页逐词字幕高亮，以及所有浮动字幕/旁白字幕组件。
- 第 11–14 页终端、聊天、浏览器、代码/API 示例不纳入历史版式目录；第 14 页有用的指标结构合并进 sparkline。
- 第 44–46 页整套直播贴片、常驻频道角标、当前说话人、跑马字幕、场记板均不默认提供；必要人物介绍用 concept-card，不带 LIVE/时钟。
- 展示系统导航、页脚B-ROLL、FRAME/BUILD等样张元信息不导入；其余标签范围遵从SKILL.md。
- 第21页素材占位组件不采用，审阅和成片都用有内容的完整构图，缺项写备注/清单。
- 原 PDF 和外部仓库仅供参考，不能整页栅格化当视频成片，也不能将原版黑底、白框和全部禁令自动变成 Skill 规则。
