"use client"

interface ScoreGaugeProps {
	score: number
	label: string
	size?: "sm" | "md" | "lg"
}

function getScoreColor(score: number): string {
	if (score >= 80) return "#22c55e" // green
	if (score >= 60) return "#80CDC6" // brand mint
	if (score >= 40) return "#eab308" // yellow
	return "#ef4444" // red
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
		sm: { width: 96, strokeWidth: 8, fontSize: 18, labelSize: 10 },
		md: { width: 128, strokeWidth: 10, fontSize: 24, labelSize: 12 },
		lg: { width: 160, strokeWidth: 12, fontSize: 30, labelSize: 14 },
	}
	
	const { width, strokeWidth, fontSize, labelSize } = sizes[size]
	const radius = (width - strokeWidth) / 2
	const circumference = 2 * Math.PI * radius
	const progress = (safeScore / 100) * circumference
	const offset = circumference - progress

	return (
		<div className="relative inline-flex items-center justify-center" style={{ width, height: width }}>
			<svg
				width={width}
				height={width}
				className="-rotate-90"
			>
				{/* Background circle */}
				<circle
					cx={width / 2}
					cy={width / 2}
					r={radius}
					fill="none"
					stroke="hsl(var(--muted))"
					strokeWidth={strokeWidth}
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
					className="transition-all duration-500 ease-out"
				/>
			</svg>
			<div className="absolute inset-0 flex flex-col items-center justify-center">
				<span className="font-bold" style={{ color, fontSize }}>
					{safeScore}
				</span>
				<span
					className="text-muted-foreground text-center max-w-[80%] truncate"
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
		<div className="flex flex-col items-center gap-2 rounded-lg border bg-card p-4">
			<ScoreGauge score={score} label={label} size="sm" />
			<div className="text-center">
				<p className="text-sm font-medium" style={{ color }}>
					{scoreLabel}
				</p>
				{description && (
					<p className="mt-1 text-xs text-muted-foreground">{description}</p>
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
		<div className="grid gap-4">
			<div className="flex justify-center">
				<div className="flex flex-col items-center gap-2">
					<ScoreGauge score={scores.overall} label="Overall Score" size="lg" />
					<p
						className="text-sm font-medium"
						style={{ color: getScoreColor(scores.overall) }}
					>
						{getScoreLabel(scores.overall)}
					</p>
				</div>
			</div>

			<div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
				<ScoreCard
					score={scores.technical}
					label="Technical"
					description="HTTPS, headers, speed"
				/>
				<ScoreCard
					score={scores.on_page}
					label="On-Page"
					description="Meta tags, headings"
				/>
				<ScoreCard
					score={scores.content}
					label="Content"
					description="Word count, readability"
				/>
				<ScoreCard
					score={scores.structured_data}
					label="Schema"
					description="JSON-LD, Open Graph"
				/>
				<ScoreCard
					score={scores.ai_readiness}
					label="AI Ready"
					description="llms.txt, bot access"
				/>
			</div>
		</div>
	)
}
