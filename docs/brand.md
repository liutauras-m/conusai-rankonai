# ConusAI Brand Guidelines

Technical brand specifications for Next.js + Tailwind CSS + shadcn/ui projects.

---

## Brand Message

> **Challenge the norm to invent the new.**

---

## Color Palette

### Primary Brand Colors

| Name | Hex | HSL | CSS Variable | Usage |
|------|-----|-----|--------------|-------|
| **Primary Mint** | `#80CDC6` | `hsl(174.7, 43.3%, 65.3%)` | `--primary` | Main brand color, primary buttons, highlights, key elements |
| **Forest Green** | `#529273` | `hsl(148, 29%, 38%)` | `--secondary-brand` | Supporting elements, complements primary mint |

### Accent Colors

| Name | Hex | HSL | CSS Variable | Usage |
|------|-----|-----|--------------|-------|
| **Gold** | `#F9A826` | `hsl(40, 95%, 56%)` | `--accent-gold` | Emphasis, calls-to-action, highlights |
| **Coral** | `#F26E50` | `hsl(11, 87%, 63%)` | `--accent-coral` | Sparingly for notifications, visual interest |

### Neutral Colors

| Name | Hex | HSL | Usage |
|------|-----|-----|-------|
| **Black** | `#000000` | `hsl(0, 0%, 0%)` | Dark backgrounds, text |
| **White** | `#FFFFFF` | `hsl(0, 0%, 100%)` | Light backgrounds, text on dark |
| **Background Dark** | `#0a0a0a` | `hsl(0, 0%, 4%)` | Main dark theme background |
| **Foreground Light** | `#ededed` | `hsl(0, 0%, 93%)` | Text on dark backgrounds |

---

## Typography

### Font Family

| Usage | Font | Fallbacks |
|-------|------|-----------|
| **Display/Headings** | Archivo | system-ui, sans-serif |
| **Body Text** | Inter | system-ui, sans-serif |
| **Monospace/Code** | Space Mono | ui-monospace, monospace |

### Font Weights & Styles

```css
/* Headings */
.brand-heading {
  font-family: var(--font-display, "Archivo", system-ui, sans-serif);
  font-weight: 600;
  letter-spacing: -0.02em;
  line-height: 1.1;
}

/* Navigation */
.brand-nav {
  font-family: var(--font-display, "Archivo", system-ui, sans-serif);
  font-weight: 500;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  font-size: 0.875rem;
}

/* Body */
.brand-body {
  font-family: var(--font-sans, "Inter", system-ui, sans-serif);
  font-weight: 400;
  line-height: 1.6;
  letter-spacing: 0.01em;
}

/* Monospace */
.brand-mono {
  font-family: var(--font-mono, "Space Mono", ui-monospace, monospace);
  font-weight: 400;
  letter-spacing: -0.01em;
}
```

### Type Scale

| Element | Size | Weight | Font |
|---------|------|--------|------|
| H1 | 48px (3rem) | Bold (700) | Archivo |
| H2 | 36px (2.25rem) | Bold (700) | Archivo |
| H3 | 24px (1.5rem) | SemiBold (600) | Archivo |
| Body Large | 18px (1.125rem) | Regular (400) | Inter |
| Body | 16px (1rem) | Regular (400) | Inter |
| Small/Caption | 14px (0.875rem) | Regular (400) | Inter |

---

## Logo Assets

| Variant | URL |
|---------|-----|
| **Dark Mode** (white text) | `https://blobs.vusercontent.net/blob/conusai_logo_darkmode-z33w2LAAePCdCUohqrXENhL3xEDSxL.svg` |
| **Light Mode** (dark text) | `https://blobs.vusercontent.net/blob/conusai_logo_lightmode-3c5V99MXBqojhYps1uhJpWj9aLYXuM.svg` |

---

## Tailwind CSS Configuration

### tailwind.config.ts

```typescript
import type { Config } from "tailwindcss"

const config: Config = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Brand colors
        brand: {
          mint: "#80CDC6",
          forest: "#529273",
          gold: "#F9A826",
          coral: "#F26E50",
        },
        // shadcn/ui compatible
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      fontFamily: {
        display: ["var(--font-display)", "Archivo", "system-ui", "sans-serif"],
        sans: ["var(--font-sans)", "Inter", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "Space Mono", "ui-monospace", "monospace"],
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}

export default config
```

---

## CSS Variables (globals.css)

