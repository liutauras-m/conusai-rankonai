"use client"

import {
	BarChart3,
	Check,
	ChevronRight,
	Compass,
	Link2,
	Mail,
	Megaphone,
	Radio,
	Search,
	Share2,
} from "lucide-react"
import type { Route } from "next"
import Image from "next/image"
import Link from "next/link"
import { usePathname, useSearchParams } from "next/navigation"
import { Suspense, useMemo, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import {
	Sidebar,
	SidebarContent,
	SidebarFooter,
	SidebarGroup,
	SidebarGroupLabel,
	SidebarHeader,
	SidebarInset,
	SidebarMenu,
	SidebarMenuButton,
	SidebarMenuItem,
	SidebarProvider,
	SidebarSeparator,
	SidebarTrigger,
} from "@/components/ui/sidebar"
import { LoadingOverlay } from "@/components/ui/spinner"
import { ReportProvider, useReportContext } from "./report-context"

const navItems = [
	{ href: "/report/overview", label: "Overview", icon: BarChart3 },
	{ href: "/report/insights", label: "Insights", icon: Compass },
	{ href: "/report/signals", label: "Signals", icon: Radio },
	{ href: "/report/keywords", label: "Keywords", icon: Search },
	{ href: "/report/marketing", label: "Marketing", icon: Megaphone },
	{ href: "/report/social", label: "Social", icon: Share2 },
]

function ReportLayoutShell({ children }: { children: React.ReactNode }) {
	const { status, formattedTimestamp, error, queryString } = useReportContext()
	const searchParams = useSearchParams()
	const pathname = usePathname()
	const [copied, setCopied] = useState(false)

	const navSuffix = useMemo(() => (queryString ? `?${queryString}` : ""), [queryString])
	const isActive = useMemo(() => {
		return (href: string) => pathname === href
	}, [pathname])

	const displayUrl = useMemo(() => {
		const url = searchParams.get("url")
		if (!url) return null
		try {
			return new URL(url.startsWith("http") ? url : `https://${url}`).hostname
		} catch {
			return url
		}
	}, [searchParams])

	const handleCopyLink = async () => {
		try {
			// Generate clean shareable URL with only 'url' param (no jobId)
			const urlParam = searchParams.get("url")
			if (urlParam) {
				const cleanParams = new URLSearchParams({ url: urlParam })
				const cleanUrl = `${window.location.origin}${window.location.pathname}?${cleanParams.toString()}`
				await navigator.clipboard.writeText(cleanUrl)
			} else {
				await navigator.clipboard.writeText(window.location.href)
			}
			setCopied(true)
			setTimeout(() => setCopied(false), 2000)
		} catch (err) {
			console.error("Failed to copy:", err)
		}
	}

	return (
		<SidebarProvider>
			<div className="flex min-h-screen bg-background text-foreground">
				<Sidebar
					side="left"
					variant="inset"
					collapsible="icon"
					className="border-border/50 border-r"
				>
					<SidebarHeader className="p-4">
						<Link href="/" className="group flex items-center gap-2">
							<div className="flex h-8 w-8 shrink-0 items-center justify-center">
								<Image
									src="/favicon.png"
									alt="Rank on AI"
									width={32}
									height={32}
									className="h-8 w-8"
								/>
							</div>
							<span className="font-semibold text-sm tracking-tight group-data-[collapsible=icon]:hidden">
								Rank on AI
							</span>
						</Link>
					</SidebarHeader>
					<SidebarSeparator />
					<SidebarContent className="px-2">
						<SidebarGroup>
							<SidebarGroupLabel className="px-2 text-[10px] uppercase tracking-widest group-data-[collapsible=icon]:hidden">
								Report
							</SidebarGroupLabel>
							<SidebarMenu className="space-y-1">
								{navItems.map((item) => {
									const href = `${item.href}${navSuffix}`
									const Icon = item.icon
									const active = isActive(item.href)
									return (
										<SidebarMenuItem key={item.href}>
											<SidebarMenuButton
												asChild
												size="default"
												isActive={active}
												className={`group rounded-lg transition-all duration-200 ${active ? "bg-primary/10 text-primary" : "hover:bg-muted"}`}
											>
												<Link
													href={href as Route}
													className="flex items-center gap-3 px-3 py-2.5 group-data-[collapsible=icon]:justify-center group-data-[collapsible=icon]:px-2"
												>
													<Icon
														className={`h-4 w-4 shrink-0 transition-colors ${active ? "text-primary" : "text-muted-foreground group-hover:text-foreground"}`}
													/>
													<span className="flex-1 font-medium text-sm group-data-[collapsible=icon]:hidden">
														{item.label}
													</span>
													{active && (
														<ChevronRight className="h-3 w-3 text-primary/60 group-data-[collapsible=icon]:hidden" />
													)}
												</Link>
											</SidebarMenuButton>
										</SidebarMenuItem>
									)
								})}
							</SidebarMenu>
						</SidebarGroup>
					</SidebarContent>
					<SidebarFooter className="border-border/50 border-t p-4">
						<a
							href="https://www.conusai.com/#contact-form"
							target="_blank"
							rel="noopener noreferrer"
							className="flex items-center gap-2 rounded-lg px-3 py-2 text-muted-foreground text-sm transition-colors hover:bg-muted hover:text-foreground group-data-[collapsible=icon]:justify-center group-data-[collapsible=icon]:px-2"
						>
							<Mail className="h-4 w-4 shrink-0" />
							<span className="group-data-[collapsible=icon]:hidden">Contact Us</span>
						</a>
						<a
							href="/docs/terms-and-conditions.md"
							target="_blank"
							rel="noopener noreferrer"
							className="flex items-center gap-2 rounded-lg px-3 py-2 text-muted-foreground/70 text-xs transition-colors hover:bg-muted hover:text-foreground group-data-[collapsible=icon]:justify-center group-data-[collapsible=icon]:px-2"
						>
							<span className="group-data-[collapsible=icon]:hidden">Terms & Conditions</span>
						</a>
						<SidebarSeparator className="my-2 group-data-[collapsible=icon]:hidden" />
						<div className="space-y-1 group-data-[collapsible=icon]:hidden">
							<div className="flex items-center gap-2">
								<div
									className={`h-1.5 w-1.5 rounded-full ${status === "success" ? "bg-emerald-500" : status === "loading" ? "animate-pulse bg-amber-500" : "bg-muted-foreground"}`}
								/>
								<p className="text-muted-foreground text-xs capitalize">{status}</p>
							</div>
							<p className="text-[10px] text-muted-foreground/70">{formattedTimestamp}</p>
						</div>
						<SidebarTrigger className="mt-3 group-data-[collapsible=icon]:mt-0" />
					</SidebarFooter>
				</Sidebar>

				<SidebarInset className="flex-1">
					{status === "loading" && <LoadingOverlay message="Analyzing..." />}
					<div className="flex flex-col gap-4 p-4 sm:gap-6 sm:p-6 lg:p-8">
						{/* Header */}
						<header className="space-y-1">
							<p className="font-medium text-[10px] text-muted-foreground uppercase tracking-[0.2em]">
								AI Visibility Report
							</p>
							<h1 className="font-semibold text-xl tracking-tight sm:text-2xl lg:text-3xl">
								{displayUrl ? (
									<span className="flex flex-wrap items-center gap-2">
										<span className="text-foreground">{displayUrl}</span>
										<button
											type="button"
											onClick={handleCopyLink}
											className="inline-flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
											title={copied ? "Copied!" : "Copy link to share"}
										>
											{copied ? (
												<Check className="h-4 w-4 text-green-500" />
											) : (
												<Link2 className="h-4 w-4" />
											)}
										</button>
									</span>
								) : (
									"Enter a URL to begin"
								)}
							</h1>
						</header>

						{error && (
							<Card className="border-destructive/30 bg-destructive/5">
								<CardHeader className="pb-2">
									<CardTitle className="font-medium text-destructive text-sm">Error</CardTitle>
								</CardHeader>
								<CardContent>
									<p className="text-destructive/90 text-sm">{error}</p>
								</CardContent>
							</Card>
						)}

						<Separator className="bg-border/50" />

						<main className="fade-in slide-in-from-bottom-4 animate-in duration-300">
							{children}
						</main>
					</div>
				</SidebarInset>
			</div>
		</SidebarProvider>
	)
}

export default function ReportLayout({ children }: { children: React.ReactNode }) {
	return (
		<Suspense
			fallback={
				<div className="flex h-screen items-center justify-center bg-background">
					<LoadingOverlay message="Loading..." />
				</div>
			}
		>
			<ReportProvider>
				<ReportLayoutShell>{children}</ReportLayoutShell>
			</ReportProvider>
		</Suspense>
	)
}
