#!/usr/bin/env python3
"""
DynamoDB에 테스트 Q&A 데이터 삽입
"""
import boto3
import json
from datetime import datetime
import numpy as np

# AWS 설정
dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
bedrock = boto3.client('bedrock-runtime', region_name='ap-northeast-1')

TABLE_NAME = 'qa-documents'
BEDROCK_MODEL_ID = 'amazon.titan-embed-text-v1'

# 테스트 Q&A 데이터
TEST_DATA = [
    {
        'question': 'AWS Lambda란?',
        'answer': 'AWS Lambda는 서버를 관리할 필요 없이 코드를 실행할 수 있는 컴퓨팅 서비스입니다. 이벤트에 응답하여 자동으로 스케일링됩니다.'
    },
    {
        'question': 'DynamoDB의 장점은?',
        'answer': 'DynamoDB는 높은 성능, 자동 스케일링, 완전 관리형 NoSQL 데이터베이스로 유연한 데이터 모델을 제공합니다.'
    },
    {
        'question': 'CloudFront는 무엇인가?',
        'answer': 'CloudFront는 AWS의 Content Delivery Network(CDN)로 전 세계 엣지 로케이션을 통해 콘텐츠를 빠르게 전송합니다.'
    },
    {
        'question': 'S3 버킷이란?',
        'answer': 'S3는 Simple Storage Service의 약자로 AWS의 객체 스토리지 서비스입니다. 버킷은 S3 내의 최상위 폴더 개념입니다.'
    },
    {
        'question': 'Bedrock이란?',
        'answer': 'Amazon Bedrock은 기초 모델(Foundation Models)을 API로 제공하는 완전 관리형 서비스입니다. Claude, Llama 등의 모델을 사용할 수 있습니다.'
    }
]

def get_embedding(text):
    """Bedrock Titan으로 임베딩 생성"""
    try:
        response = bedrock.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps({'inputText': text})
        )
        result = json.loads(response['body'].read())
        embedding = result['embedding']
        # 임베딩을 정규화
        embedding_array = np.array(embedding)
        normalized = embedding_array / np.linalg.norm(embedding_array)
        return normalized.tolist()
    except Exception as e:
        print(f"❌ 임베딩 생성 오류: {e}")
        return None

def insert_test_data():
    """테스트 데이터를 DynamoDB에 삽입"""
    table = dynamodb.Table(TABLE_NAME)
    
    print(f"📊 테스트 데이터 {len(TEST_DATA)}개를 DynamoDB에 삽입 중...")
    
    for idx, qa in enumerate(TEST_DATA, 1):
        question = qa['question']
        answer = qa['answer']
        
        print(f"\n[{idx}/{len(TEST_DATA)}] Q: {question}")
        
        # 질문의 임베딩 생성
        embedding = get_embedding(question)
        if not embedding:
            print(f"⚠️  임베딩 생성 실패, 스킵")
            continue
        
        # DynamoDB에 저장
        try:
            table.put_item(
                Item={
                    'id': f'test-{idx}',
                    'question': question,
                    'answer': answer,
                    'embedding': embedding,
                    'created_at': datetime.now().isoformat(),
                    'source': 'test'
                }
            )
            print(f"✅ 저장 완료")
        except Exception as e:
            print(f"❌ 저장 오류: {e}")
    
    print("\n✅ 테스트 데이터 삽입 완료!")

if __name__ == '__main__':
    insert_test_data()
