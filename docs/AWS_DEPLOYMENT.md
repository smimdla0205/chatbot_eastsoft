# AWS 풀스택 배포 가이드

## 🏗️ 아키텍처 개요

```
CloudFront (CDN)
    ↓
S3 (Next.js 정적 파일)
    ↓
API Gateway
    ↓
Lambda (Bedrock + 벡터 검색)
    ↓
Bedrock (Claude 3 Sonnet + Titan Embeddings)
Supabase pgvector (Q&A 임베딩 저장소)
```

## 📋 필수 설정

### 1. AWS 계정 및 CLI 설정

```bash
# AWS CLI 설치 (이미 설치되었다면 스킵)
pip install awscli

# 자격증명 설정
aws configure
# 입력:
# - AWS Access Key ID: YOUR_ACCESS_KEY
# - AWS Secret Access Key: YOUR_SECRET_KEY
# - Default region: ap-northeast-1 (서울)
# - Default output format: json
```

### 2. Bedrock 모델 활성화

AWS Console에서 수동으로:

1. **Bedrock 콘솔 접속**
   - https://console.aws.amazon.com/bedrock/

2. **모델 활성화**
   - Model access → Edit model access
   - ✅ `Claude 3 Sonnet` 활성화
   - ✅ `Titan Embeddings` 활성화

### 3. IAM 역할 생성 (Lambda 실행 역할)

```bash
# 1. 신뢰 정책 파일 생성
cat > /tmp/trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# 2. IAM 역할 생성
aws iam create-role \
  --role-name LambdaChatbotRole \
  --assume-role-policy-document file:///tmp/trust-policy.json

# 3. Bedrock 권한 정책 생성
cat > /tmp/bedrock-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "*"
    }
  ]
}
EOF

# 4. 정책 연결
aws iam put-role-policy \
  --role-name LambdaChatbotRole \
  --policy-name BedrockPolicy \
  --policy-document file:///tmp/bedrock-policy.json

# 5. Lambda 기본 실행 권한도 추가
aws iam attach-role-policy \
  --role-name LambdaChatbotRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

### 4. Supabase 설정

```bash
# .env 파일에 추가
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
```

## 🚀 배포 단계

### Step 1: 데이터 임베딩 (Q&A.xlsx → Supabase)

```bash
# 환경 변수 설정
export SUPABASE_URL=https://your-project.supabase.co
export SUPABASE_ANON_KEY=your_key

# 데이터 임베딩 (Bedrock Titan Embeddings 사용)
python scripts/ingest.py data/Q&A.xlsx
```

### Step 2: Lambda 배포

```bash
cd backend

# serverless.yml 설정 (아래 참고)
# 또는 AWS CLI로 직접 배포

# AWS Lambda에 배포
serverless deploy --stage prod
```

**serverless.yml 예시:**

```yaml
service: vectordb-qa-chatbot

provider:
  name: aws
  runtime: python3.11
  region: ap-northeast-1
  role: arn:aws:iam::YOUR_ACCOUNT_ID:role/LambdaChatbotRole
  environment:
    SUPABASE_URL: ${env:SUPABASE_URL}
    SUPABASE_ANON_KEY: ${env:SUPABASE_ANON_KEY}
    BEDROCK_REGION: ap-northeast-1
    BEDROCK_MODEL_ID: anthropic.claude-3-sonnet-20240229-v1:0

functions:
  chat:
    handler: lambda/index.handler
    events:
      - http:
          path: ask
          method: post
          cors: true
    timeout: 30
    memorySize: 256

plugins:
  - serverless-python-requirements

custom:
  pythonRequirements:
    dockerizePip: true
```

### Step 3: API Gateway 엔드포인트 확인

배포 후 출력되는 URL:
```
endpoint: https://YOUR_API_ID.execute-api.ap-northeast-1.amazonaws.com/prod/ask
```

### Step 4: 프론트엔드 배포 (Vercel)

```bash
# .env.local에 Lambda 엔드포인트 추가
NEXT_PUBLIC_CHATBOT_API_URL=https://YOUR_API_ID.execute-api.ap-northeast-1.amazonaws.com/prod/ask

# GitHub에 푸시
git add .
git commit -m "AWS Bedrock integration"
git push origin main

# Vercel에서 자동 배포 (GitHub 연결 필요)
```

### Step 5: S3 + CloudFront 배포 (선택)

```bash
# 1. S3 버킷 생성
aws s3 mb s3://my-chatbot-bucket --region ap-northeast-1

# 2. Next.js 빌드
npm run build

# 3. S3에 업로드
aws s3 sync out/ s3://my-chatbot-bucket/ --delete

# 4. CloudFront 배포 생성 (AWS Console)
# Origin: S3 버킷
# Default Root Object: index.html
# Cache Behavior: 
#   - /api/* → Lambda (API Gateway 포함)
#   - /* → S3 (정적 파일)
```

## 🧪 테스트

### Lambda 로컬 테스트

```bash
# SAM으로 로컬 테스트 (선택)
sam local start-api

# 또는 직접 호출
curl -X POST http://localhost:3000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "회사 정보를 알려줘"}'
```

### 배포된 Lambda 테스트

```bash
curl -X POST https://YOUR_API_ID.execute-api.ap-northeast-1.amazonaws.com/prod/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "회사 정보를 알려줘"}'
```

## 📊 비용 추정

| 서비스 | 무료 티어 | 추가 비용 |
|--------|---------|----------|
| Lambda | 100만 요청/월 | $0.0000002/요청 |
| Bedrock | 첫 3개월 일부 무료 | Claude 3 Sonnet: $3/백만 토큰 |
| Titan Embeddings | - | $0.1/백만 토큰 |
| S3 | 5GB | $0.023/GB |
| CloudFront | 1TB/월 | $0.085/GB |
| API Gateway | 100만 호출/월 | $3.5/백만 호출 |

**월 예상 비용 (1,000 요청/일 기준):**
- Lambda: ~$0
- Bedrock (응답 생성): ~$2.50
- Embeddings: ~$0.50
- 기타: ~$1
- **총계: ~$4/월**

## 🔧 트러블슈팅

### Lambda 타임아웃

**문제**: Lambda 실행 시간 초과
```
Task timed out after 30 seconds
```

**해결**:
```bash
# serverless.yml에서 타임아웃 증가
timeout: 60  # 30초 → 60초
```

### Bedrock 모델 접근 불가

**문제**:
```
AccessDeniedException: User is not authorized to perform action
```

**해결**:
1. Bedrock 콘솔에서 모델 활성화 확인
2. IAM 역할에 Bedrock 권한 확인

### Supabase 연결 오류

**문제**:
```
Connection refused: SUPABASE_URL
```

**해결**:
1. 환경 변수 확인
2. Supabase 프로젝트 활성 상태 확인
3. pgvector RPC 함수 생성 확인

## 📖 유용한 링크

- [AWS Lambda 문서](https://docs.aws.amazon.com/lambda/)
- [AWS Bedrock 문서](https://docs.aws.amazon.com/bedrock/)
- [Serverless Framework](https://www.serverless.com/)
- [Supabase pgvector 가이드](https://supabase.com/docs/guides/database/extensions/pgvector)

---

**배포 예상 시간**: 30분~1시간
**난이도**: ⭐⭐⭐⭐ (중상)
