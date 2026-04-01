//
//  ManagementView.swift
//  MoeChef - 管理中心：猫咪档案（SwiftData）、禁忌清单、账户设置
//

import SwiftUI
import SwiftData

struct ManagementView: View {
    var onBack: () -> Void

    @Environment(\.modelContext) private var modelContext
    @Query(sort: \CatProfile.name) private var catProfiles: [CatProfile]
    @State private var forbiddenList: [ForbiddenItem] = ForbiddenItem.placeholders
    @State private var editorCat: CatProfile?
    @State private var showAccountSettings = false
    @State private var didLoadRemote = false
    
    var body: some View {
        ScrollView {
            VStack(spacing: 24) {
                catProfileCard
                forbiddenCard
                settingsCard
            }
            .padding(20)
            .padding(.top, 18)
            .padding(.bottom, 40)
        }
        .background(Theme.Colors.background)
        .safeAreaInset(edge: .top, spacing: 0) {
            topBar
        }
        .sheet(item: $editorCat) { cat in
            CatProfileEditorView(cat: cat, onDismiss: { editorCat = nil })
        }
        .sheet(isPresented: $showAccountSettings) {
            AccountSettingsSheet(onDismiss: { showAccountSettings = false })
        }
        .navigationBarHidden(true)
        .task {
            guard !didLoadRemote else { return }
            didLoadRemote = true
            await loadForbiddenFromBackend()
        }
    }

    /// 与详情页一致的顶部栏：返回箭头位置、内边距与背景
    private var topBar: some View {
        HStack {
            backButton
            Spacer()
        }
        .padding(.horizontal, 18)
        .padding(.top, 10)
        .padding(.bottom, 6)
        .background(Theme.Colors.background.opacity(0.96))
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
    
    private var catProfileCard: some View {
        Button {
            if let first = catProfiles.first {
                editorCat = first
            } else {
                let newCat = CatProfile(name: "", breed: "", bodyWeight: 5.0)
                modelContext.insert(newCat)
                editorCat = newCat
            }
        } label: {
            HStack {
                Image(systemName: "cat.fill")
                    .font(.title2)
                    .foregroundStyle(Theme.Colors.coral)
                VStack(alignment: .leading, spacing: 4) {
                    Text("猫咪档案")
                        .font(.headline)
                        .foregroundStyle(Theme.Colors.text)
                    if let cat = catProfiles.first, !cat.name.isEmpty {
                        let breedText = cat.breed.isEmpty ? "未知品种" : cat.breed
                        let extra = cat.birthDate.map { Self.formatBirthDate($0) } ?? ""
                        Text("\(cat.name) · \(breedText) · \((cat.gender ?? .unknown).rawValue)\(extra.isEmpty ? "" : " · \(extra)")")
                            .font(.subheadline)
                            .foregroundStyle(Theme.Colors.textSecondary)
                    } else {
                        Text("点击设置")
                            .font(.subheadline)
                            .foregroundStyle(Theme.Colors.textSecondary)
                    }
                }
                Spacer()
                Image(systemName: "chevron.right")
                    .font(.system(size: 20, weight: .semibold))
                    .foregroundStyle(Theme.Colors.textSecondary)
                    .frame(width: 34, height: 34)
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 16)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Theme.cardBackground())
            .clipShape(RoundedRectangle(cornerRadius: Theme.cardCornerRadius, style: .continuous))
            .shadow(color: Theme.premiumShadowColor.opacity(Theme.premiumShadowOpacity), radius: Theme.premiumShadowRadius, x: 0, y: 4)
        }
        .buttonStyle(.plain)
    }

    private static func formatBirthDate(_ date: Date) -> String {
        let f = DateFormatter()
        f.locale = Locale(identifier: "zh_CN")
        f.dateFormat = "yyyy年M月d日"
        return "生于" + f.string(from: date)
    }
    
    private var forbiddenCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "exclamationmark.triangle.fill")
                    .foregroundStyle(Theme.Colors.danger)
                Text("禁忌清单：铲屎官安全红线")
                    .font(.headline)
                    .foregroundStyle(Theme.Colors.text)
            }
            VStack(alignment: .leading, spacing: 10) {
                ForEach(forbiddenList) { item in
                    HStack(alignment: .firstTextBaseline, spacing: 8) {
                        Circle()
                            .fill(item.level == .fatal ? Theme.Colors.danger : Theme.Colors.warning)
                            .frame(width: 8, height: 8)
                        Text("\(item.level.rawValue)：\(item.name)")
                            .font(.subheadline)
                            .foregroundStyle(Theme.Colors.textSecondary)
                    }
                }
            }
            .padding(16)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Theme.Colors.background)
            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
        }
        .padding(20)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Theme.cardBackground())
        .clipShape(RoundedRectangle(cornerRadius: Theme.cardCornerRadius, style: .continuous))
        .shadow(color: Theme.premiumShadowColor.opacity(Theme.premiumShadowOpacity), radius: Theme.premiumShadowRadius, x: 0, y: 4)
    }
    
    private var settingsCard: some View {
        Button {
            showAccountSettings = true
        } label: {
            HStack {
                Image(systemName: "gearshape.fill")
                    .foregroundStyle(Theme.Colors.coral)
                Text("账户设置")
                    .font(.headline)
                    .foregroundStyle(Theme.Colors.text)
                Spacer()
                Image(systemName: "chevron.right")
                    .font(.system(size: 20, weight: .semibold))
                    .foregroundStyle(Theme.Colors.textSecondary)
                    .frame(width: 34, height: 34)
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 16)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Theme.cardBackground())
            .clipShape(RoundedRectangle(cornerRadius: Theme.cardCornerRadius, style: .continuous))
            .shadow(color: Theme.premiumShadowColor.opacity(Theme.premiumShadowOpacity), radius: Theme.premiumShadowRadius, x: 0, y: 4)
        }
        .buttonStyle(.plain)
    }
}

