"use client"

import {
	Activity,
	CheckCircle2,
	FileCode,
	Gauge,
	Lock,
	Server,
	Shield,
	Target,
	Zap,
} from "lucide-react"
import { useCallback } from "react"

import { AIBotStatus } from "@/components/ai-bot-status"
import { Spinner } from "@/components/ui/spinner"
import { AwaitingAnalysis } from "../../awaiting-analysis"
import { useReportContext } from "../../report-context"

export default function SignalsPage() {
	const {
		analysis,
		aiIndexing,
		keyMetrics,
		preferences,
		setPreferences,
		preferenceOptions,
		preferenceOptionsLoading,
		bestFeatures,
		topFeatures,
	} = useReportContext()

	const togglePreference = useCallback(
		(id: string) => {
			setPreferences((current) =>
				current.includes(id) ? current.filter((pref) => pref !== id) : [...current, id]
			)
		},
		[setPreferences]
	)

	if (!analysis) return <AwaitingAnalysis />

	const technicalMetrics = [
		{
			label: "HTTPS",
			value: analysis.technical?.https ? "Enabled" : "Disabled",
			icon: Lock,
			status: analysis.technical?.https,
		},
		{
			label: "Response Time",
			value: `${analysis.technical?.response_time_ms ?? "—"}ms`,
			icon: Zap,
			status: (analysis.technical?.response_time_ms ?? 1000) < 500,
		},
		{
			label: "Content Type",
			value: analysis.technical?.content_type ?? "—",
			icon: FileCode,
			status: true,
		},
		{
			label: "Server",
			value: analysis.technical?.server ?? "—",
			icon: Server,
			status: true,
		},
	]

	return (
		<div className="space-y-6">
			{/* AI Bot Status */}
			<AIBotStatus botStatus={aiIndexing.robots_txt.ai_bots_status} />

			{/* Technical Signals */}
			<section className="space-y-4">
				<div className="flex items-center gap-2">
					<Shield className="h-4 w-4 text-primary" />
					<h2 className="font-medium text-muted-foreground text-sm uppercase tracking-wider">
						Technical Signals
					</h2>
				</div>

				<div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
					{technicalMetrics.map((metric) => {
						const Icon = metric.icon
						return (
							<div
								key={metric.label}
								className="group rounded-xl border border-border/50 bg-card p-4 transition-all duration-200 hover:border-primary/20"
							>
								<div className="flex items-center gap-2 text-muted-foreground">
									<Icon className="h-3.5 w-3.5" />
									<p className="font-medium text-xs">{metric.label}</p>
								</div>
								<p
									className="mt-1.5 truncate font-medium text-foreground text-sm"
									title={metric.value}
								>
									{metric.value}
								</p>
							</div>
						)
					})}
				</div>
			</section>

			{/* Key Metrics */}
			<section className="space-y-4">
				<div className="flex items-center gap-2">
					<Gauge className="h-4 w-4 text-primary" />
					<h2 className="font-medium text-muted-foreground text-sm uppercase tracking-wider">
						Key Metrics
					</h2>
				</div>

				<div className="rounded-xl border border-border/50 bg-card p-4 sm:p-6">
					{keyMetrics.length === 0 ? (
						<p className="py-4 text-center text-muted-foreground text-sm">
							No additional metrics captured.
						</p>
					) : (
						<div className="space-y-3">
							{keyMetrics.map(([key, value]) => (
								<div
									key={key}
									className="flex items-center justify-between border-border/30 border-b py-2 last:border-0"
								>
									<span className="text-muted-foreground text-sm capitalize">
										{key.replace(/_/g, " ")}
									</span>
									<span className="font-medium text-foreground text-sm tabular-nums">
										{value?.toString()}
									</span>
								</div>
							))}
						</div>
					)}
				</div>
			</section>

			{/* AI Priorities */}
			<section className="space-y-4">
				<div className="flex items-center gap-2">
					<Target className="h-4 w-4 text-primary" />
					<h2 className="font-medium text-muted-foreground text-sm uppercase tracking-wider">
						Optimization Priorities
					</h2>
				</div>

				<div className="rounded-xl border border-border/50 bg-card p-4 sm:p-6">
					{preferenceOptionsLoading && (
						<div className="flex items-center justify-center gap-3 py-8">
							<Spinner size="sm" />
							<span className="text-muted-foreground text-sm">Generating priorities...</span>
						</div>
					)}

					{!preferenceOptionsLoading && preferenceOptions.length === 0 && (
						<p className="py-4 text-center text-muted-foreground text-sm">
							No priority recommendations available.
						</p>
					)}

					{!preferenceOptionsLoading && preferenceOptions.length > 0 && (
						<div className="space-y-4">
							<div className="flex flex-wrap gap-2">
								{preferenceOptions.map((option) => {
									const active = preferences.includes(option.id)
									return (
										<button
											type="button"
											key={option.id}
											onClick={() => togglePreference(option.id)}
											className={`rounded-full border px-4 py-1.5 font-medium text-sm transition-all duration-200 ${
												active
													? "border-primary bg-primary/10 text-primary"
													: "border-border/50 text-muted-foreground hover:border-primary/30 hover:text-foreground"
											}`}
											title={option.detail}
										>
											{option.label}
										</button>
									)
								})}
							</div>

							{preferences.length > 0 && (
								<div className="space-y-2 border-border/50 border-t pt-2">
									{preferenceOptions
										.filter((opt) => preferences.includes(opt.id))
										.map((opt) => (
											<div key={opt.id} className="flex gap-2 text-sm">
												<CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
												<span>
													<span className="font-medium text-foreground">{opt.label}:</span>{" "}
													<span className="text-muted-foreground">{opt.detail}</span>
												</span>
											</div>
										))}
								</div>
							)}
						</div>
					)}
				</div>
			</section>

			{/* Top Features */}
			{topFeatures.length > 0 && (
				<section className="space-y-4">
					<div className="flex items-center gap-2">
						<Activity className="h-4 w-4 text-primary" />
						<h2 className="font-medium text-muted-foreground text-sm uppercase tracking-wider">
							Top Strengths
						</h2>
					</div>

					{bestFeatures.length > 0 && (
						<p className="text-muted-foreground text-sm">
							{bestFeatures
								.map(([label, value]) => `${label.replace(/_/g, " ")}: ${value}`)
								.join(" · ")}
						</p>
					)}

					<div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
						{topFeatures.map(([label, value]) => (
							<div
								key={label}
								className="group rounded-xl border border-border/50 bg-card p-4 transition-all duration-200 hover:border-primary/20"
							>
								<p className="font-medium text-muted-foreground text-xs uppercase capitalize tracking-wider">
									{label.replace(/_/g, " ")}
								</p>
								<p className="mt-1.5 font-semibold text-2xl text-foreground tabular-nums">
									{value}
								</p>
								<p className="mt-1 text-muted-foreground text-xs">Strong AI visibility signal</p>
							</div>
						))}
					</div>
				</section>
			)}
		</div>
	)
}
