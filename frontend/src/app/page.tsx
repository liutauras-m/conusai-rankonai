"use client"

import Image from "next/image"
import { useState } from "react"
import { useRouter } from "next/navigation"
import { ThemeToggle } from "@/components/theme-toggle"
import { LoadingOverlay } from "@/components/ui/spinner"
import { Turnstile } from "@/components/turnstile"

const TURNSTILE_SITE_KEY = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY || ""

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
			setError("Please complete the CAPTCHA verification")
			return
		}
		
		setLoading(true)
		setError(null)

		// Normalize URL
		let normalizedUrl = url.trim()
		if (!normalizedUrl.startsWith("http://") && !normalizedUrl.startsWith("https://")) {
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
			{loading && <LoadingOverlay message="Starting analysis..." />}
			
			<div className="absolute top-4 right-4">
				<ThemeToggle />
			</div>

			<main className="flex w-full max-w-md flex-col items-center gap-8">
				<Image
					src="/favicon.png"
					alt="ConusAI"
					width={48}
					height={48}
					priority
				/>

				<div className="text-center">
					<h1 className="font-display text-3xl font-semibold tracking-tight text-foreground">
						SEO Analyser
					</h1>
					<p className="mt-2 text-sm text-muted-foreground">
						Enter a URL to analyse its SEO performance
					</p>
				</div>

				<div className="flex w-full flex-col gap-3">
					<input
						type="url"
						value={url}
						onChange={(e) => setUrl(e.target.value)}
						onKeyDown={handleKeyDown}
						placeholder="https://example.com"
						className="h-12 w-full rounded-md border border-input bg-background px-4 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-[#80CDC6]"
						disabled={loading}
					/>
					
					{/* CAPTCHA - only shown if site key is configured */}
					{TURNSTILE_SITE_KEY && (
						<div className="flex justify-center">
							<Turnstile
								siteKey={TURNSTILE_SITE_KEY}
								onVerify={(token) => setCaptchaToken(token)}
								onExpire={() => setCaptchaToken(null)}
								onError={() => setError("CAPTCHA failed. Please try again.")}
								theme="auto"
								size="normal"
							/>
						</div>
					)}
					
					{error && (
						<p className="text-sm text-destructive">{error}</p>
					)}
					<button
						onClick={handleAnalyze}
						disabled={!url || loading || (!!TURNSTILE_SITE_KEY && !captchaToken)}
						className="h-12 w-full rounded-md bg-[#80CDC6] font-medium text-white transition-colors hover:bg-[#80CDC6]/90 disabled:pointer-events-none disabled:opacity-50"
					>
						{loading ? "Starting..." : "Analyse"}
					</button>
				</div>

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