### shadcn/ui Theme Variables

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    /* Background & Foreground */
    --background: 0 0% 100%;
    --foreground: 240 10% 3.9%;

    /* Primary - Brand Mint */
    --primary: 174.7 43.3% 65.3%;
    --primary-foreground: 0 0% 100%;

    /* Secondary */
    --secondary: 240 4.8% 95.9%;
    --secondary-foreground: 240 5.9% 10%;

    /* Muted */
    --muted: 240 4.8% 95.9%;
    --muted-foreground: 240 3.8% 46.1%;

    /* Accent */
    --accent: 240 4.8% 95.9%;
    --accent-foreground: 240 5.9% 10%;

    /* Destructive */
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 0 0% 98%;

    /* Border, Input, Ring */
    --border: 240 5.9% 90%;
    --input: 240 5.9% 90%;
    --ring: 174.7 43.3% 65.3%;

    /* Radius */
    --radius: 0.5rem;

    /* Card */
    --card: 0 0% 100%;
    --card-foreground: 240 10% 3.9%;

    /* Popover */
    --popover: 0 0% 100%;
    --popover-foreground: 240 10% 3.9%;

    /* Chart Colors */
    --chart-1: 174 60% 50%;
    --chart-2: 200 58% 39%;
    --chart-3: 220 37% 24%;
    --chart-4: 160 74% 66%;
    --chart-5: 140 87% 67%;

    /* Sidebar */
    --sidebar-background: 240 5% 96%;
    --sidebar-foreground: 240 10% 20%;
    --sidebar-primary: 174.7 43.3% 65.3%;
    --sidebar-primary-foreground: 0 0% 98%;
    --sidebar-accent: 240 10% 90%;
    --sidebar-accent-foreground: 240 10% 20%;
    --sidebar-border: 240 5% 85%;
    --sidebar-ring: 217.2 91.2% 59.8%;
  }

  .dark {
    /* Background & Foreground */
    --background: 0 0% 4%;
    --foreground: 0 0% 93%;

    /* Primary - Brand Mint */
    --primary: 174.7 43.3% 65.3%;
    --primary-foreground: 0 0% 0%;

    /* Secondary */
    --secondary: 240 3.7% 15.9%;
    --secondary-foreground: 0 0% 98%;

    /* Muted */
    --muted: 240 3.7% 15.9%;
    --muted-foreground: 240 5% 64.9%;

    /* Accent */
    --accent: 240 3.7% 15.9%;
    --accent-foreground: 0 0% 98%;

    /* Destructive */
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 0 0% 98%;

    /* Border, Input, Ring */
    --border: 240 3.7% 15.9%;
    --input: 240 3.7% 15.9%;
    --ring: 174.7 43.3% 65.3%;

    /* Card */
    --card: 240 10% 3.9%;
    --card-foreground: 0 0% 98%;

    /* Popover */
    --popover: 240 10% 3.9%;
    --popover-foreground: 0 0% 98%;

    /* Chart Colors (dark mode) */
    --chart-1: 220 70% 50%;
    --chart-2: 160 60% 45%;
    --chart-3: 30 80% 55%;
    --chart-4: 280 65% 60%;
    --chart-5: 340 75% 55%;

    /* Sidebar */
    --sidebar-background: 240 5.9% 10%;
    --sidebar-foreground: 240 4.8% 95.9%;
    --sidebar-primary: 174.7 43.3% 65.3%;
    --sidebar-primary-foreground: 0 0% 100%;
    --sidebar-accent: 240 3.7% 15.9%;
    --sidebar-accent-foreground: 240 4.8% 95.9%;
    --sidebar-border: 240 3.7% 15.9%;
    --sidebar-ring: 217.2 91.2% 59.8%;
  }
}

@layer base {
  * {
    @apply border-border;
  }

  body {
    @apply bg-background text-foreground;
  }
}
```

---

## Next.js Font Setup

### layout.tsx

```tsx
import { Archivo, Inter, Space_Mono } from 'next/font/google'

const archivo = Archivo({
  subsets: ['latin'],
  variable: '--font-display',
  display: 'swap',
})

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-sans',
  display: 'swap',
})

const spaceMono = Space_Mono({
  subsets: ['latin'],
  weight: ['400', '700'],
  variable: '--font-mono',
  display: 'swap',
})

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${archivo.variable} ${inter.variable} ${spaceMono.variable}`}>
      <body className="font-sans antialiased">{children}</body>
    </html>
  )
}
```

---

## Button Variants

### Primary Button

```tsx
// Use for main CTAs
<Button className="bg-brand-mint hover:bg-brand-mint/90 text-white">
  Primary Action
</Button>

// With shadcn/ui
<Button>Primary Action</Button>
```

### Secondary Button (Outline)

```tsx
<Button 
  variant="outline" 
  className="border-2 border-brand-mint text-brand-mint hover:bg-brand-mint/10"
>
  Secondary Action
</Button>
```

### Button Guidelines

- Always use white text (`text-white`) on primary mint buttons
- Maintain consistent padding and sizing
- Limit primary buttons per screen
- Ensure WCAG 2.1 AA contrast compliance

---

## Quick Reference

### Color Tokens (Direct Use)

```tsx
// Tailwind classes
className="bg-brand-mint"      // #80CDC6
className="bg-brand-forest"    // #529273
className="bg-brand-gold"      // #F9A826
className="bg-brand-coral"     // #F26E50

// Text colors
className="text-brand-mint"
className="text-[#80CDC6]"

// With opacity
className="bg-brand-mint/50"   // 50% opacity
className="border-brand-mint/30"
```

### HSL Values for Custom CSS

```css
/* Primary Mint */
hsl(174.7, 43.3%, 65.3%)

/* Forest Green */
hsl(148, 29%, 38%)

/* Gold */
hsl(40, 95%, 56%)

/* Coral */
hsl(11, 87%, 63%)
```

---

## Dependencies

```bash
# Required packages
pnpm add tailwindcss-animate class-variance-authority clsx tailwind-merge

# shadcn/ui CLI
pnpm dlx shadcn@latest init
```

---

## File Structure

```
├── app/
│   ├── globals.css          # CSS variables & base styles
│   └── layout.tsx           # Font configuration
├── components/
│   └── ui/                   # shadcn/ui components
├── lib/
│   └── utils.ts             # cn() helper function
└── tailwind.config.ts       # Tailwind configuration
```

---

*Last updated: December 2024*
