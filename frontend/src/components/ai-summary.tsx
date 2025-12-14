"use client"

import { useState, useEffect } from "react"
import { Sparkles, AlertCircle, ChevronDown, ChevronUp, Copy, Check } from "lucide-react"
import { Spinner } from "@/components/ui/spinner"
import { Markdown } from "@/components/ui/markdown"
import { cn } from "@/lib/utils"

interface AISummaryProps {
  analysis: Record<string, unknown> | null
}

export function AISummary({ analysis }: AISummaryProps) {
  const [markdown, setMarkdown] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [expanded, setExpanded] = useState(true)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (!analysis) {
      setMarkdown(null)
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
          throw new Error("Failed to generate AI report")
        }

        const data = await response.json()
        if (data.success && data.markdown) {
          setMarkdown(data.markdown)
        } else {
          throw new Error(data.error || "Invalid response")
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load report")
      } finally {
        setLoading(false)
      }
    }

    fetchSummary()
  }, [analysis])

  const handleCopy = async () => {
    if (!markdown) return
    try {
      await navigator.clipboard.writeText(markdown)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Clipboard API not available
    }
  }

  if (!analysis) return null

  if (loading) {
    return (
      <div className="rounded-xl border border-border/50 bg-card p-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
            <Sparkles className="h-5 w-5 animate-pulse text-primary" />
          </div>
          <div className="flex-1">
            <p className="font-medium text-foreground text-sm">Generating AI Report</p>
            <p className="text-muted-foreground text-xs">Analyzing your website for AI discoverability...</p>
          </div>
          <Spinner size="sm" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-xl border border-border/50 bg-card p-4">
        <div className="flex items-center gap-2 text-muted-foreground">
          <AlertCircle className="h-4 w-4" />
          <p className="text-sm">{error}</p>
        </div>
      </div>
    )
  }

  if (!markdown) return null

  return (
    <div className="overflow-hidden rounded-xl border border-border/50 bg-card">
      {/* Header */}
      <div className="flex items-center justify-between border-border/50 border-b p-4">
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-3"
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
            <Sparkles className="h-4 w-4 text-primary" />
          </div>
          <div className="text-left">
            <p className="font-medium text-foreground text-sm">AI Discoverability Report</p>
            <p className="text-muted-foreground text-xs">Comprehensive analysis & recommendations</p>
          </div>
        </button>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleCopy}
            className={cn(
              "flex items-center gap-1.5 rounded-lg border border-border/50 px-3 py-1.5 font-medium text-xs transition-colors",
              copied 
                ? "border-primary/50 bg-primary/10 text-primary" 
                : "text-muted-foreground hover:bg-muted/50 hover:text-foreground"
            )}
            title="Copy as Markdown to use as AI prompt"
          >
            {copied ? (
              <>
                <Check className="h-3.5 w-3.5" />
                Copied!
              </>
            ) : (
              <>
                <Copy className="h-3.5 w-3.5" />
                Copy Report
              </>
            )}
          </button>
          <button
            type="button"
            onClick={() => setExpanded(!expanded)}
            className="rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-muted/50"
          >
            {expanded ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </button>
        </div>
      </div>

      {/* Content */}
      {expanded && (
        <div className="max-h-[600px] overflow-y-auto p-4 sm:p-6">
          <Markdown content={markdown} />
        </div>
      )}
    </div>
  )
}
