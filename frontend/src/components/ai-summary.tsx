"use client"

import { useState, useEffect } from "react"
import Image from "next/image"
import { 
  Sparkles, 
  TrendingUp, 
  AlertCircle, 
  CheckCircle2, 
  Zap, 
  Target,
  ChevronDown,
  ChevronUp,
  Lightbulb,
  Clock,
  ArrowRight,
  Bot
} from "lucide-react"
import { Spinner } from "@/components/ui/spinner"
import { cn } from "@/lib/utils"

interface ScoreBreakdown {
  category: string
  score: number
  rating: string
  explanation: string
  improvement: string
}

interface PlatformInsight {
  platform: string
  status: string
  tip: string
  botName: string
}

interface PrioritizedAction {
  priority: number
  action: string
  impact: string
  effort: string
  category: string
}

interface AISummaryData {
  overallAssessment: {
    rating: string
    summary: string
    primaryStrength: string
    primaryWeakness: string
  }
  scoreBreakdown: ScoreBreakdown[]
  platformInsights: PlatformInsight[]
  prioritizedActions: PrioritizedAction[]
  quickWins: string[]
}

interface AISummaryProps {
  analysis: Record<string, unknown> | null
}

// Platform logo mapping
const PLATFORM_LOGOS: Record<string, string> = {
  ChatGPT: "/logos/platforms/chatgpt.png",
  Claude: "/logos/platforms/claude.png",
  Gemini: "/logos/platforms/gemini.png",
  Perplexity: "/logos/platforms/perplexity.ico",
  Copilot: "/logos/platforms/microsoft-copilot.svg",
  Mistral: "/logos/platforms/mistral.png",
}

function getRatingColor(rating: string): string {
  switch (rating.toLowerCase()) {
    case "excellent":
      return "text-green-500"
    case "good":
      return "text-blue-500"
    case "fair":
    case "needs improvement":
      return "text-amber-500"
    case "poor":
      return "text-red-500"
    default:
      return "text-muted-foreground"
  }
}

function getRatingBg(rating: string): string {
  switch (rating.toLowerCase()) {
    case "excellent":
      return "bg-green-500/10 border-green-500/20"
    case "good":
      return "bg-blue-500/10 border-blue-500/20"
    case "fair":
    case "needs improvement":
      return "bg-amber-500/10 border-amber-500/20"
    case "poor":
      return "bg-red-500/10 border-red-500/20"
    default:
      return "bg-muted/50 border-border/50"
  }
}

function getStatusIcon(status: string) {
  switch (status.toLowerCase()) {
    case "optimized":
      return <CheckCircle2 className="h-4 w-4 text-green-500" />
    case "partially optimized":
      return <AlertCircle className="h-4 w-4 text-amber-500" />
    case "needs work":
      return <AlertCircle className="h-4 w-4 text-red-500" />
    default:
      return <Bot className="h-4 w-4 text-muted-foreground" />
  }
}

function getImpactBadge(impact: string) {
  const colors = {
    high: "bg-red-500/10 text-red-600 dark:text-red-400",
    medium: "bg-amber-500/10 text-amber-600 dark:text-amber-400",
    low: "bg-green-500/10 text-green-600 dark:text-green-400",
  }
  return colors[impact.toLowerCase() as keyof typeof colors] || colors.medium
}

function getEffortBadge(effort: string) {
  const colors = {
    "quick win": "bg-green-500/10 text-green-600 dark:text-green-400",
    moderate: "bg-amber-500/10 text-amber-600 dark:text-amber-400",
    significant: "bg-red-500/10 text-red-600 dark:text-red-400",
  }
  return colors[effort.toLowerCase() as keyof typeof colors] || colors.moderate
}

