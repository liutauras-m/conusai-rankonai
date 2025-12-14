"use client"

import { useSearchParams, useRouter } from "next/navigation"
import { Suspense, useEffect, useState } from "react"
import Image from "next/image"
import { ThemeToggle } from "@/components/theme-toggle"
import { ScoresOverview } from "@/components/score-gauge"
import { LoadingOverlay } from "@/components/ui/spinner"
import { FileGenerator } from "@/components/file-generator"
import { AIBotStatus } from "@/components/ai-bot-status"
import { AIRecommendations } from "@/components/ai-recommendations"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card"

// Types for SEO Report
interface SEOReport {
	url: string
	timestamp: string
	crawl_time_ms: number
	scores: {
		overall: number
		technical: number
		on_page: number
		content: number
		structured_data: number
		ai_readiness: number
	}
	metadata: {
		title: { value: string | null; length: number; issues: string[] }
		description: { value: string | null; length: number; issues: string[] }
		canonical: string | null
		robots_meta: string | null
		viewport: string | null
		language: string | null
	}
	headings: {
		h1: { count: number; values: string[]; issues: string[] }
		h2: { count: number; values: string[] }
		h3: { count: number; values: string[] }
		h4: { count: number; values: string[] }
		h5: { count: number; values: string[] }
		h6: { count: number; values: string[] }
		hierarchy_valid: boolean
	}
	images: {
		total: number
		missing_alt: number
		missing_alt_urls: string[]
		lazy_loading_count: number
	}
	links: {
		internal_count: number
		external_count: number
		nofollow_count: number
		broken_count: number
	}
	content: {
		word_count: number
		readability: {
			flesch_reading_ease: number
			flesch_kincaid_grade: number
			gunning_fog: number
			smog_index: number
			automated_readability_index: number
			reading_time_minutes: number
		}
		keywords_tfidf: Array<{
			keyword: string
			tfidf_score: number
			count: number
		}>
		keywords_frequency: Array<{
			keyword: string
			count: number
			density_percent: number
		}>
		top_bigrams: Array<{ phrase: string; count: number }>
		top_trigrams: Array<{ phrase: string; count: number }>
	}
	structured_data: {
		json_ld: Array<{ type: string }>
		microdata: boolean
		rdfa: boolean
		open_graph: Record<string, string>
		twitter_card: Record<string, string>
	}
	technical: {
		https: boolean
		response_time_ms: number
		content_type: string
		server: string
		content_security_policy: boolean
	}
	ai_indexing: {
		robots_txt: {
			present: boolean
			ai_bots_status: Record<string, string>
			sitemaps_declared: string[]
		}
		llms_txt: {
			present: boolean
			content_preview: string | null
		}
		sitemap_xml: {
			present: boolean
		}
	}
	issues: Array<{
		severity: string
		category: string
		code: string
		message: string
		element?: string
	}>
	recommendations: Array<{
		priority: number
		category: string
		action: string
	}>
}

