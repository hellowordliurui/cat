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
    /// Supabase REST API 直接返回数组，不需要外层包装
    struct APIRecipe: Decodable {
        let id: String
        let title: String
        let subtitle: String?
        let category: String?
        let image_url: String?
        let ingredients: [APIIngredient]?
        let steps: [String]?
        let ai_breed_note: String?
        let safety_passed: Bool?
    }

    struct APIIngredient: Decodable {
        let name: String
        let amount: String
    }

    func loadRecipes() async {
        // 直接调用 Supabase PostgREST API，绕过 Vercel 后端（解决国内网络超时问题）
        let cols = "id,title,subtitle,category,image_url,ingredients,steps,ai_breed_note,safety_passed"
        let baseURL = SupabaseConfig.supabaseURL.absoluteString
        let urlString = "\(baseURL)/rest/v1/recipes?select=\(cols)&order=created_at.desc"

        guard let url = URL(string: urlString) else {
            logger.error("❌ URL 构造失败: \(urlString)")
            await MainActor.run {
                state.loadError = "URL 构造失败"
                state.recipes = []
                state.isLoadingRecipes = false
            }
            return
        }

        logger.info("📡 loadRecipes 直连 Supabase: \(url.absoluteString)")

        var request = URLRequest(url: url, timeoutInterval: 15)
        request.setValue(SupabaseConfig.supabaseAnonKey, forHTTPHeaderField: "apikey")
        request.setValue("Bearer \(SupabaseConfig.supabaseAnonKey)", forHTTPHeaderField: "Authorization")

        do {
            let (data, response) = try await URLSession.shared.data(for: request)
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
                let msg = "HTTP \(httpResponse.statusCode)\n\(body.prefix(300))"
                logger.error("❌ 非 2xx: \(msg)")
                await MainActor.run {
                    state.loadError = "Supabase 返回 \(msg)"
                    state.recipes = []
                    state.isLoadingRecipes = false
                }
                return
            }
            // Supabase PostgREST 直接返回 JSON 数组
            let decoded = try JSONDecoder().decode([APIRecipe].self, from: data)
            logger.info("✅ 解码成功，共 \(decoded.count) 条食谱")
            let mapped = decoded.map { item in
                Recipe(
                    id: item.id,
                    title: item.title,
                    subtitle: item.subtitle ?? "",
                    category: RecipeCategory(apiValue: item.category ?? "all"),
                    imageURL: item.image_url,
                    ingredients: (item.ingredients ?? []).map { Ingredient(name: $0.name, amount: $0.amount) },
                    steps: item.steps ?? [],
                    aiBreedNote: item.ai_breed_note,
                    safetyPassed: item.safety_passed ?? true
                )
            }
            await MainActor.run {
                state.recipes = mapped
                state.isLoadingRecipes = false
            }
        } catch {
            let msg = "Supabase: \(url.host ?? "")\n错误: \(error.localizedDescription)"
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
