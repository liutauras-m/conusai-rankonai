"use client"

import { Bot, AlertTriangle, Layers, ChevronDown } from "lucide-react"

// Map bot names to user-friendly names and icons
const BOT_INFO: Record<string, { name: string; platform: string; importance: "high" | "medium" | "low" }> = {
	GPTBot: { name: "ChatGPT", platform: "OpenAI", importance: "high" },
	"OAI-SearchBot": { name: "ChatGPT Search", platform: "OpenAI", importance: "high" },
	"ChatGPT-User": { name: "ChatGPT Browsing", platform: "OpenAI", importance: "high" },
	ClaudeBot: { name: "Claude", platform: "Anthropic", importance: "high" },
	"Claude-Web": { name: "Claude Web", platform: "Anthropic", importance: "high" },
	"anthropic-ai": { name: "Anthropic AI", platform: "Anthropic", importance: "medium" },
	"Google-Extended": { name: "Gemini", platform: "Google", importance: "high" },
	GoogleOther: { name: "Google AI", platform: "Google", importance: "medium" },
	PerplexityBot: { name: "Perplexity", platform: "Perplexity", importance: "high" },
	Bytespider: { name: "ByteDance", platform: "TikTok", importance: "low" },
	CCBot: { name: "Common Crawl", platform: "AI Training", importance: "medium" },
	Amazonbot: { name: "Alexa/Amazon", platform: "Amazon", importance: "medium" },
	"Applebot-Extended": { name: "Siri/Apple AI", platform: "Apple", importance: "high" },
	"cohere-ai": { name: "Cohere", platform: "Cohere", importance: "medium" },
	Diffbot: { name: "Diffbot", platform: "Diffbot", importance: "low" },
	FacebookBot: { name: "Meta AI", platform: "Meta", importance: "medium" },
	"Meta-ExternalAgent": { name: "Meta Agent", platform: "Meta", importance: "medium" },
	omgili: { name: "Webz.io", platform: "Data", importance: "low" },
	Timpibot: { name: "Timpi", platform: "Search", importance: "low" },
}

interface AIBotStatusProps {
	botStatus: Record<string, string>
}

function getStatusDisplay(status: string): { allowed: boolean } {
	return {
		allowed: status.toLowerCase() === "allowed" || status.toLowerCase() === "allowed_by_default"
	}
}

