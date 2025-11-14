#!/bin/bash
# S3 + CloudFront 배포 스크립트

set -e

# 설정
STAGE=${1:-prod}
BUCKET_NAME="qa-chatbot-${STAGE}-$(aws sts get-caller-identity --query Account --output text)"
CLOUDFRONT_ID=${2:-}  # CloudFront Distribution ID

echo "🚀 프론트엔드 배포 시작"
echo "Stage: $STAGE"
echo "Bucket: $BUCKET_NAME"

# 1. Next.js 빌드
echo "📦 Next.js 빌드 중..."
npm run build

# 2. S3에 업로드
echo "📤 S3에 파일 업로드 중..."
aws s3 sync ./out s3://$BUCKET_NAME \
  --delete \
  --cache-control "public, max-age=31536000, immutable" \
  --exclude "*.html" \
  --exclude "_next" \
  --region ap-northeast-1

# HTML 파일은 캐시 안 함
aws s3 sync ./out s3://$BUCKET_NAME \
  --delete \
  --cache-control "public, max-age=0, must-revalidate" \
  --include "*.html" \
  --region ap-northeast-1

# 3. CloudFront 캐시 무효화
if [ -n "$CLOUDFRONT_ID" ]; then
  echo "🔄 CloudFront 캐시 무효화 중..."
  aws cloudfront create-invalidation \
    --distribution-id $CLOUDFRONT_ID \
    --paths "/*" \
    --region ap-northeast-1
fi

echo "✅ 배포 완료!"
echo "🌐 URL: https://$BUCKET_NAME"
