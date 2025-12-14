"use client"

import Image from "next/image"
import { useState } from "react"
import { useRouter } from "next/navigation"
import { ThemeToggle } from "@/components/theme-toggle"
import { LoadingOverlay } from "@/components/ui/spinner"
import { Turnstile } from "@/components/turnstile"

const TURNSTILE_SITE_KEY = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY || ""

// AI platforms we check visibility for
const AI_PLATFORMS = [
	{ name: "ChatGPT", icon: "🤖" },
	{ name: "Perplexity", icon: "🔍" },
	{ name: "Claude", icon: "🧠" },
	{ name: "Gemini", icon: "✨" },
	{ name: "Grok", icon: "⚡" },
]

export default function Home() {
	const [url, setUrl] = useState("")
	const [loading, setLoading] = useState(false)
	const [error, setError] = useState<string | null>(null)
	const [captchaToken, setCaptchaToken] = useState<string | null>(null)
	const router = useRouter()

	const handleAnalyze = async () => {
		if (!url) return

		// Require CAPTCHA in production
		if (TURNSTILE_SITE_KEY && !captchaToken) {
			setError("Please complete the verification")
			return
		}

		setLoading(true)
		setError(null)

		// Normalize URL
		let normalizedUrl = url.trim()
		if (
			!normalizedUrl.startsWith("http://") &&
			!normalizedUrl.startsWith("https://")
		) {
			normalizedUrl = `https://${normalizedUrl}`
		}

		// Navigate to report page with URL and captcha token as query params
		const params = new URLSearchParams({ url: normalizedUrl })
		if (captchaToken) {
			params.set("token", captchaToken)
		}
		router.push(`/report?${params.toString()}`)
	}

	const handleKeyDown = (e: React.KeyboardEvent) => {
		if (e.key === "Enter" && url && (captchaToken || !TURNSTILE_SITE_KEY)) {
			handleAnalyze()
		}
	}

	return (
		<div className="relative flex min-h-screen flex-col items-center justify-center bg-background px-4">
			{loading && <LoadingOverlay message="Checking AI visibility..." />}

			<div className="absolute top-4 right-4">
				<ThemeToggle />
			</div>

			<main className="flex w-full max-w-lg flex-col items-center gap-8">
				{/* Logo */}
				<div className="flex items-center gap-3">
					<Image
						src="/favicon.png"
						alt="Rank on AI Search"
						width={48}
						height={48}
						priority
					/>
				</div>

				{/* Hero Section */}
				<div className="text-center">
					<h1 className="font-display text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">
						Rank on AI Search
					</h1>
					<p className="mt-4 text-lg text-muted-foreground">
						Check if ChatGPT, Perplexity & Claude recommend your brand
					</p>
				</div>

				{/* Value Proposition */}
				<div className="flex flex-wrap justify-center gap-3">
					{AI_PLATFORMS.map((platform) => (
						<span
							key={platform.name}
							className="inline-flex items-center gap-1.5 rounded-full bg-muted px-3 py-1.5 text-sm text-muted-foreground"
						>
							<span>{platform.icon}</span>
							{platform.name}
						</span>
					))}
				</div>

				{/* URL Input */}
				<div className="flex w-full flex-col gap-3">
					<div className="relative">
						<input
							type="url"
							value={url}
							onChange={(e) => setUrl(e.target.value)}
							onKeyDown={handleKeyDown}
							placeholder="Enter your website URL"
							className="h-14 w-full rounded-lg border border-input bg-background px-4 pr-12 text-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
							disabled={loading}
						/>
						<div className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground">
							<svg
								className="h-5 w-5"
								fill="none"
								stroke="currentColor"
								viewBox="0 0 24 24"
							>
								<path
									strokeLinecap="round"
									strokeLinejoin="round"
									strokeWidth={2}
									d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
								/>
							</svg>
						</div>
					</div>

					{/* CAPTCHA - only shown if site key is configured */}
					{TURNSTILE_SITE_KEY && (
						<div className="flex justify-center">
							<Turnstile
								siteKey={TURNSTILE_SITE_KEY}
								onVerify={(token) => setCaptchaToken(token)}
								onExpire={() => setCaptchaToken(null)}
								onError={() => setError("Verification failed. Please try again.")}
								theme="auto"
								size="normal"
							/>
						</div>
					)}

					{error && <p className="text-center text-sm text-destructive">{error}</p>}

					<button
						onClick={handleAnalyze}
						disabled={
							!url || loading || (!!TURNSTILE_SITE_KEY && !captchaToken)
						}
						className="h-14 w-full rounded-lg bg-primary font-semibold text-primary-foreground transition-all hover:bg-primary/90 hover:shadow-lg disabled:pointer-events-none disabled:opacity-50"
					>
						{loading ? "Analyzing..." : "Check AI Visibility"}
					</button>
				</div>

				{/* Key Benefits */}
				<div className="mt-4 grid w-full gap-4 sm:grid-cols-3">
					<div className="rounded-lg border border-border bg-card p-4 text-center">
						<div className="text-2xl">🎯</div>
						<h3 className="mt-2 font-medium text-foreground">AI Visibility Score</h3>
						<p className="mt-1 text-xs text-muted-foreground">
							See if AI assistants can find & recommend you
						</p>
					</div>
					<div className="rounded-lg border border-border bg-card p-4 text-center">
						<div className="text-2xl">📄</div>
						<h3 className="mt-2 font-medium text-foreground">Get AI-Ready Files</h3>
						<p className="mt-1 text-xs text-muted-foreground">
							Download optimized robots.txt & llms.txt
						</p>
					</div>
					<div className="rounded-lg border border-border bg-card p-4 text-center">
						<div className="text-2xl">💡</div>
						<h3 className="mt-2 font-medium text-foreground">AI Recommendations</h3>
						<p className="mt-1 text-xs text-muted-foreground">
							Get actionable tips to boost visibility
						</p>
					</div>
				</div>

				{/* Why AI Search Matters */}
				<div className="mt-4 rounded-lg border border-primary/20 bg-primary/5 p-4 text-center">
					<p className="text-sm text-muted-foreground">
						<span className="font-semibold text-foreground">Why it matters:</span>{" "}
						AI tools are the new search. When someone asks ChatGPT for a
						recommendation, will your brand show up?
					</p>
				</div>

				{/* Footer */}
				<p className="flex items-center gap-1.5 text-xs text-muted-foreground">
					Powered by{" "}
					<a
						href="https://www.conusai.com"
						target="_blank"
						rel="noopener noreferrer"
						className="inline-block"
					>
						<Image
							src="/logos/conusai_logo_darkmode.png"
							alt="ConusAI"
							width={80}
							height={20}
							className="hidden dark:block"
						/>
						<Image
							src="/logos/conusai_logo_lightmode.png"
							alt="ConusAI"
							width={80}
							height={20}
							className="block dark:hidden"
						/>
					</a>
				</p>
			</main>
		</div>
	)
}
