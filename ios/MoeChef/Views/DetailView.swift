//
//  DetailView.swift
//  MoeChef - 详情页：AI 动态适配与制作，3 步流程 + 品种补丁
//

import SwiftUI

struct DetailView: View {
    let recipe: Recipe
    /// 当前猫咪档案（名字、品种、体重），用于 AI 建议区展示；nil 时显示「未设置档案」
    var catName: String?
    var catBreed: String?
    /// 档案体重 (kg)，用于结合 RER/DER_snack 给出辅食热量建议
    var catBodyWeightKg: Double?
    var onBack: () -> Void
    
    var body: some View {
        GeometryReader { proxy in
            ScrollView(showsIndicators: false) {
                VStack(alignment: .leading, spacing: 20) {
                    // 高清成品图占位
                    heroImage
                    // 副标题
                    Text(recipe.subtitle)
                        .font(.body)
                        .foregroundStyle(Theme.Colors.textSecondary)
                        .padding(.horizontal, 20)
                    // 极简食材
                    ingredientsSection
                    // 3 步变身
                    stepsSection
                    // AI 品种建议（含品种文案与体重热量建议）
                    if (recipe.aiBreedNote.map { !$0.isEmpty } ?? false) || aiWeightAdviceText != nil {
                        aiBreedSection(note: recipe.aiBreedNote ?? "")
                    }
                }
                .padding(.top, 18)
                .padding(.bottom, max(44, proxy.safeAreaInsets.bottom + 32))
                .frame(maxWidth: .infinity, alignment: .topLeading)
                .frame(minHeight: proxy.size.height, alignment: .topLeading)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
            .background(detailBackground.ignoresSafeArea())
            .safeAreaInset(edge: .top, spacing: 0) {
                topBar
            }
        }
        .navigationBarHidden(true)
    }
    
    private var topBar: some View {
        HStack(spacing: 12) {
            backButton
            Spacer()
            Text(recipe.title)
                .font(.system(size: 17, weight: .semibold))
                .foregroundStyle(Theme.Colors.text)
                .lineLimit(1)
                .truncationMode(.tail)
            Spacer()
            Color.clear.frame(width: 34, height: 34)
        }
        .padding(.horizontal, 18)
        .padding(.top, 10)
        .padding(.bottom, 6)
        .background(detailBackground.opacity(0.96))
    }
    
    private var backButton: some View {
        Button(action: onBack) {
            Image(systemName: "chevron.left")
                .font(.system(size: 20, weight: .semibold))
                .foregroundStyle(Theme.Colors.text)
                .frame(width: 34, height: 34)
        }
        .buttonStyle(.plain)
    }
    
    private var detailBackground: Color {
        Color(red: 0.985, green: 0.982, blue: 0.985)
    }
    
    private var heroImage: some View {
        ZStack {
            if let url = recipe.resolvedImageURL {
                CachedRemoteImage(url: url) { image in
                    image
                        .resizable()
                        .scaledToFill()
                } placeholder: {
                    RecipeDefaultPlaceholder(iconSize: 54, subtitleSize: 15)
                }
            } else {
                RecipeDefaultPlaceholder(iconSize: 54, subtitleSize: 15)
            }
        }
        .frame(height: 240)
        .frame(maxWidth: .infinity)
        .clipShape(RoundedRectangle(cornerRadius: 26, style: .continuous))
        .padding(.horizontal, 24)
    }
    
    private var ingredientsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(alignment: .center, spacing: 10) {
                Image(systemName: "cart.fill")
                    .font(.system(size: 17, weight: .semibold))
                Text("极简食材 (一餐份)")
                    .font(.system(size: 18, weight: .semibold))
            }
                .foregroundStyle(Theme.Colors.text)
            VStack(alignment: .leading, spacing: 8) {
                ForEach(Array(recipe.ingredients.enumerated()), id: \.offset) { _, ing in
                    HStack(alignment: .firstTextBaseline, spacing: 8) {
                        Circle()
                            .fill(Theme.Colors.coral.opacity(0.75))
                            .frame(width: 4, height: 4)
                        Text(ing.name + ": " + ing.amount)
                            .foregroundStyle(Theme.Colors.textSecondary)
                    }
                    .font(.system(size: 16))
                }
            }
            .padding(.leading, 4)
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 22)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(detailCardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 24, style: .continuous))
        .overlay(alignment: .topTrailing) {
            Circle()
                .fill(Color(red: 0.86, green: 0.86, blue: 0.86))
                .frame(width: 42, height: 42)
                .overlay {
                    Circle()
                        .stroke(.white.opacity(0.6), lineWidth: 1)
                }
                .shadow(color: .black.opacity(0.08), radius: 8, x: 0, y: 4)
                .padding(.top, 18)
                .padding(.trailing, 18)
        }
        .shadow(color: Color.black.opacity(0.03), radius: 16, x: 0, y: 8)
        .padding(.horizontal, 20)
    }
    
    private var stepsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(alignment: .center, spacing: 10) {
                Image(systemName: "person.fill")
                    .font(.system(size: 16, weight: .semibold))
                Text("3步变身")
                    .font(.system(size: 18, weight: .semibold))
            }
                .foregroundStyle(Theme.Colors.text)
            VStack(alignment: .leading, spacing: 10) {
                ForEach(Array(recipe.steps.enumerated()), id: \.offset) { index, step in
                    HStack(alignment: .top, spacing: 10) {
                        Text("\(index + 1).")
                            .font(.system(size: 18, weight: .semibold))
                            .foregroundStyle(Theme.Colors.coral.opacity(0.9))
                            .frame(width: 24, alignment: .leading)
                        Text(step)
                            .font(.system(size: 16))
                            .foregroundStyle(Theme.Colors.textSecondary)
                            .lineSpacing(3)
                    }
                }
            }
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 22)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(detailCardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 24, style: .continuous))
        .shadow(color: Color.black.opacity(0.03), radius: 16, x: 0, y: 8)
        .padding(.horizontal, 20)
    }
    
    /// 根据档案名字、品种生成 AI 建议区标题；未填档案时显示「未设置档案」
    private var aiBreedSectionHeader: String {
        let name = (catName ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
        let breed = (catBreed ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
        if !name.isEmpty {
            let breedText = breed.isEmpty ? "未知品种" : breed
            return "💡 \(name)是【\(breedText)】，AI 建议："
        }
        return "💡 未设置档案，AI 建议："
    }

    /// PRD 3.8：RER = 70 × body_weight^0.75（静息能量需求 kcal/天）
    private static func rerKcalPerDay(bodyWeightKg: Double) -> Double {
        70.0 * pow(bodyWeightKg, 0.75)
    }
    /// 辅食热量上限 = RER × 10%
    private static func derSnackKcal(rer: Double, fraction: Double = 0.10) -> Double {
        rer * fraction
    }
    /// 根据档案体重生成辅食热量建议文案（通俗说法）；体重无效时返回 nil
    private var aiWeightAdviceText: String? {
        guard let w = catBodyWeightKg, w > 0 else { return nil }
        let rer = Self.rerKcalPerDay(bodyWeightKg: w)
        let derSnack = Self.derSnackKcal(rer: rer)
        let kcal = Int(round(derSnack))
        // 熟鸡胸肉约 1.5 大卡/克，换算成「约多少克」更好懂
        let grams = max(1, Int(round(derSnack / 1.5)))
        return "按当前体重，每天零食加餐建议在 \(kcal) 大卡以内（约 \(grams) 克熟鸡胸肉的热量），相当于一天所需能量的一成，不会影响正餐。"
    }

    private func aiBreedSection(note: String) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(aiBreedSectionHeader)
                .font(.system(size: 16, weight: .medium))
                .foregroundStyle(Theme.Colors.textSecondary)
            if !note.isEmpty {
                Text(note)
                    .font(.system(size: 16))
                    .foregroundStyle(Theme.Colors.text)
                    .lineSpacing(3)
                    .multilineTextAlignment(.leading)
            }
            if let weightLine = aiWeightAdviceText {
                Text(weightLine)
                    .font(.system(size: 16))
                    .foregroundStyle(Theme.Colors.textSecondary)
                    .lineSpacing(3)
            }
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 22)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(red: 0.973, green: 0.949, blue: 0.84))
        .clipShape(RoundedRectangle(cornerRadius: 24, style: .continuous))
        .shadow(color: Color.black.opacity(0.025), radius: 14, x: 0, y: 7)
        .padding(.horizontal, 20)
    }
    
    private var detailCardBackground: some View {
        Color.white.opacity(0.92)
    }
}

#Preview {
    DetailView(recipe: Recipe.placeholders[0], catName: "大黄", catBreed: "英国短毛猫", catBodyWeightKg: 4.5, onBack: {})
}
