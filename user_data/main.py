# import logging
# import os
# import time
# from datetime import datetime, timedelta
from utils.fees import calculate_fee_type
from utils.slippage import estimate_slippage_advanced
from models import Order, Position
from utils.metrics import calculate_var, calculate_mdd

# from persistence.database_manager import DatabaseManager
# from collectors.news import NewsCollector
# from collectors.orderbook import OrderbookCollector
# from collectors.fear_greed import FearGreedCollector
# from collectors.funding_rate import FundingRateCollector
# from collectors.social_media import SocialMediaCollector

# from strategies.HybridAlligatorATRRelaxedStrategy import HybridAlligatorATRRelaxedStrategy
# from strategies.rsi_momentum_strategy import RSIMomentumStrategy
# from strategies.funding_rate_strategy import FundingRateStrategy
# from strategies.news_sentiment_strategy import NewsSentimentStrategy

# from strategies.short_rsi_overbought_strategy import ShortRSIOverboughtStrategy
# from strategies.short_funding_rate_strategy import ShortFundingRateStrategy
# from strategies.short_orderbook_imbalance_strategy import ShortOrderbookImbalanceStrategy
# from strategies.short_news_strategy import ShortNewsStrategy

# # 환경변수 로드
# load_dotenv()

# TELEGRAM_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
# TELEGRAM_CHAT_ID = os.getenv("TG_CHAT_ID")

# def send_alert(msg):
#     url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
#     payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg}
#     try:
#         requests.post(url, json=payload, timeout=10)  # data → json
#     except Exception as e:
#         print(f"[ALERT 실패] {e}")

# # 1. 환경/보안/운영 분리
# API_KEYS = {
#     "binance": os.getenv("BINANCE_KEY"),
#     "news_api": os.getenv("NEWSAPI_KEY"),
# }
# DB_PATH = os.getenv("TRADE_DB", "sqlite:///user_data/trades.sqlite")
# ENV = os.getenv("ENV", "dev")
# IS_PROD = ENV == "prod"

# # 2. 장애/알림/이력/자동복구 관리
# collector_error_count = {k: 0 for k in ["news", "orderbook", "fg", "funding", "trends"]}
# COLLECTOR_ERROR_LIMIT = 3
# trading_state = {"paused": False, "pause_reason": None, "paused_at": None}
# incident_log = []  # 장애이력 기록용

# def send_alert(msg):
#     print(f"[ALERT]{msg}")
#     # 실전은 슬랙, 카톡, SMS, 이메일 등으로 확장

# def record_incident(type_, reason):
#     now = datetime.now()
#     incident_log.append({
#         "type": type_,
#         "reason": reason,
#         "timestamp": now
#     })
#     send_alert(f"[장애기록] {type_}: {reason} ({now})")

# def pause_trading(reason):
#     trading_state["paused"] = True
#     trading_state["pause_reason"] = reason
#     trading_state["paused_at"] = datetime.now()
#     record_incident("pause", reason)

# def resume_trading():
#     trading_state["paused"] = False
#     trading_state["pause_reason"] = None
#     trading_state["paused_at"] = None
#     record_incident("resume", "collector 정상화")

# def backup_db_and_logs():
#     # 실전은 S3/FTP/클라우드 업로드 등 자동화 필요
#     os.system("cp user_data/trades.sqlite user_data/trades_backup.sqlite")
#     os.system("cp logs/app.log logs/app_backup.log")

# # 3. 포지션/주문 상태(실거래소 동기화)
# class PositionManager:
#     def __init__(self):
#         self.open_positions = {}  # symbol -> Position 객체

#     def has_open_position(self, symbol):
#         return symbol in self.open_positions

#     def open_position(self, symbol, position_obj):
#         self.open_positions[symbol] = position_obj  # dict → DTO

#     def close_position(self, symbol):
#         if symbol in self.open_positions:
#             del self.open_positions[symbol]

#     def sync_with_exchange(self):
#         # 실전 거래소 API fetch→내부 포지션 동기화 (예시)
#         pass

# position_manager = PositionManager()

# # 4. 신호 중복/이상치/스푸핑 감시
# def is_duplicate_signal(signal, prev_signals, dt_limit=timedelta(minutes=5)):
#     for prev in prev_signals:
#         if (
#             prev.symbol == signal.symbol
#             and prev.strategy_name == signal.strategy_name
#             and prev.direction == signal.direction
#             and abs(prev.timestamp - signal.timestamp) < dt_limit
#         ):
#             return True
#     return False

# def is_invalid_strength(strength):
#     return strength is None or not (-1 <= strength <= 1) or abs(strength) < 0.01

