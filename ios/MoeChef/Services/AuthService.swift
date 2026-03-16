//
//  AuthService.swift
//  MoeChef - Supabase Auth + Sign in with Apple 封装
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
