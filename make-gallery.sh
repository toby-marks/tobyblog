#!/bin/bash

# Usage: ./make-gallery.sh <photo_directory> <gallery_title> [description]
# Example: ./make-gallery.sh ~/Desktop/caf "Cottonwood Art Festival 2026" "Photos from the Cottonwood Art Festival"

if [ $# -lt 2 ]; then
    echo "Usage: $0 <photo_directory> <gallery_title> [description]"
    echo "Example: $0 ~/Desktop/caf \"Cottonwood Art Festival 2026\" \"Photos from the festival\""
    exit 1
fi

PHOTO_DIR="$1"
GALLERY_TITLE="$2"
DESCRIPTION="${3:-$GALLERY_TITLE}"

# Expand tilde in path
PHOTO_DIR="${PHOTO_DIR/#\~/$HOME}"

if [ ! -d "$PHOTO_DIR" ]; then
    echo "Error: Directory '$PHOTO_DIR' does not exist"
    exit 1
fi

# Get today's date for filename
DATE=$(date +%Y%m%d)
# Create slug from title
SLUG=$(echo "$GALLERY_TITLE" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//' | sed 's/-$//')
FILENAME="$DATE-$SLUG.md"
FILEPATH="content/galleries/$FILENAME"

# Check if file already exists
if [ -f "$FILEPATH" ]; then
    echo "Error: Gallery file '$FILEPATH' already exists"
    exit 1
fi

echo "Creating gallery from photos in: $PHOTO_DIR"
echo "Title: $GALLERY_TITLE"
echo "Output file: $FILEPATH"
echo ""

# Step 1: Upload photos to Cloudflare
echo "Step 1: Uploading photos to Cloudflare..."
source ~/Projects/blog-photos/.venv/bin/activate
TEMP_OUTPUT=$(mktemp)
python ~/Projects/blog-photos/upload_photos_to_blog.py "$PHOTO_DIR" > "$TEMP_OUTPUT" 2>&1

# Extract Cloudflare IDs from the output
# Looking for lines like: "Uploaded: filename.jpg -> cloudflare-id"
PHOTO_IDS=($(grep -oE '26-[0-9]{2}-[0-9]{5}' "$TEMP_OUTPUT" | sort -u))

if [ ${#PHOTO_IDS[@]} -eq 0 ]; then
    echo "Error: No photos were uploaded. Upload output:"
    cat "$TEMP_OUTPUT"
    rm "$TEMP_OUTPUT"
    exit 1
fi

echo "Successfully uploaded ${#PHOTO_IDS[@]} photos"
rm "$TEMP_OUTPUT"

# Step 2: Generate gallery markdown
echo "Step 2: Generating gallery post..."

# Get current timestamp in Hugo format
TIMESTAMP=$(date +"%Y-%m-%dT%H:%M:%S%z" | sed 's/\([0-9][0-9]\)$/:\1/')

# Start writing the file
cat > "$FILEPATH" << EOF
+++
title = "$GALLERY_TITLE"
description = "$DESCRIPTION"
date = "$TIMESTAMP"
categories = ["photography"]
draft = false

# Used for preview cards / social sharing
images = ["https://imagedelivery.net/zJmFZzaNuqC_Q5Caqyu8nQ/${PHOTO_IDS[0]}/fit=scale-down,w=1024,sharpen=1,f=auto,q=0.9,slow-connection-quality=0.3"]

EOF

# Add gallery entries for each photo
COUNTER=1
for PHOTO_ID in "${PHOTO_IDS[@]}"; do
    cat >> "$FILEPATH" << EOF
[[gallery]]
src = "https://imagedelivery.net/zJmFZzaNuqC_Q5Caqyu8nQ/$PHOTO_ID/fit=scale-down,w=1600,sharpen=1,f=auto,q=0.9,slow-connection-quality=0.3"
thumb = "https://imagedelivery.net/zJmFZzaNuqC_Q5Caqyu8nQ/$PHOTO_ID/fit=scale-down,w=480,sharpen=1,f=auto,q=0.9,slow-connection-quality=0.3"
caption = "Photo $COUNTER"

EOF
    ((COUNTER++))
done

# Add closing and gallery shortcode
cat >> "$FILEPATH" << 'EOF'
+++

{{< gallery >}}
EOF

echo ""
echo "✅ Gallery created successfully!"
echo "   File: $FILEPATH"
echo "   Photos: ${#PHOTO_IDS[@]}"
echo ""
echo "Next steps:"
echo "  - Edit the file to add custom captions"
echo "  - Preview with: npm run dev"
echo "  - Format with: npm run format"
