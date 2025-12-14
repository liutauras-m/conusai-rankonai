"use client"

import Image from "next/image"
import { useMemo, useState } from "react"

type PlatformLogo = {
	name: string
	logo?: {
		light?: string
		dark?: string
		src?: string
		alt?: string
	}
}

const DEFAULT_PLATFORMS: PlatformLogo[] = [
	{
		name: "ChatGPT",
		logo: {
			src: "/logos/platforms/chatgpt.png",
			alt: "ChatGPT",
		},
	},
	{
		name: "Perplexity",
		logo: {
			src: "/logos/platforms/perplexity.ico",
			alt: "Perplexity",
		},
	},
	{
		name: "Claude",
		logo: {
			src: "/logos/platforms/claude.png",
			alt: "Claude (Anthropic)",
		},
	},
	{
		name: "Gemini",
		logo: {
			src: "/logos/platforms/gemini.png",
			alt: "Gemini (Google)",
		},
	},
	{
		name: "Grok",
		logo: {
			src: "/logos/platforms/grok.png",
			alt: "Grok (xAI)",
		},
	},
	{
		name: "Microsoft Copilot",
		logo: {
			src: "/logos/platforms/microsoft-copilot.svg",
			alt: "Microsoft Copilot",
		},
	},
	{
		name: "Mistral",
		logo: {
			src: "/logos/platforms/mistral.png",
			alt: "Mistral",
		},
	},
	{
		name: "Cohere",
		logo: {
			src: "/logos/platforms/cohere.png",
			alt: "Cohere",
		},
	},
	{
		name: "DeepSeek",
		logo: {
			src: "/logos/platforms/deepseek.ico",
			alt: "DeepSeek",
		},
	},
]

export function AIPlatformLogos({
	platforms = DEFAULT_PLATFORMS,
	className,
}: {
	platforms?: PlatformLogo[]
	className?: string
}) {
	const [failed, setFailed] = useState<Record<string, boolean>>({})

	const safePlatforms = useMemo(() => {
		return platforms.map((p) => ({
			...p,
			logo: p.logo
				? {
					...p.logo,
					src: p.logo.src || undefined,
					alt: p.logo.alt || p.name,
				}
				: undefined,
		}))
	}, [platforms])

	return (
		<section className={className} aria-label="Supported AI platforms">
			<div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-3">
				{safePlatforms.map((platform) => {
					if (failed[platform.name]) {
						return (
							<span
								key={platform.name}
								className="rounded-full bg-muted px-3 py-1.5 text-muted-foreground text-sm"
							>
								{platform.name}
							</span>
						)
					}

					const hasLogos =
						!!platform.logo?.src || !!platform.logo?.light || !!platform.logo?.dark
					if (!hasLogos) {
						return (
							<span
								key={platform.name}
								className="rounded-full bg-muted px-3 py-1.5 text-muted-foreground text-sm"
							>
								{platform.name}
							</span>
						)
					}

					return (
						<span
							key={platform.name}
							className="flex items-center rounded-md px-1 py-1"
							title={platform.name}
						>
							{platform.logo?.src ? (
								<Image
									src={platform.logo.src}
									alt={platform.logo.alt}
									width={28}
									height={28}
									className="h-7 w-7 opacity-90"
									onError={() =>
										setFailed((prev) => ({ ...prev, [platform.name]: true }))
									}
								/>
							) : null}
							{platform.logo?.dark ? (
								<Image
									src={platform.logo.dark}
									alt={platform.logo.alt}
									width={120}
									height={28}
									className="hidden h-6 w-auto opacity-80 dark:block"
									onError={() => setFailed((prev) => ({ ...prev, [platform.name]: true }))}
								/>
							) : null}
							{platform.logo?.light ? (
								<Image
									src={platform.logo.light}
									alt={platform.logo.alt}
									width={120}
									height={28}
									className="block h-6 w-auto opacity-80 dark:hidden"
									onError={() => setFailed((prev) => ({ ...prev, [platform.name]: true }))}
								/>
							) : null}
							{!platform.logo?.src && !platform.logo?.dark && !platform.logo?.light ? (
								<span className="text-muted-foreground text-sm">{platform.name}</span>
							) : null}
						</span>
					)
				})}
			</div>
		</section>
	)
}