// MARK: - 账户设置（内含退出登录）
private struct AccountSettingsSheet: View {
    var onDismiss: () -> Void

    var body: some View {
        NavigationStack {
            List {
                Button {
                    Task {
                        try? await AuthService.shared.signOut()
                    }
                    onDismiss()
                } label: {
                    HStack {
                        Image(systemName: "rectangle.portrait.and.arrow.right")
                            .foregroundStyle(Theme.Colors.textSecondary)
                        Text("退出登录")
                            .font(.headline)
                            .foregroundStyle(Theme.Colors.text)
                    }
                }
            }
            .navigationTitle("账户设置")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button(action: onDismiss) {
                        Image(systemName: "chevron.left")
                            .font(.system(size: 20, weight: .semibold))
                            .foregroundStyle(Theme.Colors.text)
                            .frame(width: 34, height: 34)
                    }
                }
            }
        }
    }
}

private extension ManagementView {
    struct APIForbiddenResponse: Decodable {
        let items: [APIForbiddenItem]
    }

    struct APIForbiddenItem: Decodable {
        let id: String
        let name: String
        let level: String
    }

    func loadForbiddenFromBackend() async {
        guard let url = URL(string: "\(AppConfig.backendBaseURL)/api/forbidden") else { return }
        do {
            let (data, response) = try await URLSession.shared.data(from: url)
            guard let httpResponse = response as? HTTPURLResponse, (200...299).contains(httpResponse.statusCode) else {
                return
            }
            let decoded = try JSONDecoder().decode(APIForbiddenResponse.self, from: data)
            let mapped = decoded.items.map { item in
                ForbiddenItem(
                    id: item.id,
                    name: item.name,
                    level: ForbiddenLevel(apiValue: item.level)
                )
            }
            if !mapped.isEmpty {
                await MainActor.run {
                    forbiddenList = mapped
                }
            }
        } catch {
            // 保留占位数据，避免页面空白
        }
    }
}

extension ForbiddenItem {
    static var placeholders: [ForbiddenItem] {
        [
            ForbiddenItem(id: "f1", name: "洋葱、巧克力、葡萄", level: .fatal),
            ForbiddenItem(id: "f2", name: "牛奶、生蛋白、高盐", level: .risk)
        ]
    }
}

private extension ForbiddenLevel {
    init(apiValue: String) {
        let value = apiValue.lowercased()
        if value == "fatal" || apiValue == "致命类" {
            self = .fatal
        } else {
            self = .risk
        }
    }
}

// MARK: - 猫咪档案编辑（SwiftData 持久化）
private struct CatProfileEditorView: View {
    @Bindable var cat: CatProfile
    var onDismiss: () -> Void

    var body: some View {
        NavigationStack {
            Form {
                Section("基本信息") {
                    HStack {
                        Text("名字")
                        Spacer()
                        TextField("请输入名字", text: $cat.name)
                            .multilineTextAlignment(.trailing)
                    }

                    Picker("品种", selection: $cat.breed) {
                        ForEach(CatProfile.commonBreeds, id: \.self) { breed in
                            Text(breed).tag(breed)
                        }
                    }

                    Picker("性别", selection: Binding(get: { cat.gender ?? .unknown }, set: { cat.gender = $0 })) {
                        ForEach(CatGender.allCases, id: \.self) { gender in
                            Text(gender.rawValue).tag(gender)
                        }
                    }

                    Picker("是否绝育", selection: Binding(get: { cat.sterilization ?? .unknown }, set: { cat.sterilization = $0 })) {
                        ForEach(CatSterilization.allCases, id: \.self) { status in
                            Text(status.rawValue).tag(status)
                        }
                    }

                    DatePicker("出生日期", selection: Binding(
                        get: { cat.birthDate ?? Calendar.current.date(byAdding: .year, value: -1, to: Date()) ?? Date() },
                        set: { cat.birthDate = $0 }
                    ), displayedComponents: .date)
                }

                Section("健康数据") {
                    HStack {
                        Text("体重")
                        Spacer()
                        HStack(spacing: 4) {
                            TextField("0.0", value: $cat.bodyWeight, format: .number)
                                .keyboardType(.decimalPad)
                                .multilineTextAlignment(.trailing)
                            Text("kg")
                                .foregroundStyle(.secondary)
                        }
                    }
                }
            }
            .navigationTitle("猫咪档案")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("完成", action: onDismiss)
                }
            }
        }
    }
}

#Preview {
    ManagementView(onBack: {})
        .modelContainer(for: CatProfile.self, inMemory: true)
}
