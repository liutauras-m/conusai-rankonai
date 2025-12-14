import { cn } from "@/lib/utils"

interface SpinnerProps {
	size?: "sm" | "md" | "lg"
	className?: string
}

export function Spinner({ size = "md", className }: SpinnerProps) {
	const sizeClasses = {
		sm: "h-4 w-4 border-2",
		md: "h-8 w-8 border-2",
		lg: "h-12 w-12 border-3",
	}

	return (
		<div
			className={cn(
				"animate-spin rounded-full border-muted-foreground/30 border-t-[#80CDC6]",
				sizeClasses[size],
				className
			)}
		/>
	)
}

interface LoadingOverlayProps {
	message?: string
}

export function LoadingOverlay({
	message = "Analysing...",
}: LoadingOverlayProps) {
	return (
		<div className="fixed inset-0 z-50 flex flex-col items-center justify-center gap-4 bg-background/80 backdrop-blur-sm">
			<Spinner size="lg" />
			<p className="font-medium text-lg text-muted-foreground">{message}</p>
			<p className="text-muted-foreground/70 text-sm">
				This may take up to 30 seconds
			</p>
		</div>
	)
}
