# Well Smart 设计工作流 skill — 员工安装指南

只做一次，之后自动更新。装完以后，Claude 一听到项目、阶段（S0–S10）、图纸、计算、审阅这些词就会自己按公司流程干活，你不用在提示里写任何标准或格式，每一步该说什么见 skill 里的 `references/operator-prompts.md`（提示卡）。

## Cowork（Claude 桌面版）

1. 打开 Claude 桌面版，左侧 **Customize（自定义）→ Plugins（插件）**。
2. 点 **Add marketplace（添加插件市场）**，填仓库地址：`jackjia6/wellsmart-skills`（或完整地址 `https://github.com/jackjia6/wellsmart-skills`），确定。
   仓库是私有的，第一次会要求登录 GitHub，用你被加进仓库的那个 GitHub 账号登录。
3. 在插件列表里找到 **wellsmart-design-workflow**，点 **Install（安装）**。
4. 打开这个插件，确认 Skills 里有 `wellsmart-design-workflow`，开关是打开的。
5. 验证：新建一个 Cowork 任务，输入"我们的设计工作流有几个阶段、每个 gate 冻结什么？"——回答里出现 S0–S10、G0–G7、G4a 就说明装对了。

更新：Jack 推了新版本后，Plugins 页面里这个 marketplace 会提示更新；点 **Update** 就行（Cowork 也会自己定期检查）。

## Claude Code（桌面版的 Code 标签，或终端）

在对话框输入两条命令：

```
/plugin marketplace add jackjia6/wellsmart-skills
/plugin install wellsmart-design-workflow@wellsmart-skills
```

私有仓库需要这台电脑已经登录过 GitHub（终端里 `gh auth login` 一次即可）。更新：`/plugin update wellsmart-design-workflow@wellsmart-skills`，或者等它后台自动刷新。

## claude.ai 网页 / 手机聊天版

聊天版不支持插件。需要的话向 Jack 要 `wellsmart-design-workflow.skill` 文件，在 Settings → Capabilities → Skills 里上传。日常设计工作请用 Cowork 或 Claude Code，不要用聊天版。

## 常见问题

- **看不到插件 / 提示无权限**：你的 GitHub 账号还没被加进仓库，找 Jack 加你为 collaborator，然后在 Cowork 里重新登录 GitHub。
- **装了但 Claude 没按流程做**：先看插件是否处于启用状态；再确认你的提示里提到了项目名和阶段（例如"<项目> 跑 S6，专业 MECH"）。仍然不对，把 Claude 的回复截图发给 Jack，这算 skill 缺陷。
- **版本号在哪看**：Plugins 页面插件卡片上；仓库里 `plugins/wellsmart-design-workflow/.claude-plugin/plugin.json` 的 `version`。

（仓库在 Jack 的 GitHub 账号 jackjia6 下；若日后迁到公司组织，把 jackjia6 换成组织名。）
