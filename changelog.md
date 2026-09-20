# v3.0.7-action-only

个人精简版，仅保留安装和管理器 Action 主动入口；保留开机服务和卸载流程。

- 移除 WebUI 及其全部专用脚本、资源和设备信息采集。
- 移除清数据、清检测痕迹、删除 TWRP、Widevine 密钥置备、HMA/Zygisk/RKA 配置等额外功能。
- 修复 `teeBroken=true` 时新增目标使用 `!`（证书生成模式）。
- 修复下载失败退出状态丢失；下载失败、空响应或 Base64 解码失败时保留现有 keybox 和备份。
- 禁用上游自动更新，防止重新安装原版入口。

## 安装

下载下方 `Yurikey-v3.0.7-action-only.zip`，在 Root 管理器中安装。不要下载 GitHub 自动生成的 Source code 压缩包。

仍需 Tricky Store；Action 中的指纹更新仍会调用已安装的 PIF 模块。保留的 Action 和开机服务仍会修改配置及系统属性。

已通过自动回归测试和 Shell 语法检查，未做真机测试。此 ZIP 未进行额外的安装包签名。
