# 安装与支持清单

安装、迁移或升级本技能时，先给用户这份支持清单并运行检查；用户要求连同环境安装时，按已授权范围直接补齐、回检，不再逐包询问。首次使用没有安装记录时补做一次；已有记录且环境未变时，只检查当前新增功能的依赖。

技能文件、Python环境、制作工程的node_modules、图像工具及插件是不同部分。目录复制不会自动安装运行环境；用下面的统一入口把支持安装具体落实。

## 基础与版本

| 支持项 | 基线与安装位置 |
|---|---|
| Python | 最低3.10，推荐3.11／3.12；制作目录使用.venv。若使用Codex内置文档运行时，按该运行时检查，不往托管目录pip安装 |
| Node.js、npm、npx | Node最低18，推荐22／24 LTS；需要命令可用 |
| Remotion | 新工程随附锁文件：remotion与@remotion/cli均4.0.535；所有额外@remotion/*包与工程Remotion同版本 |
| React与TypeScript | 随附工程为react/react-dom 19.1.0、TypeScript 5.8.3及匹配类型包；唯一实际版本表为assets/remotion-kit/package.json |
| Chromium | Remotion的Chrome Headless Shell；执行npx remotion browser ensure，随后渲染一帧验证。Playwright需要浏览器时优先复用已验证的可执行文件 |
| FFmpeg、FFprobe | 提供可执行路径；检查器也查当前工程Remotion compositor自带的程序。实际滤镜、音频和编码能力由对应任务检验 |
| Git | 下载／更新Git参考缓存时使用；固定版本HTTPS文本快照无需Git |

已有Remotion工程以自己的package.json与lockfile为准，保持@remotion版本一致，不为套用示例升级或降级整个工程。更多官方组件如@remotion/three、@remotion/lottie、@remotion/transitions仅在实际采用时安装，并与该工程版本一致；基础工程不把它们视为缺项。

基础运行时缺失时使用[Python官方](https://www.python.org/downloads/)与[Node.js官方](https://nodejs.org/en/download)入口；不要把技能压缩包当成这些运行时的安装程序。PDF页图还需可用的渲染器（优先Poppler，或已验证的PyMuPDF）；Word页图需要文档运行时或可用的LibreOffice／Word渲染链。安装检查会提示另做真实渲染测试，不因Python包齐全就宣称这些外部能力已验证。

## 功能包

`--feature`可重复；默认core+documents，`all`选择下表全部功能。仅修改文字或分析规则不必为整个制作栈装包。

| feature | 何时需要 | 支持项 |
|---|---|---|
| documents | 中文Word与5页风格PDF | python-docx、reportlab、pypdf、pdfplumber、Pillow；PDF、Documents技能；中文字体及文档运行时的渲染器 |
| images | 原创插图／图片编辑 | imagegen技能及可用的内置图像工具；内置工具不要求用户配置API Key |
| maps | 地理与路线 | D3 7.9.0、@types/d3；来源明确的GeoJSON／坐标 |
| charts | 数据图表 | D3 7.9.0、@types/d3；CSV／JSON数据与出处 |
| diagrams | 流程、白板、拆层 | Mermaid 12.2.0、Rough.js 4.6.6 |
| doodle | 手绘角色／程序动画 | 原生Canvas、SVG；Rough.js 4.6.6按需辅助 |
| collage | 拼贴与图像扩展 | imagegen；原图、抠图／遮罩和项目统一设计参数 |
| logo | 采用pixel2motion的几何检查方法 | Pillow、numpy、Python Playwright；SVG本身由Remotion合成。只有使用上游浏览器检查脚本时才配置其Chromium |
| asr | 已有录音缺可靠时间戳 | 默认faster-whisper、numpy、soundfile；模型在实际选择后下载。若选FireRed后端，另按所选对齐脚本配sherpa-onnx、zhconv、pypinyin与对应模型 |
| review | 动作与性能回修 | 现有Remotion渲染与媒体检查工具，无额外重型引擎 |

## 会调用的技能

- **imagegen**：生成／编辑原创位图时调用；一般已随Codex提供。
- **pdf**：生成与检查风格选择稿、文字画面PDF。
- **documents**：制作中文屏显文字Word及录制文稿。
- **yu-yin-sheng-cheng**：仅需要生成用户指定旁白时调用；沿用其独立声音环境，不覆盖为通用ASR环境。
- **spreadsheets**：需要编辑或核算复杂XLSX时调用；普通CSV读取不用另装。

安装时检查当前可用技能及真实工具。脚本只报告配置目录里是否找到SKILL.md，不代表插件、账号或生图工具已经连通。内置技能不重复安装；PDF／Documents来自相应插件时启用该插件。需要独立安装其他技能时使用可用的skill-installer。

iart、Talkcraft、Doodle、Vox、Pixel2Motion、Emil等作为本技能的可检索方法来源接入，通常不必把每套都注册成独立技能；需要原项目的独立功能时才单独安装，并适配其流程。缓存清单与真实源文件见motion-sources.json。

## 安装入口

在本技能目录运行，制作目录换成用户指定的独立工程路径：

~~~powershell
# 只检查并打印支持清单与命令计划，不安装软件
py -3.11 -X utf8 scripts/check_installation.py --project-root "D:\VideoProjects\my-film" --feature all

# 连同支持安装：为新空目录复制Remotion工程，创建.venv并补选定支持
py -3.11 -X utf8 scripts/setup_support.py --project-root "D:\VideoProjects\my-film" --feature all --install --with-references

# 只做部分功能，也会包含基础制作环境
py -3.11 -X utf8 scripts/setup_support.py --project-root "D:\VideoProjects\my-film" --feature documents --feature maps --feature charts --install --with-references
~~~

其他平台使用选定的python3解释器。安装程序不更改系统Python或Node版本；缺基础运行时先说明下载入口与缺项。npm包放制作工程，Python包放其.venv；保留已有工程和锁文件。包下载失败可检查具体错误后续跑，已经装好的部分保留。

安装后以工程.venv解释器重检，报告保存在`.jianji/installation.json`。再用工程真实Composition渲染一帧；全新示例工程可执行检查报告给出的smoke_test命令。确认中文字体、浏览器、PDF／Word渲染能力与实时工具后，才写相应“已验证”状态。安装成功不等于新参考已全部移植或所有视频效果已验收。

机器清单为`support-manifest.json`；不要在其他文档再维护一份不同的依赖版本。用户已授权安装时直接补齐已选项；仅查看规则／清单时保持检查模式。
