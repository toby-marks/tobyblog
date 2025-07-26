# Cloudflare Image Upload Setup Guide

You have two main options for hosting your 3.4GB of images on Cloudflare:

## Option 1: Cloudflare Images (Recommended for blogs)
**Best for:** Image-heavy websites, automatic optimization, built-in CDN
**Cost:** ~$5/month for first 100K images, then $1 per 100K additional images
**Pros:** Automatic optimization, resizing, format conversion, built-in CDN
**Cons:** More expensive for large volumes

## Option 2: Cloudflare R2 (Most cost-effective)
**Best for:** Large amounts of data, cost optimization
**Cost:** ~$0.36/month for 3.4GB storage + bandwidth costs
**Pros:** Very cheap storage, S3-compatible, can use custom domain
**Cons:** No automatic image optimization

## Setup Instructions

### For Cloudflare Images:

1. **Get your Cloudflare credentials:**
   ```bash
   # Go to Cloudflare Dashboard → Images → API tokens
   export CLOUDFLARE_ACCOUNT_ID="your_account_id_here"
   export CLOUDFLARE_API_TOKEN="your_api_token_here"
   ```

2. **Upload images:**
   ```bash
   source venv/bin/activate
   python upload_to_cloudflare_images.py upload
   ```

3. **Update content links:**
   ```bash
   python upload_to_cloudflare_images.py update
   ```

### For Cloudflare R2 (Recommended for cost):

1. **Create R2 bucket and get credentials:**
   ```bash
   # Go to Cloudflare Dashboard → R2 → Create bucket
   # Then go to R2 → Manage R2 API tokens
   export CLOUDFLARE_R2_ACCESS_KEY_ID="your_access_key"
   export CLOUDFLARE_R2_SECRET_ACCESS_KEY="your_secret_key"
   export CLOUDFLARE_R2_BUCKET_NAME="your_bucket_name"
   export CLOUDFLARE_R2_ACCOUNT_ID="your_account_id"
   export CLOUDFLARE_R2_CUSTOM_DOMAIN="your_custom_domain"  # Optional
   ```

2. **Setup bucket:**
   ```bash
   source venv/bin/activate
   python upload_to_cloudflare_r2.py setup
   ```

3. **Upload images and update links:**
   ```bash
   python upload_to_cloudflare_r2.py both
   ```

## Step-by-Step R2 Setup (Detailed):

### 1. Create R2 Bucket
- Go to [Cloudflare Dashboard](https://dash.cloudflare.com/)
- Navigate to R2 Object Storage
- Click "Create bucket"
- Name it something like `tobyblog-images`
- Choose a location close to your users

### 2. Create R2 API Token
- Go to R2 → Manage R2 API tokens
- Click "Create API token"
- Give it a name like "TobyblogImageUpload"
- Permissions: Object Read and Write
- Copy the Access Key ID and Secret Access Key

### 3. Optional: Setup Custom Domain
- In your bucket settings, go to "Settings" → "Custom domains"
- Add a subdomain like `images.yourdomain.com`
- Add a CNAME record in your DNS: `images CNAME your-bucket-name.your-account-id.r2.cloudflarestorage.com`

### 4. Set Environment Variables
Add these to your shell profile (`.zshrc`, `.bashrc`, etc.):
```bash
export CLOUDFLARE_R2_ACCESS_KEY_ID="your_access_key_id"
export CLOUDFLARE_R2_SECRET_ACCESS_KEY="your_secret_access_key"
export CLOUDFLARE_R2_BUCKET_NAME="tobyblog-images"
export CLOUDFLARE_R2_ACCOUNT_ID="your_account_id"
export CLOUDFLARE_R2_CUSTOM_DOMAIN="images.yourdomain.com"  # If using custom domain
```

## Usage Examples:

### Upload everything in one go:
```bash
source venv/bin/activate
python upload_to_cloudflare_r2.py both
```

### Upload first, then update links separately:
```bash
python upload_to_cloudflare_r2.py upload
# Review the uploads, then:
python upload_to_cloudflare_r2.py update
```

## Features:

- **Resume capability:** If uploads fail, you can re-run and it will skip already uploaded images
- **Progress tracking:** Shows progress and saves mapping periodically
- **Automatic content type detection:** Sets proper MIME types for images
- **Cache headers:** Sets 1-year cache headers for optimal performance
- **Mapping file:** Creates `cloudflare_r2_mapping.json` to track all uploads

## Cost Comparison (for 3.4GB):

- **Cloudflare Images:** ~$20-25/month (assuming ~5K images)
- **Cloudflare R2:** ~$0.36/month storage + bandwidth costs
- **Current setup (local):** Free but no CDN benefits

## Recommended Approach:

I recommend **Cloudflare R2** for your use case because:
1. Much more cost-effective for 3.4GB of images
2. Still gets Cloudflare's global CDN
3. Can add image optimization later via Cloudflare's Transform Rules
4. Easy to migrate from if needed

Would you like me to help you set up the R2 option?
