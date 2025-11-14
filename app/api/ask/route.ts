import { NextRequest, NextResponse } from 'next/server';

/**
 * 벡터 검색 API 라우트
 * 
 * 요청:
 * POST /api/ask
 * {
 *   "question": "사용자 질문"
 * }
 * 
 * 응답:
 * {
 *   "answer": "답변 텍스트",
 *   "source": {
 *     "question": "원본 질문",
 *     "similarity": 0.95
 *   },
 *   "success": true
 * }
 */

interface AskRequest {
  question: string;
}

interface AskResponse {
  answer: string;
  source: {
    question: string;
    similarity: number;
  } | null;
  success: boolean;
  error?: string;
}

export async function POST(request: NextRequest): Promise<NextResponse<AskResponse>> {
  try {
    const body: AskRequest = await request.json();
    const { question } = body;

    if (!question || question.trim() === '') {
      return NextResponse.json(
        {
          answer: '',
          source: null,
          success: false,
          error: '질문이 비어있습니다',
        },
        { status: 400 }
      );
    }

    // Lambda 엔드포인트 호출
    const lambdaUrl = process.env.NEXT_PUBLIC_CHATBOT_API_URL;

    if (!lambdaUrl) {
      console.warn('⚠️  NEXT_PUBLIC_CHATBOT_API_URL이 설정되지 않았습니다');
      // 로컬 개발용 Mock 응답
      return NextResponse.json({
        answer: `[Mock] 질문: "${question}" - 실제 Lambda 연결 필요`,
        source: null,
        success: true,
      });
    }

    const response = await fetch(lambdaUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ question }),
    });

    if (!response.ok) {
      throw new Error(`Lambda 오류: ${response.statusText}`);
    }

    const lambdaResponse: AskResponse = await response.json();
    
    return NextResponse.json(lambdaResponse);

  } catch (error) {
    console.error('❌ API 오류:', error);
    return NextResponse.json(
      {
        answer: '죄송하지만, 처리 중 오류가 발생했습니다.',
        source: null,
        success: false,
        error: error instanceof Error ? error.message : '알 수 없는 오류',
      },
      { status: 500 }
    );
  }
}
