//
//  ContentView.swift
//  MoeChef - 根视图：全屏流 + 右上角 [👤] 进入管理中心
//

import SwiftUI
import SwiftData

@Observable
final class AppState {
    var showManagement = false
    var selectedRecipe: Recipe?
    var recipes: [Recipe] = []
    var isLoadingRecipes = true
    var didLoadRecipes = false
}

struct ContentView: View {
    @State private var state = AppState()
    @Query private var catProfiles: [CatProfile]

    var body: some View {
        Group {
            if state.showManagement {
                ManagementView(onBack: { state.showManagement = false })
            } else if let recipe = state.selectedRecipe {
                DetailView(
                    recipe: recipe,
                    catName: catProfiles.first?.name,
                    catBreed: catProfiles.first?.breed,
                    catBodyWeightKg: catProfiles.first?.bodyWeight,
                    onBack: { state.selectedRecipe = nil }
                )
            } else {
                HomeView(
                    onProfileTap: { state.showManagement = true },
                    onRecipeTap: { state.selectedRecipe = $0 },
                    currentCatName: catProfiles.first?.name,
                    recipes: state.recipes,
                    isLoading: state.isLoadingRecipes
                )
            }
        }
        .animation(.easeInOut(duration: 0.25), value: state.showManagement)
        .animation(.easeInOut(duration: 0.25), value: state.selectedRecipe?.id)
        .task {
            guard !state.didLoadRecipes else { return }
            state.didLoadRecipes = true
            await loadRecipes()
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
        do {
            let (data, response) = try await URLSession.shared.data(from: url)
            guard let httpResponse = response as? HTTPURLResponse,
                  (200...299).contains(httpResponse.statusCode) else {
                await MainActor.run {
                    state.recipes = []
                    state.isLoadingRecipes = false
                }
                return
            }
            let decoded = try JSONDecoder().decode(APIRecipesResponse.self, from: data)
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
            await MainActor.run {
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
