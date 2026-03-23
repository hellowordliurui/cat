# 喵食记 App 图标

- **miaoshiji-app-icon.svg**：图标源文件（冷瓷白→香槟金→蒂芙尼蓝渐变背景 + 白碗 + 落日珊瑚色猫爪印）。
- **导出为 PNG**：
  1. 用浏览器打开 **export-app-icon.html**（需与 SVG 同目录），点击「下载 1024×1024 PNG」。
  2. 或将 **miaoshiji-app-icon.svg** 在 [CloudConvert](https://cloudconvert.com/svg-to-png) 等站转为 1024×1024 PNG。
- **接入 Xcode**：将得到的 1024×1024 PNG 命名为 `AppIcon.png`，拖入 `ios/MoeChef/Assets.xcassets/AppIcon.appiconset/`，并在该 appiconset 的 Contents.json 里为 1024x1024 的项设置 `"filename": "AppIcon.png"`。
