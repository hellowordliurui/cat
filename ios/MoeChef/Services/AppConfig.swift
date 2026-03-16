//
//  AppConfig.swift
//  MoeChef - 后端 API 地址配置
//

import Foundation

enum AppConfig {
    /// 后端 base URL
    /// - Debug/模拟器：http://localhost:8000
    /// - 真机调试：可改为 Mac 局域网 IP，如 http://192.168.1.100:8000
    /// - TestFlight/发布：必须改为已部署到服务器的地址，如 https://api.你的域名.com
    static var backendBaseURL: String {
        #if DEBUG
        return "http://localhost:8000"
        #else
        // 发布/TestFlight 前请改为你的后端服务器地址（需 HTTPS）
        return "https://你的后端域名或IP"
        #endif
    }

    /// 食谱列表接口
    static var recipesURL: URL {
        URL(string: "\(backendBaseURL)/api/recipes")!
    }
}
