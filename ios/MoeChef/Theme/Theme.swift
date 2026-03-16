//
//  Theme.swift
//  MoeChef - PRD 1.1 视觉与交互：色系 / 卡片玻璃态 / 投影 / 渐变
//

import SwiftUI

/// PRD 1.1 温馨治愈色调 + 大圆角 28pt
enum Theme {
    /// 卡片统一圆角
    static let cardCornerRadius: CGFloat = 28

    /// 投影规范：落日珊瑚深色 10% 透明度，20pt 模糊，禁止纯黑
    static let premiumShadowColor = Color(red: 1, green: 0.49, blue: 0.37)   // #FF7E5F 深调
    static let premiumShadowOpacity: Double = 0.10
    static let premiumShadowRadius: CGFloat = 20

    /// 色系视觉层级：70% 冷瓷白 / 20% 香槟金+蒂芙尼蓝 / 10% 落日珊瑚
    enum Colors {
        /// 70% 底色：冷瓷白（清透、高级、留白）
        static let background = Color(red: 0.97, green: 0.98, blue: 0.99)   // 冷瓷白 #F7F9FC
        /// 卡片：瓷白 0.8 透明度（与 .ultraThinMaterial 搭配）
        static let cardPorcelain = Color(red: 1, green: 0.995, blue: 0.98)   // 瓷白
        static let cardPorcelainOpacity: Double = 0.8
        /// 10% 亮色：落日珊瑚（点睛）
        static let coral = Color(red: 1, green: 0.494, blue: 0.373)         // #FF7E5F
        /// 20% 辅助：香槟缎面
        static let champagne = Color(red: 0.953, green: 0.898, blue: 0.671) // #F3E5AB
        /// 20% 辅助：蒂芙尼蓝
        static let tiffany = Color(red: 0.494, green: 0.784, blue: 0.89)     // #7EC8E3
        /// 文案
        static let text = Color(red: 0.22, green: 0.22, blue: 0.25)
        static let textSecondary = Color(red: 0.45, green: 0.45, blue: 0.5)
        /// 致命 / 风险（保留）
        static let danger = Color(red: 0.85, green: 0.35, blue: 0.35)
        static let warning = Color(red: 0.95, green: 0.75, blue: 0.35)

        /// 核心按钮渐变：落日珊瑚 → 香槟缎面（发光感）
        static let gradientPrimary = LinearGradient(
            colors: [coral, champagne],
            startPoint: .leading,
            endPoint: .trailing
        )
    }

    /// 卡片背景：磨砂玻璃 + 瓷白 0.8，呼吸感（先 material 再瓷白衬底）
    static func cardBackground() -> some View {
        Color.clear
            .background(Colors.cardPorcelain.opacity(Colors.cardPorcelainOpacity))
            .background(.ultraThinMaterial)
    }
}
