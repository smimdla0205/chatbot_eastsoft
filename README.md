# Estsoft 인턴십 과제 – Vector DB 기반 Q&A 챗봇

## 프로젝트 개요
이 프로젝트는 제공된 엑셀 자료를 기반으로 정확한 응답만을 반환하는 지식 기반 챗봇을 구축하는 과제입니다. 사용자가 질문을 입력하면 임베딩을 통해 질문을 벡터화하고, 벡터 데이터베이스에서 가장 유사한 질문을 찾아 해당 답변만을 돌려줍니다. 생성형 모델을 통해 새로운 내용을 만들어내는 것이 아니라, 데이터셋에 있는 정답을 그대로 제공하는 것이 핵심입니다.

## 핵심 목표
- 질문‑답변 데이터셋(xlsx)을 활용하여 할루시네이션 없이 정확한 응답을 제공하는 챗봇을 만들고 배포합니다.
- 데이터셋 이외의 내용을 생성하지 않도록 유사도 임계값을 설정하여 잘못된 매칭을 줄입니다.
- Web UI와 API를 구축하고, 실제 서비스 환경(CloudFront/S3, API Gateway, Lambda)에 배포합니다.

## 사용 기술 스택
### 프런트엔드
- **Next.js + TypeScript**: 빠른 페이지 전환과 서버리스 환경과의 적합성.
- **Tailwind CSS**: 간결한 스타일 구성.

### 백엔드
- **AWS API Gateway + Lambda**: 서버 관리 없이 API 배포 가능. Lambda는 TypeScript로 작성.

### 임베딩 모델
- **AWS Bedrock – amazon.titan‑embed‑text‑v1**: 1536차원 벡터 생성, AWS 환경과 자연스러운 통합.

### 벡터 저장소
- **Amazon DynamoDB**: 질문·답변·임베딩 벡터를 JSON 형태로 저장. 데이터 규모가 작아도 빠른 처리 가능.

### 인프라
- 프런트는 **S3 + CloudFront**로 정적 배포.
- API는 별도 도메인 기반으로 구성.

## 설계 및 구현 설명
### 1. 데이터 준비 및 임베딩
- **scripts/ingest.py** 스크립트로 엑셀 데이터를 로딩.
- Titan 모델로 질문을 임베딩하여 1536차원 벡터 생성.
- 결과를 DynamoDB 테이블(`qa-documents`)에 저장.

### 2. 질의 처리 흐름
1. 사용자 질문을 /api/ask로 전달.
2. 입력 검증 후 Lambda에서 Titan 임베딩 API 호출.
3. 저장된 문서들과 코사인 유사도 계산.
4. 임계값(예: 0.75) 이하이면 "답변 없음" 반환.
5. 가장 유사한 질문의 답변을 반환.

### 3. 시스템 아키텍처
```
사용자 → API Gateway/Lambda → Bedrock 임베딩 → DynamoDB → Lambda 응답 → 사용자
```
서버리스 구조로 비용 최적화 및 확장성 확보.

## 정확도 향상 및 할루시네이션 방지 전략
- 입력 정규화(공백/대소문자/특수문자 통일).
- 유사도 임계값 도입.
- Top‑k=1 설정으로 잘못된 매칭 최소화.
- LLM 응답 비활성화, 오직 데이터셋 답변만 반환.

## 설치 및 실행 방법
### 로컬 개발
```
npm install
```
- `.env.local`에 API Gateway 주소 및 Bedrock 모델 설정.
```
npm run dev
```

### 데이터 ingest
```
python scripts/ingest.py --file data/샘플데이터.xlsx
```

### 배포
- 프론트: `npm run build` → S3 업로드 → CloudFront 연결.
- 백엔드: Lambda Zip 업로드 → API Gateway 연결.

## 평가 기준과 맞닿은 설계 포인트
| 평가 항목 | 반영 내용 |
|-----------|-----------|
| 정확성 40% | 임계값 기반 유사도 검색, 데이터셋 외 답변 차단 |
| 기술 설계 30% | 서버리스 구조, Bedrock 임베딩, 벡터 검색 구조의 타당성 |
| 완성도 20% | Next.js UI, CloudFront 배포, 안정적인 동작 |
| 문서/논리성 10% | 설계 이유·흐름을 명확한 구조로 기술 |

## 마무리 및 향후 확장
- 데이터 증가 시 Kendra, Qdrant 등 전용 벡터DB 도입 가능.
- 파라프레이즈 대응을 위한 semantic search 고도화 가능.
- 사용자 피드백 기반 정확도 조정 및 데이터 확장 가능.



## 배포 정보

### CloudFront 배포 주소
https://dwqkuear27d2d.cloudfront.net

### API Gateway 엔드포인트
https://t9886330ae.execute-api.ap-northeast-1.amazonaws.com/prod/ask

### S3 버킷
qa-chatbot-prod-887078546492

---

## AWS 인프라 구성

### DynamoDB 테이블
- 테이블명: `qa-documents`
- 주요 필드:
  - id (PK)
  - question
  - answer
  - embedding(1536차원)
  - created_at
  - source

### Bedrock
- 임베딩 모델: amazon.titan-embed-text-v1  
- LLM 모델: anthropic.claude-3-sonnet… (불사용, 데이터셋 기반 답변 보장)

---

## 주요 기능 요약

- Bedrock Titan 기반 임베딩 생성
- DynamoDB 벡터 스토리지
- 코사인 유사도 기반 검색
- Top-1 반환 + 임계값 기반 Zero Hallucination
- ChatGPT 스타일 Web UI (Next.js)
- API Gateway + Lambda 서버리스 구조


## 폴더 구조

```
project/
├── app/                        # Next.js App Router, 메인 페이지 및 글로벌 스타일
│   ├── globals.css
│   ├── layout.tsx
│   ├── page.tsx
│   └── api/
│       └── ask/
│           └── route.ts
├── components/                 # 프론트엔드 UI 컴포넌트
│   ├── ChatUI.tsx
│   └── ui/
│       └── button.tsx
├── lib/                        # 유틸리티 함수 및 모듈
│   └── utils.ts
├── backend/                    # AWS Lambda 백엔드 및 서버리스 설정
│   ├── package.json
│   ├── serverless.yml
│   ├── serverless.yml.bak
│   └── lambda/
│       ├── index.py
│       ├── chatbot-handler.py
│       ├── enhanced-chatbot-handler.py
│       ├── http-handler.py
│       ├── requirements.txt
│       ├── simple-chatbot-handler.py
│       ├── test-handler.py
│       └── bin/
│           └── jp.py
│       └── boto3/              # AWS SDK 소스 (로컬 패키징)
│       └── botocore/
│       └── 기타 라이브러리 폴더
├── scripts/                    # 데이터 처리 및 배포 스크립트
│   ├── ingest.py
│   ├── ingest_dynamodb.py
│   ├── insert_perso_qa.py
│   ├── insert_test_data.py
│   └── deploy-frontend.sh
├── public/                    
├── docs/                       # 프로젝트 문서 및 이슈 기록
│   ├── COMMIT_HISTORY.txt
│   ├── ISSUES.txt
├── README.md                  
├── package.json                
├── tsconfig.json            
├── postcss.config.mjs         
├── eslint.config.mjs           
├── next.config.ts             
├── next-env.d.ts               
```