# # 5. 실체결·DB 기록·주문상태 완전 일치
# def execute_and_record_trade(signal, dbm):
#     if is_invalid_strength(signal.strength):
#         logger.warning(f"[강도이상치] {signal.strategy_name} {signal.direction} {signal.strength} - 신호 무시")
#         return
#     if position_manager.has_open_position(signal.symbol):
#         logger.info(f"[포지션 중복] {signal.symbol} - 기존 포지션 유지, 신호 무시")
#         return
#     try:
#         order_id, status, fill_qty, fill_price = execute_broker_trade(signal)

#         fee = calculate_fee_type(fill_qty, fill_price, fee_type="taker")
#         slippage = estimate_slippage_advanced(fill_price, fill_qty, orderbook_depth=1, volatility=0.01)
#         position = Position(
#             symbol=signal.symbol,
#             entry_price=fill_price,
#             size=fill_qty,
#             entry_time=datetime.now(),
#             fee=fee,
#             slippage=slippage,
#             side=signal.direction,
#             status="open"
#         )
#         position_manager.open_position(signal.symbol, position)

#         dbm.record_trade(
#             signal,
#             order_id=order_id,
#             status=status,
#             fill_qty=fill_qty,
#             fill_price=fill_price,
#             position=position.__dict__,  # DTO → dict
#         )
#         logger.info(
#             f"[주문체결] {signal.strategy_name} {signal.direction} {signal.strength} {order_id} {status} fee={fee:.4f} slippage={slippage:.4f}"
#         )
#     except Exception as e:
#         logger.error(f"[실체결/DB기록 실패] {e}")
#         record_incident("order_fail", str(e))

# def execute_broker_trade(signal):
#     # 실전 API 연동, 부분체결/슬리피지/미체결 등 지원 필요
#     return "ORDER123456", "executed", 1, 70000

# # 6. 장기 DB/로그/메모리 관리 자동화
# def rotate_logs_and_prune_db():
#     os.system("truncate -s 0 logs/app.log")  # 로그 자동 순환 예시
#     # 오래된 신호/주문 DB 삭제 등 추가

# # 7. 백테스트/실거래 통계·리포트 자동화 (예시)
# def generate_report():
#     # 손익, 승률, 슬리피지, 장애통계 등 리포트 생성
#     pass

# # 8. 장애·알림·복구/확장에 대비한 비동기 구조 준비(예시)
# # (실전에서는 fetch/generate에 async/await 적용, 멀티프로세스, 큐·클러스터로 확장)

# # ================== 메인 트레이딩 루프 ====================
# def main_trading_cycle(ctx, prev_signals):
#     if trading_state["paused"]:
#         now = datetime.now()
#         if trading_state["paused_at"] and (now - trading_state["paused_at"]).seconds > 600:
#             try:
#                 test_news = NewsCollector().fetch(ctx)
#                 if test_news:
#                     resume_trading()
#                 else:
#                     send_alert("[복구실패] Collector 여전히 이상")
#                     return
#             except Exception:
#                 return
#         else:
#             logger.warning(f"[트레이딩 일시정지] {trading_state['pause_reason']}")
#             return

#     dbm = DatabaseManager(DB_PATH)
#     position_manager.sync_with_exchange()  # 실거래소 상태 동기화

#     try:
#         with dbm.transaction():
#             # collector fetch(장애 감시/알림/자동정지)
#             collector_data = {}
#             for name, collector in [
#                 ("orderbook", OrderbookCollector()),
#                 ("news", NewsCollector()),
#                 ("fg", FearGreedCollector()),
#                 ("funding", FundingRateCollector()),
#                 ("trends", SocialMediaCollector()),
#             ]:
#                 try:
#                     result = collector.fetch(ctx)
#                     collector_data[name] = result
#                     if not result:
#                         collector_error_count[name] += 1
#                         if collector_error_count[name] >= COLLECTOR_ERROR_LIMIT:
#                             pause_trading(f"{name} 3회 연속 실패")
#                             return
#                     else:
#                         collector_error_count[name] = 0
#                 except Exception as e:
#                     collector_error_count[name] += 1
#                     logger.warning(f"[{name} collector 에러] {e}")
#                     if collector_error_count[name] >= COLLECTOR_ERROR_LIMIT:
#                         pause_trading(f"{name} 3회 연속 에러")
#                         return

