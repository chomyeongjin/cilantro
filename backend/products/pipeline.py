"""Explicit batch work; public GETs never trigger crawling or paid AI calls."""
from .ai import Analyzer, PROMPT_VERSION
from .connectors import CoupangClient, IntegrationError, fetch_source
from .models import ManualProduct, SourceBundle
from .registration import read_entries
from . import store


def discover(keyword, limit=10, client=None, path=None):
    run = store.start_run('discovery', path)
    try:
        listings = (client or CoupangClient()).search(keyword, limit)
        store.save_listings(listings, path)
        result = {'discovered': len(listings), 'productIds': [p['id'] for p in listings]}
        store.finish_run(run, 'success', result, path)
        return result
    except Exception as error:
        code = str(error) if isinstance(error, IntegrationError) else 'DISCOVERY_FAILED'
        store.finish_run(run, 'failed', {'errorCode': code}, path)
        raise


def load_manifest(filename):
    raw = read_entries(filename)
    bundles = [ManualProduct.model_validate(row).source_bundle() if isinstance(row, dict) and 'id' in row
               else SourceBundle.model_validate(row) for row in raw]
    if len({b.productId for b in bundles}) != len(bundles):
        raise ValueError('manifest 내 상품 ID가 중복됩니다.')
    return bundles


def analyze_bundles(bundles, max_products=10, analyzer=None, fetcher=fetch_source, path=None):
    if not 1 <= max_products <= 100:
        raise ValueError('max-products는 1~100이어야 합니다.')
    if analyzer is None:
        analyzer = Analyzer()
        analyzer.require_credentials()  # Fail before fetching any source when the key is missing.
    run = store.start_run('analysis', path)
    results = []
    for bundle in bundles[:max_products]:
        try:
            listing = store.get_listing(bundle.productId, path)
            if not listing:
                raise IntegrationError('PRODUCT_NOT_REGISTERED')
            if bundle.expectedProductName != listing['product']:
                raise IntegrationError('PRODUCT_VARIANT_NAME_MISMATCH')
            if listing.get('source') == 'manual-manufacturer':
                registered = ManualProduct.model_validate(listing['raw']).source_bundle()
                if bundle != registered:
                    raise IntegrationError('REGISTERED_SOURCES_MISMATCH')
            sources = [fetcher(spec) for spec in bundle.sources]
            digest = store.fingerprint(listing, sources, bundle.variantNote, analyzer.model, PROMPT_VERSION,
                                       provider=getattr(analyzer, 'provider', 'openai'))
            analysis_id = store.existing_draft(listing['id'], digest, path)
            cached = analysis_id is not None
            if not cached:
                analysis, provenance = analyzer.analyze(listing, sources, bundle.variantNote)
                analysis_id = store.save_draft(listing, analysis, sources, provenance,
                                              bundle.variantNote, digest, path)
            results.append({'productId': listing['id'], 'analysisId': analysis_id,
                            'state': 'cached' if cached else 'needs_review'})
        except Exception as error:
            code = str(error) if isinstance(error, IntegrationError) else 'ANALYSIS_VALIDATION_FAILED'
            results.append({'productId': bundle.productId, 'state': 'failed', 'errorCode': code})
    failures = sum(r['state'] == 'failed' for r in results)
    state = 'failed' if failures == len(results) else 'partial' if failures else 'success'
    result = {'state': state, 'results': results, 'remaining': max(0, len(bundles) - max_products)}
    store.finish_run(run, state, result, path)
    return result
