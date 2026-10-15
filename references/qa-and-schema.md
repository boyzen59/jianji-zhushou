# 场景数据与审阅回修

## 唯一数据入口

正文、原声、章节、素材、屏显修订和翻译分层保存，共用场景ID与稳定REV。场景至少含：
- 原声起止与成片起止、时基名称、start_frame/end_frame_exclusive、镜内settled_frame。
- 对应正文句/句ID、layout来源/ID、reference来源/具体文件、mechanism、adaptation、Remotion组件/实现路径、engine=remotion、真人安排。
- narrative_intent、触发词/cue精度、motion_beats（主体、参数、开始/高潮/落定帧）、transition_in/out（持续对象、位置/尺度/速度、重叠和时基）、阅读停留与验证状态。validator只证明数据结构。
- texts数组：稳定字段id、role、zh/en、原稿/用户修订来源及落实状态。
- media_layers数组：asset_id、真实路径、源入点、成片可见区间、位置/尺寸/裁切、层级；纯图解场景可没有媒体图层，但不能留下空媒体容器。

只向画面投影title、point、source、chart_label等内容角色；旁白稿用于录制与时间定位，旧逐句字幕字段不迁入texts。3.0默认subtitles.mode=off，旧SUB记录留在对齐资料，不因旧PDF中出现过而投屏。内容角色和禁用标签见content-and-approval.md。缺失人工原稿与已批准状态分开记录，不能用旧草稿填成“已恢复”。

内部帧区间右开：首帧为0、相邻边界相等、每镜至少一帧，落定帧在镜内；章卡时长按当前文案与项目决定。所有帧由绝对时间边界统一量化，不逐镜累加误差。素材可读只代表技术就绪，不等于语义/视觉/人工审批已通过。

## 可机器检查的分镜数据

`assets/templates/storyboard-example.json`是两镜结构示例，非用户原稿、非已实现工程。新增分镜数据使用schema_version=5（不是Skill版本号），root含engine、fps、duration_frames、production_policy、source_sentences、reference_sources和scenes。旧schema4兼容读取但提示未验证3.0策略。帧率此校验器支持整数1–240，不悄悄将29.97变为29或30；需其他时基时先适配实际工程。

production_policy记录subtitles（mode=off、reserve_space=true、safe_area归一化x/y/width/height）、ai_video（source_in_seconds=0、duration_seconds=10、playback_rate=1、plays=1）、presenter（opening_fullscreen_seconds=15、later_mode=bottom_right_pip）及review（storyboard_approval_required=false、word_language=zh、pdf_aspect=16:9、english=placeholder_until_zh_revision）。未来明确修改默认值时记录用户覆盖依据，不从外部Skill推定授权。

当前校验器严格验证这些3.0默认值；未来用户明确变更时须同步适配项目校验，不能以校验器旧值否定用户新指示。它只检查策略声明，不验证真人实际露脸时长、安全区像素避让或英文是否经过人工校对；这些由执行布局与验收核对。使用pending模式不意味着素材可渲染。

每个media_layer写kind、asset_id、availability（pending/available）、path（pending可为空）和可见窗口。AI视频另写playback_id、source_in_seconds、source_out_seconds、playback_rate；其播放窗口持续10×fps帧。跨多个语义场景引用同一播放使用相同playback_id与全局窗口，不重建/重播；同一asset不能悄悄换playback_id重复用。计划允许pending；`--check-files`是到位检查，pending必须报缺项。区间字段声明可见不代表实际像素已可辨认，须执行阶段验证。

reference_sources.origin区分user_supplied、supplementary、legacy。每镜reference_uses含source_id、status(adopted/considered_not_used)、mechanism、reason、adaptation；至少实际考虑用户收录的参考。没有采用时写original_design_reason，不为通过校验伪造使用记录。

镜内motion_beats使用全局帧的start_frame/peak_frame/settled_frame；跨镜动作写transition_in/out的window_frames，不伪装成镜内越界。shared转场两侧使用相同object_id、boundary_state和全局窗口；boundary_state记录边界的坐标、尺度和速度，其连续不代表软件已经验证视觉上平滑。

运行：`python scripts/validate_storyboard.py <storyboard.json>`；`--check-files <素材根目录>`额外检查媒体真实路径。结构验证不读取文意、不证明参考已认真学习，也不能认证审美；渲染和实际观察仍须单独记录。

## 默认交付和文字登记

默认前期包是导演执行MD、选用/备用/待生成素材清单、完整真人录制包、中文屏显文字Word、16:9文字画面PDF和ID映射。分镜由导演定稿，不要求用户审批；文字须留给用户校对。只完成当前请求的部分时注明其余已有交付位置，不无故重建。

登记每项实际可见文字：片名/章节、开头浮动字、真人小窗关联说明、人物地名、年月日/数字/单位、图表标签/图例、关键词、引文、史料题注与来源、必要声明；包括动态中间值的来源和终值。中文Word为唯一人工修改入口，保留稳定ID、场景/时间索引、中文原值与可修改正文。字改后重排对应画面并从中文生成英文，不能用旧英语逆向覆盖中文。