#             # 전략 신호 생성, 중복/이상치/강도 체크
#             signals = []
#             # 롱 전략
#             try:
#                 signals.append(HybridAlligatorATRStrategy().generate(ctx, orderbook=collector_data["orderbook"]))
#             except Exception as e:
#                 logger.warning(f"[HybridAlligatorATR 롱 전략 오류] {e}")
#             try:
#                 signals.append(RSIMomentumStrategy().generate(ctx, orderbook=collector_data["orderbook"], fg=collector_data["fg"]))
#             except Exception as e:
#                 logger.warning(f"[RSIMomentum 롱 전략 오류] {e}")
#             try:
#                 signals.append(FundingRateStrategy().generate(ctx, funding=collector_data["funding"], orderbook=collector_data["orderbook"]))
#             except Exception as e:
#                 logger.warning(f"[FundingRate 롱 전략 오류] {e}")
#             try:
#                 signals.append(NewsSentimentStrategy().generate(ctx, news=collector_data["news"], trends=collector_data["trends"]))
#             except Exception as e:
#                 logger.warning(f"[NewsSentiment 롱 전략 오류] {e}")
#             # 숏 전략
#             try:
#                 signals.append(ShortRSIOverboughtStrategy().generate(ctx, orderbook=collector_data["orderbook"], fg=collector_data["fg"]))
#             except Exception as e:
#                 logger.warning(f"[ShortRSIOverbought 숏 전략 오류] {e}")
#             try:
#                 signals.append(ShortFundingRateStrategy().generate(ctx, funding=collector_data["funding"], orderbook=collector_data["orderbook"]))
#             except Exception as e:
#                 logger.warning(f"[ShortFundingRate 숏 전략 오류] {e}")
#             try:
#                 signals.append(ShortOrderbookImbalanceStrategy().generate(ctx, orderbook=collector_data["orderbook"]))
#             except Exception as e:
#                 logger.warning(f"[ShortOrderbookImbalance 숏 전략 오류] {e}")
#             try:
#                 signals.append(ShortNewsStrategy().generate(ctx, news=collector_data["news"], trends=collector_data["trends"]))
#             except Exception as e:
#                 logger.warning(f"[ShortNewsStrategy 숏 전략 오류] {e}")

#             # 중복/이상치/강도 체크, 최우선 신호 1개만 집행
#             valid_signals = [
#                 s for s in signals
#                 if s is not None and hasattr(s, "direction")
#                 and not is_duplicate_signal(s, prev_signals)
#                 and not is_invalid_strength(getattr(s, "strength", None))
#             ]
#             if not valid_signals:
#                 logger.info("[신호 없음 or 모두 중복/이상치]")
#                 return

#             selected_signal = max(valid_signals, key=lambda s: abs(getattr(s, "strength", 0)))
#             execute_and_record_trade(selected_signal, dbm)
#             prev_signals.append(selected_signal)

#     except Exception as e:
#         logger.error(f"[트랜잭션 전체 실패/롤백됨] {e}")
#         record_incident("transaction_fail", str(e))

#     # 백업/로테이트/리포트 자동화 예시
#     if int(datetime.utcnow().minute) % 30 == 0:  # 30분마다
#         backup_db_and_logs()
#         rotate_logs_and_prune_db()
#         generate_report()

if __name__ == "__main__":
#     # 실전 트레이딩 루프 비활성화 (테스트만 할 때)
#     # for symbol in config["symbols"]:
#     #     ctx = {...}
#     #     prev_signals = []
#     #     while True:
#     #         main_trading_cycle(ctx, prev_signals)
#     #         time.sleep(60)

    # 슬리피지/수수료/Order/Position print 테스트
    # send_alert("텔레그램 알림 테스트! 🎉")
    fee = calculate_fee_type(1, 35000, fee_type="taker")
    slippage = estimate_slippage_advanced(35000, 1, orderbook_depth=1, volatility=0.01)
    order = Order("BTC/USDT", 35000, 1, "buy", "market", fee=fee, slippage=slippage)
    position = Position("BTC/USDT", 35000, 1, "2025-07-01 12:00:00", fee=fee, slippage=slippage)
    print("Order 객체:", order.__dict__)
    print("Position 객체:", position.__dict__)

    # ================= VAR/MDD 테스트 코드 =================
    # 가상 누적 잔고 리스트 예시 (실전에서는 DB/전략에서 생성)
    equity_curve = [1000, 1030, 980, 1100, 1200, 900, 850, 890, 950, 1200]
    var = calculate_var(equity_curve, confidence_level=0.95, window=5)
    mdd = calculate_mdd(equity_curve)
    print(f"VAR(5일, 95% 신뢰): {var:.4f}")
    print(f"MDD(최대 낙폭): {mdd:.4f}")

    # 임계치 예시
    MDD_THRESHOLD = -0.2
    VAR_THRESHOLD = -0.1

    # 위험 임계치 초과시 경고 print
    if mdd < MDD_THRESHOLD:
        print(f"[경고] MDD가 {MDD_THRESHOLD*100}% 이하! (현재 {mdd*100:.2f}%)")
    if var < VAR_THRESHOLD:
        print(f"[경고] VAR가 {VAR_THRESHOLD*100}% 이하! (현재 {var*100:.2f}%)")
