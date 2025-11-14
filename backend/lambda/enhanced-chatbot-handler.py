import json
import boto3
import requests
import os
from datetime import datetime, timedelta
import logging

# 로깅 설정
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    RAG 기반 Claude 챗봇 Lambda 핸들러
    메인: Claude 순수 응답 / RAG: BigKinds + 퀴즈 기사 + 퀴즈 문제
    """
    
    # CORS 헤더
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    }
    
    # OPTIONS 요청 처리
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
        quiz_article_url = body.get('quizArticleUrl', '')
        
        if not user_question:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'error': '질문이 필요합니다.',
                    'success': False
                })
            }
        
        logger.info(f"RAG Query: {user_question[:50]}... (Game: {game_type})")
        
        # RAG 지식 베이스 수집
        knowledge_base = build_rag_knowledge_base(
            user_question, 
            question_text, 
            quiz_article_url, 
            game_type
        )
        
        # Claude 순수 응답 생성 (RAG 컨텍스트 포함)
        claude_response = generate_claude_rag_response(
            user_question,
            knowledge_base,
            game_type
        )
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'response': claude_response,
                'knowledge_sources': len(knowledge_base.get('sources', [])),
                'timestamp': datetime.now().isoformat(),
                'success': True
            })
        }
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': '서버 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.',
                'success': False
            })
        }

def build_rag_knowledge_base(user_question, question_text, quiz_article_url, game_type):
    """
    RAG 지식 베이스 구축 (3개 소스)
    1. BigKinds API 뉴스
    2. 퀴즈 관련 기사
    3. 퀴즈 문제 컨텍스트
    """
    knowledge_base = {
        'sources': [],
        'summary': ''
    }
    
    # 1. BigKinds API 뉴스 검색
    bigkinds_data = fetch_bigkinds_knowledge(user_question, game_type)
    if bigkinds_data:
        knowledge_base['sources'].append({
            'type': 'news_search',
            'title': 'BigKinds 뉴스 검색 결과',
            'content': bigkinds_data['content'],
            'articles_count': bigkinds_data['count']
        })
    
    # 2. 퀴즈 관련 기사 (URL이 제공된 경우)
    if quiz_article_url:
        article_data = fetch_quiz_article_knowledge(quiz_article_url)
        if article_data:
            knowledge_base['sources'].append({
                'type': 'quiz_article',
                'title': '퀴즈 관련 기사',
                'content': article_data['content'],
                'url': quiz_article_url
            })
    
    # 3. 퀴즈 문제 컨텍스트
    if question_text:
        knowledge_base['sources'].append({
            'type': 'quiz_context',
            'title': '퀴즈 문제 컨텍스트',
            'content': question_text,
            'game_type': game_type
        })
    
    # 지식 베이스 요약
    source_count = len(knowledge_base['sources'])
    knowledge_base['summary'] = f"{source_count}개 외부 지식 소스 활용"
    
    return knowledge_base

def fetch_bigkinds_knowledge(user_question, game_type):
    """
    BigKinds API에서 관련 뉴스 지식 수집
    """
    try:
        api_key = os.environ.get('BIGKINDS_API_KEY')
        if not api_key:
            logger.warning("BigKinds API key not found")
            return None
        
        # 게임별 키워드 추출
        keywords = extract_search_keywords(user_question, game_type)
        logger.info(f"BigKinds search keywords: {keywords}")
        
        # API 호출
        news_data = call_bigkinds_api(keywords, api_key)
        
        if news_data and news_data.get('return_object', {}).get('documents'):
            articles = news_data['return_object']['documents'][:3]
            
            # 뉴스 내용 통합
            combined_content = ""
            for i, article in enumerate(articles, 1):
                title = article.get('title', '')
                content = article.get('content', '')[:200]
                provider = article.get('provider', '')
                
                combined_content += f"[뉴스 {i}] {provider}: {title}\n{content}...\n\n"
            
            return {
                'content': combined_content.strip(),
                'count': len(articles)
            }
    
    except Exception as e:
        logger.error(f"BigKinds knowledge fetch error: {str(e)}")
    
    return None

def fetch_quiz_article_knowledge(article_url):
    """
    퀴즈 관련 기사 내용 추출 (URL에서)
    """
    try:
        # 실제 구현에서는 웹 스크래핑 또는 기사 API 사용
        # 현재는 URL 정보만 반환
        return {
            'content': f"퀴즈 관련 기사: {article_url}\n(기사 내용 추출 기능 구현 예정)",
            'url': article_url
        }
    
    except Exception as e:
        logger.error(f"Quiz article fetch error: {str(e)}")
    
    return None

def extract_search_keywords(user_question, game_type):
    """
    사용자 질문에서 검색 키워드 추출
    """
    # 기본 키워드
    base_keywords = []
    
    # 사용자 질문에서 핵심 단어 추출
    question_words = user_question.replace('?', '').replace('!', '').split()
    meaningful_words = [word for word in question_words if len(word) > 2]
    base_keywords.extend(meaningful_words[:3])
    
    # 게임별 관련 키워드 추가
    game_keywords = {
        'BlackSwan': ['위기', '리스크', '예측', '충격'],
        'PrisonersDilemma': ['경쟁', '협력', '전략', '딜레마'],
        'SignalDecoding': ['지표', '신호', '분석', '데이터']
    }
    
    if game_type in game_keywords:
        base_keywords.extend(game_keywords[game_type][:2])
    
    # 경제 관련 키워드 추가
    base_keywords.extend(['경제', '금융'])
    
    return ' '.join(base_keywords[:5])

def call_bigkinds_api(keywords, api_key):
    """
    BigKinds API 호출
    """
    try:
        url = "https://www.bigkinds.or.kr/api/news/search"
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        params = {
            'access_key': api_key,
            'argument': {
                'query': keywords,
                'published_at': {
                    'from': start_date.strftime('%Y-%m-%d'),
                    'until': end_date.strftime('%Y-%m-%d')
                },
                'provider': ['서울경제', '한국경제', '매일경제', '연합뉴스'],
                'category': ['경제', '사회', '정치'],
                'sort': {'date': 'desc'},
                'hilight': 200,
                'return_from': 0,
                'return_size': 3
            }
        }
        
        response = requests.post(url, json=params, timeout=15)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"BigKinds API error: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"BigKinds API call failed: {str(e)}")
        return None

def generate_claude_rag_response(user_question, knowledge_base, game_type):
    """
    RAG 기반 Claude 순수 응답 생성
    """
    try:
        # Bedrock 클라이언트 초기화
        bedrock = boto3.client(
            service_name='bedrock-runtime',
            region_name='us-east-1'
        )
        
        # 외부 지식이 있는지 확인
        has_external_knowledge = knowledge_base.get('sources') and len(knowledge_base['sources']) > 0
        
        if has_external_knowledge:
            # RAG 컨텍스트 구성
            rag_context = build_rag_context(knowledge_base)
            
            # 게임별 전문 시스템 프롬프트 (RAG 버전)
            system_prompt = f"""당신은 경제 전문 AI 어시스턴트입니다.

