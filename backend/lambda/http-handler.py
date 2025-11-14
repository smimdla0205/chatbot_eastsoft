import json
import logging
from datetime import datetime

# 로깅 설정
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    HTTP API v2용 챗봇 핸들러
    """
    
    logger.info(f"Received event: {json.dumps(event)}")
    
    # CORS 헤더
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    }
    
    # OPTIONS 요청 처리
    if event.get('requestContext', {}).get('http', {}).get('method') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    try:
        # HTTP API v2 형식에서 body 파싱
        body_str = event.get('body', '{}')
        logger.info(f"Body string: {body_str}")
        
        body = json.loads(body_str)
        user_question = body.get('question', '')
        game_type = body.get('gameType', '')
        
        logger.info(f"Question: {user_question}, Game: {game_type}")
        
        if not user_question:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'error': '질문이 필요합니다.',
                    'success': False
                })
            }
        
        # 간단한 응답 생성
        response_text = generate_response(user_question, game_type)
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'response': response_text,
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
                'error': f'서버 오류: {str(e)}',
                'success': False
            })
        }

def generate_response(user_question, game_type):
    """
    질문에 따른 맞춤형 응답 생성
    """
    
    # "정답이 이해가 안 간다" 패턴 감지
    if any(word in user_question for word in ["정답", "이해", "헷갈", "모르겠"]):
        if game_type == "BlackSwan":
            return """블랙스완 게임에서 정답이 이해가 안 가신다면, 다음을 고려해보세요:

1. **예측 불가능성**: 블랙스완 이벤트는 일반적인 예측 모델로는 파악하기 어려운 극단적 사건입니다.

2. **낮은 확률, 높은 영향**: 발생 확률은 매우 낮지만, 한 번 발생하면 경제 전체에 큰 충격을 줍니다.

3. **사후 설명 가능성**: 일어난 후에는 그럴듯한 설명이 가능하지만, 사전에는 예측하기 어렵습니다.

구체적으로 어떤 문제나 개념이 궁금하신지 알려주시면 더 자세히 설명해드릴게요."""

        elif game_type == "PrisonersDilemma":
            return """죄수의 딜레마에서 정답이 헷갈리신다면, 핵심 원리를 이해해보세요:

1. **개인 vs 집단 이익**: 각자가 자신의 이익만 추구하면 모두에게 나쁜 결과가 나올 수 있습니다.

2. **협력의 딜레마**: 협력이 최선이지만, 상대방이 배신할 가능성 때문에 협력하기 어렵습니다.

3. **경제적 적용**: 가격 경쟁, 환경 보호, 공공재 문제 등에서 자주 나타납니다.

어떤 상황이나 문제가 특히 어려우신지 말씀해주세요."""

        elif game_type == "SignalDecoding":
            return """경제 신호 해석이 어려우시다면, 다음 접근법을 시도해보세요:

1. **다중 지표 분석**: 하나의 지표만 보지 말고 여러 경제 지표를 종합적으로 판단하세요.

2. **맥락 이해**: 같은 지표라도 경제 상황에 따라 다른 의미를 가질 수 있습니다.

3. **시간적 관점**: 단기적 변동과 장기적 추세를 구분해서 해석하세요.

구체적으로 어떤 경제 지표나 신호가 궁금하신가요?"""

        else:
            return """경제 문제의 정답을 이해하기 어려우시군요. 경제학에서는 다음과 같은 접근이 도움됩니다:

1. **기본 원리 파악**: 수요와 공급, 기회비용 등 기본 개념부터 차근차근 이해하세요.

2. **실제 사례 연결**: 이론을 현실의 경제 상황과 연결해서 생각해보세요.

3. **단계별 분석**: 복잡한 문제는 작은 단위로 나누어 분석하세요.

어떤 구체적인 부분이 가장 궁금하신지 알려주시면 더 도움을 드릴 수 있습니다."""
    
    # 일반적인 질문에 대한 응답
    game_responses = {
        'BlackSwan': f"'{user_question}'에 대한 블랙스완 관점에서 답변드리겠습니다. 예측하기 어려운 극단적 경제 상황에서는 리스크 관리와 불확실성 대응이 핵심입니다. 더 구체적인 질문이 있으시면 언제든 말씀해주세요.",
        
        'PrisonersDilemma': f"'{user_question}'에 대한 게임이론적 분석을 제공하겠습니다. 경제적 딜레마에서는 개별 최적화와 집단 최적화 간의 균형이 중요합니다. 어떤 부분이 더 궁금하신가요?",
        
        'SignalDecoding': f"'{user_question}'에 대한 경제 신호 분석을 해드리겠습니다. 다양한 경제 지표를 종합적으로 해석하는 것이 필요합니다. 구체적으로 어떤 신호나 지표가 궁금하신지 알려주세요."
    }
    
    return game_responses.get(game_type, f"'{user_question}'에 대한 질문을 주셨네요. 경제적 관점에서 분석해보면, 다양한 요인들을 종합적으로 고려해야 합니다. 더 구체적인 질문이 있으시면 자세히 답변해드리겠습니다.")