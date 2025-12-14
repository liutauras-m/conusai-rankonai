"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

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

function getImpactLevel(issue: Issue): "critical" | "important" | "minor" {
	if (issue.severity === "high") return "critical"
	if (issue.severity === "medium") return "important"
	return "minor"
}

function getImpactColor(level: "critical" | "important" | "minor") {
	switch (level) {
		case "critical":
			return {
				bg: "bg-red-500/10",
				border: "border-red-500/30",
				text: "text-red-600 dark:text-red-400",
				icon: "🔴",
			}
		case "important":
			return {
				bg: "bg-amber-500/10",
				border: "border-amber-500/30",
				text: "text-amber-600 dark:text-amber-400",
				icon: "🟡",
			}
		case "minor":
			return {
				bg: "bg-blue-500/10",
				border: "border-blue-500/30",
				text: "text-blue-600 dark:text-blue-400",
				icon: "🔵",
			}
	}
}

export function AIRecommendations({
	issues,
	recommendations,
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
		<div className="space-y-6">
			{/* Quick Wins Summary */}
			<Card>
				<CardHeader>
					<CardTitle className="flex items-center gap-2">
						<span className="text-xl">💡</span>
						What to Improve
					</CardTitle>
					<CardDescription>
						Actions that will help AI assistants find and recommend your brand
					</CardDescription>
				</CardHeader>
				<CardContent>
					{/* Stats Bar */}
					<div className="mb-6 flex flex-wrap gap-4 rounded-lg bg-muted/50 p-4">
						<div className="flex items-center gap-2">
							<span className="text-red-500">🔴</span>
							<span className="text-sm">
								<strong>{criticalIssues.length}</strong> critical
							</span>
						</div>
						<div className="flex items-center gap-2">
							<span className="text-amber-500">🟡</span>
							<span className="text-sm">
								<strong>{importantIssues.length}</strong> important
							</span>
						</div>
						<div className="flex items-center gap-2">
							<span className="text-blue-500">🔵</span>
							<span className="text-sm">
								<strong>{minorIssues.length}</strong> minor
							</span>
						</div>
					</div>

					{/* No Issues */}
					{issues.length === 0 && smartRecommendations.length === 0 && (
						<div className="rounded-lg border border-green-200 bg-green-50 p-6 text-center dark:border-green-800/50 dark:bg-green-900/20">
							<span className="text-4xl">🎉</span>
							<h3 className="mt-2 font-semibold text-green-800 dark:text-green-200">
								Looking Great!
							</h3>
							<p className="mt-1 text-sm text-green-700 dark:text-green-300">
								Your site is well-optimized for AI search visibility.
							</p>
						</div>
					)}

					{/* Smart Recommendations */}
					{smartRecommendations.length > 0 && (
						<div className="mb-6">
							<h4 className="mb-3 font-medium text-foreground">
								🚀 Recommended Actions
							</h4>
							<div className="space-y-3">
								{smartRecommendations.map((rec, idx) => (
									<div
										key={idx}
										className={`rounded-lg border p-4 ${
											rec.impact === "high"
												? "border-primary/30 bg-primary/5"
												: "border-border bg-card"
										}`}
									>
										<div className="flex items-start gap-3">
											<span className="text-lg">
												{rec.impact === "high"
													? "⭐"
													: rec.impact === "medium"
														? "📌"
														: "💭"}
											</span>
											<div>
												<h5 className="font-medium text-foreground">{rec.title}</h5>
												<p className="mt-1 text-sm text-muted-foreground">
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
						<div className="mb-6">
							<h4 className="mb-3 font-medium text-red-600 dark:text-red-400">
								🔴 Critical Issues
							</h4>
							<div className="space-y-2">
								{criticalIssues.map((issue, idx) => {
									const explanation = ISSUE_EXPLANATIONS[issue.code]
									const colors = getImpactColor("critical")
									return (
										<div
											key={idx}
											className={`rounded-lg border ${colors.border} ${colors.bg} p-3`}
										>
											<p className="font-medium text-foreground">
												{explanation?.title || issue.message}
											</p>
											{explanation && (
												<p className="mt-1 text-sm text-muted-foreground">
													<strong>Impact:</strong> {explanation.impact}
												</p>
											)}
											<p className="mt-1 text-sm text-muted-foreground">
												<strong>Fix:</strong>{" "}
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
						<div className="mb-6">
							<h4 className="mb-3 font-medium text-amber-600 dark:text-amber-400">
								🟡 Important Improvements
							</h4>
							<div className="space-y-2">
								{importantIssues.slice(0, 5).map((issue, idx) => {
									const explanation = ISSUE_EXPLANATIONS[issue.code]
									return (
										<div key={idx} className="rounded-lg border border-border p-3">
											<p className="text-sm font-medium text-foreground">
												{explanation?.title || issue.message}
											</p>
											{explanation && (
												<p className="mt-1 text-xs text-muted-foreground">
													{explanation.action}
												</p>
											)}
										</div>
									)
								})}
								{importantIssues.length > 5 && (
									<p className="text-sm text-muted-foreground">
										+{importantIssues.length - 5} more improvements
									</p>
								)}
							</div>
						</div>
					)}

					{/* Minor Issues (collapsed) */}
					{minorIssues.length > 0 && (
						<details className="group">
							<summary className="cursor-pointer text-sm text-muted-foreground hover:text-foreground">
								🔵 {minorIssues.length} minor suggestions
							</summary>
							<div className="mt-3 space-y-2">
								{minorIssues.map((issue, idx) => (
									<div
										key={idx}
										className="rounded border border-border p-2 text-sm text-muted-foreground"
									>
										{ISSUE_EXPLANATIONS[issue.code]?.title || issue.message}
									</div>
								))}
							</div>
						</details>
					)}
				</CardContent>
			</Card>
		</div>
	)
}
