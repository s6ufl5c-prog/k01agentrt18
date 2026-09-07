# Google Service Activation Auto-Redeemer (秒抢自动兑换神器)

一个专为 `serviceactivation.google.com` 格式促销订阅链接（如 Google One、Gemini Advanced、YouTube 合作权益等）打造的高性能、防风控、全自动极速兑换工具。

由于此类链接具有极高的时效性且通常仅支持单次兑换，本工具采用**剪贴板极速监听（Sniper 模式）**与**抗指纹探测浏览器持久化会话（Patchright）**，实现“复制即秒兑”，杜绝手动打开网页卡顿和被抢先兑换的痛点。

---

## 核心特性

- **持久化 Google 登录态**：基于 Persistent Browser Context，只需首次登录一次 Google 账号，后续兑换无需重复输入账号密码与 2FA。
- **抗自动化风控 (Patchright / Anti-Bot Detection)**：绕过 Google 对标准 Playwright/Selenium 的 WebDriver 特征检测，避免触发无尽人机验证与拦截。
- **剪贴板实时监听 (Sniper 模式)**：后台静默监听系统剪贴板，一旦复制到包含 `serviceactivation.google.com` 的链接，毫秒级拉起并自动完成确认。
- **全自动点击与智能状态识别**：
  - 自动识别“开始订阅 / 同意并继续 / Agree and continue”等多种语言确认按钮。
  - 自动判断链接有效性、已失效（Expired）、已被使用（Already Redeemed）等状态。
- **多渠道消息推送**：支持 Telegram Bot 与 Webhook（Discord / 飞书 / 企业微信等），随时同步兑换结果。

---

## 快速安装

1. **克隆项目到本地**：
   ```bash
   git clone <repo-url>
   cd <repo-folder>
   ```

2. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   patchright install chromium
   ```

3. **配置文件（可选）**：
   复制 `config.example.yaml` 为 `config.yaml`：
   ```bash
   cp config.example.yaml config.yaml
   ```

---

## 使用指南

### 1. 首次运行：保存 Google 登录态 (推荐)

运行如下命令，会自动弹出一个纯净浏览器窗口供你登录需要接收权益的 Google 账号：
```bash
python main.py --login-setup
```
登录成功并确保已绑定 Google 支付方式后，关闭窗口即可。登录凭证将保存在本地的 `google_profile` 目录中。

---

### 2. 剪贴板秒抢模式 (Sniper Mode)

当你正在各大群聊、论坛蹲守放码时，开启此模式：
```bash
python main.py --watch
```
只要你在电脑上按下 `Ctrl + C` 复制到任何包含 `serviceactivation.google.com` 的文本，程序会在毫秒内自动捕获并完成兑换！

---

### 3. 单链接即时兑换

直接通过命令行指定 URL 兑换：
```bash
python main.py -u "https://serviceactivation.google.com/subscription/new/..."
```

---

### 4. 交互式菜单

直接运行 `python main.py`，根据彩色交互式菜单选择对应操作。

---

## 配置文件说明 (`config.yaml`)

```yaml
redeemer:
  headless: false              # 是否无头模式运行（建议 false 避免额外风控）
  user_data_dir: "./google_profile" # 浏览器会话与缓存持久化目录
  timeout: 30                  # 超时时间（秒）
  auto_confirm: true           # 是否自动点击最终确认订阅
  proxy: ""                    # 支持代理，如 http://127.0.0.1:7890
  clipboard_poll_interval: 1.0 # 剪贴板轮询间隔（秒）

notifications:
  enabled: false               # 是否开启通知
  type: "telegram"             # telegram 或 webhook
  telegram:
    bot_token: "YOUR_BOT_TOKEN"
    chat_id: "YOUR_CHAT_ID"
```

---

## 免责声明

本工具仅供个人学习、技术研究及合法个人账户便捷管理使用。请勿用于任何违反 Google 服务条款或相关法律法规的行为。
