"use client"

import { useEffect, useRef, useState } from "react"

declare global {
	interface Window {
		turnstile?: {
			render: (
				container: HTMLElement,
				options: {
					sitekey: string
					callback: (token: string) => void
					"error-callback"?: () => void
					"expired-callback"?: () => void
					theme?: "light" | "dark" | "auto"
					size?: "normal" | "compact"
				}
			) => string
			reset: (widgetId: string) => void
			remove: (widgetId: string) => void
		}
	}
}

interface TurnstileProps {
	siteKey: string
	onVerify: (token: string) => void
	onError?: () => void
	onExpire?: () => void
	theme?: "light" | "dark" | "auto"
	size?: "normal" | "compact"
	className?: string
}

export function Turnstile({
	siteKey,
	onVerify,
	onError,
	onExpire,
	theme = "auto",
	size = "normal",
	className,
}: TurnstileProps) {
	const containerRef = useRef<HTMLDivElement>(null)
	const widgetIdRef = useRef<string | null>(null)
	const [isLoaded, setIsLoaded] = useState(false)

	useEffect(() => {
		// Load Turnstile script
		if (!document.getElementById("turnstile-script")) {
			const script = document.createElement("script")
			script.id = "turnstile-script"
			script.src = "https://challenges.cloudflare.com/turnstile/v0/api.js"
			script.async = true
			script.onload = () => setIsLoaded(true)
			document.head.appendChild(script)
		} else if (window.turnstile) {
			setIsLoaded(true)
		}

		return () => {
			// Cleanup widget on unmount
			if (widgetIdRef.current && window.turnstile) {
				window.turnstile.remove(widgetIdRef.current)
			}
		}
	}, [])

	useEffect(() => {
		if (!isLoaded || !containerRef.current || !window.turnstile) return

		// Remove existing widget if any
		if (widgetIdRef.current) {
			window.turnstile.remove(widgetIdRef.current)
		}

		// Render new widget
		widgetIdRef.current = window.turnstile.render(containerRef.current, {
			sitekey: siteKey,
			callback: onVerify,
			"error-callback": onError,
			"expired-callback": onExpire,
			theme,
			size,
		})
	}, [isLoaded, siteKey, onVerify, onError, onExpire, theme, size])

	return <div ref={containerRef} className={className} />
}

export function resetTurnstile(widgetId: string) {
	if (window.turnstile) {
		window.turnstile.reset(widgetId)
	}
}