export function AIBotStatus({ botStatus }: AIBotStatusProps) {
	// Separate bots by importance
	const highImportance = Object.entries(botStatus).filter(
		([bot]) => BOT_INFO[bot]?.importance === "high"
	)
	const mediumImportance = Object.entries(botStatus).filter(
		([bot]) => BOT_INFO[bot]?.importance === "medium"
	)
	const otherBots = Object.entries(botStatus).filter(
		([bot]) => !BOT_INFO[bot] || BOT_INFO[bot]?.importance === "low"
	)

	// Calculate stats
	const totalBots = Object.keys(botStatus).length
	const allowedBots = Object.values(botStatus).filter(
		(s) => s === "allowed" || s === "allowed_by_default"
	).length
	const blockedBots = Object.values(botStatus).filter((s) => s === "blocked").length

	// Check critical bots
	const criticalBots = ["GPTBot", "ClaudeBot", "PerplexityBot", "Google-Extended"]
	const criticalBlocked = criticalBots.filter((bot) => botStatus[bot] === "blocked")

	return (
		<section className="space-y-4">
			<div className="flex items-center gap-2">
				<Bot className="h-4 w-4 text-primary" />
				<h2 className="font-medium text-muted-foreground text-sm uppercase tracking-wider">AI Crawler Status</h2>
			</div>

			<div className="rounded-xl border border-border/50 bg-card p-4 sm:p-6">
				{/* Summary Stats */}
				<div className="mb-5 grid grid-cols-3 gap-3">
					<div className="rounded-lg bg-primary/5 p-3 text-center">
						<div className="font-semibold text-primary text-xl tabular-nums">
							{allowedBots}
						</div>
						<div className="text-muted-foreground text-xs">Allowed</div>
					</div>
					<div className="rounded-lg bg-destructive/5 p-3 text-center">
						<div className="font-semibold text-destructive text-xl tabular-nums">
							{blockedBots}
						</div>
						<div className="text-muted-foreground text-xs">Blocked</div>
					</div>
					<div className="rounded-lg bg-muted/50 p-3 text-center">
						<div className="font-semibold text-muted-foreground text-xl tabular-nums">{totalBots}</div>
						<div className="text-muted-foreground text-xs">Total</div>
					</div>
				</div>

				{/* Critical Alert */}
				{criticalBlocked.length > 0 && (
					<div className="mb-5 rounded-lg border border-destructive/20 bg-destructive/5 p-4">
						<p className="flex items-center gap-2 font-medium text-destructive text-sm">
							<AlertTriangle className="h-4 w-4" /> Critical crawlers blocked
						</p>
						<p className="mt-1 text-muted-foreground text-xs">
							{criticalBlocked.map((b) => BOT_INFO[b]?.name || b).join(", ")} cannot
							index your site.
						</p>
					</div>
				)}

				{/* High Importance Bots */}
				{highImportance.length > 0 && (
					<div className="mb-4">
						<h4 className="mb-3 font-medium text-muted-foreground text-xs uppercase tracking-wider">
							Major Platforms
						</h4>
						<div className="grid gap-2 sm:grid-cols-2">
							{highImportance.map(([bot, status]) => {
								const info = BOT_INFO[bot] || { name: bot, platform: "" }
								const { allowed } = getStatusDisplay(status)
								return (
									<div
										key={bot}
										className="flex items-center justify-between rounded-lg border border-border/50 bg-background p-3 transition-all duration-200 hover:border-primary/20"
									>
										<div className="flex items-center gap-2.5">
											<div className={`h-2 w-2 rounded-full ${allowed ? "bg-primary" : "bg-destructive"}`} />
											<div>
												<p className="font-medium text-foreground text-sm">{info.name}</p>
												<p className="text-muted-foreground text-xs">{info.platform}</p>
											</div>
										</div>
										<span className={`font-medium text-xs ${allowed ? "text-primary" : "text-destructive"}`}>
											{allowed ? "Allowed" : "Blocked"}
										</span>
									</div>
								)
							})}
						</div>
					</div>
				)}

				{/* Medium Importance Bots */}
				{mediumImportance.length > 0 && (
					<div className="mb-4">
						<h4 className="mb-3 flex items-center gap-2 font-medium text-muted-foreground text-xs uppercase tracking-wider">
							<Layers className="h-3 w-3" /> Other AI Services
						</h4>
						<div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
							{mediumImportance.map(([bot, status]) => {
								const info = BOT_INFO[bot] || { name: bot, platform: "" }
								const { allowed } = getStatusDisplay(status)
								return (
									<div
										key={bot}
										className="flex items-center justify-between rounded-lg border border-border/50 bg-background px-3 py-2"
									>
										<div className="flex items-center gap-2">
											<div className={`h-1.5 w-1.5 rounded-full ${allowed ? "bg-primary" : "bg-destructive"}`} />
											<span className="text-foreground text-sm">{info.name}</span>
										</div>
										<span className={`text-xs ${allowed ? "text-primary" : "text-destructive"}`}>
											{allowed ? "✓" : "✗"}
										</span>
									</div>
								)
							})}
						</div>
					</div>
				)}

				{/* Other Bots (collapsed) */}
				{otherBots.length > 0 && (
					<details className="group">
						<summary className="flex cursor-pointer items-center gap-1 text-muted-foreground text-xs transition-colors hover:text-foreground">
							<ChevronDown className="h-3 w-3 transition-transform group-open:rotate-180" />
							{otherBots.length} other crawlers
						</summary>
						<div className="mt-3 grid gap-2 sm:grid-cols-3">
							{otherBots.map(([bot, status]) => {
								const info = BOT_INFO[bot] || { name: bot, platform: "" }
								const { allowed } = getStatusDisplay(status)
								return (
									<div
										key={bot}
										className="flex items-center justify-between rounded border border-border/30 px-2.5 py-1.5 text-xs"
									>
										<span className="text-muted-foreground">{info.name}</span>
										<span className={allowed ? "text-primary" : "text-destructive"}>
											{allowed ? "✓" : "✗"}
										</span>
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
