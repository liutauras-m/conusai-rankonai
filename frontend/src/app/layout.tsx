import type { Metadata } from "next"
import { Archivo, Inter, Space_Mono } from "next/font/google"
import "./globals.css"
import { PostHogProvider } from "@/components/posthog-provider"
import { ThemeProvider } from "@/components/theme-provider"

const archivo = Archivo({
	subsets: ["latin"],
	variable: "--font-display",
	display: "swap",
})

const inter = Inter({
	subsets: ["latin"],
	variable: "--font-sans",
	display: "swap",
})

const spaceMono = Space_Mono({
	subsets: ["latin"],
	weight: ["400", "700"],
	variable: "--font-mono",
	display: "swap",
})

export const metadata: Metadata = {
	title: "Rank on AI Search - Check Your AI Visibility",
	description:
		"See if ChatGPT, Perplexity, Claude and other AI assistants can find and recommend your brand. Get your AI visibility score and optimize for AI search.",
	keywords: [
		"AI search",
		"AI visibility",
		"ChatGPT ranking",
		"Perplexity SEO",
		"Claude optimization",
		"AI recommendations",
		"brand visibility",
		"AI SEO",
		"LLM optimization",
	],
	authors: [{ name: "Rank on AI" }],
	creator: "Rank on AI",
	publisher: "Rank on AI",
	metadataBase: new URL("https://rankonai.com"),
	alternates: {
		canonical: "/",
	},
	icons: {
		icon: "/favicon.png",
		apple: "/favicon.png",
	},
	openGraph: {
		type: "website",
		locale: "en_US",
		url: "https://rankonai.com",
		siteName: "Rank on AI",
		title: "Rank on AI Search - Check Your AI Visibility",
		description:
			"See if ChatGPT, Perplexity, Claude and other AI assistants can find and recommend your brand. Get your AI visibility score and optimize for AI search.",
		images: [
			{
				url: "/social.png",
				width: 1200,
				height: 630,
				alt: "Rank on AI - Check Your AI Visibility Score",
			},
		],
	},
	twitter: {
		card: "summary_large_image",
		title: "Rank on AI Search - Check Your AI Visibility",
		description:
			"See if ChatGPT, Perplexity, Claude and other AI assistants can find and recommend your brand. Get your AI visibility score.",
		images: ["/social.png"],
		creator: "@rankonai",
	},
	robots: {
		index: true,
		follow: true,
		googleBot: {
			index: true,
			follow: true,
			"max-video-preview": -1,
			"max-image-preview": "large",
			"max-snippet": -1,
		},
	},
}

export default function RootLayout({
	children,
}: Readonly<{
	children: React.ReactNode
}>) {
	return (
		<html lang="en" suppressHydrationWarning>
			<body
				className={`${archivo.variable} ${inter.variable} ${spaceMono.variable} font-sans antialiased`}
				suppressHydrationWarning
			>
				<PostHogProvider>
					<ThemeProvider
						attribute="class"
						defaultTheme="light"
						enableSystem
						disableTransitionOnChange
					>
						{children}
					</ThemeProvider>
				</PostHogProvider>
			</body>
		</html>
	)
}
