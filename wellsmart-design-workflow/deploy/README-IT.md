# 公司设计服务器 — IT 部署说明（一台 Linux，三个容器，员工零配置）

## 这台机器做什么

三件事，全自动，员工不用登录、不用密钥、不用装任何东西：

1. 双模型审阅：员工的 Claude 在项目文件夹里放一个 `reviews/<任务>/REQUEST.json`，服务器几十秒内冻结快照、预检、打包（盲算包 `packet/blind/` 与完整包 `packet/full/` 分开）、自检盲算包、调审阅模型 API、把 `feedback.json` 和答复模板写回同一个文件夹。每轮状态记录在 `reviews/<任务>/state.json`：REQUESTED → VALIDATING（预检）→ FROZEN（已打包、已哈希）→ REVIEWING → RESPONSE_REQUIRED（设计方须逐条答复）→ CLOSED（通过）或 HUMAN_REQUIRED（审阅方要求人工、第 5 轮仍未通过、超时或格式错误重试一次后仍失败）；预检出现硬 FAIL 时不打包，请求改名为 `REQUEST.error.txt` 并列出预检清单，状态停在 VALIDATING。这台 runner 是 ProjectBook 门户（目标平台见 `references/hosting.md`，尚未建成、状态 UNVERIFIED）建成前的替代品：同一个 `scripts/peer_review.py` 将来在门户的 Runner 上运行，文件夹投递方式届时换成门户提交，轮次记录格式不变。
2. 图纸检查：项目文件夹里任何一张 `drawings/*.html` 新增或改动，服务器跑标注 / QA 检查，结果写到 `drawings/qa/`。
3. 项目 book 网站：项目文件夹有任何变化，服务器重建该项目的静态站，通过 Cloudflare Tunnel 以公司域名公开发布（可被 AI 抓取、Pagefind 人工搜索）。

员工和服务器之间的"连接"就是共享的 Google Drive 文件夹：员工电脑装着 Google Drive 桌面版（本来就有），服务器用 rclone 把同一个共享盘挂载在 `/srv/projects`。谁能访问哪个项目，用 Drive 的共享权限管，不另建账号。

## 机器要求

任意 Linux（Ubuntu 22.04/24.04 即可），4 核 8 GB 起，磁盘按项目数（每个项目预留 5–20 GB，含快照）。装 Docker Engine + Compose 插件、rclone、git。要能出公网（调审阅模型 API、Cloudflare Tunnel）；不需要公网 IP，不需要开任何入站端口。

## 一次性步骤（约 40 分钟）

1. 共享盘：在公司 Google Workspace 建共享云端硬盘 `Projects`，一个项目一个文件夹；员工按项目授权（编辑者）。
2. rclone：`rclone config` 新建远程 `gdrive`（Google Drive；用公司账号授权，或用服务账号 + 把共享盘授权给它）。把 `rclone-mount.service` 复制到 `/etc/systemd/system/`，`sudo systemctl enable --now rclone-mount`，确认 `ls /srv/projects` 能看到项目文件夹。
3. 代码：`git clone` skill 仓库到 `/opt/wellsmart-skills`（或复制解压包），`cd /opt/wellsmart-skills/wellsmart-design-workflow/deploy`。有公司 design-library 仓库的话也 clone 到 `/srv/library`（可选，里面的 gen_book.py 会替代内置的简版 book）。
4. 密钥：`cp .env.example .env`，填审阅模型的 API key（OpenAI 或 Gemini，一把，只在这台机器上）、book 的公网地址、Cloudflare Tunnel token。
5. Cloudflare Tunnel：Zero Trust 控制台 → Networks → Tunnels → 新建 → 复制 token 到 `.env`；在 tunnel 里加 public hostname `books.公司域名` → `http://web:8080`。同一个域名下把 "Block AI bots / AI Scrapers and Crawlers" 关掉，不开 Bot Fight Mode、不加 Access（这个站按决定是公开的）。
6. 启动：`docker compose up -d --build`。看 `docker compose logs -f runner`，出现 `runner start` 即可。
7. 验收：先用 `python3 /opt/wellsmart-skills/wellsmart-design-workflow/scripts/peer_review.py demo /srv/projects/DEMO-01` 生成一个假项目（含 brief、带单位的 DB、calcs、两张带 manifest 的图、`reports/checks.json`），再放一个 `reviews/G4-MECH/REQUEST.json`（内容 `{"task":"G4-MECH"}`；任务名只接受 `G1-*`、`G3-*`、`G4-<专业>`、`G4A-*`、`G5-*`、`S8-*`、`ADHOC-*`），一分钟内应出现 `STATUS.md`、`drawings/qa/`、`reviews/G4-MECH/round-1/feedback.json`、`round-1/blind/answer.json`、`round-1/record.json`，`state.json` 里 `state` 为 `RESPONSE_REQUIRED`，浏览器打开 `https://books.公司域名/<项目>/` 能看到 book。先用 `WS_REVIEWER_PROVIDER=mock` 跑通，再换真 key。

## 日常

- 员工什么都不用做。Claude Code / Cowork 里说"提交 G4 机电审阅"，Claude 写 REQUEST.json；说"看审阅结果"，Claude 读 feedback.json 和 state.json；每个项目根目录的 `STATUS.md` 是服务器最近做了什么的一页清单。出现 `REQUEST.error.txt` 时，里面是预检清单（脚本结果一栏、"技术判定：无（脚本）"一栏）；修好文件后重新投递，或在请求里加 `"allow_fail": "<理由>"`（理由记入本轮记录并交给审阅模型；缺必需文件不能这样跳过）。
- 更新代码：`git pull` 后 `docker compose up -d --build`。
- 备份：`/srv/git`（每次审阅的快照）和 `.env`。项目文件本体在 Drive 里，Drive 自己有版本历史。
- 日志：`docker compose logs --tail 200 runner`。
- 换审阅模型：改 `.env` 里的 `WS_REVIEWER_PROVIDER` / `WS_REVIEWER_MODEL`，`docker compose restart runner`。

## 为什么不给员工发 API key、不做登录

审阅要的是"另一个模型家族独立看一遍"，key 只在服务器上用一把就够；员工那边用的是自己的 Claude 订阅，本来就有。登录只在"服务器要判断是谁在写"时才需要，而这里谁能写哪个文件夹已经由 Drive 权限决定了。少一层账号就少一层要维护、会出错、要教员工的东西。

## 安全边界

- 服务器上的 key 不出这台机器；`.env` 权限 600。
- book 公开，只读，不接受任何写入；保密靠子域名猜不到，客户要求保密的项目在 `.env` 的 `PRIVATE_PROJECTS` 里列出，runner 不为它们建公开 book（审阅和图纸检查照常）。
- runner 只写它自己的文件（`reviews/*/round-*`、`reviews/*/state.json`、`issues/issue-register.csv`、`drawings/qa/`、`STATUS.md`、`REQUEST.done.json` / `REQUEST.error.txt`），不删员工文件；`feedback.json` 写后不再改写，第 6 轮永不建立。
- 快照 git 放在 `/srv/git`，不进 Drive，员工看不到也改不了。
