//
//  SupabaseConfig.swift
//  MoeChef - Supabase 项目配置（可改为从 plist 读取）
//

import Foundation

enum SupabaseConfig {
    /// 项目 URL（Supabase Dashboard → Project Settings → API）
    static let supabaseURL = URL(string: "https://jqigumxkgbkxccvymotd.supabase.co")!

    /// 匿名/公钥 anon key（用于客户端 Auth，不要放 service_role）
    static let supabaseAnonKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpxaWd1bXhrZ2JreGNjdnltb3RkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzI1OTIxNzMsImV4cCI6MjA4ODE2ODE3M30.gZ5MiHsov_AZYqMb8o-1KQciFDHejl8Za9WIetoHsmw"
}