// Helper to ensure all arrays have safe defaults
function normalizeReport(data: Partial<SEOReport>): SEOReport {
	return {
		url: data.url || "",
		timestamp: data.timestamp || new Date().toISOString(),
		crawl_time_ms: data.crawl_time_ms || 0,
		scores: {
			overall: data.scores?.overall ?? 0,
			technical: data.scores?.technical ?? 0,
			on_page: data.scores?.on_page ?? 0,
			content: data.scores?.content ?? 0,
			structured_data: data.scores?.structured_data ?? 0,
			ai_readiness: data.scores?.ai_readiness ?? 0,
		},
		metadata: {
			title: data.metadata?.title || { value: null, length: 0, issues: [] },
			description: data.metadata?.description || { value: null, length: 0, issues: [] },
			canonical: data.metadata?.canonical || null,
			robots_meta: data.metadata?.robots_meta || null,
			viewport: data.metadata?.viewport || null,
			language: data.metadata?.language || null,
		},
		headings: {
			h1: data.headings?.h1 || { count: 0, values: [], issues: [] },
			h2: data.headings?.h2 || { count: 0, values: [] },
			h3: data.headings?.h3 || { count: 0, values: [] },
			h4: data.headings?.h4 || { count: 0, values: [] },
			h5: data.headings?.h5 || { count: 0, values: [] },
			h6: data.headings?.h6 || { count: 0, values: [] },
			hierarchy_valid: data.headings?.hierarchy_valid ?? true,
		},
		images: {
			total: data.images?.total ?? 0,
			missing_alt: data.images?.missing_alt ?? 0,
			missing_alt_urls: data.images?.missing_alt_urls || [],
			lazy_loading_count: data.images?.lazy_loading_count ?? 0,
		},
		links: {
			internal_count: data.links?.internal_count ?? 0,
			external_count: data.links?.external_count ?? 0,
			nofollow_count: data.links?.nofollow_count ?? 0,
			broken_count: data.links?.broken_count ?? 0,
		},
		content: {
			word_count: data.content?.word_count ?? 0,
			readability: data.content?.readability || {
				flesch_reading_ease: 0,
				flesch_kincaid_grade: 0,
				gunning_fog: 0,
				smog_index: 0,
				automated_readability_index: 0,
				reading_time_minutes: 0,
			},
			keywords_tfidf: data.content?.keywords_tfidf || [],
			keywords_frequency: data.content?.keywords_frequency || [],
			top_bigrams: data.content?.top_bigrams || [],
			top_trigrams: data.content?.top_trigrams || [],
		},
		structured_data: {
			json_ld: data.structured_data?.json_ld || [],
			microdata: data.structured_data?.microdata ?? false,
			rdfa: data.structured_data?.rdfa ?? false,
			open_graph: data.structured_data?.open_graph || {},
			twitter_card: data.structured_data?.twitter_card || {},
		},
		technical: {
			https: data.technical?.https ?? false,
			response_time_ms: data.technical?.response_time_ms ?? 0,
			content_type: data.technical?.content_type || "",
			server: data.technical?.server || "",
			content_security_policy: data.technical?.content_security_policy ?? false,
		},
		ai_indexing: {
			robots_txt: data.ai_indexing?.robots_txt || {
				present: false,
				ai_bots_status: {},
				sitemaps_declared: [],
			},
			llms_txt: data.ai_indexing?.llms_txt || {
				present: false,
				content_preview: null,
			},
			sitemap_xml: data.ai_indexing?.sitemap_xml || { present: false },
		},
		issues: data.issues || [],
		recommendations: data.recommendations || [],
	}
}

// Get readability description
function getReadabilityDescription(score: number): string {
	if (score >= 80) return "Very easy to read"
	if (score >= 60) return "Easy to read"
	if (score >= 40) return "Moderate difficulty"
	if (score >= 20) return "Difficult to read"
	return "Very difficult to read"
}

