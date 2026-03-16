import SwiftUI
import UIKit

struct CachedRemoteImage<Content: View, Placeholder: View>: View {
    let url: URL?
    @ViewBuilder let content: (Image) -> Content
    @ViewBuilder let placeholder: () -> Placeholder

    @StateObject private var loader = CachedImageLoader()

    var body: some View {
        Group {
            if let image = loader.image {
                content(Image(uiImage: image))
            } else {
                placeholder()
            }
        }
        .task(id: url) {
            await loader.load(from: url)
        }
    }
}

@MainActor
private final class CachedImageLoader: ObservableObject {
    @Published var image: UIImage?

    private static let memoryCache = NSCache<NSURL, UIImage>()

    func load(from url: URL?) async {
        guard let url else {
            image = nil
            return
        }

        let nsURL = url as NSURL
        if let cachedImage = Self.memoryCache.object(forKey: nsURL) {
            image = cachedImage
            return
        }

        let request = URLRequest(
            url: url,
            cachePolicy: .returnCacheDataElseLoad,
            timeoutInterval: 60
        )

        if let cachedResponse = URLCache.shared.cachedResponse(for: request),
           let cachedImage = UIImage(data: cachedResponse.data) {
            Self.memoryCache.setObject(cachedImage, forKey: nsURL)
            image = cachedImage
            return
        }

        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            guard let downloadedImage = UIImage(data: data) else {
                image = nil
                return
            }

            Self.memoryCache.setObject(downloadedImage, forKey: nsURL)
            URLCache.shared.storeCachedResponse(
                CachedURLResponse(response: response, data: data),
                for: request
            )
            image = downloadedImage
        } catch {
            image = nil
        }
    }
}
