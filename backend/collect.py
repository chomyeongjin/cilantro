"""One-shot collection; use --daily for a foreground 24-hour collection loop."""
import argparse
import time
from datetime import date
from service import collect


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--end', type=date.fromisoformat)
    parser.add_argument('--daily', action='store_true')
    args = parser.parse_args()
    if args.daily and args.end:
        parser.error('--daily와 고정 --end는 함께 사용할 수 없습니다.')
    while True:
        try:
            items = collect(end=args.end)
            print(f"저장 완료: {len(items)}개 주제, 데이터 기준일 {items[0]['dataThrough']}", flush=True)
        except (ValueError, OSError, KeyError, TypeError) as error:
            print(f'수집 실패: {error}', flush=True)
            if not args.daily:
                raise SystemExit(1)
        if not args.daily:
            break
        time.sleep(24 * 60 * 60)