게임 컨텍스트: {get_game_description(game_type)}

다음 원칙을 따라 답변하세요:
1. 제공된 외부 지식을 적극 활용하되, 순수한 Claude의 분석력으로 답변
2. 최신 뉴스와 퀴즈 컨텍스트를 종합적으로 고려
3. 명확하고 전문적인 경제 분석 제공
4. 250-350자 내외의 적절한 길이
5. 한국어로 자연스럽게 작성"""

            # 사용자 프롬프트 (RAG 컨텍스트 포함)
            user_prompt = f"""질문: {user_question}

외부 지식 베이스:
{rag_context}

위 정보를 바탕으로 질문에 대해 전문적이고 통찰력 있는 답변을 해주세요."""
        else:
            # 순수 Claude 응답 (외부 지식 없음)
            system_prompt = f"""당신은 경제 전문 AI 어시스턴트입니다.

게임 컨텍스트: {get_game_description(game_type)}

다음 원칙을 따라 답변하세요:
1. 경제학적 지식과 분석력을 바탕으로 전문적인 답변 제공
2. 명확하고 이해하기 쉬운 설명
3. 실용적이고 통찰력 있는 관점 제시
4. 250-350자 내외의 적절한 길이
5. 한국어로 자연스럽게 작성"""

            user_prompt = f"""질문: {user_question}

