//
//  ContentView.swift
//  MoeChef - 根视图：全屏流 + 右上角 [👤] 进入管理中心
//

import SwiftUI
import SwiftData
import os.log

private let logger = Logger(subsystem: "com.moechef.app", category: "Recipes")

@Observable
final class AppState {
    var showManagement = false
    var selectedRecipe: Recipe?
    var recipes: [Recipe] = []
    var isLoadingRecipes = true
    var didLoadRecipes = false
    var loadError: String?
}

struct ContentView: View {
    @State private var state = AppState()
    @Query private var catProfiles: [CatProfile]

    var body: some View {
        Group {
            if state.showManagement {
                ManagementView(onBack: { state.showManagement = false })
            } else {
                // 首页常驻底层，详情叠在上面，返回时不会重建 HomeView，从而保留滚动位置与搜索/分类状态
                ZStack {
                    HomeView(
                        onProfileTap: { state.showManagement = true },
                        onRecipeTap: { state.selectedRecipe = $0 },
                        currentCatName: catProfiles.first?.name,
                        recipes: state.recipes,
                        isLoading: state.isLoadingRecipes
                    )
                    if let recipe = state.selectedRecipe {
                        DetailView(
                            recipe: recipe,
                            catName: catProfiles.first?.name,
                            catBreed: catProfiles.first?.breed,
                            catBodyWeightKg: catProfiles.first?.bodyWeight,
                            onBack: { state.selectedRecipe = nil }
                        )
                        .transition(.move(edge: .trailing))
                        .zIndex(1)
                    }
                }
            }
        }
        .animation(.easeInOut(duration: 0.25), value: state.showManagement)
        .animation(.easeInOut(duration: 0.25), value: state.selectedRecipe?.id)
        .task {
            guard !state.didLoadRecipes else { return }
            state.didLoadRecipes = true
            await loadRecipes()
        }
        .alert("加载失败", isPresented: .init(
            get: { state.loadError != nil },
            set: { if !$0 { state.loadError = nil } }
        )) {
            Button("重试") {
                state.didLoadRecipes = false
                state.isLoadingRecipes = true
                Task { await loadRecipes() }
            }
            Button("知道了", role: .cancel) {}
        } message: {
            Text(state.loadError ?? "")
        }
    }
}

private extension ContentView {
    struct APIRecipesResponse: Decodable {
        let items: [APIRecipe]
    }

    struct APIRecipe: Decodable {
        let id: String
        let title: String
        let subtitle: String
        let category: String
        let imageURL: String?
        let ingredients: [APIIngredient]
        let steps: [String]
        let aiBreedNote: String?
        let safetyPassed: Bool?

        private enum CodingKeys: String, CodingKey {
            case id
            case title
            case subtitle
            case category
            case imageURL
            case image_url
            case ingredients
            case steps
            case aiBreedNote
            case safetyPassed
            case ai_breed_note
            case safety_passed
        }

        init(from decoder: Decoder) throws {
            let c = try decoder.container(keyedBy: CodingKeys.self)
            id = try c.decode(String.self, forKey: .id)
            title = try c.decode(String.self, forKey: .title)
            subtitle = try c.decode(String.self, forKey: .subtitle)
            category = try c.decode(String.self, forKey: .category)
            imageURL = try c.decodeIfPresent(String.self, forKey: .imageURL)
                ?? c.decodeIfPresent(String.self, forKey: .image_url)
            ingredients = try c.decode([APIIngredient].self, forKey: .ingredients)
            steps = try c.decode([String].self, forKey: .steps)
            aiBreedNote = try c.decodeIfPresent(String.self, forKey: .aiBreedNote)
                ?? c.decodeIfPresent(String.self, forKey: .ai_breed_note)
            safetyPassed = try c.decodeIfPresent(Bool.self, forKey: .safetyPassed)
                ?? c.decodeIfPresent(Bool.self, forKey: .safety_passed)
        }
    }

    struct APIIngredient: Decodable {
        let name: String
        let amount: String
    }

    func loadRecipes() async {
        let url = AppConfig.recipesURL
        logger.info("📡 loadRecipes 请求 URL: \(url.absoluteString)")
        do {
            let (data, response) = try await URLSession.shared.data(from: url)
            guard let httpResponse = response as? HTTPURLResponse else {
                let msg = "响应不是 HTTP 类型"
                logger.error("❌ \(msg)")
                await MainActor.run {
                    state.loadError = msg
                    state.recipes = []
                    state.isLoadingRecipes = false
                }
                return
            }
            logger.info("📡 HTTP 状态码: \(httpResponse.statusCode)")
            guard (200...299).contains(httpResponse.statusCode) else {
                let body = String(data: data, encoding: .utf8) ?? "(无法解码)"
                let msg = "HTTP \(httpResponse.statusCode)\n\(body.prefix(200))"
                logger.error("❌ 非 2xx: \(msg)")
                await MainActor.run {
                    state.loadError = "服务器返回 \(msg)"
                    state.recipes = []
                    state.isLoadingRecipes = false
                }
                return
            }
            let decoded = try JSONDecoder().decode(APIRecipesResponse.self, from: data)
            logger.info("✅ 解码成功，共 \(decoded.items.count) 条食谱")
            let mapped = decoded.items.map { item in
                Recipe(
                    id: item.id,
                    title: item.title,
                    subtitle: item.subtitle,
                    category: RecipeCategory(apiValue: item.category),
                    imageURL: item.imageURL,
                    ingredients: item.ingredients.map { Ingredient(name: $0.name, amount: $0.amount) },
                    steps: item.steps,
                    aiBreedNote: item.aiBreedNote,
                    safetyPassed: item.safetyPassed ?? true
                )
            }
            await MainActor.run {
                state.recipes = mapped
                state.isLoadingRecipes = false
            }
        } catch {
            let msg = "URL: \(url.absoluteString)\n错误: \(error.localizedDescription)"
            logger.error("❌ loadRecipes 失败: \(msg)")
            await MainActor.run {
                state.loadError = msg
                state.recipes = []
                state.isLoadingRecipes = false
            }
        }
    }
}

#Preview {
    ContentView()
        .modelContainer(for: CatProfile.self, inMemory: true)
}
