"use client"

import { BarChart2, Clock, FileText, Sparkles, Zap } from "lucide-react"
import { AIRecommendations } from "@/components/ai-recommendations"
import { AISummary } from "@/components/ai-summary"
import { ScoresOverview } from "@/components/score-gauge"
import { Card, CardContent } from "@/components/ui/card"
import { AwaitingAnalysis } from "../../awaiting-analysis"
import { useReportContext } from "../../report-context"

export default function OverviewPage() {
	const { analysis, aiIndexing, formattedTimestamp } = useReportContext()

	if (!analysis) return <AwaitingAnalysis />

	const metrics = [
		{
			label: "Response Time",
			value: analysis.crawl_time_ms != null ? `${analysis.crawl_time_ms}ms` : "—",
			icon: Clock,
		},
		{
			label: "Last Checked",
			value: formattedTimestamp,
			icon: Clock,
		},
		{
			label: "Word Count",
			value: analysis.content?.word_count?.toLocaleString() ?? "—",
			icon: FileText,
		},
		{
			label: "AI Score",
			value: analysis.scores?.ai_readiness ?? "—",
			icon: Zap,
		},
	]

	return (
		<div className="space-y-6">
			{/* Hero Section: AI Summary + Scorecard - Two columns on desktop, stacked on mobile */}
			<section className="grid gap-6 lg:grid-cols-2">
				{/* AI Summary - Left on desktop, first on mobile */}
				<div className="order-1 space-y-4">
					<div className="flex items-center gap-2">
						<Sparkles className="h-4 w-4 text-primary" />
						<h2 className="font-medium text-muted-foreground text-sm uppercase tracking-wider">
							AI Insights
						</h2>
					</div>
					<AISummary analysis={analysis as Record<string, unknown>} />
				</div>

				{/* Scorecard - Right on desktop, second on mobile */}
				<div className="order-2 space-y-4">
					<div className="flex items-center gap-2">
						<BarChart2 className="h-4 w-4 text-primary" />
						<h2 className="font-medium text-muted-foreground text-sm uppercase tracking-wider">
							Scorecard
						</h2>
					</div>

					<Card className="overflow-hidden border-border/50">
						<CardContent className="p-4 sm:p-6">
							<ScoresOverview
								scores={{
									overall: analysis.scores?.overall ?? 0,
									technical: analysis.scores?.technical ?? 0,
									on_page: analysis.scores?.on_page ?? 0,
									content: analysis.scores?.content ?? 0,
									structured_data: analysis.scores?.structured_data ?? 0,
									ai_readiness: analysis.scores?.ai_readiness ?? 0,
								}}
							/>
						</CardContent>
					</Card>
				</div>
			</section>

			{/* Quick Metrics */}
			<section className="grid grid-cols-2 gap-3 sm:grid-cols-4">
				{metrics.map((metric) => {
					const Icon = metric.icon
					return (
						<div
							key={metric.label}
							className="group rounded-xl border border-border/50 bg-card p-4 transition-all duration-200 hover:border-primary/20 hover:shadow-sm"
						>
							<div className="flex items-center gap-2 text-muted-foreground">
								<Icon className="h-3.5 w-3.5" />
								<p className="font-medium text-xs">{metric.label}</p>
							</div>
							<p className="mt-1.5 font-semibold text-foreground text-lg tabular-nums">
								{metric.value}
							</p>
						</div>
					)
				})}
			</section>

			{/* Metadata */}
			{analysis.metadata && (
				<section className="grid gap-3 sm:grid-cols-2">
					<div className="rounded-xl border border-border/50 bg-card p-4">
						<p className="font-medium text-muted-foreground text-xs uppercase tracking-wider">
							Page Title
						</p>
						<p className="mt-1.5 text-foreground text-sm leading-relaxed">
							{analysis.metadata.title?.value || (
								<span className="text-muted-foreground italic">Not set</span>
							)}
						</p>
					</div>
					<div className="rounded-xl border border-border/50 bg-card p-4">
						<p className="font-medium text-muted-foreground text-xs uppercase tracking-wider">
							Meta Description
						</p>
						<p className="mt-1.5 line-clamp-3 text-foreground text-sm leading-relaxed">
							{analysis.metadata.description?.value || (
								<span className="text-muted-foreground italic">Not set</span>
							)}
						</p>
					</div>
				</section>
			)}

			{/* Recommendations */}
			<AIRecommendations
				issues={analysis.issues ?? []}
				recommendations={analysis.recommendations ?? []}
				scores={{
					ai_readiness: analysis.scores?.ai_readiness ?? 0,
					content: analysis.scores?.content ?? 0,
					structured_data: analysis.scores?.structured_data ?? 0,
				}}
				aiIndexing={{
					robots_txt: { present: aiIndexing.robots_txt.present },
					llms_txt: { present: aiIndexing.llms_txt.present },
					sitemap_xml: { present: aiIndexing.sitemap_xml.present },
				}}
			/>
		</div>
	)
}