图片/地图本身可辨识的内嵌文字须另登记并标“素材内嵌，非直接可编辑”，对原文给中文语义及处理方案。计划阶段未检查真实素材的，写待执行转写，不声称这些也已全部审过；必要时在执行中按用户修正做覆盖重排或换素材，不伪造史料。排版页脚、REV、页号、占位说明是审阅辅助层，不入片、不混成正式屏显登记。

## 16:9文字画面PDF

PDF是视频构图中的文字截图参考，不是文字清单、分镜表或文档截图。每页16:9，使用与执行MD一致的镜头语言、动效模块、字体比例、构图锚点及层级；标准设计坐标1920×1080，按实际规格缩放。记录文字x/y/width/height、字体/颜色和出现模式。画面文字可作为Remotion静帧渲染；中文编辑在Word，不能把PNG冒充可编辑对象。

- 每个不同文字组合/布局有落定状态；开场浮动字、形变或入场方式影响理解时加必要的中间状态。同一文字长期不变不按每条SRT重复造页；字幕关闭时不渲染CN/EN逐句字幕。
- 英文标题/说明预留位置，EN正文为空，不提前定稿翻译。字幕安全区单独保留，可在仅审阅层标示边界；这与必要屏显文字的英文预留位置是两件事。正式画面关闭所有占位/边界标签。
- 已有素材按需用于构图；AI视频、图片或真人未到位时用有内容的示意占位，明确说明只是位置/层次参考。计划阶段不为了填PDF调用生成服务，不批量反复检查素材，不输出动态模板预览。
- 页脚给scene_id、源/成片时间、text_ids、出现模式、入场/落定状态；不覆盖有效画面。加章节书签和ID→页码索引。中文Word、屏显注册表、PDF文字/位置映射来自同一数据源。
- 核对所有拟上屏文字ID被覆盖、实际渲染文字与登记一致、16:9页幅、长字换行、英文预留、人物及字幕区避让；检查最终PDF页面的可读性与裁切。明确检查范围。静帧只能证明采样状态的排版，实际动效在执行阶段检查。

## 可编辑PPT

仅在用户要求PPT时每镜一页PPTX，采用最后稳定构图；用户选择PDF则输出PDF，不能自动追加PPT。静态预览记录早先媒体序列；需要审阅运动时交实际动效样片。
- 文本、卡片、箭头/连线及有真实数据的图表用原生可编辑对象；图片独立可替换。不用整页PNG冒充可编辑PPT，不把画面文字烧进背景。
- 玻璃以半透明淡黑形状近似；必要局部折射可用无文字效果图，文字和容器仍可编辑，备注说明预览近似。
- 备注写REV、页序、章节、时码、素材序列和未决事项；独立索引用于检索，画面不叠审阅信息。镜内早先出现的素材保留在备注/使用清单，不能因为落定帧没显示就从视频删掉。
- 对象使用REV-0001.heading.zh、REV-0001.heading.en、REV-0001.asset.main等稳定名称；页面重排后按REV识别，不按页号猜对应关系。
- 回写读取文字、位置/尺寸、字体/颜色、裁切和层级变化；更新关联英文。新增、删除、复制对象记录差异，无法确定的映射只列具体缺口。

## 中文Word

默认Word只校对实际屏显中文，不交分镜审批表，不把全部旁白SRT作为待校字幕。原文完整台词另放真人录制包/内容档案。Word不放英文栏或双语截图；只有英文的必要字段给出可修改中文语义。稳定ID保持不变，允许一个文字ID对应多张画面，不强求Word一页等于PDF一页。用户回传后按ID记录修改、更新全部出现位置和关联英文；无法匹配的新增/删项列具体差异。只有用户另行要求才做分镜Word或英文定稿审阅。

## 轻量检查与续跑

按请求一次生成完整审阅包；样张仅在用户要求时生成。按交付类型检查可读性、溢出和来源映射；用户负责审阅决定，不以人工审阅为由跳过必要检查，也不反复改写已批准文字。
一次检查文件可打开、页数/REV/对象映射、实际路径、完整帧覆盖、允许角色、真实数字来源、参考落实及相邻镜头衔接。AI覆盖从media_layers的有效区间统计，按[素材规则](assets-and-history.md)分别报告已分配/已输出；不靠仅存在路径证明全部使用。章节衔接按当前项目安排，不以重复旁白或无意义镜头凑变化。

回修只更新受影响字段、翻译、页和渲染段；项目指定REV意见留在项目回修清单，不写成通用镜头。检查点以输入指纹追踪：文件存在不等于输入未变，已完成计划也不得被无条件重建。技术/内容待办分别记录，不把工作版称为全部终审通过。母版ffprobe只证明流参数；像素中无烧字幕不能由它单独证明，需渲染配置/角色约束配合。
