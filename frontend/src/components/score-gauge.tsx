"use client"

import {
	RadialBarChart,
	RadialBar,
	ResponsiveContainer,
	PolarAngleAxis,
} from "recharts"

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

	const data = [
		{
			name: label,
			value: score,
			fill: color,
		},
	]

	const sizeClasses = {
		sm: "h-24 w-24",
		md: "h-32 w-32",
		lg: "h-40 w-40",
	}

	const textSizes = {
		sm: "text-lg",
		md: "text-2xl",
		lg: "text-3xl",
	}

	const labelSizes = {
		sm: "text-[10px]",
		md: "text-xs",
		lg: "text-sm",
	}

	return (
		<div className={`relative ${sizeClasses[size]}`}>
			<ResponsiveContainer width="100%" height="100%">
				<RadialBarChart
					cx="50%"
					cy="50%"
					innerRadius="70%"
					outerRadius="100%"
					barSize={size === "sm" ? 8 : size === "md" ? 10 : 12}
					data={data}
					startAngle={90}
					endAngle={-270}
				>
					<PolarAngleAxis
						type="number"
						domain={[0, 100]}
						angleAxisId={0}
						tick={false}
					/>
					<RadialBar
						background={{ fill: "hsl(var(--muted))" }}
						dataKey="value"
						cornerRadius={10}
						angleAxisId={0}
					/>
				</RadialBarChart>
			</ResponsiveContainer>
			<div className="absolute inset-0 flex flex-col items-center justify-center">
				<span className={`font-bold ${textSizes[size]}`} style={{ color }}>
					{score}
				</span>
				<span
					className={`text-muted-foreground ${labelSizes[size]} max-w-[80%] truncate text-center`}
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
