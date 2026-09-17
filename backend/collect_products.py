"""Operator CLI. No collection/review endpoints are exposed to site visitors."""
import argparse
import json
import sqlite3
from pathlib import Path

from products import store
from products.config import readiness
from products.connectors import CoupangClient, IntegrationError
from products.pipeline import analyze_bundles, discover, load_manifest
from products.models import Analysis
from products.registration import register_file


def main():
    parser = argparse.ArgumentParser(description='공식 제품 직접 등록 또는 쿠팡 검색 → AI 분석 → 검토 후 공개')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('status', help='키 설정 유무와 저장 상태 (키 값은 출력하지 않음)')
    commands.add_parser('list', help='출처 연결에 필요한 상품 ID/이름')
    register = commands.add_parser('register', help='쿠팡/AI 키 없이 공식 제품과 출처를 JSON으로 등록')
    register.add_argument('--file', required=True)
    register.add_argument('--update-existing', action='store_true', help='기존 ID의 등록 정보를 수정 (공개 버전은 유지)')
    search = commands.add_parser('discover', help='파트너스 API 상품 검색')
    search.add_argument('--keyword', required=True)
    search.add_argument('--limit', type=int, default=10, choices=range(1, 11))
    category = commands.add_parser('seller-category', help='판매자 카테고리 구조 조회 (상품 검색 아님)')
    category.add_argument('--code', default='0')
    analyze = commands.add_parser('analyze', help='연결한 출처를 읽어 AI 분석 초안 저장')
    analyze.add_argument('--sources', required=True)
    analyze.add_argument('--product-id', help='등록 파일에서 이 제품만 분석 (다른 제품은 수집/호출하지 않음)')
    analyze.add_argument('--max-products', type=int, default=10)
    review = commands.add_parser('review', help='출처 원문과 AI 초안을 읽고 검토')
    review.add_argument('--analysis-id', type=int, required=True)
    revise = commands.add_parser('revise', help='원문과 대조해 수정한 분석 JSON을 새 초안으로 저장')
    revise.add_argument('--analysis-id', type=int, required=True)
    revise.add_argument('--analysis-file', required=True)
    revise.add_argument('--editor', required=True)
    approve = commands.add_parser('approve', help='검토한 분석 버전을 공개')
    approve.add_argument('--analysis-id', type=int, required=True)
    approve.add_argument('--reviewer', required=True)
    approve.add_argument('--confirm-label-review', action='store_true', required=True,
                         help='제품 일치·함량·단위·기능성·대상 연령·전체 중량을 원문과 대조했음을 확인')
    args = parser.parse_args()
    try:
        if args.command == 'status':
            result = {**readiness(), **store.stats()}
        elif args.command == 'list':
            result = [{k: p.get(k) for k in ('id', 'product', 'source', 'productUrl', 'buyLink')} for p in store.list_listings()]
        elif args.command == 'register':
            result = register_file(args.file, args.update_existing)
        elif args.command == 'discover':
            result = discover(args.keyword, args.limit)
        elif args.command == 'seller-category':
            result = CoupangClient().category(args.code)
        elif args.command == 'analyze':
            bundles = load_manifest(args.sources)
            if args.product_id:
                bundles = [bundle for bundle in bundles if bundle.productId == args.product_id]
                if not bundles:
                    raise IntegrationError('PRODUCT_NOT_IN_MANIFEST')
            result = analyze_bundles(bundles, args.max_products)
        elif args.command == 'review':
            result = store.draft(args.analysis_id)
        elif args.command == 'revise':
            analysis = Analysis.model_validate_json(Path(args.analysis_file).read_text(encoding='utf-8-sig'))
            result = {'analysisId': store.revise(args.analysis_id, analysis, args.editor), 'state': 'needs_review'}
        else:
            store.approve(args.analysis_id, args.reviewer)
            result = {'publishedAnalysisId': args.analysis_id}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if isinstance(result, dict) and result.get('state') in ('failed', 'partial'):
            return 1
        return 0
    except IntegrationError as error:
        print(json.dumps({'errorCode': str(error)}, ensure_ascii=False))
    except (ValueError, OSError, sqlite3.Error, KeyError):
        print(json.dumps({'errorCode': 'INVALID_INPUT_OR_STORAGE',
                          'message': '입력 파일/분석 ID/원문 근거/함량 검증/저장소를 확인하세요.'}, ensure_ascii=False))
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
