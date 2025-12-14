"use client"

import Image from "next/image"
import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { ThemeToggle } from "@/components/theme-toggle"
import { LoadingOverlay } from "@/components/ui/spinner"
import { Turnstile } from "@/components/turnstile"
import {
	Target,
	FileText,
	Lightbulb,
	Rocket,
	CheckCircle2,
	Sparkles,
	Zap,
} from "lucide-react"

const TURNSTILE_SITE_KEY = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY || ""

// AI Platforms with their logos
const AI_PLATFORMS = [
	{ name: "ChatGPT", logo: "/logos/platforms/chatgpt.png" },
	{ name: "Claude", logo: "/logos/platforms/claude.png" },
	{ name: "Gemini", logo: "/logos/platforms/gemini.png" },
	{ name: "Perplexity", logo: "/logos/platforms/perplexity.ico" },
	{ name: "Copilot", logo: "/logos/platforms/microsoft-copilot.svg" },
	{ name: "Mistral", logo: "/logos/platforms/mistral.png" },
]

export default function Home() {
	const [url, setUrl] = useState("")
	const [loading, setLoading] = useState(false)
	const [error, setError] = useState<string | null>(null)
	const [captchaToken, setCaptchaToken] = useState<string | null>(null)
	const [mounted, setMounted] = useState(false)
	const router = useRouter()

	useEffect(() => {
		setMounted(true)
	}, [])

	const handleAnalyze = async () => {
		if (!url) return

		if (TURNSTILE_SITE_KEY && !captchaToken) {
			setError("Please complete the verification")
			return
		}

		setLoading(true)
		setError(null)

		let normalizedUrl = url.trim()
		if (
			!normalizedUrl.startsWith("http://") &&
			!normalizedUrl.startsWith("https://")
		) {
			normalizedUrl = `https://${normalizedUrl}`
		}

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
		<div className="relative min-h-screen overflow-hidden bg-gradient-to-b from-background via-background to-muted/20">
			{loading && <LoadingOverlay message="Checking AI visibility..." />}

			{/* Animated background elements */}
			<div className="pointer-events-none absolute inset-0 overflow-hidden">
				<div className="-top-40 -left-40 absolute h-80 w-80 animate-blob rounded-full bg-primary/5 blur-3xl" />
				<div className="animation-delay-2000 -bottom-40 -right-40 absolute h-80 w-80 animate-blob rounded-full bg-primary/5 blur-3xl" />
				<div className="animation-delay-4000 -translate-x-1/2 -translate-y-1/2 absolute top-1/2 left-1/2 h-60 w-60 animate-blob rounded-full bg-primary/3 blur-3xl" />
			</div>

			{/* Header */}
			<header className="relative z-10 flex items-center justify-between px-6 py-4">
				<div className="flex items-center gap-2">
					<Image
						src="/favicon.png"
						alt="Rank on AI Search"
						width={32}
						height={32}
						className="transition-transform hover:scale-110"
					/>
					<span className="hidden font-medium text-foreground sm:inline">
						Rank on AI Search
					</span>
				</div>
				<ThemeToggle />
			</header>

			{/* Main Content */}
			<main className="relative z-10 flex flex-col items-center px-4 pt-12 pb-20 sm:pt-20">
				{/* Hero Section */}
				<div
					className={`flex max-w-3xl flex-col items-center text-center transition-all duration-700 ${
						mounted ? "translate-y-0 opacity-100" : "translate-y-8 opacity-0"
					}`}
				>
					{/* Badge */}
					<div className="mb-6 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-4 py-1.5 text-primary text-sm">
						<span className="relative flex h-2 w-2">
							<span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-75" />
							<span className="relative inline-flex h-2 w-2 rounded-full bg-primary" />
						</span>
						AI Search is the new SEO
					</div>

					{/* Headline */}
					<h1 className="font-bold font-display text-4xl text-foreground tracking-tight sm:text-5xl md:text-6xl">
						Does AI recommend{" "}
						<span className="bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
							your brand?
						</span>
					</h1>

					{/* Subheadline */}
					<p className="mt-6 max-w-xl text-lg text-muted-foreground sm:text-xl">
						Check if ChatGPT, Claude, Perplexity and other AI assistants can
						find and recommend your business.
					</p>
				</div>

				{/* Platform Logos */}
				<div
					className={`mt-10 transition-all delay-200 duration-700 ${
						mounted ? "translate-y-0 opacity-100" : "translate-y-8 opacity-0"
					}`}
				>
					<p className="mb-4 text-center font-medium text-muted-foreground text-xs uppercase tracking-wider">
						Check your visibility across
					</p>
					<div className="flex flex-wrap items-center justify-center gap-3 sm:gap-4">
						{AI_PLATFORMS.map((platform, index) => (
							<div
								key={platform.name}
								className="group flex items-center gap-2 rounded-full border border-border/50 bg-card/50 px-3 py-2 backdrop-blur-sm transition-all hover:border-primary/30 hover:bg-card hover:shadow-md"
								style={{
									animationDelay: `${index * 100}ms`,
								}}
							>
								<Image
									src={platform.logo}
									alt={platform.name}
									width={20}
									height={20}
									className="h-5 w-5 transition-transform group-hover:scale-110"
								/>
								<span className="font-medium text-foreground text-sm">
									{platform.name}
								</span>
							</div>
						))}
					</div>
				</div>

				{/* Search Box */}
				<div
					className={`mt-12 w-full max-w-xl transition-all delay-300 duration-700 ${
						mounted ? "translate-y-0 opacity-100" : "translate-y-8 opacity-0"
					}`}
				>
					<div className="rounded-2xl border border-border/50 bg-card/80 p-6 shadow-xl backdrop-blur-sm">
						{/* Input */}
						<div className="relative">
							<div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-4">
								<svg
									aria-hidden="true"
									className="h-5 w-5 text-muted-foreground"
									fill="none"
									stroke="currentColor"
									viewBox="0 0 24 24"
								>
									<path
										strokeLinecap="round"
										strokeLinejoin="round"
										strokeWidth={2}
										d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"
									/>
								</svg>
							</div>
							<input
								type="url"
								value={url}
								onChange={(e) => setUrl(e.target.value)}
								onKeyDown={handleKeyDown}
								placeholder="yourwebsite.com"
								className="h-14 w-full rounded-xl border-0 bg-muted/50 pr-4 pl-12 text-foreground text-lg placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
								disabled={loading}
							/>
						</div>

						{/* CAPTCHA */}
						{TURNSTILE_SITE_KEY && (
							<div className="mt-4 flex justify-center">
								<Turnstile
									siteKey={TURNSTILE_SITE_KEY}
									onVerify={(token) => setCaptchaToken(token)}
									onExpire={() => setCaptchaToken(null)}
									onError={() =>
										setError("Verification failed. Please try again.")
									}
									theme="auto"
									size="normal"
								/>
							</div>
						)}

						{error && (
							<p className="mt-3 text-center text-destructive text-sm">
								{error}
							</p>
						)}

						{/* CTA Button */}
						<button
							type="button"
							onClick={handleAnalyze}
							disabled={
								!url || loading || (!!TURNSTILE_SITE_KEY && !captchaToken)
							}
							className="group relative mt-4 h-14 w-full overflow-hidden rounded-xl bg-primary font-semibold text-primary-foreground transition-all hover:shadow-lg hover:shadow-primary/25 disabled:pointer-events-none disabled:opacity-50"
						>
							<span className="relative z-10 flex items-center justify-center gap-2">
								{loading ? (
									"Analyzing..."
								) : (
									<>
										Check AI Visibility
										<svg
											aria-hidden="true"
											className="h-5 w-5 transition-transform group-hover:translate-x-1"
											fill="none"
											stroke="currentColor"
											viewBox="0 0 24 24"
										>
											<path
												strokeLinecap="round"
												strokeLinejoin="round"
												strokeWidth={2}
												d="M13 7l5 5m0 0l-5 5m5-5H6"
											/>
										</svg>
									</>
								)}
							</span>
							<div className="-translate-x-full absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent transition-transform group-hover:translate-x-full" />
						</button>
					</div>
				</div>

				{/* Features */}
				<div
					className={`mt-16 grid w-full max-w-4xl gap-6 px-4 transition-all delay-500 duration-700 sm:grid-cols-3 ${
						mounted ? "translate-y-0 opacity-100" : "translate-y-8 opacity-0"
					}`}
				>
					{/* AI Visibility Score */}
					<div className="group relative overflow-hidden rounded-2xl border border-border/50 bg-gradient-to-br from-card/80 to-card/40 p-6 backdrop-blur-sm transition-all duration-300 hover:border-primary/30 hover:shadow-primary/5 hover:shadow-xl">
						<div className="-right-4 -top-4 absolute h-24 w-24 rounded-full bg-primary/5 blur-2xl transition-all group-hover:bg-primary/10" />
						<div className="relative">
							<div className="mb-4 inline-flex rounded-xl bg-primary/10 p-3 text-primary transition-transform duration-300 group-hover:scale-110">
								<Target className="h-6 w-6" strokeWidth={1.5} />
							</div>
							<h3 className="font-semibold text-foreground text-lg">AI Visibility Score</h3>
							<p className="mt-2 text-muted-foreground text-sm leading-relaxed">
								See how discoverable you are to AI assistants
							</p>
						</div>
					</div>

					{/* Get AI-Ready Files */}
					<div className="group relative overflow-hidden rounded-2xl border border-border/50 bg-gradient-to-br from-card/80 to-card/40 p-6 backdrop-blur-sm transition-all duration-300 hover:border-primary/30 hover:shadow-primary/5 hover:shadow-xl">
						<div className="-right-4 -top-4 absolute h-24 w-24 rounded-full bg-blue-500/5 blur-2xl transition-all group-hover:bg-blue-500/10" />
						<div className="relative">
							<div className="mb-4 inline-flex rounded-xl bg-blue-500/10 p-3 text-blue-500 transition-transform duration-300 group-hover:scale-110">
								<FileText className="h-6 w-6" strokeWidth={1.5} />
							</div>
							<h3 className="font-semibold text-foreground text-lg">Get AI-Ready Files</h3>
							<p className="mt-2 text-muted-foreground text-sm leading-relaxed">
								Download optimized robots.txt & llms.txt
							</p>
						</div>
					</div>

					{/* Smart Recommendations */}
					<div className="group relative overflow-hidden rounded-2xl border border-border/50 bg-gradient-to-br from-card/80 to-card/40 p-6 backdrop-blur-sm transition-all duration-300 hover:border-primary/30 hover:shadow-primary/5 hover:shadow-xl">
						<div className="-right-4 -top-4 absolute h-24 w-24 rounded-full bg-amber-500/5 blur-2xl transition-all group-hover:bg-amber-500/10" />
						<div className="relative">
							<div className="mb-4 inline-flex rounded-xl bg-amber-500/10 p-3 text-amber-500 transition-transform duration-300 group-hover:scale-110">
								<Lightbulb className="h-6 w-6" strokeWidth={1.5} />
							</div>
							<h3 className="font-semibold text-foreground text-lg">Smart Recommendations</h3>
							<p className="mt-2 text-muted-foreground text-sm leading-relaxed">
								Actionable tips to improve your AI presence
							</p>
						</div>
					</div>
				</div>

				{/* Social Proof / Why it matters */}
				<div
					className={`mt-16 max-w-2xl text-center transition-all delay-700 duration-700 ${
						mounted ? "translate-y-0 opacity-100" : "translate-y-8 opacity-0"
					}`}
				>
					<div className="relative overflow-hidden rounded-2xl border border-primary/10 bg-gradient-to-br from-primary/5 via-transparent to-primary/5 p-8">
						{/* Decorative elements */}
						<div className="-left-10 -top-10 absolute h-32 w-32 rounded-full bg-primary/10 blur-3xl" />
						<div className="-bottom-10 -right-10 absolute h-32 w-32 rounded-full bg-primary/10 blur-3xl" />
						
						<div className="relative">
							<div className="mb-5 inline-flex rounded-2xl bg-gradient-to-br from-primary/20 to-primary/10 p-4">
								<Rocket className="h-8 w-8 text-primary" strokeWidth={1.5} />
							</div>
							<h2 className="font-bold text-2xl text-foreground">
								AI is the new search engine
							</h2>
							<p className="mx-auto mt-4 max-w-lg text-muted-foreground leading-relaxed">
								More people are asking ChatGPT, Claude, and Perplexity for
								recommendations instead of searching on Google. When someone asks
								&quot;What&apos;s the best [your category]?&quot; — will your brand show up?
							</p>
							<div className="mt-8 flex flex-wrap items-center justify-center gap-6 text-sm">
								<div className="flex items-center gap-2 rounded-full bg-green-500/10 px-4 py-2 text-green-600 dark:text-green-400">
									<CheckCircle2 className="h-4 w-4" strokeWidth={2} />
									<span className="font-medium">Free analysis</span>
								</div>
							<div className="flex items-center gap-2 rounded-full bg-blue-500/10 px-4 py-2 text-blue-600 dark:text-blue-400">
									<Sparkles className="h-4 w-4" strokeWidth={2} />
									<span className="font-medium">No signup required</span>
								</div>
								<div className="flex items-center gap-2 rounded-full bg-amber-500/10 px-4 py-2 text-amber-600 dark:text-amber-400">
									<Zap className="h-4 w-4" strokeWidth={2} />
									<span className="font-medium">Instant results</span>
								</div>
							</div>
						</div>
					</div>
				</div>
			</main>

			{/* Footer */}
			<footer className="relative z-10 py-8 text-center">
				<p className="flex items-center justify-center gap-1.5 text-muted-foreground text-xs">
					Powered by{" "}
					<a
						href="https://www.conusai.com"
						target="_blank"
						rel="noopener noreferrer"
						className="inline-block transition-opacity hover:opacity-80"
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
			</footer>

			{/* Custom animations */}
			<style jsx>{`
				@keyframes blob {
					0% {
						transform: translate(0px, 0px) scale(1);
					}
					33% {
						transform: translate(30px, -50px) scale(1.1);
					}
					66% {
						transform: translate(-20px, 20px) scale(0.9);
					}
					100% {
						transform: translate(0px, 0px) scale(1);
					}
				}
				.animate-blob {
					animation: blob 7s infinite;
				}
				.animation-delay-2000 {
					animation-delay: 2s;
				}
				.animation-delay-4000 {
					animation-delay: 4s;
				}
			`}</style>
		</div>
	)
}
