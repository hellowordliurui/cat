//
//  MoeChefApp.swift
//  MoeChef - 猫咪精致辅食指南
//

import SwiftUI
import SwiftData

@main
struct MoeChefApp: App {
    init() {
        URLCache.shared = URLCache(
            memoryCapacity: 50 * 1024 * 1024,
            diskCapacity: 300 * 1024 * 1024,
            diskPath: "moechef-image-cache"
        )
    }

    var body: some Scene {
        WindowGroup {
            RootView()
        }
        .modelContainer(for: CatProfile.self)
    }
}

/// 根据 AuthService 登录状态切换登录页 / 主界面（Observable 驱动刷新）
private struct RootView: View {
    // 用 @State 持有 @Observable 单例，确保 SwiftUI 正确建立观察依赖
    @State private var auth = AuthService.shared

    var body: some View {
        Group {
            if auth.isLoggedIn {
                ContentView()
            } else {
                LoginView()
            }
        }
        .animation(.easeInOut(duration: 0.25), value: auth.isLoggedIn)
    }
}
