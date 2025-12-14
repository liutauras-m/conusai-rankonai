"use client"

import { useSearchParams, useRouter } from "next/navigation"
import { Suspense, useEffect, useState } from "react"
import Image from "next/image"
import { ThemeToggle } from "@/components/theme-toggle"
import { ScoresOverview } from "@/components/score-gauge"
import { LoadingOverlay } from "@/components/ui/spinner"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card"
import {
	Table,
	TableBody,
	TableCell,
	TableHead,
	TableHeader,
	TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"

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
				// Handle both direct data and nested data.data structure (from nginx routing)
				const reportData = responseData.data || responseData
				setReport(normalizeReport(reportData))
			} catch (err) {
				setError(err instanceof Error ? err.message : "Something went wrong")
			} finally {
				setLoading(false)
			}
		}

		fetchReport()
	}, [url, router])

	if (loading) {
		return <LoadingOverlay message={`Analysing ${url}...`} />
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
					className="mt-4 rounded-md bg-[#80CDC6] px-6 py-2 font-medium text-white hover:bg-[#80CDC6]/90"
				>
					Try Again
				</button>
			</div>
		)
	}

	if (!report) return null

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
				{/* URL & Summary */}
				<div className="mb-8">
					<h1 className="text-xl font-semibold text-foreground sm:text-2xl">
						SEO Report
					</h1>
					<a
						href={report.url}
						target="_blank"
						rel="noopener noreferrer"
						className="mt-1 inline-flex items-center gap-1 text-sm text-[#80CDC6] hover:underline"
					>
						{report.url}
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

				{/* Scores Overview */}
				<Card className="mb-8">
					<CardHeader>
						<CardTitle>Scores Overview</CardTitle>
						<CardDescription>
							Analysis completed in {report.crawl_time_ms}ms
						</CardDescription>
					</CardHeader>
					<CardContent>
						<ScoresOverview scores={report.scores} />
					</CardContent>
				</Card>

				{/* Tabbed Content */}
				<Tabs defaultValue="issues" className="w-full">
					<TabsList className="mb-4 flex-wrap">
						<TabsTrigger value="issues">
							Issues ({report.issues.length})
						</TabsTrigger>
						<TabsTrigger value="metadata">Metadata</TabsTrigger>
						<TabsTrigger value="content">Content</TabsTrigger>
						<TabsTrigger value="technical">Technical</TabsTrigger>
						<TabsTrigger value="ai">AI Indexing</TabsTrigger>
						<TabsTrigger value="structured">Structured Data</TabsTrigger>
					</TabsList>

					{/* Issues Tab */}
					<TabsContent value="issues">
						<Card>
							<CardHeader>
								<CardTitle>Issues & Recommendations</CardTitle>
								<CardDescription>
									{report.issues.filter((i) => i.severity === "high").length}{" "}
									high,{" "}
									{report.issues.filter((i) => i.severity === "medium").length}{" "}
									medium,{" "}
									{report.issues.filter((i) => i.severity === "low").length} low
									priority issues
								</CardDescription>
							</CardHeader>
							<CardContent>
								{report.issues.length === 0 ? (
									<p className="text-center text-muted-foreground">
										No issues found! 🎉
									</p>
								) : (
									<div className="space-y-3">
										{report.issues.map((issue, idx) => (
											<div
												key={idx}
												className="flex items-start gap-3 rounded-lg border p-3"
											>
												<Badge
													variant={
														issue.severity === "high"
															? "destructive"
															: issue.severity === "medium"
																? "default"
																: "secondary"
													}
													className="mt-0.5 shrink-0"
												>
													{issue.severity}
												</Badge>
												<div className="min-w-0 flex-1">
													<p className="font-medium">{issue.message}</p>
													<p className="mt-1 text-sm text-muted-foreground">
														{issue.category} • {issue.code}
													</p>
													{issue.element && (
														<code className="mt-2 block truncate rounded bg-muted px-2 py-1 text-xs">
															{issue.element}
														</code>
													)}
												</div>
											</div>
										))}
									</div>
								)}

								{report.recommendations.length > 0 && (
									<div className="mt-6">
										<h4 className="mb-3 font-semibold">Recommendations</h4>
										<div className="space-y-2">
											{report.recommendations.map((rec, idx) => (
												<div key={idx} className="flex items-start gap-3">
													<Badge variant="outline" className="shrink-0">
														P{rec.priority}
													</Badge>
													<p className="text-sm">{rec.action}</p>
												</div>
											))}
										</div>
									</div>
								)}
							</CardContent>
						</Card>
					</TabsContent>

					{/* Metadata Tab */}
					<TabsContent value="metadata">
						<div className="grid gap-4 md:grid-cols-2">
							<Card>
								<CardHeader>
									<CardTitle>Title Tag</CardTitle>
								</CardHeader>
								<CardContent>
									<p className="text-sm">
										{report.metadata.title.value || (
											<span className="text-destructive">Missing</span>
										)}
									</p>
									<p className="mt-2 text-xs text-muted-foreground">
										Length: {report.metadata.title.length} characters
										(recommended: 50-60)
									</p>
								</CardContent>
							</Card>

							<Card>
								<CardHeader>
									<CardTitle>Meta Description</CardTitle>
								</CardHeader>
								<CardContent>
									<p className="text-sm">
										{report.metadata.description.value || (
											<span className="text-destructive">Missing</span>
										)}
									</p>
									<p className="mt-2 text-xs text-muted-foreground">
										Length: {report.metadata.description.length} characters
										(recommended: 150-160)
									</p>
								</CardContent>
							</Card>

							<Card>
								<CardHeader>
									<CardTitle>Headings</CardTitle>
								</CardHeader>
								<CardContent>
									<Table>
										<TableHeader>
											<TableRow>
												<TableHead>Tag</TableHead>
												<TableHead>Count</TableHead>
												<TableHead>Status</TableHead>
											</TableRow>
										</TableHeader>
										<TableBody>
											{(
												["h1", "h2", "h3", "h4", "h5", "h6"] as const
											).map((tag) => (
												<TableRow key={tag}>
													<TableCell className="font-mono">{tag}</TableCell>
													<TableCell>
														{report.headings[tag].count}
													</TableCell>
													<TableCell>
														{tag === "h1" &&
														report.headings.h1.count !== 1 ? (
															<Badge variant="destructive">
																{report.headings.h1.count === 0
																	? "Missing"
																	: "Multiple"}
															</Badge>
														) : (
															<Badge variant="secondary">OK</Badge>
														)}
													</TableCell>
												</TableRow>
											))}
										</TableBody>
									</Table>
									{report.headings.h1.values.length > 0 && (
										<div className="mt-3">
											<p className="text-xs text-muted-foreground">
												H1: {report.headings.h1.values[0]}
											</p>
										</div>
									)}
								</CardContent>
							</Card>

							<Card>
								<CardHeader>
									<CardTitle>Other Meta</CardTitle>
								</CardHeader>
								<CardContent>
									<div className="space-y-2 text-sm">
										<div className="flex justify-between">
											<span className="text-muted-foreground">Canonical</span>
											<span className="max-w-[200px] truncate">
												{report.metadata.canonical || "Not set"}
											</span>
										</div>
										<div className="flex justify-between">
											<span className="text-muted-foreground">Language</span>
											<span>{report.metadata.language || "Not set"}</span>
										</div>
										<div className="flex justify-between">
											<span className="text-muted-foreground">Viewport</span>
											<span>
												{report.metadata.viewport ? "Set" : "Missing"}
											</span>
										</div>
										<div className="flex justify-between">
											<span className="text-muted-foreground">Robots</span>
											<span>{report.metadata.robots_meta || "Not set"}</span>
										</div>
									</div>
								</CardContent>
							</Card>
						</div>
					</TabsContent>

					{/* Content Tab */}
					<TabsContent value="content">
						<div className="grid gap-4 md:grid-cols-2">
							<Card>
								<CardHeader>
									<CardTitle>Content Stats</CardTitle>
								</CardHeader>
								<CardContent>
									<div className="space-y-3">
										<div className="flex justify-between">
											<span className="text-muted-foreground">Word Count</span>
											<span className="font-medium">
												{report.content.word_count}
											</span>
										</div>
										<div className="flex justify-between">
											<span className="text-muted-foreground">
												Reading Time
											</span>
											<span className="font-medium">
												{report.content.readability.reading_time_minutes} min
											</span>
										</div>
										<div className="flex justify-between">
											<span className="text-muted-foreground">
												Flesch Reading Ease
											</span>
											<span className="font-medium">
												{report.content.readability.flesch_reading_ease}
											</span>
										</div>
										<div className="flex justify-between">
											<span className="text-muted-foreground">
												Reading Grade
											</span>
											<span className="font-medium">
												{report.content.readability.flesch_kincaid_grade}
											</span>
										</div>
									</div>
								</CardContent>
							</Card>

							<Card>
								<CardHeader>
									<CardTitle>Images & Links</CardTitle>
								</CardHeader>
								<CardContent>
									<div className="space-y-3">
										<div className="flex justify-between">
											<span className="text-muted-foreground">
												Total Images
											</span>
											<span className="font-medium">
												{report.images.total}
											</span>
										</div>
										<div className="flex justify-between">
											<span className="text-muted-foreground">Missing Alt</span>
											<span
												className={
													report.images.missing_alt > 0
														? "font-medium text-destructive"
														: "font-medium"
												}
											>
												{report.images.missing_alt}
											</span>
										</div>
										<div className="flex justify-between">
											<span className="text-muted-foreground">
												Internal Links
											</span>
											<span className="font-medium">
												{report.links.internal_count}
											</span>
										</div>
										<div className="flex justify-between">
											<span className="text-muted-foreground">
												External Links
											</span>
											<span className="font-medium">
												{report.links.external_count}
											</span>
										</div>
									</div>
								</CardContent>
							</Card>

							<Card className="md:col-span-2">
								<CardHeader>
									<CardTitle>Top Keywords</CardTitle>
									<CardDescription>
										Based on frequency analysis
									</CardDescription>
								</CardHeader>
								<CardContent>
									<div className="flex flex-wrap gap-2">
										{report.content.keywords_frequency
											.slice(0, 15)
											.map((kw, idx) => (
												<Badge
													key={idx}
													variant="outline"
													className="text-sm"
												>
													{kw.keyword}{" "}
													<span className="ml-1 text-muted-foreground">
														({kw.count})
													</span>
												</Badge>
											))}
									</div>
									{report.content.top_bigrams.length > 0 && (
										<div className="mt-4">
											<h4 className="mb-2 text-sm font-medium">
												Top Phrases
											</h4>
											<div className="flex flex-wrap gap-2">
												{report.content.top_bigrams.slice(0, 8).map((bg, idx) => (
													<Badge key={idx} variant="secondary" className="text-sm">
														{bg.phrase}{" "}
														<span className="ml-1 text-muted-foreground">
															({bg.count})
														</span>
													</Badge>
												))}
											</div>
										</div>
									)}
								</CardContent>
							</Card>
						</div>
					</TabsContent>

					{/* Technical Tab */}
					<TabsContent value="technical">
						<Card>
							<CardHeader>
								<CardTitle>Technical Details</CardTitle>
							</CardHeader>
							<CardContent>
								<Table>
									<TableBody>
										<TableRow>
											<TableCell className="font-medium">HTTPS</TableCell>
											<TableCell>
												{report.technical.https ? (
													<Badge variant="secondary">Yes</Badge>
												) : (
													<Badge variant="destructive">No</Badge>
												)}
											</TableCell>
										</TableRow>
										<TableRow>
											<TableCell className="font-medium">
												Response Time
											</TableCell>
											<TableCell>{report.technical.response_time_ms}ms</TableCell>
										</TableRow>
										<TableRow>
											<TableCell className="font-medium">Content Type</TableCell>
											<TableCell className="font-mono text-sm">
												{report.technical.content_type}
											</TableCell>
										</TableRow>
										<TableRow>
											<TableCell className="font-medium">Server</TableCell>
											<TableCell>
												{report.technical.server || "Not disclosed"}
											</TableCell>
										</TableRow>
										<TableRow>
											<TableCell className="font-medium">CSP Header</TableCell>
											<TableCell>
												{report.technical.content_security_policy ? (
													<Badge variant="secondary">Present</Badge>
												) : (
													<Badge variant="outline">Missing</Badge>
												)}
											</TableCell>
										</TableRow>
									</TableBody>
								</Table>
							</CardContent>
						</Card>
					</TabsContent>

					{/* AI Indexing Tab */}
					<TabsContent value="ai">
						<div className="grid gap-4 md:grid-cols-2">
							<Card>
								<CardHeader>
									<CardTitle>AI Readiness Files</CardTitle>
								</CardHeader>
								<CardContent>
									<div className="space-y-3">
										<div className="flex items-center justify-between">
											<span>robots.txt</span>
											{report.ai_indexing.robots_txt.present ? (
												<Badge variant="secondary">Found</Badge>
											) : (
												<Badge variant="destructive">Missing</Badge>
											)}
										</div>
										<div className="flex items-center justify-between">
											<span>llms.txt</span>
											{report.ai_indexing.llms_txt.present ? (
												<Badge variant="secondary">Found</Badge>
											) : (
												<Badge variant="outline">Missing</Badge>
											)}
										</div>
										<div className="flex items-center justify-between">
											<span>sitemap.xml</span>
											{report.ai_indexing.sitemap_xml.present ? (
												<Badge variant="secondary">Found</Badge>
											) : (
												<Badge variant="destructive">Missing</Badge>
											)}
										</div>
									</div>
								</CardContent>
							</Card>

							<Card>
								<CardHeader>
									<CardTitle>AI Bot Access</CardTitle>
									<CardDescription>
										Status from robots.txt
									</CardDescription>
								</CardHeader>
								<CardContent>
									<div className="max-h-[300px] space-y-2 overflow-y-auto">
										{Object.entries(
											report.ai_indexing.robots_txt.ai_bots_status
										).map(([bot, status]) => (
											<div
												key={bot}
												className="flex items-center justify-between text-sm"
											>
												<span className="font-mono">{bot}</span>
												<Badge
													variant={
														status.includes("blocked")
															? "destructive"
															: status.includes("allowed")
																? "secondary"
																: "outline"
													}
													className="text-xs"
												>
													{status}
												</Badge>
											</div>
										))}
									</div>
								</CardContent>
							</Card>

							{report.ai_indexing.llms_txt.content_preview && (
								<Card className="md:col-span-2">
									<CardHeader>
										<CardTitle>llms.txt Preview</CardTitle>
									</CardHeader>
									<CardContent>
										<pre className="max-h-[200px] overflow-auto rounded bg-muted p-3 text-xs">
											{report.ai_indexing.llms_txt.content_preview}
										</pre>
									</CardContent>
								</Card>
							)}
						</div>
					</TabsContent>

					{/* Structured Data Tab */}
					<TabsContent value="structured">
						<div className="grid gap-4 md:grid-cols-2">
							<Card>
								<CardHeader>
									<CardTitle>Schema.org (JSON-LD)</CardTitle>
								</CardHeader>
								<CardContent>
									{report.structured_data.json_ld.length > 0 ? (
										<div className="space-y-2">
											{report.structured_data.json_ld.map((schema, idx) => (
												<Badge key={idx} variant="secondary">
													{schema.type || "Unknown"}
												</Badge>
											))}
										</div>
									) : (
										<p className="text-sm text-muted-foreground">
											No JSON-LD schemas found
										</p>
									)}
									<div className="mt-4 space-y-2">
										<div className="flex items-center justify-between text-sm">
											<span>Microdata</span>
											{report.structured_data.microdata ? (
												<Badge variant="secondary">Found</Badge>
											) : (
												<Badge variant="outline">Not found</Badge>
											)}
										</div>
										<div className="flex items-center justify-between text-sm">
											<span>RDFa</span>
											{report.structured_data.rdfa ? (
												<Badge variant="secondary">Found</Badge>
											) : (
												<Badge variant="outline">Not found</Badge>
											)}
										</div>
									</div>
								</CardContent>
							</Card>

							<Card>
								<CardHeader>
									<CardTitle>Social Meta Tags</CardTitle>
								</CardHeader>
								<CardContent>
									<div className="space-y-4">
										<div>
											<h4 className="mb-2 text-sm font-medium">Open Graph</h4>
											{Object.keys(report.structured_data.open_graph).length >
											0 ? (
												<div className="space-y-1 text-sm">
													{Object.entries(
														report.structured_data.open_graph
													).map(([key, value]) => (
														<div key={key} className="flex gap-2">
															<span className="font-mono text-muted-foreground">
																{key}:
															</span>
															<span className="truncate">{value}</span>
														</div>
													))}
												</div>
											) : (
												<p className="text-sm text-muted-foreground">
													No Open Graph tags found
												</p>
											)}
										</div>
										<div>
											<h4 className="mb-2 text-sm font-medium">Twitter Card</h4>
											{Object.keys(report.structured_data.twitter_card).length >
											0 ? (
												<div className="space-y-1 text-sm">
													{Object.entries(
														report.structured_data.twitter_card
													).map(([key, value]) => (
														<div key={key} className="flex gap-2">
															<span className="font-mono text-muted-foreground">
																{key}:
															</span>
															<span className="truncate">{value}</span>
														</div>
													))}
												</div>
											) : (
												<p className="text-sm text-muted-foreground">
													No Twitter Card tags found
												</p>
											)}
										</div>
									</div>
								</CardContent>
							</Card>
						</div>
					</TabsContent>
				</Tabs>
			</main>

			{/* Footer */}
			<footer className="border-t py-6">
				<div className="container mx-auto flex items-center justify-center gap-2 px-4 text-xs text-muted-foreground">
					<span>Powered by</span>
					<a
						href="https://www.conusai.com"
						target="_blank"
						rel="noopener noreferrer"
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
