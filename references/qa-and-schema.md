# 场景数据与审阅回修

## 数据与机器校验

使用 `assets/templates/storyboard-example.json` 的schema 5结构（示例不是实际工程或用户稿）。根字段为engine、fps、duration_frames、production_policy、source_sentences、reference_sources、scenes。正文、原声、素材、屏显文字、翻译分层保存，共用场景ID与稳定文字ID。

- 时间：全局右开帧区间[start_frame, end_frame_exclusive)，从绝对时间边界量化；相邻镜头首尾相接，settled_frame在镜内。校验器支持整数1–240 fps，其他时基先适配，不能静默取整。
- 叙事：source_ids、narrative_intent、cue的anchor及precision；start_state、end_state、component。句级SRT不冒称逐词精确。
- 动作：motion_beats写主体、动作、参数和镜内start/peak/settled_frame。跨镜动作写transition_in/out及全局window_frames；shared交接共用object_id、boundary_state和窗口。
- 文字：texts含稳定id、role、zh/en及原稿／修订依据。重复ID的内容必须一致；旁白存内容层，字幕是否上屏按项目策略。
- 素材：media_layers含kind、asset_id、availability(pending/available)、path、全局可见窗口。pending路径为空；渲染前必须到位。AI视频另含playback_id、源入出点和rate；跨语义镜头的同一播放共用ID和全局时钟。
- 参考：reference_sources登记origin(user_supplied/supplementary/legacy)与具体location；reference_uses写source_id、adopted/considered_not_used、mechanism、reason、adaptation。至少考虑用户收录的相关来源，不合适时写original_design_reason；不要伪造使用记录。
- 状态：planned／implemented／rendered／reviewed；后两种必须有实际evidence路径。文件存在、结构通过均不代表视觉质量。

production_policy的字段与默认值见[制作默认值](production-defaults.md)及JSON示例；这是可覆盖的项目策略，不是模型限制。明确变更时在对应字段写新值，并用`production_policy.overrides`保存用户要求，例如：

~~~json
{
  "subtitles": {"mode": "burned"},
  "overrides": {"subtitles.mode": "用户要求：本片烧录中文字幕"}
}
~~~

以上是局部片段，需合并进完整策略。支持对已有策略字段逐项覆盖；无依据的变化仍报错。字幕mode可为off／burned／external；外置字幕不投射到画面。AI窗口按源时长÷速度量化为帧，播放次数按plays限制。修改策略时同时更新实际图层与交付配置，不能只改声明。覆盖原话是追溯资料，脚本不会验证其真实性。

`python scripts/validate_storyboard.py <storyboard.json>` 检查结构与策略；加`--check-files <素材根目录>`检查到位情况。schema 4兼容但提示未验证制作策略。脚本不验证实际露脸时长、安全区像素、事实、听感或英文校对。

## 文字唯一登记

登记拟上屏的标题、关键词、人物地点、日期数字单位、图表标签、引文和来源；动态数字登记依据与终值。素材内嵌文字另标“非直接可编辑”，给中文语义和处理方案；未查看真实素材则标待转写。页码、占位提示、REV等仅是审阅层，不进入成片登记。

中文Word是人工修改入口，含稳定ID、场景／时间索引、原值与可编辑正文；旁白完整台词另放录制包。用户回传后按ID更新所有出现位置、关联英文和受影响布局。一个文字ID可对应多张画面；新增／删除／无法匹配项单列，不按页号猜映射。英文状态按项目策略，不用旧译文逆向覆盖中文。

## 文字画面PDF

PDF展示视频真实构图，不是文字清单或文档截图。每个不同文字组合／布局给落定状态；入场或变形影响理解时补关键中间态。页面按项目画幅，默认16:9；源于实际Remotion布局，登记坐标、尺寸、字体、颜色及出现方式。

- 同一数据生成Word、文字注册表、PDF及ID→页码映射；保留章节书签、scene_id、源／成片时间、text_ids、状态页脚，审阅信息不遮画面。
- 中文修改入口仍是Word；可用渲染静帧作PDF画面，但不称PNG为可编辑文本。
- 按策略预留英文与字幕区，两者分开；正式画面去除预留框和占位标签。
- 未到素材可在审阅层作明确示意；不据此声称素材已检查。风格对比预览按[导演流程](storyboard-direction.md)，PDF本身不强制生成额外视频。
- 核对文字ID覆盖、实际文字与登记一致、长文换行、裁切、字号、面部及安全区避让，并查看最终PDF页面。静帧只能证明采样状态，运动另查。

## 可编辑PPT（仅按要求）

每镜采用稳定构图；文字、卡片、箭头及真实数据图表用原生对象，图片可替换。不要用整页PNG冒充可编辑PPT。玻璃／折射可局部近似，备注说明差异，文字与容器仍可编辑。

对象命名如`REV-0001.heading.zh`、`REV-0001.asset.main`。备注保存时码、素材序列、版本和未决项；早于落定帧的素材仍保留在清单。回写文字、坐标、尺寸、字体、裁切和层级变化，新增／复制对象明确映射。

## 回修与验收

按本次交付检查可打开、页幅、ID映射、文本溢出、来源和实际渲染。真人录制和默认前期交付见[制作默认值](production-defaults.md)，此处不重复展开。回修只更新受影响文字、译文、页面和片段；检查点追踪输入指纹，避免无条件重建已完成成果。明确未完成的用户校对和技术检查，不将工作版称为终审通过。
