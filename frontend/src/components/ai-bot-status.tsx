"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

// Map bot names to user-friendly names and icons
const BOT_INFO: Record<string, { name: string; platform: string; icon: string; importance: "high" | "medium" | "low" }> = {
	GPTBot: { name: "ChatGPT", platform: "OpenAI", icon: "🤖", importance: "high" },
	"OAI-SearchBot": { name: "ChatGPT Search", platform: "OpenAI", icon: "🔎", importance: "high" },
	"ChatGPT-User": { name: "ChatGPT Browsing", platform: "OpenAI", icon: "💬", importance: "high" },
	ClaudeBot: { name: "Claude", platform: "Anthropic", icon: "🧠", importance: "high" },
	"Claude-Web": { name: "Claude Web", platform: "Anthropic", icon: "🌐", importance: "high" },
	"anthropic-ai": { name: "Anthropic AI", platform: "Anthropic", icon: "🔬", importance: "medium" },
	"Google-Extended": { name: "Gemini", platform: "Google", icon: "✨", importance: "high" },
	GoogleOther: { name: "Google AI", platform: "Google", icon: "🔍", importance: "medium" },
	PerplexityBot: { name: "Perplexity", platform: "Perplexity", icon: "🎯", importance: "high" },
	Bytespider: { name: "ByteDance", platform: "TikTok", icon: "📱", importance: "low" },
	CCBot: { name: "Common Crawl", platform: "AI Training", icon: "📚", importance: "medium" },
	Amazonbot: { name: "Alexa/Amazon", platform: "Amazon", icon: "🛒", importance: "medium" },
	"Applebot-Extended": { name: "Siri/Apple AI", platform: "Apple", icon: "🍎", importance: "high" },
	"cohere-ai": { name: "Cohere", platform: "Cohere", icon: "🔮", importance: "medium" },
	Diffbot: { name: "Diffbot", platform: "Diffbot", icon: "🕸️", importance: "low" },
	FacebookBot: { name: "Meta AI", platform: "Meta", icon: "📘", importance: "medium" },
	"Meta-ExternalAgent": { name: "Meta Agent", platform: "Meta", icon: "🤳", importance: "medium" },
	omgili: { name: "Webz.io", platform: "Data", icon: "📊", importance: "low" },
	Timpibot: { name: "Timpi", platform: "Search", icon: "🔎", importance: "low" },
}

interface AIBotStatusProps {
	botStatus: Record<string, string>
}

