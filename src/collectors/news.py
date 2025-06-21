def fetch_news(symbol: str):
    # 8개 코인별 테스트용 더미 뉴스 반환
    return [
        {
            "title": f"테스트 뉴스 for {symbol}",
            "timestamp": 1710000000,
            "url": f"https://example.com/{symbol}/news",
            "source": "test",
            "content": "테스트 뉴스 컨텐츠입니다.",
        }
    ]
