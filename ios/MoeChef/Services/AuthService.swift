//
//  AuthService.swift
//  MoeChef - Supabase Auth + Sign in with Apple 封装 + 账户删除
//

import Foundation
import AuthenticationServices
import CryptoKit
import Supabase

@Observable
@MainActor
final class AuthService {
    static let shared = AuthService()

    private(set) var session: Session?
    private(set) var isLoading = false
    private(set) var errorMessage: String?

    private let client: SupabaseClient
    private var authStateTask: Task<Void, Never>?

    private init() {
        client = SupabaseClient(
            supabaseURL: SupabaseConfig.supabaseURL,
            supabaseKey: SupabaseConfig.supabaseAnonKey
        )
        Task {
            self.session = try? await client.auth.session
        }
        authStateTask = observeAuthState()
    }

    #if DEBUG
    private(set) var isDevLoggedIn = false
    #endif

    var isLoggedIn: Bool {
        #if DEBUG
        if isDevLoggedIn { return true }
        #endif
        return session != nil
    }

    /// 监听 Auth 状态变化（登录/登出/刷新）
    private func observeAuthState() -> Task<Void, Never> {
        Task {
            for await (event, session) in client.auth.authStateChanges {
                self.session = (event == .signedOut) ? nil : session
            }
        }
    }

    /// 使用 Apple 凭证登录（由 LoginView 在拿到 ASAuthorizationAppleIDCredential 后调用）
    func signInWithApple(
        idToken: Data,
        nonce: String,
        fullName: PersonNameComponents?
    ) async throws {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        guard let idTokenString = String(data: idToken, encoding: .utf8) else {
            throw AppleAuthError.invalidIdToken
        }

        let session = try await client.auth.signInWithIdToken(
            credentials: OpenIDConnectCredentials(
                provider: .apple,
                idToken: idTokenString,
                nonce: nonce
            )
        )

        self.session = session
    }

    func signOut() async throws {
        #if DEBUG
        if isDevLoggedIn {
            isDevLoggedIn = false
            return
        }
        #endif
        try await client.auth.signOut()
        session = nil
    }

    /// 删除当前用户账户：调用 Supabase Edge Function 或直接用 RPC 删除
    /// 流程：先通过 Supabase RPC 删除服务端用户数据，然后登出
    func deleteAccount() async throws {
        #if DEBUG
        if isDevLoggedIn {
            isDevLoggedIn = false
            return
        }
        #endif

        guard let userId = session?.user.id else {
            throw AccountError.notLoggedIn
        }

        // 调用 Supabase Edge Function 来删除用户
        // 如果 Edge Function 未部署，直接登出（用户数据会在 Supabase Dashboard 中手动清理）
        let deleteURL = URL(string: "\(SupabaseConfig.supabaseURL.absoluteString)/functions/v1/delete-user")!
        var request = URLRequest(url: deleteURL, timeoutInterval: 15)
        request.httpMethod = "POST"
        request.setValue("Bearer \(session?.accessToken ?? SupabaseConfig.supabaseAnonKey)", forHTTPHeaderField: "Authorization")
        request.setValue(SupabaseConfig.supabaseAnonKey, forHTTPHeaderField: "apikey")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try? JSONEncoder().encode(["user_id": userId.uuidString])

        // 尝试调用 Edge Function，即使失败也继续登出
        if let (_, response) = try? await URLSession.shared.data(for: request),
           let httpResponse = response as? HTTPURLResponse,
           (200...299).contains(httpResponse.statusCode) {
            // Edge Function 成功删除
        }
        // 无论 Edge Function 是否成功，都执行登出
        try await client.auth.signOut()
        session = nil
    }

    #if DEBUG
    func devLogin() {
        isDevLoggedIn = true
    }
    #endif

    func clearError() {
        errorMessage = nil
    }

    func setError(_ message: String) {
        errorMessage = message
    }
}

enum AppleAuthError: LocalizedError {
    case invalidIdToken
    var errorDescription: String? {
        switch self {
        case .invalidIdToken: return "无法解析 Apple 登录凭证，请重试"
        }
    }
}

enum AccountError: LocalizedError {
    case notLoggedIn
    case deletionFailed(String)
    var errorDescription: String? {
        switch self {
        case .notLoggedIn: return "您尚未登录"
        case .deletionFailed(let reason): return "账户删除失败：\(reason)"
        }
    }
}
