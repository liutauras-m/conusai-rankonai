# SEO & AI Model Indexing Best Practices

A comprehensive guide to optimizing your website for search engines and AI models (ChatGPT, Grok, Perplexity, Claude, etc.).

---

## Table of Contents

1. [Traditional SEO Essentials](#traditional-seo-essentials)
2. [AI Model Indexing](#ai-model-indexing)
3. [Structured Data (Schema.org)](#structured-data-schemaorg)
4. [Technical SEO](#technical-seo)
5. [Content Optimization](#content-optimization)
6. [Files to Include](#files-to-include)

---

## Traditional SEO Essentials

### Meta Tags (in `<head>`)

```html
<!-- Primary Meta Tags -->
<title>Page Title - Brand Name (50-60 characters)</title>
<meta name="description" content="Compelling description of your page (150-160 characters)">
<meta name="keywords" content="keyword1, keyword2, keyword3">
<meta name="author" content="Author Name">
<meta name="robots" content="index, follow">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="canonical" href="https://example.com/page-url">

<!-- Open Graph (Facebook, LinkedIn) -->
<meta property="og:title" content="Page Title">
<meta property="og:description" content="Page description">
<meta property="og:image" content="https://example.com/image.jpg">
<meta property="og:url" content="https://example.com/page-url">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Site Name">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@username">
<meta name="twitter:title" content="Page Title">
<meta name="twitter:description" content="Page description">
<meta name="twitter:image" content="https://example.com/image.jpg">
```

---

## AI Model Indexing

### 1. Allow AI Crawlers in `robots.txt`

```txt
# robots.txt

User-agent: *
Allow: /

# AI Crawlers - Explicitly Allow
User-agent: GPTBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: anthropic-ai
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Claude-Web
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Applebot-Extended
Allow: /

User-agent: cohere-ai
Allow: /

User-agent: Bytespider
Allow: /

Sitemap: https://example.com/sitemap.xml
```

### 2. Create `llms.txt` File (Root Directory)

A new standard for AI-friendly content discovery:

```txt
# llms.txt - AI Model Instructions

# Site Information
name: Your Website Name
description: A brief description of what your website offers
url: https://example.com

# Content Guidelines
- This website provides information about [topic]
- Key sections include: [section1], [section2], [section3]
- Updated frequency: [daily/weekly/monthly]

# Important Pages
/about - Company information
/products - Product catalog
/docs - Documentation
/api - API reference
/blog - Latest articles

# Contact
contact: contact@example.com

# Preferred Citation Format
cite_as: "Website Name (year). Page Title. Retrieved from [URL]"
```

### 3. Create `llms-full.txt` (Optional - Detailed Version)

```txt
# llms-full.txt - Comprehensive AI Context

## About This Site
[Detailed description of your website, mission, and content]

## Content Structure
### Main Sections
1. **Products** - Description of products/services
2. **Documentation** - Technical guides and tutorials
3. **Blog** - Industry insights and updates

## Key Facts
- Founded: [Year]
- Industry: [Industry]
- Expertise: [Areas of expertise]

## Frequently Asked Questions
Q: [Common question 1]
A: [Answer]

Q: [Common question 2]
A: [Answer]

## Data Accuracy
- Last verified: [Date]
- Update frequency: [Frequency]
- Data sources: [Sources]
```

### 4. AI-Specific Meta Tags

```html
<!-- AI Model Instructions -->
<meta name="ai-content-declaration" content="human-created">
<meta name="ai-training" content="allowed">

<!-- Bing/Copilot -->
<meta name="msnbot" content="index, follow">

<!-- Content Freshness -->
<meta name="last-modified" content="2024-12-14">
<meta name="content-frequency" content="weekly">
```

---

## Structured Data (Schema.org)

### Organization Schema

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Company Name",
  "url": "https://example.com",
  "logo": "https://example.com/logo.png",
  "description": "Company description",
  "foundingDate": "2020",
  "sameAs": [
    "https://twitter.com/company",
    "https://linkedin.com/company/company",
    "https://github.com/company"
  ],
  "contactPoint": {
    "@type": "ContactPoint",
    "email": "contact@example.com",
    "contactType": "customer service"
  }
}
</script>
```

### Article Schema (for Blog Posts)

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Article Title",
  "description": "Article description",
  "author": {
    "@type": "Person",
    "name": "Author Name"
  },
  "publisher": {
    "@type": "Organization",
    "name": "Publisher Name",
    "logo": {
      "@type": "ImageObject",
      "url": "https://example.com/logo.png"
    }
  },
  "datePublished": "2024-12-14",
  "dateModified": "2024-12-14",
  "image": "https://example.com/article-image.jpg",
  "mainEntityOfPage": "https://example.com/article-url"
}
</script>
```

### FAQ Schema (Great for AI Answers)

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "What is your product?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Our product is a comprehensive solution for..."
      }
    },
    {
      "@type": "Question",
      "name": "How much does it cost?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Pricing starts at $X per month..."
      }
    }
  ]
}
</script>
```

### Product Schema

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Product Name",
  "description": "Product description",
  "image": "https://example.com/product.jpg",
  "brand": {
    "@type": "Brand",
    "name": "Brand Name"
  },
  "offers": {
    "@type": "Offer",
    "price": "99.99",
    "priceCurrency": "USD",
    "availability": "https://schema.org/InStock"
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.5",
    "reviewCount": "100"
  }
}
</script>
```

