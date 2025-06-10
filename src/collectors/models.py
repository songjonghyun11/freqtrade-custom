from pydantic import BaseModel
from typing import List, Optional

# 1. 뉴스 데이터 모델
class NewsData(BaseModel):
    title: str
    summary: Optional[str] = None
    url: Optional[str] = None
    timestamp: int

# 2. 오더북 데이터 모델
class OrderbookData(BaseModel):
    symbol: str
    bids: Optional[list] = None  # [(가격, 수량), ...]
    asks: Optional[list] = None
    timestamp: int

# 3. 공포·탐욕지수 데이터 모델
class FearGreedData(BaseModel):
    value: float           # 탐욕/공포 수치 (예: 72.0)
    value_classification: str  # (예: "Greed", "Fear")
    timestamp: int

# 4. 펀딩레이트 데이터 모델
class FundingRateData(BaseModel):
    symbol: str
    funding_rate: float
    timestamp: int

# 5. 소셜미디어 트렌드 데이터 모델
class SocialMediaTrend(BaseModel):
    keyword: str
    score: float
    timestamp: int

# 6. (필요시) 기타 데이터 모델도 여기에 추가
# 예시: YoutubeData, ChartVisionData 등
