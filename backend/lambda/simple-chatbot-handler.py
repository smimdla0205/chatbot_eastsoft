import json
import boto3
import logging
from datetime import datetime

# 로깅 설정
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    간단하고 효과적인 Claude 챗봇 Lambda 핸들러
    """
    
    # CORS 헤더
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    }
    
    # OPTIONS 요청 처리
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    try:
        # 요청 데이터 파싱
        body = json.loads(event.get('body', '{}'))
        user_question = body.get('question', '')
        game_type = body.get('gameType', '')
        question_text = body.get('questionText', '')
        
        if not user_question:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'error': '질문이 필요합니다.',
                    'success': False
                }, ensure_ascii=False)
            }
        
        logger.info(f"Question: {user_question[:100]}... (Game: {game_type})")
        
        # Claude 응답 생성
        claude_response = generate_claude_response(user_question, game_type, question_text)
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'response': claude_response,
                'timestamp': datetime.now().isoformat(),
                'success': True
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': '서버 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.',
                'success': False
            }, ensure_ascii=False)
        }

def generate_claude_response(user_question, game_type, question_text):
    """
    Claude를 사용한 응답 생성
    """
    try:
        # Bedrock 클라이언트 초기화
        bedrock = boto3.client(
            service_name='bedrock-runtime',
            region_name='us-east-1'
        )
        
        # 게임별 컨텍스트 설정
        game_context = get_game_context(game_type)
        
        # 시스템 프롬프트
        system_prompt = f"""당신은 경제 전문 AI 어시스턴트입니다.

게임 컨텍스트: {game_context}

다음 원칙을 따라 답변하세요:
1. 사용자의 질문에 직접적이고 유용한 답변 제공
2. 경제학적 관점에서 명확하고 이해하기 쉬운 설명
3. 구체적인 예시나 분석 포함
4. 200-300자 내외의 적절한 길이
5. 친근하고 전문적인 톤으로 한국어 작성"""

        # 사용자 프롬프트 구성
        user_prompt = f"질문: {user_question}"
        
        if question_text:
            user_prompt += f"\n\n현재 퀴즈 문제: {question_text}"
        
        user_prompt += "\n\n위 질문에 대해 경제학적 관점에서 도움이 되는 답변을 해주세요."

        # Claude 모델 호출
        model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 800,
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
        
        logger.info("Calling Claude API...")
        
        response = bedrock.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        logger.info(f"Claude response received: {response_body}")
        
        if response_body.get('content') and len(response_body['content']) > 0:
            claude_response = response_body['content'][0]['text']
            logger.info("Claude response generated successfully")
            return claude_response
        else:
            logger.error("Empty response from Claude")
            return generate_simple_response(user_question, game_type)
            
    except Exception as e:
        logger.error(f"Claude API error: {str(e)}")
        return generate_simple_response(user_question, game_type)

def get_game_context(game_type):
    """
    게임별 컨텍스트 반환
    """
    contexts = {
        'BlackSwan': '예측하기 어려운 극단적 경제 이벤트와 리스크 분석에 특화된 게임입니다.',
        'PrisonersDilemma': '경제적 딜레마 상황과 게임이론을 다루는 게임입니다.',
        'SignalDecoding': '경제 신호와 지표 해석을 다루는 게임입니다.'
    }
    return contexts.get(game_type, '경제 뉴스와 관련된 퀴즈 게임입니다.')

def generate_simple_response(user_question, game_type):
    """
    Claude 실패 시 간단한 응답
    """
    responses = {
        'BlackSwan': f"'{user_question}'에 대한 질문을 주셨네요. 블랙스완 이벤트는 예측하기 어려운 극단적 상황을 의미합니다. 경제에서는 이런 예상치 못한 사건들이 큰 영향을 미칠 수 있어 리스크 관리가 중요합니다. 더 구체적인 부분이 궁금하시면 자세히 설명해드릴게요.",
        
        'PrisonersDilemma': f"'{user_question}'에 대해 답변드리겠습니다. 죄수의 딜레마는 개인의 이익과 집단의 이익이 충돌하는 상황을 다룹니다. 경제에서는 이런 상황이 자주 발생하며, 협력과 경쟁의 균형이 중요합니다. 어떤 부분이 더 궁금하신가요?",
        
        'SignalDecoding': f"'{user_question}'에 대한 질문이군요. 경제 신호 해석은 다양한 지표와 데이터를 종합적으로 분석하는 것이 핵심입니다. 시장의 신호를 정확히 읽어내는 것이 중요한 경제적 판단의 기초가 됩니다. 구체적으로 어떤 신호나 지표가 궁금하신지 알려주세요."
    }
    
    return responses.get(game_type, f"'{user_question}'에 대한 질문을 주셨네요. 경제적 관점에서 분석해보면, 다양한 요인들을 종합적으로 고려해야 합니다. 더 구체적인 질문이 있으시면 자세히 답변해드리겠습니다.")