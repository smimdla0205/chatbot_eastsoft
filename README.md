# Q&A 챗봇 - Vector DB 기반 질의응답 시스템

## 배포 정보

### CloudFront 배포 주소
```
https://dwqkuear27d2d.cloudfront.net
```

### API Gateway 주소
```
https://t9886330ae.execute-api.ap-northeast-1.amazonaws.com/prod/ask
```

### S3 버킷
```
qa-chatbot-prod-887078546492
```

---

## AWS 인프라

### DynamoDB 테이블 구조
**테이블명**: `qa-documents`

| 필드 | 타입 | 설명 |
|------|------|------|
| `id` | String (PK) | 문서 고유 ID |
| `question` | String | 질문 텍스트 |
| `answer` | String | 답변 텍스트 |
| `embedding` | List[Number] | Titan Embeddings (1536차원) |
| `created_at` | String | 생성 일시 (ISO 8601) |
| `source` | String | 데이터 출처 |

### Amazon Bedrock 모델
- **임베딩 모델**: `amazon.titan-embed-text-v1` (1536차원 벡터)
- **LLM 모델**: `anthropic.claude-3-sonnet-20240229-v1:0` (미사용 - 정확한 답변만 반환)

---

## 주요 기능

- Vector DB 기반 유사도 검색 (Cosine Similarity)
- Zero Hallucination (데이터셋 기반 정확한 답변만 반환)
- ChatGPT 스타일 UI
- 실시간 질의응답
- AWS 서버리스 아키텍처