위 질문에 대해 경제 전문가로서 전문적이고 통찰력 있는 답변을 해주세요."""

        # Claude 모델 호출
        model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "system": system_prompt,
            "messages": [
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        response = bedrock.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        
        if response_body.get('content') and len(response_body['content']) > 0:
            claude_response = response_body['content'][0]['text']
            knowledge_status = "RAG" if has_external_knowledge else "Pure Claude"
            logger.info(f"Claude {knowledge_status} response generated successfully")
            return claude_response
        else:
            logger.error("Empty response from Claude")
            return generate_fallback_response(user_question, game_type)
            
    except Exception as e:
        logger.error(f"Claude error: {str(e)}")
        return generate_fallback_response(user_question, game_type)

def build_rag_context(knowledge_base):
    """
    RAG 지식 베이스를 Claude 프롬프트용 컨텍스트로 변환
    """
    if not knowledge_base.get('sources'):
        return "외부 지식 정보가 없습니다."
    
    context_parts = []
    
    for i, source in enumerate(knowledge_base['sources'], 1):
        source_type = source.get('type', 'unknown')
        title = source.get('title', f'소스 {i}')
        content = source.get('content', '')
        
        if source_type == 'news_search':
            context_parts.append(f"📰 최신 뉴스 ({source.get('articles_count', 0)}건):\n{content}")
        elif source_type == 'quiz_article':
            context_parts.append(f"📄 퀴즈 관련 기사:\n{content}")
        elif source_type == 'quiz_context':
            context_parts.append(f"🎯 퀴즈 문제:\n{content}")
        else:
            context_parts.append(f"📋 {title}:\n{content}")
    
    return "\n\n".join(context_parts)

def get_game_description(game_type):
    """
    게임별 설명 반환
    """
    descriptions = {
        'BlackSwan': '예측하기 어려운 극단적 경제 이벤트 분석',
        'PrisonersDilemma': '경제적 딜레마와 게임이론 상황 분석',
        'SignalDecoding': '경제 신호와 지표 해석 분석'
    }
    return descriptions.get(game_type, '경제 뉴스 분석')

def generate_fallback_response(user_question, game_type):
    """
    Claude 실패 시 대체 응답
    """
    game_responses = {
        'BlackSwan': f"'{user_question}'에 대한 블랙스완 관점 분석을 제공하겠습니다. 예측하기 어려운 극단적 경제 상황에서는 리스크 관리와 불확실성 대응이 핵심입니다.",
        'PrisonersDilemma': f"'{user_question}'에 대한 게임이론적 분석을 제공하겠습니다. 경제적 딜레마에서는 개별 최적화와 집단 최적화 간의 균형이 중요합니다.",
        'SignalDecoding': f"'{user_question}'에 대한 경제 신호 분석을 제공하겠습니다. 다양한 경제 지표를 종합적으로 해석하는 것이 필요합니다."
    }
    
    base_response = game_responses.get(game_type, 
        f"'{user_question}'에 대한 경제적 관점에서 분석을 제공하겠습니다.")
    
    base_response += "\n\n더 구체적인 질문이 있으시면 언제든 말씀해 주세요."
    
    return base_response