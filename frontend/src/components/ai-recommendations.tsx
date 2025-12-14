"use client"

import { Lightbulb, Rocket, CheckCircle2, AlertTriangle, Info, ChevronDown } from "lucide-react"

interface Issue {
	severity: string
	category: string
	code: string
	message: string
	element?: string
}

interface Recommendation {
	priority: number
	category: string
	action: string
}

interface AIRecommendationsProps {
	issues: Issue[]
	recommendations: Recommendation[]
	scores: {
		ai_readiness: number
		content: number
		structured_data: number
	}
	aiIndexing: {
		robots_txt: { present: boolean }
		llms_txt: { present: boolean }
		sitemap_xml: { present: boolean }
	}
}

// Map technical issues to business-friendly explanations
const ISSUE_EXPLANATIONS: Record<string, { title: string; impact: string; action: string }> = {
	NO_LLMS_TXT: {
		title: "No llms.txt file found",
		impact: "AI assistants don't have a guide to understand your brand",
		action: "Add an llms.txt file to help AI accurately describe your business",
	},
	AI_BOTS_BLOCKED: {
		title: "Some AI crawlers are blocked",
		impact: "Your site may not appear in AI search results",
		action: "Update robots.txt to allow important AI crawlers like GPTBot and ClaudeBot",
	},
	NO_SCHEMA: {
		title: "No structured data (Schema.org)",
		impact: "AI can't extract key facts about your business",
		action: "Add JSON-LD schema markup for your organization, products, or services",
	},
	NO_OG: {
		title: "Missing Open Graph tags",
		impact: "AI may show incomplete information when sharing your content",
		action: "Add og:title, og:description, and og:image meta tags",
	},
	META_DESC_MISSING: {
		title: "No meta description",
		impact: "AI has less context about what your page offers",
		action: "Write a compelling 150-160 character description",
	},
	TITLE_MISSING: {
		title: "Page title is missing",
		impact: "AI won't know what to call your page",
		action: "Add a clear, descriptive page title",
	},
	H1_MISSING: {
		title: "No main heading (H1)",
		impact: "AI may struggle to understand the page's main topic",
		action: "Add a clear H1 heading that describes the page content",
	},
	NO_SITEMAP: {
		title: "No sitemap.xml found",
		impact: "AI crawlers may miss some of your pages",
		action: "Create and submit a sitemap.xml file",
	},
	CANONICAL_MISSING: {
		title: "No canonical URL specified",
		impact: "AI might index duplicate versions of your pages",
		action: "Add a canonical link tag to specify the preferred URL",
	},
}

// Extract blocked crawlers from issue message
function extractBlockedCrawlers(issue: Issue): string[] {
	if (issue.code === "AI_BOTS_BLOCKED" && issue.message) {
		const match = issue.message.match(/blocked:\s*(.+)$/i)
		if (match) {
			return match[1].split(",").map(s => s.trim()).filter(Boolean)
		}
	}
	return []
}

function getImpactLevel(issue: Issue): "critical" | "important" | "minor" {
	if (issue.severity === "high") return "critical"
	if (issue.severity === "medium") return "important"
	return "minor"
}

