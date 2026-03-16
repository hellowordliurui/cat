# MoeChef 登录（Sign in with Apple）配置指南

按以下三步完成「使用 Apple 登录」并接入 Supabase Auth。

---

## 若编译报错「No such module 'Supabase'」

说明 Swift Package 依赖尚未解析。在 Xcode 中：

1. 菜单 **File** → **Packages** → **Resolve Package Versions**（或 **Reset Package Caches** 后再点 **Resolve Package Versions**）。
2. 等待右下角「Fetching package...」完成后再编译运行。

若连接 GitHub 超时，可检查网络或使用 VPN 后重试。

---

## 第一步：在 Supabase 后台开启 Apple Provider

1. 打开 [Supabase Dashboard](https://supabase.com/dashboard) → 选择你的项目（如 **hellowordliurui's Project**）。
2. 左侧菜单 **Authentication** → **Providers**。
3. 找到 **Apple**，点击展开。
4. 打开 **Enable Sign in with Apple** 开关。
5. **仅原生 iOS 时**（本应用使用原生 Sign in with Apple，不走网页 OAuth）：
   - 在 **Client IDs** 中填写你的 **App Bundle ID**：`com.moechef.app`（与 Xcode 中 `PRODUCT_BUNDLE_IDENTIFIER` 一致）。
   - 无需配置 Services ID、Secret Key（.p8）等；原生实现不需要 6 个月更换一次密钥。
6. 保存。

若你同时要做网页版或 OAuth 跳转，再按 Supabase 文档配置 Services ID 与 Signing Key 等。

---

## 第二步：在 Xcode 中勾选 Sign in with Apple 能力

1. 用 Xcode 打开 `MoeChef.xcodeproj`。
2. 选中左侧 **TARGETS** → **MoeChef**。
3. 顶部切到 **Signing & Capabilities**。
4. 点击 **+ Capability**，搜索 **Sign in with Apple**，双击添加。
5. 确认 **MoeChef.entitlements** 已被勾选在 **Signing (Release)** 中使用（本仓库已包含该文件，若未自动关联，在 **Build Settings** 中搜索 `Code Signing Entitlements` 填：`MoeChef/MoeChef.entitlements`）。

完成后重新编译运行即可使用系统「使用 Apple 登录」按钮。

---

## 第三步：SwiftUI 登录流程（已由 Cursor 实现）

- **AuthService**：封装 Supabase 客户端与 `signInWithIdToken(provider: .apple, ...)`，并监听 `authStateChange`。
- **LoginView**：使用 PRD 色系与渐变按钮的「使用 Apple 登录」界面。
- **MoeChefApp**：未登录显示 `LoginView`，已登录显示主界面 `ContentView`。

Supabase 项目 URL 与 anon key 已在 `SupabaseConfig` 中配置（可改为从 plist / 环境读取）。

---

## 可选：更换 Supabase 项目

若使用其他 Supabase 项目，请修改 `MoeChef/Services/SupabaseConfig.swift` 中的：

- `supabaseURL`
- `supabaseAnonKey`

或在 Xcode 中添加 `Supabase-Info.plist` 从 plist 读取（需在代码中接好）。
