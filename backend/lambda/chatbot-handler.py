import json
import boto3
import requests
import os
from datetime import datetime

def lambda_handler(event, context):
    """
    AI 챗봇 Lambda 핸들러
    빅카인즈 API를 활용하여 뉴스 기반 질문에 답변
    """
    
    # CORS 헤더
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    }
    
    # OPTIONS 요청 처리 (CORS preflight)
    if event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    try:
        # 요청 데이터 파싱
        body = json.loads(event['body'])
        user_question = body.get('question', '')
        game_type = body.get('gameType', '')
        question_text = body.get('questionText', '')
        question_index = body.get('questionIndex', 0)
        
        if not user_question:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'error': '질문이 필요합니다.',
                    'success': False
                })
            }
        
        # 빅카인즈 API 호출
        bigkinds_response = call_bigkinds_api(user_question, question_text)
        
        # AI 응답 생성
        ai_response = generate_ai_response(
            user_question, 
            question_text, 
            game_type, 
            bigkinds_response
        )
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'response': ai_response,
                'timestamp': datetime.now().isoformat(),
                'success': True
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': '서버 오류가 발생했습니다.',
                'success': False
            })
        }

def call_bigkinds_api(user_question, question_text):
    """
    빅카인즈 API 호출
    """
    try:
        # 빅카인즈 API 설정
        api_key = os.environ.get('BIGKINDS_API_KEY')
        if not api_key:
            return None
            
        # 검색 키워드 추출 (간단한 구현)
        keywords = extract_keywords(user_question, question_text)
        
        # 빅카인즈 API 호출
        url = "https://www.bigkinds.or.kr/api/news/search"
        params = {
            'access_key': api_key,
            'argument': {
                'query': keywords,
                'published_at': {
                    'from': '2024-01-01',
                    'until': '2025-12-31'
                },
                'provider': ['경향신문', '동아일보', '서울신문', '한겨레'],
                'category': ['정치', '경제', '사회'],
                'sort': {'date': 'desc'},
                'hilight': 200,
                'return_from': 0,
                'return_size': 5
            }
        }
        
        response = requests.post(url, json=params, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Bigkinds API error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Bigkinds API call failed: {str(e)}")
        return None

def extract_keywords(user_question, question_text):
    """
    질문에서 키워드 추출
    """
    # 간단한 키워드 추출 로직
    combined_text = f"{user_question} {question_text}"
    
    # 경제 관련 키워드 우선 추출
    economic_keywords = [
        '금리', '환율', '주식', '부동산', '인플레이션', '경제성장',
        '수출', '수입', '무역', '투자', '소비', '고용', '실업',
        '코스피', '코스닥', '달러', '원화', 'GDP', 'CPI'
    ]
    
    found_keywords = []
    for keyword in economic_keywords:
        if keyword in combined_text:
            found_keywords.append(keyword)
    
    # 키워드가 없으면 첫 번째 명사 추출 (간단한 구현)
    if not found_keywords:
        words = combined_text.split()
        found_keywords = [word for word in words if len(word) > 1][:3]
    
    return ' '.join(found_keywords[:3])

def generate_ai_response(user_question, question_text, game_type, bigkinds_data):
    """
    AI 응답 생성
    """
    # 게임 타입별 컨텍스트
    game_context = {
        'BlackSwan': '예측하기 어려운 경제 이벤트',
        'PrisonersDilemma': '경제적 딜레마 상황',
        'SignalDecoding': '경제 신호 해석'
    }
    
    context = game_context.get(game_type, '경제 뉴스')
    
    # 기본 응답 템플릿
    if bigkinds_data and bigkinds_data.get('return_object', {}).get('documents'):
        # 빅카인즈 데이터가 있는 경우
        articles = bigkinds_data['return_object']['documents'][:2]
        
        response = f"'{user_question}'에 대한 답변을 드리겠습니다.\n\n"
        response += f"**{context} 관련 최신 뉴스:**\n"
        
        for i, article in enumerate(articles, 1):
            title = article.get('title', '제목 없음')
            content = article.get('content', '')[:200] + '...'
            response += f"{i}. {title}\n{content}\n\n"
        
        response += "위 뉴스를 바탕으로 보면, 현재 경제 상황과 관련하여 추가적인 분석이 필요합니다. 더 구체적인 질문이 있으시면 언제든 말씀해 주세요."
        
    else:
        # 빅카인즈 데이터가 없는 경우 기본 응답
        response = f"'{user_question}'에 대한 질문을 받았습니다.\n\n"
        response += f"이 질문은 {context}와 관련이 있어 보입니다. "
        response += "현재 관련 뉴스 데이터를 분석하고 있으며, 더 정확한 정보를 위해 추가적인 경제 지표와 뉴스를 검토하겠습니다.\n\n"
        response += "구체적으로 어떤 부분이 궁금하신지 알려주시면 더 자세한 답변을 드릴 수 있습니다."
    
    return response