export function AISummary({ analysis }: AISummaryProps) {
  const [summary, setSummary] = useState<AISummaryData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [expanded, setExpanded] = useState(true)
  const [platformsExpanded, setPlatformsExpanded] = useState(false)

  useEffect(() => {
    if (!analysis) {
      setSummary(null)
      return
    }

    const fetchSummary = async () => {
      setLoading(true)
      setError(null)

      try {
        const response = await fetch("/api/ai-summary", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ analysis }),
        })

        if (!response.ok) {
          throw new Error("Failed to generate AI summary")
        }

        const data = await response.json()
        if (data.success && data.summary) {
          setSummary(data.summary)
        } else {
          throw new Error(data.error || "Invalid response")
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load summary")
      } finally {
        setLoading(false)
      }
    }

    fetchSummary()
  }, [analysis])

  if (!analysis) return null

  if (loading) {
    return (
      <div className="rounded-xl border border-primary/20 bg-gradient-to-br from-primary/5 to-transparent p-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
            <Sparkles className="h-5 w-5 animate-pulse text-primary" />
          </div>
          <div>
            <h3 className="font-semibold text-foreground">AI Analysis</h3>
            <p className="text-muted-foreground text-sm">Generating personalized insights...</p>
          </div>
          <Spinner size="sm" className="ml-auto" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-xl border border-destructive/20 bg-destructive/5 p-4">
        <div className="flex items-center gap-2 text-destructive">
          <AlertCircle className="h-4 w-4" />
          <p className="text-sm">{error}</p>
        </div>
      </div>
    )
  }

  if (!summary) return null

  return (
    <div className="rounded-xl border border-primary/20 bg-gradient-to-br from-primary/5 via-transparent to-primary/5 overflow-hidden">
      {/* Overall Assessment Header */}
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between p-4 sm:p-6 text-left transition-colors hover:bg-primary/5"
      >
          <div className="flex items-center gap-4">
            <div className={cn(
              "flex h-12 w-12 items-center justify-center rounded-xl border",
              getRatingBg(summary.overallAssessment.rating)
            )}>
              <Target className={cn("h-6 w-6", getRatingColor(summary.overallAssessment.rating))} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-semibold text-foreground text-lg">
                  {summary.overallAssessment.rating}
                </h3>
                <span className={cn(
                  "rounded-full px-2 py-0.5 text-xs font-medium",
                  getRatingBg(summary.overallAssessment.rating),
                  getRatingColor(summary.overallAssessment.rating)
                )}>
                  AI Discoverability
                </span>
              </div>
              <p className="mt-1 text-muted-foreground text-sm line-clamp-2">
                {summary.overallAssessment.summary}
              </p>
            </div>
          </div>
          {expanded ? (
            <ChevronUp className="h-5 w-5 text-muted-foreground shrink-0" />
          ) : (
            <ChevronDown className="h-5 w-5 text-muted-foreground shrink-0" />
          )}
        </button>

        {expanded && (
          <div className="border-t border-border/50 p-4 sm:p-6 space-y-6">
            {/* Strengths & Weaknesses */}
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-lg border border-green-500/20 bg-green-500/5 p-4">
                <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
                  <CheckCircle2 className="h-4 w-4" />
                  <span className="font-medium text-sm">Primary Strength</span>
                </div>
                <p className="mt-2 text-foreground text-sm">
                  {summary.overallAssessment.primaryStrength}
                </p>
              </div>
              <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-4">
                <div className="flex items-center gap-2 text-amber-600 dark:text-amber-400">
                  <TrendingUp className="h-4 w-4" />
                  <span className="font-medium text-sm">Key Improvement</span>
                </div>
                <p className="mt-2 text-foreground text-sm">
                  {summary.overallAssessment.primaryWeakness}
                </p>
              </div>
            </div>

            {/* Score Breakdown */}
            <div>
              <h4 className="mb-3 font-medium text-foreground text-sm flex items-center gap-2">
                <Target className="h-4 w-4 text-primary" />
                Score Breakdown
              </h4>
              <div className="grid gap-2">
                {summary.scoreBreakdown.map((score) => (
                  <div
                    key={score.category}
                    className="group rounded-lg border border-border/50 bg-background p-3 transition-all hover:border-primary/20"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={cn(
                          "flex h-8 w-8 items-center justify-center rounded-lg text-sm font-bold",
                          getRatingBg(score.rating),
                          getRatingColor(score.rating)
                        )}>
                          {score.score}
                        </div>
                        <div>
                          <p className="font-medium text-foreground text-sm">{score.category}</p>
                          <p className="text-muted-foreground text-xs">{score.explanation}</p>
                        </div>
                      </div>
                      <span className={cn(
                        "rounded-full px-2 py-0.5 text-xs font-medium hidden sm:block",
                        getRatingBg(score.rating),
                        getRatingColor(score.rating)
                      )}>
                        {score.rating}
                      </span>
                    </div>
                    <div className="mt-2 flex items-start gap-2 rounded-md bg-muted/30 p-2">
                      <Lightbulb className="h-3.5 w-3.5 text-primary mt-0.5 shrink-0" />
                      <p className="text-muted-foreground text-xs">{score.improvement}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Platform Insights */}
            <div>
              <button
                type="button"
                onClick={() => setPlatformsExpanded(!platformsExpanded)}
                className="mb-3 flex w-full items-center justify-between"
              >
                <h4 className="font-medium text-foreground text-sm flex items-center gap-2">
                  <Bot className="h-4 w-4 text-primary" />
                  AI Platform Status
                </h4>
                <span className="text-muted-foreground text-xs flex items-center gap-1">
                  {platformsExpanded ? "Collapse" : "Expand"}
                  {platformsExpanded ? (
                    <ChevronUp className="h-3 w-3" />
                  ) : (
                    <ChevronDown className="h-3 w-3" />
                  )}
                </span>
              </button>
              
              {/* Platform icons summary */}
              {!platformsExpanded && (
                <div className="flex flex-wrap gap-2">
                  {summary.platformInsights.map((platform) => (
                    <div
                      key={platform.platform}
                      className="flex items-center gap-2 rounded-full border border-border/50 bg-card px-3 py-1.5"
                    >
                      {PLATFORM_LOGOS[platform.platform] && (
                        <Image
                          src={PLATFORM_LOGOS[platform.platform]}
                          alt={platform.platform}
                          width={16}
                          height={16}
                          className="h-4 w-4"
                        />
                      )}
                      <span className="text-xs font-medium">{platform.platform}</span>
                      {getStatusIcon(platform.status)}
                    </div>
                  ))}
                </div>
              )}

              {/* Expanded platform details */}
              {platformsExpanded && (
                <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                  {summary.platformInsights.map((platform) => (
                    <div
                      key={platform.platform}
                      className="rounded-lg border border-border/50 bg-background p-3"
                    >
                      <div className="flex items-center gap-2 mb-2">
                        {PLATFORM_LOGOS[platform.platform] && (
                          <Image
                            src={PLATFORM_LOGOS[platform.platform]}
                            alt={platform.platform}
                            width={20}
                            height={20}
                            className="h-5 w-5"
                          />
                        )}
                        <span className="font-medium text-foreground text-sm">
                          {platform.platform}
                        </span>
                        {getStatusIcon(platform.status)}
                      </div>
                      <p className="text-muted-foreground text-xs">{platform.tip}</p>
                      <p className="mt-1 text-muted-foreground/60 text-xs">
                        Bot: {platform.botName}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Prioritized Actions */}
            <div>
              <h4 className="mb-3 font-medium text-foreground text-sm flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-primary" />
                Priority Actions
              </h4>
              <div className="space-y-2">
                {summary.prioritizedActions.map((action) => (
                  <div
                    key={action.priority}
                    className="flex items-start gap-3 rounded-lg border border-border/50 bg-background p-3"
                  >
                    <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 font-bold text-primary text-xs">
                      {action.priority}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-foreground text-sm">{action.action}</p>
                      <div className="mt-1.5 flex flex-wrap gap-1.5">
                        <span className={cn(
                          "rounded-full px-2 py-0.5 text-xs font-medium",
                          getImpactBadge(action.impact)
                        )}>
                          {action.impact} Impact
                        </span>
                        <span className={cn(
                          "rounded-full px-2 py-0.5 text-xs font-medium",
                          getEffortBadge(action.effort)
                        )}>
                          {action.effort}
                        </span>
                      </div>
                    </div>
                    <ArrowRight className="h-4 w-4 text-muted-foreground shrink-0" />
                  </div>
                ))}
              </div>
            </div>

            {/* Quick Wins */}
            <div className="rounded-lg border border-green-500/20 bg-green-500/5 p-4">
              <h4 className="mb-3 font-medium text-green-600 dark:text-green-400 text-sm flex items-center gap-2">
                <Zap className="h-4 w-4" />
                Quick Wins
              </h4>
              <ul className="space-y-2">
                {summary.quickWins.map((win) => (
                  <li key={win} className="flex items-start gap-2 text-foreground text-sm">
                    <Clock className="h-4 w-4 text-green-500 mt-0.5 shrink-0" />
                    {win}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
  )
}
