"use client"

import {
	AlertTriangle,
	Camera,
	Globe2,
	Image as ImageIcon,
	Layers,
	Share2,
	Sparkles,
} from "lucide-react"
import { ScoreGauge } from "@/components/score-gauge"
import { Badge } from "@/components/ui/badge"
import { AwaitingAnalysis } from "../../awaiting-analysis"
import { useReportContext } from "../../report-context"

const PLATFORM_BADGES: Record<string, string> = {
	optimal: "border-primary/20 bg-primary/10 text-primary",
	good: "border-secondary/20 bg-secondary/10 text-secondary",
	needs_improvement: "border-border/50 bg-muted/20 text-muted-foreground",
	poor: "border-destructive/20 bg-destructive/10 text-destructive",
}

const PLATFORM_LABELS: Record<string, string> = {
	optimal: "Optimal",
	good: "Good",
	needs_improvement: "Needs Improvement",
	poor: "Poor",
}

const PRIORITY_BADGE: Record<string, "default" | "secondary" | "destructive"> = {
	high: "destructive",
	medium: "secondary",
	low: "default",
}

export default function SocialPage() {
	const { analysis, socialData } = useReportContext()

	if (!analysis) return <AwaitingAnalysis />

	if (!socialData) {
		return (
			<div className="rounded-xl border border-border/50 bg-card p-6 text-center">
				<AlertTriangle className="mx-auto mb-3 h-10 w-10 text-destructive" />
				<p className="font-semibold text-foreground text-sm">Social sharing data is warming up</p>
				<p className="text-muted-foreground text-sm">
					We'll populate the social preview, compatibility and AI recommendations once the workflow
					finishes.
				</p>
			</div>
		)
	}

	const { metadata, images, platforms, recommendations, preview, score, issues } = socialData
	const improvementList = recommendations.improvements ?? []
	const sampleTags = recommendations.sample_tags ?? {}
	const platformEntries = Object.entries(platforms)
	const { open_graph: og, twitter_card: twitter } = metadata

	return (
		<div className="space-y-6">
			<section className="space-y-4">
				<div className="flex items-center gap-2">
					<Share2 className="h-4 w-4 text-primary" />
					<h2 className="font-medium text-muted-foreground text-sm uppercase tracking-wider">
						Social Sharing Readiness
					</h2>
				</div>
				<div className="grid gap-6 rounded-xl border border-border/50 bg-card p-6 lg:grid-cols-[auto,1fr]">
					<ScoreGauge score={score} label="Social Share" size="lg" />
					<div className="space-y-2">
						<p className="text-muted-foreground text-sm">
							This score reflects how reliably social platforms will pull the right title,
							description and imagery when your page is shared. Every missing tag chips away at
							trust, so keep the essentials in place.
						</p>
						<p className="text-muted-foreground text-sm">
							Issues flagged: <span className="font-medium text-foreground">{issues.length}</span>.
							Resolve the highest severity problems first to shift more visibility into the optimal
							and good ranges.
						</p>
						<p className="text-muted-foreground text-sm">
							Brands with a score above 80 see clearer link previews and higher click-through on
							chat apps, messengers and feeds.
						</p>
					</div>
				</div>
			</section>

			<section className="space-y-4">
				<div className="flex items-center gap-2">
					<ImageIcon className="h-4 w-4 text-primary" />
					<h3 className="font-medium text-muted-foreground text-sm uppercase tracking-wider">
						Preview Snapshot
					</h3>
				</div>
				<p className="text-muted-foreground text-sm">
					This is the social storefront that potential customers see first. Keeping the title,
					description and imagery on brand keeps confidence high before they even tap through.
				</p>
				<div className="grid gap-4 rounded-xl border border-border/50 bg-card p-5 md:grid-cols-[200px,1fr]">
					<div className="flex h-44 w-full items-center justify-center overflow-hidden rounded-lg bg-muted/20">
						{preview.image ? (
							<img
								src={preview.image}
								alt={preview.image_alt || "Social preview image"}
								className="h-full w-full object-cover"
								loading="lazy"
							/>
						) : (
							<span className="text-muted-foreground text-xs">No social image provided</span>
						)}
					</div>
					<div className="space-y-1">
						<p className="line-clamp-2 font-semibold text-foreground text-sm">
							{preview.title || "No title detected"}
						</p>
						<p className="line-clamp-3 text-muted-foreground text-sm">
							{preview.description || "No description detected"}
						</p>
						<div className="flex flex-col gap-1 text-muted-foreground text-xs">
							<span>{preview.site_name || "Site name not set"}</span>
							{preview.url && <span className="text-muted-foreground/70">{preview.url}</span>}
						</div>
					</div>
				</div>
			</section>

			<section className="space-y-4">
				<div className="flex items-center gap-2">
					<Globe2 className="h-4 w-4 text-primary" />
					<h3 className="font-medium text-muted-foreground text-sm uppercase tracking-wider">
						Metadata Health
					</h3>
				</div>
				<p className="text-muted-foreground text-sm">
					Open Graph and Twitter tags tell networks what to highlight about your product or story.
					Missing or incomplete fields translate into generic previews that don't earn trust.
				</p>
				<div className="grid gap-4 md:grid-cols-2">
					{[
						{
							label: "Open Graph",
							present: og.present,
							missing: og.missing_required,
							recommended: og.missing_recommended,
							description: "Used by Facebook, LinkedIn, WhatsApp and Slack",
						},
						{
							label: "Twitter Card",
							present: twitter.present,
							missing: twitter.missing_required,
							recommended: twitter.missing_recommended,
							description: "Ensures X/Twitter renders rich previews",
						},
					].map((meta) => (
						<div
							key={meta.label}
							className="flex flex-col gap-3 rounded-xl border border-border/50 bg-card p-4"
						>
							<div className="flex items-center justify-between">
								<p className="font-semibold text-foreground text-sm">{meta.label}</p>
								<Badge variant={meta.present ? "default" : "destructive"}>
									{meta.present ? "Configured" : "Missing"}
								</Badge>
							</div>
							<p className="text-muted-foreground text-xs">{meta.description}</p>
							<div className="space-y-2 text-muted-foreground text-xs">
								<div>
									<p className="font-semibold text-[11px] text-muted-foreground uppercase tracking-wider">
										Required
									</p>
									<div className="mt-1 flex flex-wrap gap-2">
										{meta.missing.length ? (
											meta.missing.map((tag) => (
												<Badge key={`${meta.label}-${tag}`} variant="outline">
													{tag}
												</Badge>
											))
										) : (
											<span className="text-[11px] text-muted-foreground/70">None missing</span>
										)}
									</div>
								</div>
								<div>
									<p className="font-semibold text-[11px] text-muted-foreground uppercase tracking-wider">
										Recommended
									</p>
									<div className="mt-1 flex flex-wrap gap-2">
										{meta.recommended.length ? (
											meta.recommended.map((tag) => (
												<Badge key={`${meta.label}-rec-${tag}`} variant="outline">
													{tag}
												</Badge>
											))
										) : (
											<span className="text-[11px] text-muted-foreground/70">All filled</span>
										)}
									</div>
								</div>
							</div>
						</div>
					))}
				</div>
			</section>

			<section className="space-y-4">
				<div className="flex items-center gap-2">
					<Layers className="h-4 w-4 text-primary" />
					<h3 className="font-medium text-muted-foreground text-sm uppercase tracking-wider">
						Platform Compatibility
					</h3>
				</div>
				<p className="text-muted-foreground text-sm">
					Each card shows how ready a platform is to render the correct preview. Prioritize the
					networks that drive most of your referrals so those scores stay in the optimal range.
				</p>
				<div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
					{platformEntries.map(([platform, info]) => (
						<div key={platform} className="rounded-xl border border-border/50 bg-card p-4">
							<div className="flex items-center justify-between">
								<p className="font-medium text-sm capitalize">{platform}</p>
								<span
									className={`rounded-full border px-2 py-0.5 text-[10px] ${PLATFORM_BADGES[info.status] || PLATFORM_BADGES.poor}`}
								>
									{PLATFORM_LABELS[info.status] || "Unknown"}
								</span>
							</div>
							<p className="text-muted-foreground text-xs">Score {info.score}/100</p>
							<div className="mt-3 space-y-1 text-muted-foreground text-xs">
								{info.issues.length ? (
									info.issues.map((issue) => (
										<p key={`${platform}-${issue}`} className="text-muted-foreground/70">
											• {issue}
										</p>
									))
								) : (
									<p className="text-muted-foreground/70">No platform issues detected</p>
								)}
							</div>
						</div>
					))}
				</div>
			</section>

			<section className="space-y-4">
				<div className="flex items-center gap-2">
					<Camera className="h-4 w-4 text-primary" />
					<h3 className="font-medium text-muted-foreground text-sm uppercase tracking-wider">
						Social Images
					</h3>
				</div>
				<p className="text-muted-foreground text-sm">
					Verified image dimensions and alt copy keep previews looking polished. Platforms penalize
					missing attributes with blurry or missing thumbnails.
				</p>
				<div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
					{images.length ? (
						images.map((image) => (
							<div
								key={image.url}
								className="flex flex-col gap-2 rounded-xl border border-border/50 bg-card p-4"
							>
								<div className="h-36 w-full overflow-hidden rounded-lg bg-muted/20">
									<img
										src={image.url}
										alt={image.alt || image.source}
										className="h-full w-full object-cover"
										loading="lazy"
									/>
								</div>
								<div className="space-y-1 text-muted-foreground text-xs">
									<p className="font-semibold text-[11px] text-foreground">{image.source}</p>
									<p>
										{image.width ?? "?"} × {image.height ?? "?"} px
									</p>
									{image.alt && <p className="text-muted-foreground/70">Alt: {image.alt}</p>}
									{image.type && <p className="text-muted-foreground/70">Type: {image.type}</p>}
								</div>
							</div>
						))
					) : (
						<div className="rounded-xl border border-border/50 bg-card p-6 text-center text-muted-foreground text-sm">
							No sharing images detected. Add a 1200 x 630 px graphic with alt text for the best
							fidelity.
						</div>
					)}
				</div>
			</section>

			<section className="space-y-4">
				<div className="flex items-center gap-2">
					<Sparkles className="h-4 w-4 text-primary" />
					<h3 className="font-medium text-muted-foreground text-sm uppercase tracking-wider">
						AI Recommendations
					</h3>
				</div>
				<p className="text-muted-foreground text-sm">
					These tailored insights explain how to fix the gaps that hurt trust and visibility. Follow
					the actions in priority order to accelerate the lift in all networks.
				</p>
				<div className="grid gap-4 lg:grid-cols-2">
					<div className="space-y-2 rounded-xl border border-border/50 bg-card p-4">
						<p className="font-semibold text-foreground text-sm">Summary</p>
						<p className="text-muted-foreground text-sm">
							{recommendations.summary || "No AI summary available."}
						</p>
					</div>
					<div className="space-y-2 rounded-xl border border-border/50 bg-card p-4">
						<p className="font-semibold text-foreground text-sm">Best Practices</p>
						{recommendations.best_practices.length ? (
							<ul className="space-y-2 text-muted-foreground text-sm">
								{recommendations.best_practices.map((practice, index) => (
									<li key={`${practice}-${index}`}>• {practice}</li>
								))}
							</ul>
						) : (
							<p className="text-muted-foreground/70 text-sm">No best practices returned.</p>
						)}
					</div>
				</div>
				<div className="space-y-3">
					{improvementList.map((improvement, index) => (
						<div
							key={`${improvement.issue}-${index}`}
							className="space-y-2 rounded-xl border border-border/50 bg-muted/20 p-4"
						>
							<div className="flex items-center justify-between">
								<Badge variant={PRIORITY_BADGE[improvement.priority] || "default"}>
									{improvement.priority.toUpperCase()}
								</Badge>
								<span className="text-[11px] text-muted-foreground uppercase tracking-wider">
									{improvement.category.replace(/_/g, " ")}
								</span>
							</div>
							<p className="font-semibold text-foreground text-sm">{improvement.issue}</p>
							<p className="text-muted-foreground text-sm">{improvement.action}</p>
							<p className="text-muted-foreground/70 text-xs">Impact: {improvement.impact}</p>
						</div>
					))}
				</div>
				<div className="grid gap-4 lg:grid-cols-2">
					{Object.entries(sampleTags).map(([group, tags]) => (
						<div key={group} className="space-y-2 rounded-xl border border-border/50 bg-card p-4">
							<p className="font-semibold text-muted-foreground text-xs uppercase tracking-wider">
								Sample {group.replace(/_/g, " ")}
							</p>
							{tags.length ? (
								<div className="space-y-1 text-[11px] text-muted-foreground">
									{tags.map((tag) => (
										<pre
											key={tag}
											className="m-0 overflow-auto text-[11px] text-muted-foreground leading-snug"
										>
											{tag}
										</pre>
									))}
								</div>
							) : (
								<p className="text-muted-foreground/70 text-xs">None provided</p>
							)}
						</div>
					))}
				</div>
			</section>
		</div>
	)
}
