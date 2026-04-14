#!/usr/bin/env bash
set -euo pipefail

# ─── MESH Railway Deployment Script ───────────────────────────────
# Deploys the SaaS platform (API + PostgreSQL + Dashboard) to Railway.
#
# Prerequisites:
#   - Railway CLI installed: brew install railway
#   - Logged in: railway login
#
# Usage:
#   bash scripts/deploy-railway.sh
# ──────────────────────────────────────────────────────────────────

echo "╔══════════════════════════════════════════════╗"
echo "║   MESH — Railway Deployment                  ║"
echo "║   Platform API + PostgreSQL + Dashboard       ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# Check Railway CLI
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Install with: brew install railway"
    exit 1
fi

# Check login
if ! railway whoami &> /dev/null 2>&1; then
    echo "❌ Not logged in. Run: railway login"
    exit 1
fi

echo "✅ Railway CLI ready ($(railway --version))"
echo ""

# ─── Step 1: Create project ──────────────────────────────────────
echo "📦 Step 1: Creating Railway project..."
echo "   Run these commands in your terminal:"
echo ""
echo "   # Create a new project"
echo "   railway init"
echo ""
echo "   # Add PostgreSQL"
echo "   railway add --plugin postgresql"
echo ""
echo "   # Deploy the Platform API (uses Dockerfile.platform)"
echo "   railway up --dockerfile Dockerfile.platform"
echo ""
echo "   # Set environment variables"
echo "   railway vars set PLATFORM_SECRET_KEY=\$(openssl rand -hex 32)"
echo "   railway vars set PLATFORM_MQTT_HOST=your-foxmq-host"
echo "   railway vars set PLATFORM_MQTT_PORT=1883"
echo ""
echo "   # Railway auto-sets DATABASE_URL for the PostgreSQL plugin."
echo "   # But our app expects PLATFORM_DATABASE_URL, so link it:"
echo "   railway vars set PLATFORM_DATABASE_URL=\\\${{Postgres.DATABASE_URL}}"
echo ""
echo "   # Get your deployment URL"
echo "   railway domain"
echo ""

echo "─────────────────────────────────────────────────"
echo ""
echo "📋 For the Dashboard, create a second service in the same project:"
echo ""
echo "   # In Railway dashboard (railway.com):"
echo "   # 1. Click 'New Service' → 'GitHub Repo' or 'Docker Image'"
echo "   # 2. Set root directory to 'dashboard'"
echo "   # 3. Or deploy with the dashboard Dockerfile:"
echo "   railway up --dockerfile Dockerfile.dashboard --service dashboard"
echo ""
echo "─────────────────────────────────────────────────"
echo ""
echo "⚠️  FoxMQ cluster + agents need a VPS (not Railway)."
echo "   Use: docker compose up --build"
echo "   On a $5/mo VPS (Hetzner, DigitalOcean, etc.)"
echo ""