function ReportContent() {
	const searchParams = useSearchParams()
	const router = useRouter()
	const [report, setReport] = useState<SEOReport | null>(null)
	const [loading, setLoading] = useState(true)
	const [error, setError] = useState<string | null>(null)

	const url = searchParams.get("url")
	const captchaToken = searchParams.get("token")

	useEffect(() => {
		if (!url) {
			router.push("/")
			return
		}

		const fetchReport = async () => {
			try {
				setLoading(true)
				setError(null)

				const response = await fetch("/api/analyze", {
					method: "POST",
					headers: { "Content-Type": "application/json" },
					body: JSON.stringify({ url, captchaToken }),
				})

				if (!response.ok) {
					const data = await response.json()
					throw new Error(data.error || "Analysis failed")
				}

				const responseData = await response.json()
				const reportData = responseData.data || responseData
				setReport(normalizeReport(reportData))
			} catch (err) {
				setError(err instanceof Error ? err.message : "Something went wrong")
			} finally {
				setLoading(false)
			}
		}

		fetchReport()
	}, [url, captchaToken, router])

	if (loading) {
		return <LoadingOverlay message={`Checking AI visibility for ${url}...`} />
	}

	if (error) {
		return (
			<div className="flex min-h-screen flex-col items-center justify-center gap-4 px-4">
				<div className="text-center">
					<h1 className="text-2xl font-semibold text-destructive">
						Analysis Failed
					</h1>
					<p className="mt-2 text-muted-foreground">{error}</p>
				</div>
				<button
					onClick={() => router.push("/")}
					className="mt-4 rounded-md bg-primary px-6 py-2 font-medium text-primary-foreground hover:bg-primary/90"
				>
					Try Again
				</button>
			</div>
		)
	}

	if (!report) return null

	// Extract domain for display
	const domain = new URL(report.url).hostname

	return (
		<div className="min-h-screen bg-background">
			{/* Header */}
			<header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
				<div className="container mx-auto flex h-14 items-center justify-between px-4">
					<button
						onClick={() => router.push("/")}
						className="flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-foreground"
					>
						<svg
							className="h-4 w-4"
							fill="none"
							stroke="currentColor"
							viewBox="0 0 24 24"
						>
							<path
								strokeLinecap="round"
								strokeLinejoin="round"
								strokeWidth={2}
								d="M15 19l-7-7 7-7"
							/>
						</svg>
						New Analysis
					</button>
					<div className="flex items-center gap-4">
						<span className="text-sm text-muted-foreground">
							{new Date(report.timestamp).toLocaleString()}
						</span>
						<ThemeToggle />
					</div>
				</div>
			</header>

			<main className="container mx-auto px-4 py-8">
				{/* Hero Section */}
				<div className="mb-8 text-center">
					<h1 className="font-display text-2xl font-semibold text-foreground sm:text-3xl">
						AI Visibility Report
					</h1>
					<a
						href={report.url}
						target="_blank"
						rel="noopener noreferrer"
						className="mt-2 inline-flex items-center gap-1 text-sm text-primary hover:underline"
					>
						{domain}
						<svg
							className="h-3 w-3"
							fill="none"
							stroke="currentColor"
							viewBox="0 0 24 24"
						>
							<path
								strokeLinecap="round"
								strokeLinejoin="round"
								strokeWidth={2}
								d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
							/>
						</svg>
					</a>
				</div>

				{/* AI Visibility Score - Hero */}
				<Card className="mb-8">
					<CardHeader className="text-center">
						<CardTitle>Your AI Visibility Score</CardTitle>
						<CardDescription>
							How well can AI assistants discover and recommend your brand?
						</CardDescription>
					</CardHeader>
					<CardContent>
						<ScoresOverview scores={report.scores} />
					</CardContent>
				</Card>

				{/* Tabbed Content - Reordered for business users */}
				<Tabs defaultValue="visibility" className="w-full">
					<TabsList className="mb-4 flex-wrap justify-start">
						<TabsTrigger value="visibility" className="gap-1">
							<span className="hidden sm:inline">🤖</span> AI Crawlers
						</TabsTrigger>
						<TabsTrigger value="files" className="gap-1">
							<span className="hidden sm:inline">📄</span> Get Files
						</TabsTrigger>
						<TabsTrigger value="recommendations" className="gap-1">
							<span className="hidden sm:inline">💡</span> Actions
						</TabsTrigger>
						<TabsTrigger value="content" className="gap-1">
							<span className="hidden sm:inline">📝</span> Content
						</TabsTrigger>
						<TabsTrigger value="details" className="gap-1">
							<span className="hidden sm:inline">⚙️</span> Details
						</TabsTrigger>
					</TabsList>

					{/* AI Visibility Tab */}
					<TabsContent value="visibility">
						<AIBotStatus botStatus={report.ai_indexing.robots_txt.ai_bots_status} />
					</TabsContent>

					{/* Get Files Tab */}
					<TabsContent value="files">
						<FileGenerator
							url={report.url}
							aiIndexing={report.ai_indexing}
							metadata={report.metadata}
							content={report.content}
						/>
					</TabsContent>

					{/* Recommendations Tab */}
					<TabsContent value="recommendations">
						<AIRecommendations
							issues={report.issues}
							recommendations={report.recommendations}
							scores={report.scores}
							aiIndexing={report.ai_indexing}
						/>
					</TabsContent>

					{/* Content Tab */}
					<TabsContent value="content">
						<div className="space-y-6">
							{/* Content Overview */}
							<Card>
								<CardHeader>
									<CardTitle className="flex items-center gap-2">
										<span>📝</span> Content Quality
									</CardTitle>
									<CardDescription>
										How well AI can understand your content
									</CardDescription>
								</CardHeader>
								<CardContent>
									<div className="grid gap-6 md:grid-cols-2">
										{/* Quick Stats */}
										<div className="space-y-4">
											<div className="rounded-lg bg-muted/50 p-4">
												<div className="text-3xl font-bold text-foreground">
													{report.content.word_count.toLocaleString()}
												</div>
												<div className="text-sm text-muted-foreground">
													words on page
												</div>
											</div>
											<div className="rounded-lg bg-muted/50 p-4">
												<div className="text-3xl font-bold text-foreground">
													{report.content.readability.reading_time_minutes} min
												</div>
												<div className="text-sm text-muted-foreground">
													reading time
												</div>
											</div>
											<div className="rounded-lg bg-muted/50 p-4">
												<div className="text-2xl font-bold text-foreground">
													{getReadabilityDescription(
														report.content.readability.flesch_reading_ease
													)}
												</div>
												<div className="text-sm text-muted-foreground">
													readability level (Flesch:{" "}
													{report.content.readability.flesch_reading_ease})
												</div>
											</div>
										</div>

										{/* Top Keywords */}
										<div>
											<h4 className="mb-3 font-medium text-foreground">
												Top Keywords AI Will Associate With You
											</h4>
											{report.content.keywords_frequency.length > 0 ? (
												<div className="flex flex-wrap gap-2">
													{report.content.keywords_frequency
														.slice(0, 15)
														.map((kw, idx) => (
															<span
																key={idx}
																className="rounded-full bg-primary/10 px-3 py-1 text-sm text-primary"
															>
																{kw.keyword}
															</span>
														))}
												</div>
											) : (
												<p className="text-sm text-muted-foreground">
													No significant keywords found
												</p>
											)}

											{report.content.top_bigrams.length > 0 && (
												<>
													<h4 className="mb-3 mt-6 font-medium text-foreground">
														Key Phrases
													</h4>
													<div className="flex flex-wrap gap-2">
														{report.content.top_bigrams.slice(0, 8).map((p, idx) => (
															<span
																key={idx}
																className="rounded-full bg-muted px-3 py-1 text-sm text-muted-foreground"
															>
																{p.phrase}
															</span>
														))}
													</div>
												</>
											)}
										</div>
									</div>
								</CardContent>
							</Card>

							{/* Page Structure */}
							<Card>
								<CardHeader>
									<CardTitle className="flex items-center gap-2">
										<span>🏗️</span> Page Structure
									</CardTitle>
									<CardDescription>
										How your content is organized for AI understanding
									</CardDescription>
								</CardHeader>
								<CardContent>
									<div className="grid gap-4 md:grid-cols-2">
										{/* Meta Info */}
										<div className="space-y-3">
											<div className="rounded-lg border p-3">
												<p className="text-xs font-medium uppercase text-muted-foreground">
													Page Title
												</p>
												<p className="mt-1 font-medium text-foreground">
													{report.metadata.title.value || "⚠️ Missing"}
												</p>
												{report.metadata.title.length > 0 && (
													<p className="mt-1 text-xs text-muted-foreground">
														{report.metadata.title.length} characters
														{report.metadata.title.length > 60
															? " (may be truncated)"
															: ""}
													</p>
												)}
											</div>
											<div className="rounded-lg border p-3">
												<p className="text-xs font-medium uppercase text-muted-foreground">
													Meta Description
												</p>
												<p className="mt-1 text-sm text-foreground">
													{report.metadata.description.value ||
														"⚠️ Missing - AI won't have a summary"}
												</p>
												{report.metadata.description.length > 0 && (
													<p className="mt-1 text-xs text-muted-foreground">
														{report.metadata.description.length} characters
													</p>
												)}
											</div>
										</div>

										{/* Headings */}
										<div className="space-y-3">
											<h4 className="font-medium text-foreground">Headings</h4>
											<div className="space-y-2">
												<div className="flex items-center justify-between rounded border p-2">
													<span className="text-sm">H1 (Main Topic)</span>
													<span
														className={`font-medium ${
															report.headings.h1.count === 1
																? "text-green-600 dark:text-green-400"
																: report.headings.h1.count === 0
																	? "text-red-600 dark:text-red-400"
																	: "text-amber-600 dark:text-amber-400"
														}`}
													>
														{report.headings.h1.count === 1
															? "✓"
															: report.headings.h1.count === 0
																? "Missing"
																: `${report.headings.h1.count} found`}
													</span>
												</div>
												<div className="flex items-center justify-between rounded border p-2">
													<span className="text-sm">H2 (Sections)</span>
													<span className="font-medium text-foreground">
														{report.headings.h2.count}
													</span>
												</div>
												<div className="flex items-center justify-between rounded border p-2">
													<span className="text-sm">H3-H6 (Subsections)</span>
													<span className="font-medium text-foreground">
														{report.headings.h3.count +
															report.headings.h4.count +
															report.headings.h5.count +
															report.headings.h6.count}
													</span>
												</div>
											</div>
											{report.headings.h1.values.length > 0 && (
												<div className="rounded-lg bg-muted/50 p-3">
													<p className="text-xs text-muted-foreground">
														Main heading:
													</p>
													<p className="mt-1 font-medium text-foreground">
														{report.headings.h1.values[0]}
													</p>
												</div>
											)}
										</div>
									</div>
								</CardContent>
							</Card>
						</div>
					</TabsContent>

					{/* Technical Details Tab */}
					<TabsContent value="details">
						<div className="space-y-6">
							{/* Technical Health */}
							<Card>
								<CardHeader>
									<CardTitle className="flex items-center gap-2">
										<span>⚙️</span> Technical Health
									</CardTitle>
									<CardDescription>
										Infrastructure that affects AI crawling
									</CardDescription>
								</CardHeader>
								<CardContent>
									<div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
										<div className="flex items-center justify-between rounded-lg border p-3">
											<span className="text-sm text-foreground">HTTPS Secure</span>
											<span
												className={
													report.technical.https
														? "text-green-600 dark:text-green-400"
														: "text-red-600 dark:text-red-400"
												}
											>
												{report.technical.https ? "✓ Yes" : "✗ No"}
											</span>
										</div>
										<div className="flex items-center justify-between rounded-lg border p-3">
											<span className="text-sm text-foreground">Response Time</span>
											<span
												className={`font-medium ${
													report.technical.response_time_ms < 500
														? "text-green-600 dark:text-green-400"
														: report.technical.response_time_ms < 1000
															? "text-amber-600 dark:text-amber-400"
															: "text-red-600 dark:text-red-400"
												}`}
											>
												{report.technical.response_time_ms}ms
											</span>
										</div>
										<div className="flex items-center justify-between rounded-lg border p-3">
											<span className="text-sm text-foreground">robots.txt</span>
											<span
												className={
													report.ai_indexing.robots_txt.present
														? "text-green-600 dark:text-green-400"
														: "text-amber-600 dark:text-amber-400"
												}
											>
												{report.ai_indexing.robots_txt.present ? "✓ Found" : "Not found"}
											</span>
										</div>
										<div className="flex items-center justify-between rounded-lg border p-3">
											<span className="text-sm text-foreground">llms.txt</span>
											<span
												className={
													report.ai_indexing.llms_txt.present
														? "text-green-600 dark:text-green-400"
														: "text-amber-600 dark:text-amber-400"
												}
											>
												{report.ai_indexing.llms_txt.present ? "✓ Found" : "Not found"}
											</span>
										</div>
										<div className="flex items-center justify-between rounded-lg border p-3">
											<span className="text-sm text-foreground">Sitemap</span>
											<span
												className={
													report.ai_indexing.sitemap_xml.present
														? "text-green-600 dark:text-green-400"
														: "text-amber-600 dark:text-amber-400"
												}
											>
												{report.ai_indexing.sitemap_xml.present
													? "✓ Found"
													: "Not found"}
											</span>
										</div>
										<div className="flex items-center justify-between rounded-lg border p-3">
											<span className="text-sm text-foreground">Language</span>
											<span className="font-medium text-foreground">
												{report.metadata.language || "Not set"}
											</span>
										</div>
									</div>
								</CardContent>
							</Card>

							{/* Structured Data */}
							<Card>
								<CardHeader>
									<CardTitle className="flex items-center gap-2">
										<span>🏷️</span> Rich Data (Schema Markup)
									</CardTitle>
									<CardDescription>
										Structured information AI can extract about your business
									</CardDescription>
								</CardHeader>
								<CardContent>
									<div className="grid gap-4 md:grid-cols-2">
										{/* JSON-LD */}
										<div>
											<h4 className="mb-2 font-medium text-foreground">
												JSON-LD Schema
											</h4>
											{report.structured_data.json_ld.length > 0 ? (
												<div className="space-y-2">
													{report.structured_data.json_ld.map((schema, idx) => (
														<div
															key={idx}
															className="flex items-center gap-2 rounded border p-2"
														>
															<span className="text-green-600 dark:text-green-400">
																✓
															</span>
															<span className="text-sm">{schema.type}</span>
														</div>
													))}
												</div>
											) : (
												<p className="rounded-lg bg-amber-500/10 p-3 text-sm text-amber-600 dark:text-amber-400">
													⚠️ No JSON-LD schema found. Adding schema helps AI
													understand your business type.
												</p>
											)}
										</div>

										{/* Open Graph */}
										<div>
											<h4 className="mb-2 font-medium text-foreground">
												Social/Open Graph
											</h4>
											{Object.keys(report.structured_data.open_graph).length > 0 ? (
												<div className="space-y-2">
													{Object.entries(report.structured_data.open_graph)
														.slice(0, 6)
														.map(([key, value]) => (
															<div key={key} className="rounded border p-2">
																<p className="text-xs text-muted-foreground">
																	{key}
																</p>
																<p className="truncate text-sm text-foreground">
																	{value}
																</p>
															</div>
														))}
												</div>
											) : (
												<p className="rounded-lg bg-amber-500/10 p-3 text-sm text-amber-600 dark:text-amber-400">
													⚠️ No Open Graph tags. These help when your content is
													shared.
												</p>
											)}
										</div>
									</div>
								</CardContent>
							</Card>

							{/* Links & Images */}
							<Card>
								<CardHeader>
									<CardTitle className="flex items-center gap-2">
										<span>🔗</span> Links & Images
									</CardTitle>
								</CardHeader>
								<CardContent>
									<div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
										<div className="rounded-lg bg-muted/50 p-4 text-center">
											<div className="text-2xl font-bold text-foreground">
												{report.links.internal_count}
											</div>
											<div className="text-sm text-muted-foreground">
												Internal Links
											</div>
										</div>
										<div className="rounded-lg bg-muted/50 p-4 text-center">
											<div className="text-2xl font-bold text-foreground">
												{report.links.external_count}
											</div>
											<div className="text-sm text-muted-foreground">
												External Links
											</div>
										</div>
										<div className="rounded-lg bg-muted/50 p-4 text-center">
											<div className="text-2xl font-bold text-foreground">
												{report.images.total}
											</div>
											<div className="text-sm text-muted-foreground">Images</div>
										</div>
										<div className="rounded-lg bg-muted/50 p-4 text-center">
											<div
												className={`text-2xl font-bold ${
													report.images.missing_alt > 0
														? "text-amber-600 dark:text-amber-400"
														: "text-green-600 dark:text-green-400"
												}`}
											>
												{report.images.missing_alt}
											</div>
											<div className="text-sm text-muted-foreground">
												Missing Alt Text
											</div>
										</div>
									</div>
								</CardContent>
							</Card>
						</div>
					</TabsContent>
				</Tabs>
			</main>

			{/* Footer */}
			<footer className="border-t bg-muted/30 py-6">
				<div className="container mx-auto px-4 text-center">
					<p className="flex items-center justify-center gap-1.5 text-xs text-muted-foreground">
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
				</div>
			</footer>
		</div>
	)
}

export default function ReportPage() {
	return (
		<Suspense fallback={<LoadingOverlay />}>
			<ReportContent />
		</Suspense>
	)
}
