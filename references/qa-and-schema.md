# 场景数据与审阅回修

## 唯一数据入口

正文、原声、章节、素材、屏显修订和翻译分层保存，共用场景ID与稳定REV。场景至少含：
- 原声起止与成片起止、时基名称、start_frame/end_frame_exclusive、镜内settled_frame。
- 对应正文句/句ID、layout来源/ID、reference来源/具体文件、mechanism、adaptation、Remotion组件/实现路径、engine=remotion、真人安排。
- narrative_intent、触发词/cue精度、motion_beats（主体、参数、开始/高潮/落定帧）、transition_in/out（持续对象、位置/尺度/速度、重叠和时基）、阅读停留与验证状态。validator只证明数据结构。
- texts数组：稳定字段id、role、zh/en、原稿/用户修订来源及落实状态。
- media_layers数组：asset_id、真实路径、源入点、成片可见区间、位置/尺寸/裁切、层级；纯图解场景可没有媒体图层，但不能留下空媒体容器。

只向画面投影title、point、source、chart_label等内容角色；旁白稿用于录制与时间定位，旧字幕/装饰标签字段不迁入texts。内容角色和禁用标签见content-and-approval.md。缺失人工原稿与已批准状态分开记录，不能用旧草稿填成“已恢复”。

内部帧区间右开：首帧为0、相邻边界相等、每镜至少一帧，落定帧在镜内；章卡时长按当前文案与项目决定。所有帧由绝对时间边界统一量化，不逐镜累加误差。素材可读只代表技术就绪，不等于语义/视觉/人工审批已通过。

## 可机器检查的分镜数据

`assets/templates/storyboard-example.json`是两镜结构示例，非用户原稿、非已实现工程。新增分镜数据使用schema_version=4，root含engine、fps、duration_frames、source_sentences、reference_sources和scenes。帧率此校验器支持整数1–240，不悄悄将29.97变为29或30；需其他时基时先适配实际工程。

reference_sources.origin区分user_supplied、supplementary、legacy。每镜reference_uses含source_id、status(adopted/considered_not_used)、mechanism、reason、adaptation；至少实际考虑用户收录的参考。没有采用时写original_design_reason，不为通过校验伪造使用记录。

镜内motion_beats使用全局帧的start_frame/peak_frame/settled_frame；跨镜动作写transition_in/out的window_frames，不伪装成镜内越界。shared转场两侧使用相同object_id、boundary_state和全局窗口；boundary_state记录边界的坐标、尺度和速度，其连续不代表软件已经验证视觉上平滑。

运行：`python scripts/validate_storyboard.py <storyboard.json>`；`--check-files <素材根目录>`额外检查媒体真实路径。结构验证不读取文意、不证明参考已认真学习，也不能认证审美；渲染和实际观察仍须单独记录。

## 可编辑PPT

仅在用户要求PPT时每镜一页PPTX，采用最后稳定构图；用户选择PDF则输出PDF，不能自动追加PPT。静态预览记录早先媒体序列；需要审阅运动时交实际动效样片。
- 文本、卡片、箭头/连线及有真实数据的图表用原生可编辑对象；图片独立可替换。不用整页PNG冒充可编辑PPT，不把画面文字烧进背景。
- 玻璃以半透明淡黑形状近似；必要局部折射可用无文字效果图，文字和容器仍可编辑，备注说明预览近似。
- 备注写REV、页序、章节、时码、素材序列和未决事项；独立索引用于检索，画面不叠审阅信息。镜内早先出现的素材保留在备注/使用清单，不能因为落定帧没显示就从视频删掉。
- 对象使用REV-0001.heading.zh、REV-0001.heading.en、REV-0001.asset.main等稳定名称；页面重排后按REV识别，不按页号猜对应关系。
- 回写读取文字、位置/尺寸、字体/颜色、裁切和层级变化；更新关联英文。新增、删除、复制对象记录差异，无法确定的映射只列具体缺口。

## 中文Word

用户需要分镜Word时，提供原句、素材、动效时序、跨镜衔接和参考采用说明；需要旧式屏显校对Word时才采用一页对应同REV审阅页的方式。两类均以中文为主，按当前要求选字段。不放英文栏、双语截图或已取消的字幕/时长栏目。只有英文的必要字段给出可修改中文语义；源图片内文字属于素材本体，不伪造为可编辑字段。英文留在场景数据和用户选择的双语预览，由最终中文与用户英文参考稿生成。

## 轻量检查与续跑

按请求一次生成完整审阅包；样张仅在用户要求时生成。按交付类型检查可读性、溢出和来源映射；用户负责审阅决定，不以人工审阅为由跳过必要检查，也不反复改写已批准文字。
一次检查文件可打开、页数/REV/对象映射、实际路径、完整帧覆盖、允许角色、真实数字来源、参考落实及相邻镜头衔接。AI覆盖从media_layers的有效区间统计，按[素材规则](assets-and-history.md)分别报告已分配/已输出；不靠仅存在路径证明全部使用。章节衔接按当前项目安排，不以重复旁白或无意义镜头凑变化。

回修只更新受影响字段、翻译、页和渲染段；项目指定REV意见留在项目回修清单，不写成通用镜头。检查点以输入指纹追踪：文件存在不等于输入未变，已完成计划也不得被无条件重建。技术/内容待办分别记录，不把工作版称为全部终审通过。母版ffprobe只证明流参数；像素中无烧字幕不能由它单独证明，需渲染配置/角色约束配合。
