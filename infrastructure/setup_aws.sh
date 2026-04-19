#!/usr/bin/env bash
set -euo pipefail

: "${AWS_ACCOUNT_ID:?Set AWS_ACCOUNT_ID}"
: "${AWS_REGION:?Set AWS_REGION}"
: "${DOMAIN_NAME:?Set DOMAIN_NAME}"
: "${VPC_MODE:=new}"

APP=querymind
BACKEND_REPO="$APP-backend"
FRONTEND_BUCKET="$APP-frontend-$AWS_ACCOUNT_ID"

echo "QueryMind AWS bootstrap"
echo "Account: $AWS_ACCOUNT_ID"
echo "Region : $AWS_REGION"
echo "Domain : $DOMAIN_NAME"
echo "VPC    : $VPC_MODE"

aws ecr describe-repositories --repository-names "$BACKEND_REPO" --region "$AWS_REGION" >/dev/null 2>&1 ||
  aws ecr create-repository --repository-name "$BACKEND_REPO" --region "$AWS_REGION" >/dev/null

aws s3api head-bucket --bucket "$FRONTEND_BUCKET" >/dev/null 2>&1 ||
  aws s3api create-bucket \
    --bucket "$FRONTEND_BUCKET" \
    --region "$AWS_REGION" \
    --create-bucket-configuration LocationConstraint="$AWS_REGION" >/dev/null

aws secretsmanager describe-secret --secret-id "$APP/production" --region "$AWS_REGION" >/dev/null 2>&1 ||
  aws secretsmanager create-secret \
    --name "$APP/production" \
    --description "QueryMind production secrets" \
    --secret-string '{"DJANGO_SECRET_KEY":"replace-me","ANTHROPIC_API_KEY":"replace-me","POSTGRES_PASSWORD":"replace-me"}' \
    --region "$AWS_REGION" >/dev/null

echo "Created baseline ECR, S3, and Secrets Manager resources."
echo "Next: create RDS, ECS Fargate service, ALB, ACM cert, CloudFront, and Route53 records."
echo "This script is intentionally conservative; it avoids creating billable compute until you confirm account/VPC details."
