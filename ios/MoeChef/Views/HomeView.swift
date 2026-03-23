//
//  HomeView.swift
//  MoeChef - 首页：灵感画廊，顶部 Tab + 瀑布流卡片
//

import SwiftUI

struct HomeView: View {
    var onProfileTap: () -> Void
    var onRecipeTap: (Recipe) -> Void
    var currentCatName: String?
    var recipes: [Recipe]
    var isLoading: Bool

    @State private var selectedCategory: RecipeCategory = .all
    @State private var searchText = ""
    
    private var normalizedSearchText: String {
        searchText.trimmingCharacters(in: .whitespacesAndNewlines)
    }
    
    var body: some View {
        ZStack(alignment: .topTrailing) {
            Group {
                if isLoading && recipes.isEmpty {
                    loadingView
                } else if recipes.isEmpty {
                    emptyStateView
                } else {
                    VStack(spacing: 0) {
                        // 分类 Tab（固定，不随内容滚动）
                        categoryTabs
                        // 每个分类单独 ScrollView，切换 Tab 只换可见层，保留各自滚动位置
                        ZStack {
                            ForEach(RecipeCategory.allCases) { tabCategory in
                                categoryScrollPage(for: tabCategory)
                            }
                        }
                        .animation(nil, value: selectedCategory)
                    }
                }
            }
            .background(Theme.Colors.background)
            .safeAreaInset(edge: .top, spacing: 0) {
                headerBar
            }
            
            // 右上角 [👤 我的]
            profileButton
        }
        .navigationBarHidden(true)
    }
    