export function AIRecommendations({
	issues,
	recommendations: _recommendations,
	scores,
	aiIndexing,
}: AIRecommendationsProps) {
	// Group issues by impact
	const criticalIssues = issues.filter((i) => getImpactLevel(i) === "critical")
	const importantIssues = issues.filter((i) => getImpactLevel(i) === "important")
	const minorIssues = issues.filter((i) => getImpactLevel(i) === "minor")

	// Generate smart recommendations based on current state
	const smartRecommendations: Array<{
		title: string
		description: string
		impact: "high" | "medium" | "low"
		category: string
	}> = []

	// AI-specific recommendations
	if (!aiIndexing.llms_txt.present) {
		smartRecommendations.push({
			title: "Create an llms.txt file",
			description:
				"This file tells AI assistants about your brand, services, and how to recommend you accurately.",
			impact: "high",
			category: "ai_visibility",
		})
	}

	if (!aiIndexing.sitemap_xml.present) {
		smartRecommendations.push({
			title: "Add a sitemap.xml",
			description:
				"Help AI crawlers discover all your important pages so they can recommend your full content.",
			impact: "high",
			category: "ai_visibility",
		})
	}

	if (scores.structured_data < 50) {
		smartRecommendations.push({
			title: "Add structured data markup",
			description:
				"Schema.org markup helps AI extract and present your business information accurately.",
			impact: "high",
			category: "structured_data",
		})
	}

	if (scores.content < 60) {
		smartRecommendations.push({
			title: "Improve content quality",
			description:
				"Clear, well-structured content helps AI understand and recommend your site for relevant queries.",
			impact: "medium",
			category: "content",
		})
	}

	return (
		<section className="space-y-4">
			<div className="flex items-center gap-2">
				<Lightbulb className="h-4 w-4 text-primary" />
				<h2 className="font-medium text-muted-foreground text-sm uppercase tracking-wider">Recommendations</h2>
			</div>

			<div className="rounded-xl border border-border/50 bg-card p-4 sm:p-6">
				{/* Stats Bar */}
				<div className="mb-5 grid grid-cols-3 gap-3">
					<div className="rounded-lg bg-destructive/5 p-3 text-center">
						<div className="font-semibold text-destructive text-lg tabular-nums">
							{criticalIssues.length}
						</div>
						<div className="text-muted-foreground text-xs">Critical</div>
					</div>
					<div className="rounded-lg bg-secondary p-3 text-center">
						<div className="font-semibold text-lg text-secondary-foreground tabular-nums">
							{importantIssues.length}
						</div>
						<div className="text-muted-foreground text-xs">Important</div>
					</div>
					<div className="rounded-lg bg-muted/50 p-3 text-center">
						<div className="font-semibold text-lg text-muted-foreground tabular-nums">
							{minorIssues.length}
						</div>
						<div className="text-muted-foreground text-xs">Minor</div>
					</div>
				</div>

				{/* No Issues */}
				{issues.length === 0 && smartRecommendations.length === 0 && (
					<div className="rounded-xl border border-primary/20 bg-primary/5 p-6 text-center">
						<CheckCircle2 className="mx-auto h-8 w-8 text-primary" />
						<h3 className="mt-2 font-medium text-foreground">Looking Great!</h3>
						<p className="mt-1 text-muted-foreground text-sm">
							Your site is well-optimized for AI visibility.
						</p>
					</div>
				)}

				{/* Smart Recommendations */}
				{smartRecommendations.length > 0 && (
					<div className="mb-5">
						<h4 className="mb-3 flex items-center gap-2 font-medium text-muted-foreground text-xs uppercase tracking-wider">
							<Rocket className="h-3 w-3" /> Recommended Actions
						</h4>
						<div className="space-y-2">
							{smartRecommendations.map((rec) => (
								<div
									key={rec.title}
									className={`rounded-lg border p-4 transition-all duration-200 hover:border-primary/20 ${
										rec.impact === "high"
											? "border-primary/30 bg-primary/5"
											: "border-border/50 bg-background"
									}`}
								>
									<div className="flex items-start gap-3">
										<div className={`mt-0.5 h-2 w-2 shrink-0 rounded-full ${
											rec.impact === "high" ? "bg-primary" : "bg-muted-foreground"
										}`} />
										<div>
											<h5 className="font-medium text-foreground text-sm">{rec.title}</h5>
											<p className="mt-1 text-muted-foreground text-sm leading-relaxed">
												{rec.description}
											</p>
										</div>
									</div>
								</div>
							))}
						</div>
					</div>
				)}

				{/* Critical Issues */}
				{criticalIssues.length > 0 && (
					<div className="mb-5">
						<h4 className="mb-3 flex items-center gap-2 font-medium text-destructive text-xs uppercase tracking-wider">
							<AlertTriangle className="h-3 w-3" /> Critical Issues
						</h4>
						<div className="space-y-2">
							{criticalIssues.map((issue) => {
								const explanation = ISSUE_EXPLANATIONS[issue.code]
								return (
									<div
										key={issue.code}
										className="rounded-lg border border-destructive/20 bg-destructive/5 p-4"
									>
										<p className="font-medium text-foreground text-sm">
											{explanation?.title || issue.message}
										</p>
										{explanation && (
											<p className="mt-1 text-muted-foreground text-xs">
												{explanation.impact}
											</p>
										)}
										<p className="mt-2 text-foreground text-xs">
											<span className="font-medium">Fix:</span>{" "}
											{explanation?.action || "Address this issue to improve visibility"}
										</p>
									</div>
								)
							})}
						</div>
					</div>
				)}

				{/* Important Issues */}
				{importantIssues.length > 0 && (
					<div className="mb-5">
						<h4 className="mb-3 flex items-center gap-2 font-medium text-secondary-foreground text-xs uppercase tracking-wider">
							<Info className="h-3 w-3" /> Important Improvements
						</h4>
						<div className="space-y-2">
							{importantIssues.slice(0, 5).map((issue) => {
								const explanation = ISSUE_EXPLANATIONS[issue.code]
								const blockedCrawlers = extractBlockedCrawlers(issue)
								return (
									<div key={issue.code} className="rounded-lg border border-border/50 bg-background p-3">
										<p className="font-medium text-foreground text-sm">
											{explanation?.title || issue.message}
										</p>
										{blockedCrawlers.length > 0 && (
											<p className="mt-1.5 flex flex-wrap items-center gap-1.5 text-xs">
												<span className="text-muted-foreground">Blocked:</span>
												{blockedCrawlers.map((crawler) => (
													<span 
														key={crawler}
														className="rounded bg-amber-500/10 px-1.5 py-0.5 font-medium text-amber-600 dark:text-amber-400"
													>
														{crawler}
													</span>
												))}
											</p>
										)}
										{explanation && !blockedCrawlers.length && (
											<p className="mt-1 text-muted-foreground text-xs">
												{explanation.action}
											</p>
										)}
										{blockedCrawlers.length > 0 && explanation && (
											<p className="mt-1.5 text-muted-foreground text-xs">
												{explanation.action}
											</p>
										)}
									</div>
								)
							})}
							{importantIssues.length > 5 && (
								<p className="pt-1 text-muted-foreground text-xs">
									+{importantIssues.length - 5} more improvements
								</p>
							)}
						</div>
					</div>
				)}

				{/* Minor Issues (collapsed) */}
				{minorIssues.length > 0 && (
					<details className="group">
						<summary className="flex cursor-pointer items-center gap-1 text-muted-foreground text-xs transition-colors hover:text-foreground">
							<ChevronDown className="h-3 w-3 transition-transform group-open:rotate-180" />
							{minorIssues.length} minor suggestions
						</summary>
						<div className="mt-3 space-y-2">
							{minorIssues.map((issue) => {
								const blockedCrawlers = extractBlockedCrawlers(issue)
								return (
									<div
										key={issue.code}
										className="rounded border border-border/30 px-3 py-2 text-muted-foreground text-xs"
									>
										<p>{ISSUE_EXPLANATIONS[issue.code]?.title || issue.message}</p>
										{blockedCrawlers.length > 0 && (
											<p className="mt-1.5 flex flex-wrap gap-1.5">
												<span className="font-medium text-foreground">Blocked:</span>
												{blockedCrawlers.map((crawler) => (
													<span 
														key={crawler}
														className="rounded bg-amber-500/10 px-1.5 py-0.5 text-amber-600 dark:text-amber-400"
													>
														{crawler}
													</span>
												))}
											</p>
										)}
									</div>
								)
							})}
						</div>
					</details>
				)}
			</div>
		</section>
	)
}
