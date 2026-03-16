# MoeChef 在 Cursor 里预览页面

这是和 iOS 界面一致的 Web 预览版，方便在 Cursor 里直接看效果。

## 在 Cursor 中打开预览

**方式一：用 Cursor 内置浏览器**

1. 按 **⌘+Shift+P**（Mac）或 **Ctrl+Shift+P**（Windows）打开命令面板  
2. 输入并选择 **「Simple Browser: Show」**  
3. 在地址栏输入下面任一地址：
   - 本地文件：`file:///Users/liurui/Documents/AIbiancheng/Cursor/cat/web-preview/index.html`
   - 或先启动下面的本地服务，再输入：`http://localhost:8080`

**方式二：先起一个本地服务再在浏览器里看**

在终端执行（在项目根目录 `cat` 下）：

```bash
cd web-preview && python3 -m http.server 8080
```

然后在 Simple Browser 里打开：**http://localhost:8080**

---

预览页包含：首页（Tab + 卡片流）、详情页（食材 / 3 步 / AI 建议）、管理中心（猫咪档案 + 禁忌清单），点击可切换。
