//
//  LoginView.swift
//  MoeChef - 使用 Apple 登录（PRD 色系 + 渐变按钮）
//

import SwiftUI
import AuthenticationServices
import CryptoKit

struct LoginView: View {
    @State private var currentNonce: String?
    @State private var errorMessage = ""
    @State private var showErrorAlert = false

    var body: some View {
        ZStack {
            Theme.Colors.background
                .ignoresSafeArea()

            VStack(spacing: 32) {
                Spacer()

                // 标题与副标题
                VStack(spacing: 12) {
                    Text("喵食记")
                        .font(.largeTitle.weight(.semibold))
                        .foregroundStyle(Theme.Colors.text)
                    Text("用 AI 过滤风险，用美学治愈生活")
                        .font(.subheadline)
                        .foregroundStyle(Theme.Colors.textSecondary)
                        .multilineTextAlignment(.center)
                }
                .padding(.horizontal)

                Spacer()

                // 使用 Apple 登录按钮（系统样式 + 我们包一层渐变边框/背景以贴合 PRD）
                SignInWithAppleButtonView(
                    currentNonce: $currentNonce,
                    errorMessage: $errorMessage,
                    showErrorAlert: $showErrorAlert
                )
                    .frame(height: 56)
                    .padding(.horizontal, 32)

                if !errorMessage.isEmpty {
                    Text(errorMessage)
                        .font(.footnote)
                        .foregroundStyle(.red)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal, 32)
                }

                Spacer()
                    .frame(height: 48)
            }
        }
        .onAppear {
            AuthService.shared.clearError()
            errorMessage = ""
            showErrorAlert = false
        }
        .alert("登录失败", isPresented: $showErrorAlert) {
            Button("知道了", role: .cancel) {}
        } message: {
            Text(errorMessage)
        }
    }
}

// MARK: - 封装 Apple 授权请求与 Supabase 登录
private struct SignInWithAppleButtonView: View {
    @Environment(\.colorScheme) private var colorScheme
    @Binding var currentNonce: String?
    @Binding var errorMessage: String
    @Binding var showErrorAlert: Bool
    @State private var isInProgress = false

    var body: some View {
        SignInWithAppleButton(.signIn) { request in
            print("[Apple登录] onRequest 触发 ✅")
            AuthService.shared.clearError()
            errorMessage = ""
            showErrorAlert = false
            let nonce = randomNonce()
            currentNonce = nonce
            request.requestedScopes = [.fullName, .email]
            request.nonce = sha256(nonce)
            print("[Apple登录] nonce 设置完成，等待系统弹窗...")
        } onCompletion: { result in
            print("[Apple登录] onCompletion 触发，result: \(result)")
            handleCompletion(result)
        }
        .signInWithAppleButtonStyle(colorScheme == .dark ? .white : .black)
        .disabled(isInProgress)
        .overlay(isInProgress ? ProgressView().tint(.white) : nil)
    }

    private func handleCompletion(_ result: Result<ASAuthorization, Error>) {
        switch result {
        case .success(let authorization):
            guard let nonce = currentNonce else {
                let msg = "登录失败：请求 nonce 丢失，请重试"
                print("[Apple登录] ❌ \(msg)")
                presentError(msg)
                return
            }
            guard let credential = authorization.credential as? ASAuthorizationAppleIDCredential,
                  let idToken = credential.identityToken else {
                let msg = "登录失败：Apple 未返回 identityToken，请在模拟器重新登录 Apple ID 后重试"
                print("[Apple登录] ❌ \(msg)")
                presentError(msg)
                return
            }
            print("[Apple登录] ✅ 获取到 idToken，开始 Supabase 登录...")
            isInProgress = true
            Task { @MainActor in
                do {
                    try await AuthService.shared.signInWithApple(
                        idToken: idToken,
                        nonce: nonce,
                        fullName: credential.fullName
                    )
                    print("[Apple登录] ✅ Supabase 登录成功")
                } catch {
                    print("[Apple登录] ❌ Supabase 登录失败: \(error)")
                    presentError(detailedErrorMessage(error))
                }
                isInProgress = false
                currentNonce = nil
            }
        case .failure(let error):
            let msg = detailedErrorMessage(error)
            print("[Apple登录] ❌ Apple 授权失败: \(error)")
            presentError(msg)
            currentNonce = nil
        }
    }

    private func randomNonce() -> String {
        (0..<32)
            .map { _ in String("0123456789ABCDEFGHIJKLMNOPQRSTUVXYZabcdefghijklmnopqrstuvwxyz-._".randomElement()!) }
            .joined()
    }

    private func sha256(_ input: String) -> String {
        let data = Data(input.utf8)
        let hash = SHA256.hash(data: data)
        return hash.compactMap { String(format: "%02x", $0) }.joined()
    }

    private func detailedErrorMessage(_ error: Error) -> String {
        if let authError = error as? ASAuthorizationError {
            switch authError.code {
            case .canceled:
                return "已取消 Apple 登录。"
            case .failed:
                return "Apple 登录失败，请稍后重试（1004）。"
            case .invalidResponse:
                return "Apple 返回了无效的登录响应（1002）。请重试。"
            case .notHandled:
                return "Apple 登录未被处理（1003）。请确认设备已登录 Apple ID。"
            case .unknown:
                return "Apple 登录出现未知错误（1000）。模拟器请先在「设置」中登录 Sandbox Apple ID，真机请确认 Apple ID 已登录。"
            case .notInteractive:
                return "Apple 登录需要用户交互，请重试。"
            @unknown default:
                break
            }
        }

        let desc = error.localizedDescription
        let nsError = error as NSError

        // 常见 Supabase 错误提示
        let combined = "\(desc) \(nsError.domain)"
        if combined.localizedCaseInsensitiveContains("provider") {
            return "Supabase 未启用 Apple 登录，请在 Supabase Dashboard → Authentication → Providers 中开启 Apple，并填写 Bundle ID：com.moechef.app。"
        }
        if combined.localizedCaseInsensitiveContains("invalid") || combined.localizedCaseInsensitiveContains("nonce") {
            return "登录凭证验证失败，请重试。（\(desc)）"
        }
        if combined.localizedCaseInsensitiveContains("network") || nsError.code == NSURLErrorNotConnectedToInternet {
            return "网络连接失败，请检查网络后重试。"
        }

        return "\(desc) [\(nsError.domain):\(nsError.code)]"
    }

    private func presentError(_ message: String) {
        AuthService.shared.setError(message)
        errorMessage = message
        showErrorAlert = true
    }
}

#Preview {
    LoginView()
}
