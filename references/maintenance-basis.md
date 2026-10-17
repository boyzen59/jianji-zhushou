# 本次维护依据

核对日期：2026-10-17。以下是官方指导，不是新增制作限制。

- [Rethinking skills and prompts for GPT-6 Astra](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)：缩短触发描述，以任务路由逐步读取内容，清理过度规定步骤和过时暂停条件。
- [Using GPT-6 · Prompting best practices](https://developers.openai.com/api/docs/guides/latest-model#prompting-best-practices)：尊重用户要求与已有授权，明确完成标准，按变更风险验证。
- 本机 `skill-creator` 指导：保留有用的领域细节，同一规则只维护一处，检查辅助脚本及实际行为。

应用：入口只保留目标、路由和关键决策；用户默认值单独维护；按需预检；局部回修不强制重新设计或重建全片；外部Skill的作者偏好不成为模型规则。

这些调整不要求切换模型、修改API参数或升级Remotion。具体视频品质仍由素材、设计、实现和画面检查决定。
