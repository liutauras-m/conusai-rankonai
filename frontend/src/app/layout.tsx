import type { Metadata } from "next"
import { Archivo, Inter, Space_Mono } from "next/font/google"
import "./globals.css"
import { ThemeProvider } from "@/components/theme-provider"
import { PostHogProvider } from "@/components/posthog-provider"

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
	description: "See if ChatGPT, Perplexity, Claude and other AI assistants can find and recommend your brand. Get your AI visibility score and optimize for AI search.",
	icons: {
		icon: "/favicon.png",
		apple: "/favicon.png",
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
						defaultTheme="dark"
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
