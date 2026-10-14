# 旧动效入口兼容

2.0取消Shotcraft主库、RVE/Scenes补充库的等级关系及使用占比。旧入口保留，实际设计读取：

1. [用户参考索引](motion-reference-index.md)：用户收录是首要设计参考。
2. [分镜导演流程](storyboard-direction.md)：先安排素材、动作和跨镜接力。
3. [动效配方](motion-recipes.md)：将参考改写成具体状态与参数。
4. [Remotion制作](remotion-production.md)：所有新动画由统一帧时钟控制。

Shotcraft、RVE、Scenes与v2是普通候选。已验证的工程代码可以复用，不恢复主库优先级、配方配额或固定图像运动限制。