---

## Technical SEO

### Essential Files

| File | Location | Purpose |
|------|----------|---------|
| `robots.txt` | `/robots.txt` | Crawler instructions |
| `sitemap.xml` | `/sitemap.xml` | Page discovery |
| `llms.txt` | `/llms.txt` | AI model context |
| `humans.txt` | `/humans.txt` | Credits (optional) |
| `security.txt` | `/.well-known/security.txt` | Security contact |

### Sitemap.xml Template

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.com/</loc>
    <lastmod>2024-12-14</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://example.com/about</loc>
    <lastmod>2024-12-14</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
</urlset>
```

### Performance & Core Web Vitals

```html
<!-- Preconnect to important origins -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="dns-prefetch" href="https://analytics.example.com">

<!-- Preload critical resources -->
<link rel="preload" href="/fonts/main.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/css/critical.css" as="style">
```

---

## Content Optimization

### Best Practices for AI Discoverability

1. **Clear Headings Structure**
   - Use proper H1 → H6 hierarchy
   - Include keywords in headings
   - Make headings descriptive

2. **Semantic HTML**
   ```html
   <article>
     <header>
       <h1>Article Title</h1>
       <time datetime="2024-12-14">December 14, 2024</time>
     </header>
     <main>
       <section>
         <h2>Section Title</h2>
         <p>Content...</p>
       </section>
     </main>
     <footer>
       <p>Author: Name</p>
     </footer>
   </article>
   ```

3. **Accessible Images**
   ```html
   <img 
     src="image.jpg" 
     alt="Descriptive alt text explaining the image"
     title="Image title"
     loading="lazy"
     width="800"
     height="600"
   >
   ```

4. **Internal Linking**
   - Link related content
   - Use descriptive anchor text
   - Create topic clusters

5. **Content Freshness**
   - Display publication dates
   - Show last updated dates
   - Regular content updates

---

## Files to Include

### Complete Checklist

```
your-website/
├── robots.txt              # Crawler rules
├── sitemap.xml             # Page index
├── llms.txt                # AI context (basic)
├── llms-full.txt           # AI context (detailed)
├── humans.txt              # Credits (optional)
├── .well-known/
│   └── security.txt        # Security contact
├── favicon.ico             # Browser icon
├── apple-touch-icon.png    # iOS icon
└── manifest.json           # PWA manifest
```

---

## Quick Implementation Checklist

- [ ] Add all essential meta tags
- [ ] Implement Open Graph tags
- [ ] Add Twitter Card tags
- [ ] Create `robots.txt` with AI crawler permissions
- [ ] Create `llms.txt` file
- [ ] Generate `sitemap.xml`
- [ ] Add Organization schema
- [ ] Add page-specific schema (Article, Product, FAQ)
- [ ] Ensure proper heading hierarchy
- [ ] Add alt text to all images
- [ ] Implement canonical URLs
- [ ] Test with Google Rich Results Test
- [ ] Verify with Schema.org Validator

---

## Useful Tools

- [Google Search Console](https://search.google.com/search-console)
- [Google Rich Results Test](https://search.google.com/test/rich-results)
- [Schema.org Validator](https://validator.schema.org/)
- [OpenGraph Preview](https://www.opengraph.xyz/)
- [Twitter Card Validator](https://cards-dev.twitter.com/validator)
- [PageSpeed Insights](https://pagespeed.web.dev/)

---

## Resources

- [Schema.org Documentation](https://schema.org/)
- [Google SEO Starter Guide](https://developers.google.com/search/docs/fundamentals/seo-starter-guide)
- [OpenAI GPTBot Documentation](https://platform.openai.com/docs/gptbot)
- [llms.txt Proposal](https://llmstxt.org/)

---

*Last Updated: December 2024*
