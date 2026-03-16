//
//  CatProfile.swift
//  MoeChef - 猫咪档案 SwiftData 模型
//

import Foundation
import SwiftData

enum CatGender: String, CaseIterable, Codable {
    case male = "公"
    case female = "母"
    case unknown = "未知"
}

enum CatSterilization: String, CaseIterable, Codable {
    case sterilized = "已绝育"
    case notSterilized = "未绝育"
    case unknown = "未知"
}

@Model
final class CatProfile {
    var name: String
    var breed: String
    var bodyWeight: Double
    /// 可选以兼容旧持久化数据（SwiftData 迁移或历史记录可能为 nil）
    var gender: CatGender?
    var sterilization: CatSterilization?
    /// 出生日期（选填）
    var birthDate: Date?

    init(
        name: String,
        breed: String,
        bodyWeight: Double,
        gender: CatGender = .unknown,
        sterilization: CatSterilization = .unknown,
        birthDate: Date? = nil
    ) {
        self.name = name
        self.breed = breed
        self.bodyWeight = bodyWeight
        self.gender = gender
        self.sterilization = sterilization
        self.birthDate = birthDate
    }
}

extension CatProfile {
    static let commonBreeds: [String] = [
        "中华田园猫",
        "英国短毛猫",
        "美国短毛猫",
        "布偶猫",
        "苏格兰折耳猫",
        "波斯猫",
        "暹罗猫",
        "缅因猫",
        "挪威森林猫",
        "孟加拉猫",
        "阿比西尼亚猫",
        "俄罗斯蓝猫",
        "土耳其安哥拉猫",
        "缅甸猫",
        "东方短毛猫",
        "日本短尾猫",
        "斯芬克斯猫（无毛猫）",
        "德文卷毛猫",
        "柯尼斯卷毛猫",
        "其他"
    ]
}
