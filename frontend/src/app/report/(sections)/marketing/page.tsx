"use client"

import { useMemo } from "react"
import { Copy, Facebook, Linkedin, Twitter, Lightbulb, Target, TrendingUp, Clock, Hash, AlertCircle } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Spinner } from "@/components/ui/spinner"
import { AwaitingAnalysis } from "../../awaiting-analysis"
import { useReportContext } from "../../report-context"

const INTENT_STYLES: Record<string, string> = {
  informational: "bg-primary/10 text-primary border-primary/20",
  transactional: "bg-accent/80 text-accent-foreground border-accent",
  navigational: "bg-muted text-muted-foreground border-border",
  commercial: "bg-secondary text-secondary-foreground border-secondary",
}

const DIFFICULTY_STYLES: Record<string, string> = {
  low: "bg-primary/10 text-primary border-primary/20",
  medium: "bg-secondary text-secondary-foreground border-secondary",
  high: "bg-destructive/10 text-destructive border-destructive/20",
}

const PLATFORM_ICONS = {
  facebook: Facebook,
  linkedin: Linkedin,
  twitter: Twitter,
}

export default function ContentMarketingPage() {
  const { analysis, marketingData, marketingLoading } = useReportContext()

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  const formatPostWithHashtags = useMemo(() => {
    return (content: string, hashtags: string[]) => {
      const hashtagString = hashtags.map(h => h.startsWith('#') ? h : `#${h}`).join(" ")
      return `${content}\n\n${hashtagString}`
    }
  }, [])

  if (!analysis) return <AwaitingAnalysis />

  if (marketingLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="flex flex-col items-center gap-4">
          <Spinner className="h-8 w-8" />
          <p className="text-muted-foreground text-sm">Generating content recommendations...</p>
        </div>
      </div>
    )
  }

  if (!marketingData) {
    return (
      <div className="rounded-xl border border-border/50 bg-card p-6 text-center">
        <AlertCircle className="mx-auto mb-3 h-8 w-8 text-muted-foreground" />
        <p className="font-medium text-foreground text-sm">Content Marketing</p>
        <p className="mt-1 text-muted-foreground text-sm">Unable to generate recommendations. Please try again.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Target Keywords Section */}
      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <Target className="h-4 w-4 text-primary" />
          <h2 className="font-medium text-muted-foreground text-sm uppercase tracking-wider">Target Keywords</h2>
        </div>
        
        <div className="grid gap-3 sm:grid-cols-2">
          {(marketingData.targetKeywords ?? []).map((kw) => (
            <div
              key={kw.keyword}
              className="group rounded-xl border border-border/50 bg-card p-4 transition-all duration-200 hover:border-primary/20"
            >
              <div className="mb-2 flex items-start justify-between gap-2">
                <h4 className="font-medium text-foreground">{kw.keyword}</h4>
                <div className="flex shrink-0 gap-1.5">
                  <Badge variant="outline" className={`text-xs ${INTENT_STYLES[kw.searchIntent] || ""}`}>
                    {kw.searchIntent}
                  </Badge>
                  <Badge variant="outline" className={`text-xs ${DIFFICULTY_STYLES[kw.difficulty] || ""}`}>
                    {kw.difficulty}
                  </Badge>
                </div>
              </div>
              <p className="text-muted-foreground text-sm leading-relaxed">{kw.tip}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Social Media Posts Section */}
      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-primary" />
          <h2 className="font-medium text-muted-foreground text-sm uppercase tracking-wider">Social Media Posts</h2>
        </div>
        
        <div className="grid gap-4 lg:grid-cols-3">
          {(marketingData.socialPosts ?? []).map((post) => {
            const Icon = PLATFORM_ICONS[post.platform] || Facebook
            const fullPost = formatPostWithHashtags(post.content, post.hashtags)

            return (
              <div
                key={`${post.platform}-${post.content.slice(0, 20)}`}
                className="group flex flex-col overflow-hidden rounded-xl border border-border/50 bg-card transition-all duration-200 hover:border-primary/20"
              >
                {/* Platform Header */}
                <div className="flex items-center gap-2 border-border/50 border-b bg-muted/30 px-4 py-3">
                  <Icon className="h-4 w-4 text-primary" />
                  <span className="font-medium text-foreground text-sm capitalize">{post.platform}</span>
                </div>

                {/* Post Content */}
                <div className="flex flex-1 flex-col p-4">
                  <p className="flex-1 text-foreground text-sm leading-relaxed">{post.content}</p>

                  {/* Hashtags */}
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {post.hashtags.slice(0, 5).map((tag) => (
                      <span
                        key={tag}
                        className="inline-flex items-center gap-0.5 text-primary text-xs"
                      >
                        <Hash className="h-3 w-3" />
                        {tag.replace(/^#/, "")}
                      </span>
                    ))}
                  </div>

                  {/* Meta Info */}
                  <div className="mt-4 space-y-1.5 border-border/50 border-t pt-3">
                    <div className="flex items-center gap-1.5 text-muted-foreground text-xs">
                      <Lightbulb className="h-3 w-3" />
                      <span>{post.callToAction}</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-muted-foreground text-xs">
                      <Clock className="h-3 w-3" />
                      <span>{post.bestTimeToPost}</span>
                    </div>
                  </div>

                  {/* Copy Button */}
                  <Button
                    variant="outline"
                    size="sm"
                    className="mt-4 w-full"
                    onClick={() => copyToClipboard(fullPost)}
                  >
                    <Copy className="mr-2 h-3.5 w-3.5" />
                    Copy Post
                  </Button>
                </div>
              </div>
            )
          })}
        </div>
      </section>

      {/* Content Ideas Section */}
      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <Lightbulb className="h-4 w-4 text-primary" />
          <h2 className="font-medium text-muted-foreground text-sm uppercase tracking-wider">Content Ideas</h2>
        </div>
        
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {(marketingData.contentIdeas ?? []).map((idea, idx) => (
            <div
              key={idea}
              className="flex items-start gap-3 rounded-xl border border-border/50 bg-card p-4 transition-all duration-200 hover:border-primary/20"
            >
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 font-medium text-primary text-xs">
                {idx + 1}
              </span>
              <p className="text-foreground text-sm leading-relaxed">{idea}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
