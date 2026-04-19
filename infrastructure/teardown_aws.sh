#!/usr/bin/env bash
set -euo pipefail

: "${AWS_ACCOUNT_ID:?Set AWS_ACCOUNT_ID}"
: "${AWS_REGION:?Set AWS_REGION}"

APP=querymind
BACKEND_REPO="$APP-backend"
FRONTEND_BUCKET="$APP-frontend-$AWS_ACCOUNT_ID"

echo "Deleting QueryMind baseline resources in $AWS_REGION..."

aws ecr delete-repository --repository-name "$BACKEND_REPO" --force --region "$AWS_REGION" >/dev/null 2>&1 || true
aws s3 rm "s3://$FRONTEND_BUCKET" --recursive >/dev/null 2>&1 || true
aws s3api delete-bucket --bucket "$FRONTEND_BUCKET" --region "$AWS_REGION" >/dev/null 2>&1 || true
aws secretsmanager delete-secret --secret-id "$APP/production" --force-delete-without-recovery --region "$AWS_REGION" >/dev/null 2>&1 || true

echo "Baseline resource teardown complete."
