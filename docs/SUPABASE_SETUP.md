# Supabase pgvector 설정 가이드

## 📋 Supabase 프로젝트 생성

### 1단계: 프로젝트 생성

1. https://supabase.com에 접속
2. Sign Up (또는 로그인)
3. **New Project** 클릭
4. 설정:
   - **Project name**: `vectordb-qa-chatbot`
   - **Database password**: 강력한 비밀번호 설정
   - **Region**: `Asia Pacific (Singapore)` 또는 `Tokyo`
   - **Pricing Plan**: Free

### 2단계: pgvector 확장 활성화

```sql
-- SQL Editor에서 실행
CREATE EXTENSION IF NOT EXISTS vector;
```

또는 Dashboard에서:
1. Extensions 메뉴
2. `vector` 검색
3. Enable 클릭

## 🗂️ 테이블 생성

### SQL 스크립트

```sql
-- Q&A 데이터 테이블
CREATE TABLE qa_embeddings (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  question TEXT NOT NULL,
  answer TEXT NOT NULL,
  embedding VECTOR(1536),  -- OpenAI/Bedrock Titan Embeddings 차원
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- 임베딩 인덱스 (빠른 검색)
CREATE INDEX ON qa_embeddings USING IVFFLAT (embedding VECTOR_COSINE_OPS)
WITH (lists = 100);

-- 벡터 검색 함수 (RPC)
CREATE OR REPLACE FUNCTION match_qa (
  query_embedding VECTOR(1536),
  match_count INT DEFAULT 3,
  match_threshold FLOAT DEFAULT 0.7
)
RETURNS TABLE (
  id BIGINT,
  question TEXT,
  answer TEXT,
  similarity FLOAT
)
LANGUAGE SQL
AS $$
  SELECT
    id,
    question,
    answer,
    1 - (embedding <=> query_embedding) AS similarity
  FROM qa_embeddings
  WHERE 1 - (embedding <=> query_embedding) > match_threshold
  ORDER BY embedding <=> query_embedding
  LIMIT match_count;
$$;
```

### 단계별 실행

1. **Supabase Dashboard** 접속
2. **SQL Editor** 클릭
3. **New Query** 클릭
4. 위 SQL 복사 & 붙여넣기
5. **Run** 클릭

## 🔐 Row Level Security (RLS) 설정

```sql
-- RLS 활성화
ALTER TABLE qa_embeddings ENABLE ROW LEVEL SECURITY;

-- 모든 사용자가 읽기 가능 (인증 필요 없음)
CREATE POLICY "Allow read access to all users"
ON qa_embeddings
FOR SELECT
USING (true);

-- 인증된 사용자만 쓰기 가능
CREATE POLICY "Allow insert to authenticated users"
ON qa_embeddings
FOR INSERT
WITH CHECK (auth.role() = 'authenticated');
```

## 📡 API 키 얻기

1. **Settings** → **API**
2. 다음 정보 복사:
   - **Project URL**: `https://your-project.supabase.co`
   - **anon (public)**: 공개 키

### .env 파일에 추가

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_public_key
```

## 🧪 테스트

### JavaScript/TypeScript

```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
);

// 임베딩 삽입
await supabase.from('qa_embeddings').insert({
  question: '회사는 언제 설립되었나요?',
  answer: '2020년 1월에 설립되었습니다.',
  embedding: [0.1, 0.2, ...] // 1536 차원 벡터
});

// 벡터 검색 (RPC 호출)
const { data } = await supabase.rpc('match_qa', {
  query_embedding: [0.1, 0.2, ...],
  match_count: 3,
  match_threshold: 0.7
});

console.log(data);
// [
//   {
//     id: 1,
//     question: '회사는 언제 설립되었나요?',
//     answer: '2020년 1월에 설립되었습니다.',
//     similarity: 0.95
//   }
// ]
```

### Python

```python
import httpx

url = "https://your-project.supabase.co/rest/v1/rpc/match_qa"
headers = {
    "Authorization": "Bearer your_public_key",
    "Content-Type": "application/json",
}
payload = {
    "query_embedding": [0.1, 0.2, ...],  # 1536 차원
    "match_count": 3,
    "match_threshold": 0.7
}

with httpx.Client() as client:
    response = client.post(url, json=payload, headers=headers)
    print(response.json())
```

## 📊 데이터 확인

1. **Table Editor** 클릭
2. `qa_embeddings` 선택
3. 데이터 확인

## 🔄 데이터 백업

```bash
# Supabase 프로젝트 export
# Dashboard → Backups → Download

# 또는 PostgreSQL 명령어
pg_dump "postgresql://user:password@db.supabase.co/postgres" > backup.sql
```

## ⚡ 성능 최적화

### 인덱스 모니터링

```sql
-- 인덱스 통계
SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan,
  idx_tup_read,
  idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

### 벡터 검색 최적화

- **IVFFLAT**: 빠른 검색, 메모리 효율
- **HNSW**: 매우 빠른 검색, 메모리 사용 많음

```sql
-- HNSW 인덱스 (더 빠름)
CREATE INDEX ON qa_embeddings USING HNSW (embedding VECTOR_COSINE_OPS);
```

## 🆘 트러블슈팅

### "pgvector not available" 오류

**해결**: 확장이 비활성화됨
```sql
CREATE EXTENSION vector;
```

### 느린 검색 속도

**해결**: 인덱스 재생성
```sql
REINDEX INDEX qa_embeddings_embedding_idx;
```

### API 키 누출

**대응**:
1. Dashboard → API → Regenerate Key
2. 새 키로 애플리케이션 업데이트

## 📈 확장

### 용량 증대

- Free: 500MB
- Pro: 8GB (+ 추가 비용)
- Custom: 무제한

### 다중 테이블

```sql
-- 다른 데이터 소스용 테이블
CREATE TABLE faq_embeddings (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  category TEXT,
  question TEXT NOT NULL,
  answer TEXT NOT NULL,
  embedding VECTOR(1536),
  created_at TIMESTAMP DEFAULT NOW()
);

-- 통합 검색 함수
CREATE OR REPLACE FUNCTION search_all (
  query_embedding VECTOR(1536),
  match_count INT DEFAULT 5
)
RETURNS TABLE (
  source TEXT,
  id BIGINT,
  question TEXT,
  answer TEXT,
  similarity FLOAT
)
LANGUAGE SQL
AS $$
  (
    SELECT 'qa' AS source, id, question, answer, 1 - (embedding <=> query_embedding) AS similarity
    FROM qa_embeddings
    WHERE 1 - (embedding <=> query_embedding) > 0.7
    ORDER BY embedding <=> query_embedding
    LIMIT match_count
  )
  UNION ALL
  (
    SELECT 'faq' AS source, id, question, answer, 1 - (embedding <=> query_embedding) AS similarity
    FROM faq_embeddings
    WHERE 1 - (embedding <=> query_embedding) > 0.7
    ORDER BY embedding <=> query_embedding
    LIMIT match_count
  )
  ORDER BY similarity DESC
  LIMIT match_count;
$$;
```

---

**설정 예상 시간**: 15분
**난이도**: ⭐⭐ (쉬움)
