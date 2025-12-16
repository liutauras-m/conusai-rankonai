"use client"

interface ScoreGaugeProps {
	score: number
	label: string
	size?: "sm" | "md" | "lg"
}

function getScoreColor(score: number): string {
	if (score >= 80) return "oklch(0.72 0.14 142)" // forest-like green
	if (score >= 60) return "oklch(0.78 0.08 175)" // brand mint/primary
	if (score >= 40) return "oklch(0.78 0.16 75)" // brand gold
	return "oklch(0.68 0.18 25)" // brand coral/destructive
}

function getScoreLabel(score: number): string {
	if (score >= 80) return "Excellent"
	if (score >= 60) return "Good"
	if (score >= 40) return "Needs Work"
	return "Poor"
}

export function ScoreGauge({ score, label, size = "md" }: ScoreGaugeProps) {
	const color = getScoreColor(score)
	const safeScore = Math.min(100, Math.max(0, typeof score === "number" ? score : 0))

	// SVG dimensions
	const sizes = {
		sm: { width: 88, strokeWidth: 6, fontSize: 16, labelSize: 9 },
		md: { width: 120, strokeWidth: 8, fontSize: 22, labelSize: 11 },
		lg: { width: 140, strokeWidth: 10, fontSize: 28, labelSize: 12 },
	}

	const { width, strokeWidth, fontSize, labelSize } = sizes[size]
	const radius = (width - strokeWidth) / 2
	const circumference = 2 * Math.PI * radius
	const progress = (safeScore / 100) * circumference
	const offset = circumference - progress

	return (
		<div
			className="relative inline-flex items-center justify-center"
			style={{ width, height: width }}
		>
			<svg aria-hidden="true" width={width} height={width} className="-rotate-90">
				{/* Background circle */}
				<circle
					cx={width / 2}
					cy={width / 2}
					r={radius}
					fill="none"
					stroke="hsl(var(--muted))"
					strokeWidth={strokeWidth}
					opacity={0.5}
				/>
				{/* Progress circle */}
				<circle
					cx={width / 2}
					cy={width / 2}
					r={radius}
					fill="none"
					stroke={color}
					strokeWidth={strokeWidth}
					strokeLinecap="round"
					strokeDasharray={circumference}
					strokeDashoffset={offset}
					className="transition-all duration-700 ease-out"
				/>
			</svg>
			<div className="absolute inset-0 flex flex-col items-center justify-center">
				<span className="font-semibold tabular-nums" style={{ color, fontSize }}>
					{safeScore}
				</span>
				<span
					className="max-w-[80%] truncate text-center font-medium text-muted-foreground"
					style={{ fontSize: labelSize }}
				>
					{label}
				</span>
			</div>
		</div>
	)
}

interface ScoreCardProps {
	score: number
	label: string
	description?: string
}

export function ScoreCard({ score, label, description }: ScoreCardProps) {
	const color = getScoreColor(score)
	const scoreLabel = getScoreLabel(score)

	return (
		<div className="flex flex-col items-center gap-2 rounded-xl border border-border/50 bg-card p-3 transition-all duration-200 hover:border-primary/20">
			<ScoreGauge score={score} label={label} size="sm" />
			<div className="text-center">
				<p className="font-medium text-xs" style={{ color }}>
					{scoreLabel}
				</p>
				{description && (
					<p className="mt-0.5 text-[10px] text-muted-foreground leading-tight">{description}</p>
				)}
			</div>
		</div>
	)
}

interface ScoresOverviewProps {
	scores: {
		overall: number
		technical: number
		on_page: number
		content: number
		structured_data: number
		ai_readiness: number
	}
}

export function ScoresOverview({ scores }: ScoresOverviewProps) {
	return (
		<div className="grid gap-6">
			{/* Hero Score - AI Visibility */}
			<div className="flex justify-center">
				<div className="flex flex-col items-center gap-3">
					<ScoreGauge score={scores.ai_readiness} label="AI Visibility" size="lg" />
					<div className="text-center">
						<p
							className="font-medium text-sm"
							style={{ color: getScoreColor(scores.ai_readiness) }}
						>
							{getScoreLabel(scores.ai_readiness)}
						</p>
						<p className="mt-1 max-w-[200px] text-muted-foreground text-xs">
							AI assistant discoverability
						</p>
					</div>
				</div>
			</div>

			{/* Secondary Scores */}
			<div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
				<ScoreCard
					score={scores.content}
					label="Content"
					description="Clarity for AI understanding"
				/>
				<ScoreCard
					score={scores.structured_data}
					label="Rich Data"
					description="Schema markup quality"
				/>
				<ScoreCard score={scores.on_page} label="Structure" description="Headings & meta info" />
				<ScoreCard score={scores.technical} label="Technical" description="Speed & security" />
			</div>
		</div>
	)
}
