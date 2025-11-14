#!/usr/bin/env python3
"""
Perso.ai Q&A 데이터를 DynamoDB에 삽입
"""
import boto3
import json
from decimal import Decimal

# AWS 설정
dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
bedrock = boto3.client('bedrock-runtime', region_name='ap-northeast-1')

TABLE_NAME = 'qa-documents'
BEDROCK_MODEL_ID = 'amazon.titan-embed-text-v1'

# Perso.ai Q&A 데이터
QA_DATA = [
    {
        'question': 'Perso.ai는 어떤 서비스인가요?',
        'answer': 'Perso.ai는 이스트소프트가 개발한 다국어 AI 영상 더빙 플랫폼으로, 누구나 언어의 장벽 없이 영상을 제작하고 공유할 수 있도록 돕는 AI SaaS 서비스입니다.'
    },
    {
        'question': 'Perso.ai의 주요 기능은 무엇인가요?',
        'answer': 'Perso.ai는 AI 음성 합성, 립싱크, 영상 더빙 기능을 제공합니다. 사용자는 원본 영상에 다른 언어로 음성을 입히거나, 입 모양까지 자동으로 동기화할 수 있습니다.'
    },
    {
        'question': 'Perso.ai는 어떤 기술을 사용하나요?',
        'answer': 'Perso.ai는 ElevenLabs, Microsoft, Google Cloud Speech API 등과 같은 글로벌 기술 파트너의 음성합성 및 번역 기술을 활용하며, 자체 개발한 립싱크 엔진을 결합합니다.'
    },
    {
        'question': 'Perso.ai의 사용자는 어느 정도인가요?',
        'answer': '2025년 기준, 전 세계 누적 20만 명 이상의 사용자가 Perso.ai를 통해 AI 기반 영상 제작을 경험했습니다.'
    },
    {
        'question': 'Perso.ai를 사용하는 주요 고객층은 누구인가요?',
        'answer': '유튜버, 강의 제작자, 기업 마케팅 담당자 등 영상 콘텐츠를 다국어로 확장하려는 개인 및 기업 고객이 주요 타깃입니다.'
    },
    {
        'question': 'Perso.ai에서 지원하는 언어는 몇 개인가요?',
        'answer': '현재 30개 이상의 언어를 지원하며, 한국어, 영어, 일본어, 스페인어, 포르투갈어 등 주요 언어가 포함됩니다.'
    },
    {
        'question': 'Perso.ai의 요금제는 어떻게 구성되어 있나요?',
        'answer': 'Perso.ai는 사용량 기반 구독 모델을 운영합니다. Free, Creator, Pro, Enterprise 플랜이 있으며 Stripe를 통해 결제할 수 있습니다.'
    },
    {
        'question': 'Perso.ai는 어떤 기업이 개발했나요?',
        'answer': 'Perso.ai는 소프트웨어 기업 이스트소프트(ESTsoft)가 개발했습니다.'
    },
    {
        'question': '이스트소프트는 어떤 회사인가요?',
        'answer': '이스트소프트는 1993년에 설립된 IT 기업으로, 알집, 알약, 알씨 등 생활형 소프트웨어로 잘 알려져 있으며, 최근에는 인공지능 기반 서비스 개발에 집중하고 있습니다.'
    },
    {
        'question': 'Perso.ai의 기술적 강점은 무엇인가요?',
        'answer': 'AI 음성 합성과 립싱크 정확도가 높고, 다국어 영상 제작이 간편하며, 실제 사용자 인터페이스가 직관적이라는 점이 강점입니다.'
    },
    {
        'question': 'Perso.ai를 사용하려면 회원가입이 필요한가요?',
        'answer': '네, 이메일 또는 구글 계정으로 간단히 회원가입 후 서비스를 이용할 수 있습니다.'
    },
    {
        'question': 'Perso.ai를 이용하려면 영상 편집 지식이 필요한가요?',
        'answer': '아니요. Perso.ai는 누구나 쉽게 사용할 수 있도록 설계되어 있어, 영상 편집 경험이 없어도 바로 더빙을 시작할 수 있습니다.'
    },
    {
        'question': 'Perso.ai 고객센터는 어떻게 문의하나요?',
        'answer': 'Perso.ai 웹사이트 하단의 \'문의하기\' 버튼을 통해 이메일 또는 채팅으로 고객센터에 문의할 수 있습니다.'
    },
]

def get_embedding(text):
    """Bedrock Titan으로 임베딩 생성"""
    try:
        response = bedrock.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps({'inputText': text})
        )
        result = json.loads(response['body'].read())
        # Decimal로 변환 (DynamoDB 호환)
        embedding = [Decimal(str(x)) for x in result['embedding']]
        return embedding
    except Exception as e:
        print(f"❌ 임베딩 생성 오류: {e}")
        return None

def insert_qa_data():
    """Perso.ai Q&A 데이터를 DynamoDB에 삽입"""
    table = dynamodb.Table(TABLE_NAME)
    
    # 기존 테스트 데이터 삭제
    print("🗑️  기존 테스트 데이터 삭제 중...")
    response = table.scan()
    for item in response.get('Items', []):
        if item['id'].startswith('test-'):
            table.delete_item(Key={'id': item['id']})
            print(f"   삭제: {item['id']}")
    
    print(f"\n📊 Perso.ai Q&A 데이터 {len(QA_DATA)}개를 DynamoDB에 삽입 중...\n")
    
    for idx, qa in enumerate(QA_DATA, 1):
        question = qa['question']
        answer = qa['answer']
        
        print(f"[{idx}/{len(QA_DATA)}] {question}")
        
        # 질문의 임베딩 생성
        embedding = get_embedding(question)
        if not embedding:
            print(f"   ⚠️  임베딩 생성 실패, 스킵")
            continue
        
        # DynamoDB에 저장
        try:
            table.put_item(
                Item={
                    'id': f'perso-{idx}',
                    'question': question,
                    'answer': answer,
                    'embedding': embedding,
                    'created_at': '2025-11-14T00:00:00',
                    'source': 'perso.ai'
                }
            )
            print(f"   ✅ 저장 완료\n")
        except Exception as e:
            print(f"   ❌ 저장 오류: {e}\n")
    
    print("✅ Perso.ai Q&A 데이터 삽입 완료!")
    print(f"📈 총 {len(QA_DATA)}개의 Q&A가 DynamoDB에 저장되었습니다.")

if __name__ == '__main__':
    insert_qa_data()
