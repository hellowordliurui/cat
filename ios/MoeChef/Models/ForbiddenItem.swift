//
//  ForbiddenItem.swift
//  MoeChef - 禁忌清单
//

import Foundation

enum ForbiddenLevel: String {
    case fatal = "致命类"
    case risk = "风险类"
}

struct ForbiddenItem: Identifiable {
    let id: String
    let name: String
    let level: ForbiddenLevel
}
