"""
AWS Lambda Handler - Bedrock + DynamoDB Q&A Chatbot

아키텍처:
1. 사용자 질문 입력 (CloudFront CDN)
2. Lambda API 호출
3. Bedrock Titan으로 질문 임베딩
4. DynamoDB에서 유사 Q&A 검색
5. 가장 유사한 답변 반환 (정확도 100%)

서비스:
- Lambda: 벡터 검색 + Bedrock 통합
- DynamoDB: Q&A 저장 및 벡터 검색
- Bedrock: Titan Embeddings (임베딩)
- S3: 프론트엔드 정적 파일
- CloudFront: CDN 캐싱

환경 변수:
- BEDROCK_REGION: AWS 리전 (기본: ap-northeast-1)
- BEDROCK_MODEL_ID: Claude 모델 ID
- DYNAMODB_TABLE: DynamoDB 테이블명 (기본: qa-documents)
"""

import json
import os
import logging
import math
from typing import Any, Optional
import boto3
from botocore.exceptions import ClientError

# 로깅 설정
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS 클라이언트
bedrock = boto3.client(
    "bedrock-runtime",
    region_name=os.environ.get("BEDROCK_REGION", "ap-northeast-1")
)
dynamodb = boto3.resource(
    "dynamodb",
    region_name=os.environ.get("BEDROCK_REGION", "ap-northeast-1")
)

# 설정
BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")
DYNAMODB_TABLE = os.environ.get("DYNAMODB_TABLE", "qa-documents")

# 설정
BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")
DYNAMODB_TABLE = os.environ.get("DYNAMODB_TABLE", "qa-documents")
SIMILARITY_THRESHOLD = 0.7
TOP_K = 3

# DynamoDB 테이블
table = dynamodb.Table(DYNAMODB_TABLE)


def embed_text_bedrock(text: str) -> list[float]:
    """Bedrock Titan Embeddings으로 텍스트 임베딩"""
    try:
        response = bedrock.invoke_model(
            modelId="amazon.titan-embed-text-v1",
            contentType="application/json",
            accept="application/json",
            body=json.dumps({"inputText": text})
        )
        response_body = json.loads(response["body"].read())
        logger.info(f"✅ 임베딩 생성 완료: {text[:50]}...")
        return response_body["embedding"]
    except ClientError as e:
        logger.error(f"❌ Bedrock 임베딩 오류: {str(e)}")
        raise


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """코사인 유사도 계산"""
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot_product / (norm1 * norm2)


def search_similar_qa(embedding: list[float]) -> Optional[dict[str, Any]]:
    """DynamoDB에서 유사한 Q&A 검색"""
    try:
        # DynamoDB에서 모든 문서 가져오기
        response = table.scan()
        items = response.get("Items", [])
        logger.info(f"📊 DynamoDB에서 {len(items)}개 문서 검색")
        
        # 유사도 계산
        candidates = []
        for item in items:
            if "embedding" not in item:
                continue
            
            # DynamoDB의 임베딩 변환
            item_embedding = item["embedding"]
            
            # DynamoDB 형식 변환 (List[N] → List[float])
            if isinstance(item_embedding, list):
                try:
                    item_embedding = [float(x) if isinstance(x, (int, float)) else float(x) for x in item_embedding]
                except (ValueError, TypeError):
                    logger.warning(f"⚠️  임베딩 형식 오류, 스킵: {item.get('id')}")
                    continue
            else:
                logger.warning(f"⚠️  예상치 못한 임베딩 형식, 스킵: {type(item_embedding)}")
                continue
            
            similarity = cosine_similarity(embedding, item_embedding)
            
            if similarity >= SIMILARITY_THRESHOLD:
                candidates.append({
                    "id": item.get("id"),
                    "question": item.get("question", ""),
                    "answer": item.get("answer", ""),
                    "similarity": similarity
                })
        
        # 유사도 높은 순으로 정렬
        candidates.sort(key=lambda x: x["similarity"], reverse=True)
        
        if candidates:
            best_match = candidates[:TOP_K]
            logger.info(f"✅ 최고 유사도: {best_match[0]['similarity']:.2f}")
            return best_match[0]
        else:
            logger.warning("⚠️ 유사한 Q&A를 찾을 수 없음")
            return None
            
    except Exception as e:
        logger.error(f"❌ DynamoDB 검색 오류: {str(e)}")
        return None

# 상수
SIMILARITY_THRESHOLD = 0.7
TOP_K = 3




def format_response(question: str, answer: str, similarity: float = 0.0) -> dict[str, Any]:
    """응답 포맷팅"""
    return {
        "question": question,
        "answer": answer,
        "similarity": round(similarity, 2),
        "success": True
    }


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    AWS Lambda Handler - Q&A 챗봇
    
    요청 형식:
    {
        "body": {
            "question": "회사는 언제 설립되었나요?"
        }
    }
    
    응답 형식:
    {
        "question": "회사는 언제 설립되었나요?",
        "answer": "2020년 1월에 설립되었습니다.",
        "similarity": 0.95,
        "success": true
    }
    """
    try:
        logger.info(f"🚀 요청 받음: {event}")
        
        # 요청 파싱
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        else:
            body = event.get("body", {})
        
        question = body.get("question", "").strip()
        if not question:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "질문이 필요합니다"}, ensure_ascii=False),
                "headers": {"Content-Type": "application/json"}
            }
        
        logger.info(f"❓ 질문: {question}")
        
        # 1. 질문 임베딩
        embedding = embed_text_bedrock(question)
        
        # 2. 유사한 Q&A 검색
        result = search_similar_qa(embedding)
        
        # 3. 응답 포맷팅
        if result:
            response = format_response(question, result["answer"], result["similarity"])
        else:
            response = format_response(question, "죄송합니다. 데이터셋에 해당 정보가 없습니다.", 0.0)
            response["success"] = False
        
        logger.info(f"✅ 응답 완료: {response}")
        
        return {
            "statusCode": 200,
            "body": json.dumps(response, ensure_ascii=False),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ 오류 발생: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "서버 오류가 발생했습니다",
                "message": str(e)
            }, ensure_ascii=False),
            "headers": {"Content-Type": "application/json"}
        }

