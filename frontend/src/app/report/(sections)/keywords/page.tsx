"use client"

import { Tags, TrendingUp } from "lucide-react"
import { FileGenerator } from "@/components/file-generator"
import { AwaitingAnalysis } from "../../awaiting-analysis"
import { useReportContext } from "../../report-context"

export default function KeywordsPage() {
	const { analysis, aiIndexing, metadataForFiles, contentForFiles } = useReportContext()

	if (!analysis) return <AwaitingAnalysis />

	const keywords = analysis.content?.keywords_frequency ?? []
	const topKeywords = keywords.slice(0, 16)
	const maxCount = Math.max(...topKeywords.map((k) => k.count), 1)

	return (
		<div className="space-y-6">
			{/* Keywords Section */}
			<section className="space-y-4">
				<div className="flex items-center gap-2">
					<Tags className="h-4 w-4 text-primary" />
					<h2 className="font-medium text-muted-foreground text-sm uppercase tracking-wider">
						Top Keywords
					</h2>
				</div>

				<div className="overflow-hidden rounded-xl border border-border/50 bg-card">
					{topKeywords.length === 0 ? (
						<p className="py-8 text-center text-muted-foreground text-sm">No keywords detected.</p>
					) : (
						<div className="divide-y divide-border/30">
							{topKeywords.map((keyword, index) => {
								const percentage = (keyword.count / maxCount) * 100
								return (
									<div
										key={keyword.keyword}
										className="relative flex items-center justify-between px-4 py-3 transition-colors hover:bg-muted/30 sm:px-6"
									>
										{/* Background bar */}
										<div
											className="absolute inset-y-0 left-0 bg-primary/5 transition-all duration-300"
											style={{ width: `${percentage}%` }}
										/>

										<div className="relative flex items-center gap-3">
											<span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-muted font-medium text-muted-foreground text-xs">
												{index + 1}
											</span>
											<span className="font-medium text-foreground text-sm">{keyword.keyword}</span>
										</div>

										<div className="relative flex items-center gap-2">
											<TrendingUp className="h-3 w-3 text-muted-foreground" />
											<span className="font-medium text-foreground text-sm tabular-nums">
												{keyword.count}
											</span>
										</div>
									</div>
								)
							})}
						</div>
					)}
				</div>

				{keywords.length > 16 && (
					<p className="text-center text-muted-foreground text-xs">
						Showing top 16 of {keywords.length} keywords
					</p>
				)}
			</section>

			{/* File Generator */}
			<FileGenerator
				url={analysis.url ?? ""}
				report={analysis}
				aiIndexing={aiIndexing}
				metadata={metadataForFiles}
				content={contentForFiles}
			/>
		</div>
	)
}
