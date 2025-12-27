# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

Tobyblog is a personal blog built with Hugo (v0.146+) and deployed to GitHub Pages. The site features multiple content types (posts, microposts, photos, videos) with a custom theme called "internet-weblog" (managed as a git submodule). The site uses Thulite framework components and Tailwind CSS v4 for styling.

**Live URL:** https://tobyblog.com

## Essential Commands

### Development
```bash
# Start development server with performance metrics
npm run dev

# Start development server with draft content
npm run dev:drafts
```

### Content Creation
```bash
# Create new content using Hugo archetypes
npm run create posts/YYYYMMDD-slug.md
npm run create microposts/slug.md
npm run create photos/YYYYMMDD-slug.md
```

### Building & Deployment
```bash
# Production build (minified, with garbage collection)
npm run build

# Clean build artifacts
npm run clean:build

# Preview built site locally
npm run preview
```

### Formatting & Maintenance
```bash
# Format all files with Prettier (includes Tailwind plugin)
npm run format

# Check for broken image links in content
python3 check_broken_images.py

# Extract all tags from content
./show_tags.sh

# Extract all categories from content
./show_categories.sh
```

## Architecture & Key Concepts

### Content Organization
The site has four main content types, each with distinct layouts and presentation:
- **posts/**: Long-form blog posts with categories and tags
- **microposts/**: Short-form content (Twitter-like)
- **photos/**: Photo blog entries with location/camera metadata
- **videos/**: Video content

Each content type has a corresponding archetype in `archetypes/` that defines its frontmatter template.

### Frontmatter Patterns
**Posts** use TOML frontmatter (`+++` delimiters):
```toml
title = "Post Title"
date = 2024-01-01T00:00:00Z
description = "Brief description"
categories = ["category-name"]
tags = ["tag1", "tag2"]
minipost = "true"  # Optional, for shorter posts
```

**Photos** include location/camera metadata:
```toml
title = "Photo Title"
date = 2024-01-01
location = "Dallas, TX"
camera = "Sony DSC RX-100"
categories = ["category"]
images = ["url-to-featured-image"]
```

**Microposts** are minimal:
```toml
title = "Title"
date = "2024-01-01T00:00:00-05:00"
```

### Theme Architecture
The site uses a layered theme approach via Hugo modules:
1. Base theme: `themes/internet-weblog` (git submodule)
2. Thulite framework components from npm: `@thulite/core`, `@thulite/seo`
3. Custom overrides in root `layouts/` directory

The `config/_default/module.toml` defines mount points that layer these together. Custom layouts in root `layouts/` take precedence over theme layouts.

### Custom Shortcodes
Located in `layouts/_shortcodes/`:
- `applemusic.html` - Embed Apple Music content
- `flickr.html` - Embed Flickr photos
- `soundcloud.html` - Embed SoundCloud tracks
- `spotify.html` - Embed Spotify content
- `youtubepl.html` - Embed YouTube playlists
- `yt.html` - Embed YouTube videos
- `image-gallery.html` - Create image galleries

### Styling System
The site uses **Tailwind CSS v4** with custom theme variables:
- Main stylesheet: `assets/css/main.css` (imports Tailwind and defines theme)
- Additional SCSS: `assets/scss/app.scss`
- Custom color palette includes "pumpkin", "warm-gray", "deep-goldenrod" colors
- Uses custom fonts: Chicle (headings), Nanum Myeongjo (body), American Typewriter (meta)

PostCSS configuration (`config/postcss.config.js`) handles autoprefixing and PurgeCSS for production.

### Image Handling
Images are served via Cloudflare Image Delivery CDN with URL-based transformations:
```
https://imagedelivery.net/zJmFZzaNuqC_Q5Caqyu8nQ/{path}/fit=scale-down,w=780,sharpen=1,f=auto,q=0.9,slow-connection-quality=0.3
```

The `check_broken_images.py` script validates image references in content, excluding commented-out images.

### CI/CD Pipeline
GitHub Actions workflow (`.github/workflows/hugo.yaml`) handles deployment:
1. Installs Hugo Extended v0.147.7 and Dart Sass
2. Checks out code with submodules
3. Installs npm dependencies
4. Builds with Hugo (minified, with cache)
5. Runs Pagefind search indexing (`npx pagefind --site public`)
6. Deploys to GitHub Pages

The workflow runs on pushes to `master` branch.

### Photo Import Workflow
The `make-photoblog.sh` script integrates with an external Python project:
```bash
./make-photoblog.sh <argument>
```
This activates a virtualenv at `~/Projects/blog-photos/.venv` and runs `upload_photos_to_blog.py`.

## Development Guidelines

### When Creating Content
- Use npm scripts (not raw `hugo new`) to ensure proper archetype application
- Date prefixes in filenames are conventional: `YYYYMMDD-slug.md`
- The `<!--more-->` comment creates a content break for summaries
- Tags and categories should be lowercase (see helper scripts)

### When Modifying Layouts
- Check if layout exists in theme before creating override
- Custom partials go in `layouts/_partials/`
- Section-specific templates go in `layouts/section/`
- The site uses `home.html` for the homepage layout

### When Working with Styles
- Edit `assets/css/main.css` for Tailwind customizations
- Theme variables are defined in the `@theme` block
- Use existing color variables (e.g., `text-pumpkin`, `bg-warm-brown`)
- Run `npm run format` after style changes

### Important Constraints
- Hugo version must be 0.146.0+ (extended version required)
- Node.js version must be >= 20.11.0
- Never commit the `public/`, `node_modules/`, or `.DS_Store` directories
- Submodule updates require explicit git submodule commands
- Images should use the Cloudflare CDN pattern (not local paths in most cases)

## Testing Locally
Hugo's built-in server handles live reloading. The dev server runs without HTTP cache and shows template metrics for performance debugging. Use `dev:drafts` to preview content with `draft = true` in frontmatter.

## Configuration Files
Hugo configuration is split across multiple TOML files in `config/_default/`:
- `hugo.toml` - Core Hugo settings, imaging, build config
- `params.toml` - Site parameters, author info, SEO settings
- `menus.toml` - Navigation menus
- `module.toml` - Hugo module mounts and theme integration
- `taxonomies.toml` - Defines categories, tags, and series taxonomies
- `markup.toml` - Markdown rendering settings

Production-specific overrides are in `config/production/`.
