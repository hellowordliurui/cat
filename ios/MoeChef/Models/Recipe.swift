//
//  Recipe.swift
//  MoeChef
//

import Foundation

/// 食谱分类（首页 Tab）
enum RecipeCategory: String, CaseIterable, Identifiable {
    case all = "全部"
    case cold = "冷饮"
    case mousse = "慕斯"
    case cake = "蛋糕"
    
    var id: String { rawValue }
    
    var icon: String {
        switch self {
        case .all: return "leaf.fill"
        case .cold: return "snowflake"
        case .mousse: return "circle.hexagongrid.fill"
        case .cake: return "birthday.cake.fill"
        }
    }
}

/// 食谱模型
struct Recipe: Identifiable {
    let id: String
    let title: String
    let subtitle: String
    let category: RecipeCategory
    let imageURL: String?
    let ingredients: [Ingredient]
    let steps: [String]
    let aiBreedNote: String?   // AI 品种补丁
    let safetyPassed: Bool
}

extension Recipe {
    /// 兼容绝对/相对 imageURL，统一转成可加载 URL。
    /// 绝对地址（Supabase Storage HTTPS）直接使用；相对路径则拼接后端 baseURL。
    var resolvedImageURL: URL? {
        guard let raw = imageURL?.trimmingCharacters(in: .whitespacesAndNewlines), !raw.isEmpty else {
            return nil
        }
        if let direct = URL(string: raw), direct.scheme != nil {
            return direct
        }
        let base = AppConfig.backendBaseURL
        if raw.hasPrefix("/") {
            return URL(string: "\(base)\(raw)")
        }
        return URL(string: "\(base)/\(raw)")
    }
}

struct Ingredient {
    let name: String
    let amount: String
}

extension Recipe {
    static var placeholders: [Recipe] {
        [
            Recipe(
                id: "1",
                title: "海风三文鱼慕斯 (护心版)",
                subtitle: "一份充满大海味道的轻盈慕斯。",
                category: .mousse,
                imageURL: nil,
                ingredients: [
                    Ingredient(name: "三文鱼", amount: "约手掌大小"),
                    Ingredient(name: "羊奶粉", amount: "1小勺")
                ],
                steps: [
                    "将鱼肉蒸熟，与奶粉一同压成泥状。",
                    "倒入猫爪模具，冷藏 2 小时。"
                ],
                aiBreedNote: "针对其易胖体质，本配方已自动剔除原始数据中的[糖分]，建议额外添加鸭心。",
                safetyPassed: true
            ),
            Recipe(
                id: "2",
                title: "元气肉泥塔",
                subtitle: "慕斯质地，营养满分。",
                category: .mousse,
                imageURL: nil,
                ingredients: [],
                steps: [],
                aiBreedNote: nil,
                safetyPassed: true
            ),
            Recipe(
                id: "3",
                title: "蓝莓鸡肉冻",
                subtitle: "派对小食。",
                category: .cold,
                imageURL: nil,
                ingredients: [],
                steps: [],
                aiBreedNote: nil,
                safetyPassed: true
            )
        ]
    }
}