function getStatusDisplay(status: string): { label: string; color: string; bgColor: string } {
	switch (status.toLowerCase()) {
		case "allowed":
			return {
				label: "Can find you ✓",
				color: "text-green-600 dark:text-green-400",
				bgColor: "bg-green-500/10",
			}
		case "blocked":
			return {
				label: "Blocked ✗",
				color: "text-red-600 dark:text-red-400",
				bgColor: "bg-red-500/10",
			}
		case "allowed_by_default":
			return {
				label: "Allowed (default)",
				color: "text-blue-600 dark:text-blue-400",
				bgColor: "bg-blue-500/10",
			}
		default:
			return {
				label: status,
				color: "text-muted-foreground",
				bgColor: "bg-muted",
			}
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
		<Card>
			<CardHeader>
				<CardTitle className="flex items-center gap-2">
					<span className="text-xl">🤖</span>
					AI Search Crawlers
				</CardTitle>
				<CardDescription>
					Which AI assistants can discover and recommend your site
				</CardDescription>
			</CardHeader>
			<CardContent>
				{/* Summary Stats */}
				<div className="mb-6 grid grid-cols-3 gap-4 rounded-lg bg-muted/50 p-4">
					<div className="text-center">
						<div className="text-2xl font-bold text-green-600 dark:text-green-400">
							{allowedBots}
						</div>
						<div className="text-xs text-muted-foreground">Can find you</div>
					</div>
					<div className="text-center">
						<div className="text-2xl font-bold text-red-600 dark:text-red-400">
							{blockedBots}
						</div>
						<div className="text-xs text-muted-foreground">Blocked</div>
					</div>
					<div className="text-center">
						<div className="text-2xl font-bold text-muted-foreground">{totalBots}</div>
						<div className="text-xs text-muted-foreground">Total checked</div>
					</div>
				</div>

				{/* Critical Alert */}
				{criticalBlocked.length > 0 && (
					<div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800/50 dark:bg-red-900/20">
						<p className="font-medium text-red-800 dark:text-red-200">
							⚠️ Important AI crawlers are blocked
						</p>
						<p className="mt-1 text-sm text-red-700 dark:text-red-300">
							{criticalBlocked.map((b) => BOT_INFO[b]?.name || b).join(", ")} cannot
							index your site. This may prevent your brand from appearing in AI search
							results.
						</p>
					</div>
				)}

				{/* High Importance Bots */}
				{highImportance.length > 0 && (
					<div className="mb-6">
						<h4 className="mb-3 text-sm font-medium text-foreground">
							🌟 Major AI Platforms
						</h4>
						<div className="grid gap-2 sm:grid-cols-2">
							{highImportance.map(([bot, status]) => {
								const info = BOT_INFO[bot] || { name: bot, platform: "", icon: "🤖" }
								const statusDisplay = getStatusDisplay(status)
								return (
									<div
										key={bot}
										className="flex items-center justify-between rounded-lg border border-border p-3"
									>
										<div className="flex items-center gap-2">
											<span className="text-lg">{info.icon}</span>
											<div>
												<p className="font-medium text-foreground">{info.name}</p>
												<p className="text-xs text-muted-foreground">{info.platform}</p>
											</div>
										</div>
										<span
											className={`rounded-full px-2 py-0.5 text-xs font-medium ${statusDisplay.bgColor} ${statusDisplay.color}`}
										>
											{statusDisplay.label}
										</span>
									</div>
								)
							})}
						</div>
					</div>
				)}

				{/* Medium Importance Bots */}
				{mediumImportance.length > 0 && (
					<div className="mb-6">
						<h4 className="mb-3 text-sm font-medium text-foreground">
							📊 Other AI Services
						</h4>
						<div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
							{mediumImportance.map(([bot, status]) => {
								const info = BOT_INFO[bot] || { name: bot, platform: "", icon: "🤖" }
								const statusDisplay = getStatusDisplay(status)
								return (
									<div
										key={bot}
										className="flex items-center justify-between rounded-lg border border-border p-2"
									>
										<div className="flex items-center gap-2">
											<span>{info.icon}</span>
											<span className="text-sm text-foreground">{info.name}</span>
										</div>
										<span
											className={`rounded-full px-2 py-0.5 text-xs font-medium ${statusDisplay.bgColor} ${statusDisplay.color}`}
										>
											{status === "allowed" || status === "allowed_by_default"
												? "✓"
												: "✗"}
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
						<summary className="cursor-pointer text-sm text-muted-foreground hover:text-foreground">
							Show {otherBots.length} other crawlers
						</summary>
						<div className="mt-3 grid gap-2 sm:grid-cols-3">
							{otherBots.map(([bot, status]) => {
								const info = BOT_INFO[bot] || { name: bot, platform: "", icon: "🤖" }
								return (
									<div
										key={bot}
										className="flex items-center justify-between rounded border border-border p-2 text-sm"
									>
										<span className="text-muted-foreground">{info.name}</span>
										<span
											className={
												status === "allowed" || status === "allowed_by_default"
													? "text-green-600 dark:text-green-400"
													: "text-red-600 dark:text-red-400"
											}
										>
											{status === "allowed" || status === "allowed_by_default"
												? "✓"
												: "✗"}
										</span>
									</div>
								)
							})}
						</div>
					</details>
				)}
			</CardContent>
		</Card>
	)
}
