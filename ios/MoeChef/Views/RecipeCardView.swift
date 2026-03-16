//
//  RecipeCardView.swift
//  MoeChef - 大圆角卡片，每道菜配图
//

import SwiftUI

struct RecipeCardView: View {
    let recipe: Recipe
    var style: CardStyle = .small
    
    enum CardStyle {
        case large
        case small
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // 占位图（后续接真实图）
            imagePlaceholder
            Text(recipe.title)
                .font(style == .large ? .headline : .subheadline)
                .fontWeight(.medium)
                .foregroundStyle(Theme.Colors.text)
                .lineLimit(2)
                .padding(.horizontal, 12)
                .padding(.vertical, 10)
        }
        .background(Theme.cardBackground())
        .clipShape(RoundedRectangle(cornerRadius: Theme.cardCornerRadius, style: .continuous))
        .shadow(
            color: Theme.premiumShadowColor.opacity(Theme.premiumShadowOpacity),
            radius: Theme.premiumShadowRadius,
            x: 0,
            y: 4
        )
    }
    
    private var imagePlaceholder: some View {
        ZStack {
            if let url = recipe.resolvedImageURL {
                CachedRemoteImage(url: url) { image in
                    image
                        .resizable()
                        .scaledToFill()
                } placeholder: {
                    RecipeDefaultPlaceholder(
                        iconSize: style == .large ? 46 : 34,
                        subtitleSize: style == .large ? 14 : 12
                    )
                }
            } else {
                RecipeDefaultPlaceholder(
                    iconSize: style == .large ? 46 : 34,
                    subtitleSize: style == .large ? 14 : 12
                )
            }
        }
        .frame(height: style == .large ? 180 : 120)
        .frame(maxWidth: .infinity)
        .clipShape(RoundedRectangle(cornerRadius: Theme.cardCornerRadius, style: .continuous))
    }
}

#Preview {
    VStack(spacing: 16) {
        RecipeCardView(recipe: Recipe.placeholders[0], style: .large)
        HStack(spacing: 12) {
            RecipeCardView(recipe: Recipe.placeholders[1], style: .small)
            RecipeCardView(recipe: Recipe.placeholders[2], style: .small)
        }
    }
    .padding()
    .background(Theme.Colors.background)
}

struct RecipeDefaultPlaceholder: View {
    let iconSize: CGFloat
    let subtitleSize: CGFloat

    var body: some View {
        ZStack {
            LinearGradient(
                colors: [
                    Theme.Colors.tiffany.opacity(0.45),
                    Theme.Colors.champagne.opacity(0.55)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )

            VStack(spacing: 8) {
                Image(systemName: "pawprint.circle.fill")
                    .font(.system(size: iconSize))
                    .foregroundStyle(Theme.Colors.coral.opacity(0.85))
                Text("暂无封面")
                    .font(.system(size: subtitleSize, weight: .medium))
                    .foregroundStyle(Theme.Colors.textSecondary.opacity(0.9))
            }
        }
    }
}