    private var headerBar: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("猫咪漂亮饭")
                    .font(.title2.bold())
                    .foregroundStyle(Theme.Colors.text)
                Spacer()
                    .frame(width: 44)
            }

            HStack(spacing: 10) {
                Image(systemName: "magnifyingglass")
                    .foregroundStyle(Theme.Colors.textSecondary)
                TextField("搜索食品名称、食材或做法", text: $searchText)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()

                if !searchText.isEmpty {
                    Button {
                        searchText = ""
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundStyle(Theme.Colors.textSecondary.opacity(0.85))
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 12)
            .background(Theme.cardBackground())
            .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
            .overlay {
                RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .stroke(.white.opacity(0.35), lineWidth: 1)
            }
            .shadow(
                color: Theme.premiumShadowColor.opacity(0.06),
                radius: 12,
                x: 0,
                y: 4
            )
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 12)
        .background(Theme.Colors.background.opacity(0.98))
    }
    
    private var profileButton: some View {
        Button(action: onProfileTap) {
            Image(systemName: "person.circle.fill")
                .font(.title)
                .foregroundStyle(Theme.Colors.coral)
        }
        .padding(.top, 56)
        .padding(.trailing, 20)
    }
    
    private var categoryTabs: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 12) {
                ForEach(RecipeCategory.allCases) { category in
                    CategoryChip(
                        category: category,
                        isSelected: selectedCategory == category
                    ) {
                        selectedCategory = category
                    }
                }
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 12)
        }
        .background(Theme.Colors.background)
    }

    private var searchEmptyStateView: some View {
        VStack(spacing: 14) {
            Image(systemName: "magnifyingglass.circle.fill")
                .font(.system(size: 48))
                .foregroundStyle(Theme.Colors.coral.opacity(0.9))
            Text("没有找到相关漂亮饭")
                .font(.headline)
                .foregroundStyle(Theme.Colors.text)
            Text("试试搜索菜名、食材名称，或切换上方分类。")
                .font(.subheadline)
                .foregroundStyle(Theme.Colors.textSecondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 24)
        }
        .frame(maxWidth: .infinity)
        .padding(.horizontal, 24)
        .padding(.top, 48)
    }
    
    private var loadingView: some View {
        VStack(spacing: 18) {
            Spacer()
            ZStack {
                Circle()
                    .fill(Theme.Colors.cardPorcelain.opacity(0.92))
                    .frame(width: 92, height: 92)
                    .shadow(
                        color: Theme.premiumShadowColor.opacity(0.08),
                        radius: 18,
                        x: 0,
                        y: 8
                    )
                Image(systemName: "pawprint.fill")
                    .font(.system(size: 34, weight: .medium))
                    .foregroundStyle(Theme.Colors.coral)
            }
            Text("正在加载猫咪漂亮饭")
                .font(.headline)
                .foregroundStyle(Theme.Colors.text)
            Text("小猫爪正在把新鲜食谱端上来")
                .font(.subheadline)
                .foregroundStyle(Theme.Colors.textSecondary)
            ProgressView()
                .tint(Theme.Colors.coral)
                .padding(.top, 4)
            Spacer()
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding(.horizontal, 24)
    }
    
    private var emptyStateView: some View {
        VStack(spacing: 14) {
            Spacer()
            Image(systemName: "pawprint.circle.fill")
                .font(.system(size: 48))
                .foregroundStyle(Theme.Colors.coral.opacity(0.9))
            Text("暂时还没有可展示的食谱")
                .font(.headline)
                .foregroundStyle(Theme.Colors.text)
            Text("请稍后再试，或检查后端接口是否正常返回数据。")
                .font(.subheadline)
                .foregroundStyle(Theme.Colors.textSecondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 24)
            Spacer()
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding(.horizontal, 24)
    }
    
    private func filteredRecipes(for tabCategory: RecipeCategory) -> [Recipe] {
        recipes.filter { recipe in
            let matchesCategory = tabCategory == .all || recipe.category == tabCategory
            let matchesSearch = normalizedSearchText.isEmpty || recipe.matches(searchText)
            return matchesCategory && matchesSearch
        }
    }

    @ViewBuilder
    private func categoryScrollPage(for tabCategory: RecipeCategory) -> some View {
        let list = filteredRecipes(for: tabCategory)
        ScrollView(showsIndicators: false) {
            VStack(spacing: 0) {
                sectionHeader(for: tabCategory)
                if list.isEmpty {
                    searchEmptyStateView
                } else {
                    waterfallGrid(recipes: list)
                }
            }
            .padding(.top, 8)
            .padding(.bottom, 32)
        }
        .opacity(selectedCategory == tabCategory ? 1 : 0)
        .allowsHitTesting(selectedCategory == tabCategory)
        .accessibilityHidden(selectedCategory != tabCategory)
    }

    private func sectionHeader(for tabCategory: RecipeCategory) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            let title: String = {
                if !searchText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                    return "🔎 \"\(searchText)\" 的搜索结果"
                } else if tabCategory != .all {
                    return "✨ \(tabCategory.rawValue) 分类下的漂亮饭"
                } else {
                    return "🌟 属于【\(currentCatName ?? "我的猫")】的午后治愈灵感"
                }
            }()

            Text(title)
                .font(.subheadline)
                .foregroundStyle(Theme.Colors.textSecondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.horizontal, 20)
        .padding(.top, 8)
        .padding(.bottom, 12)
    }
    
    private func waterfallGrid(recipes: [Recipe]) -> some View {
        LazyVStack(spacing: 16) {
            // 首张强调大卡
            if let first = recipes.first {
                Button {
                    onRecipeTap(first)
                } label: {
                    RecipeCardView(recipe: first, style: .large)
                }
                .buttonStyle(.plain)
                .padding(.horizontal, 20)
            }

            let rest = Array(recipes.dropFirst())
            LazyVGrid(
                columns: [
                    GridItem(.flexible(), spacing: 12),
                    GridItem(.flexible(), spacing: 12)
                ],
                spacing: 16
            ) {
                ForEach(rest, id: \.id) { recipe in
                    Button {
                        onRecipeTap(recipe)
                    } label: {
                        RecipeCardView(recipe: recipe, style: .small)
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.horizontal, 20)
        }
    }
}

private extension Recipe {
    func matches(_ query: String) -> Bool {
        let keyword = query.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !keyword.isEmpty else { return true }

        let haystack = [
            title,
            subtitle,
            aiBreedNote ?? "",
            ingredients.map(\.name).joined(separator: " "),
            ingredients.map(\.amount).joined(separator: " "),
            steps.joined(separator: " ")
        ].joined(separator: " ")

        return haystack.localizedCaseInsensitiveContains(keyword)
    }
}

extension RecipeCategory {
    init(apiValue: String) {
        switch apiValue.lowercased() {
        case "cold":
            self = .cold
        case "mousse":
            self = .mousse
        case "cake":
            self = .cake
        default:
            self = .all
        }
    }
}

private struct CategoryChip: View {
    let category: RecipeCategory
    let isSelected: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            HStack(spacing: 6) {
                Image(systemName: category.icon)
                    .font(.caption)
                Text(category.rawValue)
                    .font(.subheadline.weight(.medium))
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
            .background {
                if isSelected {
                    Capsule().fill(Theme.Colors.gradientPrimary)
                } else {
                    Capsule().fill(Theme.Colors.cardPorcelain.opacity(0.9))
                }
            }
            .foregroundStyle(isSelected ? .white : Theme.Colors.text)
            .clipShape(Capsule())
            .animation(.easeInOut(duration: 0.2), value: isSelected)
        }
        .buttonStyle(.plain)
    }
}

#Preview {
    HomeView(
        onProfileTap: {},
        onRecipeTap: { _ in },
        currentCatName: "大黄",
        recipes: Recipe.placeholders,
        isLoading: false
    )
}
