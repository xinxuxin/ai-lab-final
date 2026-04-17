"""Discovery orchestration, artifact persistence, and caching."""

from __future__ import annotations

import json
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from urllib import robotparser

import httpx
import structlog
import yaml
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.collectors.discovery.base import (
    FAILURE_BLOCKED,
    FAILURE_DUPLICATE_REMOVED,
    FAILURE_NO_RESULTS,
    FAILURE_PARSE_FAILED,
    DiscoveryAdapter,
    canonicalize_url,
)
from app.collectors.discovery.bestbuy import BestBuyDiscoveryAdapter
from app.config.settings import Settings, get_settings
from app.models.schemas import DiscoveryCandidate, DiscoveryConfig, DiscoveryManifest
from app.utils.artifacts import DATA_DIR, ensure_project_dirs

logger = structlog.get_logger(__name__)

DISCOVERY_DIR = DATA_DIR / "discovery"
RAW_HTML_DIR = DISCOVERY_DIR / "raw_html"

ADAPTERS: dict[str, type[DiscoveryAdapter]] = {
    "bestbuy": BestBuyDiscoveryAdapter,
}
ROBOTS_CACHE: dict[str, robotparser.RobotFileParser] = {}


class DiscoveryError(RuntimeError):
    """Base error for discovery failures."""


@dataclass(slots=True)
class DiscoveryRunResult:
    """Return value for the discovery stage."""

    manifest: DiscoveryManifest
    candidates: list[DiscoveryCandidate]
    candidate_queries_path: Path
    candidates_path: Path
    raw_html_dir: Path


def load_discovery_config(config_path: Path) -> DiscoveryConfig:
    """Load discovery configuration from YAML."""
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise DiscoveryError(f"Discovery config must be a mapping: {config_path}")
    return DiscoveryConfig.model_validate(payload)


def required_artifact_paths(output_dir: Path) -> dict[str, Path]:
    """Return the required discovery artifact paths."""
    return {
        "candidate_queries": output_dir / "candidate_queries.json",
        "candidates": output_dir / "candidates.jsonl",
        "manifest": output_dir / "discovery_manifest.json",
        "raw_html_dir": output_dir / "raw_html",
    }


def artifacts_complete(output_dir: Path) -> bool:
    """Check whether the minimum discovery artifacts exist on disk."""
    paths = required_artifact_paths(output_dir)
    raw_html_dir = paths["raw_html_dir"]
    return (
        paths["candidate_queries"].exists()
        and paths["candidates"].exists()
        and paths["manifest"].exists()
        and raw_html_dir.exists()
        and raw_html_dir.is_dir()
    )


def load_existing_run(output_dir: Path) -> DiscoveryRunResult:
    """Load a cached discovery run from disk."""
    paths = required_artifact_paths(output_dir)
    manifest = DiscoveryManifest.model_validate_json(paths["manifest"].read_text(encoding="utf-8"))
    candidates = [
        DiscoveryCandidate.model_validate_json(line)
        for line in paths["candidates"].read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return DiscoveryRunResult(
        manifest=manifest,
        candidates=candidates,
        candidate_queries_path=paths["candidate_queries"],
        candidates_path=paths["candidates"],
        raw_html_dir=paths["raw_html_dir"],
    )


def run_discovery(
    config_path: Path,
    *,
    refresh: bool = False,
    reuse_existing: bool = True,
    output_dir: Path | None = None,
    settings: Settings | None = None,
) -> DiscoveryRunResult:
    """Run marketplace discovery and persist durable artifacts."""
    settings = settings or get_settings()
    ensure_project_dirs()
    resolved_output_dir = output_dir or DISCOVERY_DIR
    paths = required_artifact_paths(resolved_output_dir)

    if reuse_existing and not refresh and artifacts_complete(resolved_output_dir):
        cached = load_existing_run(resolved_output_dir)
        cached.manifest.reused_existing = True
        logger.info(
            "discovery_cache_reused",
            output_dir=str(resolved_output_dir),
            candidates=cached.manifest.total_candidates_saved,
        )
        return cached

    config = load_discovery_config(config_path)
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    paths["raw_html_dir"].mkdir(parents=True, exist_ok=True)

    planned_queries = _build_candidate_query_payload(config)
    paths["candidate_queries"].write_text(
        json.dumps(planned_queries, indent=2),
        encoding="utf-8",
    )

    failure_counts: Counter[str] = Counter(
        {
            FAILURE_BLOCKED: 0,
            FAILURE_PARSE_FAILED: 0,
            FAILURE_NO_RESULTS: 0,
            FAILURE_DUPLICATE_REMOVED: 0,
        }
    )

    raw_candidates: list[DiscoveryCandidate] = []
    adapter_names = _resolve_marketplaces(config)
    http_client = httpx.Client(
        timeout=settings.discovery_timeout_seconds,
        follow_redirects=True,
        headers={"user-agent": settings.discovery_user_agent},
    )

    try:
        ordinal = 1
        for query_seed in config.queries:
            marketplaces = query_seed.marketplaces or adapter_names
            for marketplace_name in marketplaces:
                adapter = _get_adapter(marketplace_name)
                search_url, raw_html_path = adapter.build_query_plan(
                    query_seed=query_seed,
                    raw_html_dir=paths["raw_html_dir"],
                    ordinal=ordinal,
                )
                ordinal += 1

                if not _can_fetch(
                    adapter=adapter,
                    search_url=search_url,
                    user_agent=settings.discovery_user_agent,
                    timeout_seconds=settings.discovery_timeout_seconds,
                ):
                    failure_counts[FAILURE_BLOCKED] += 1
                    logger.warning(
                        "discovery_query_blocked",
                        category=FAILURE_BLOCKED,
                        marketplace=marketplace_name,
                        query=query_seed.query,
                        url=search_url,
                    )
                    continue

                try:
                    response = _fetch_with_retry(
                        client=http_client,
                        url=search_url,
                        headers=adapter.default_headers(settings.discovery_user_agent),
                    )
                except httpx.HTTPError as error:
                    failure_counts[FAILURE_BLOCKED] += 1
                    logger.warning(
                        "discovery_fetch_failed",
                        category=FAILURE_BLOCKED,
                        marketplace=marketplace_name,
                        query=query_seed.query,
                        error=str(error),
                    )
                    continue

                if adapter.is_blocked_response(response):
                    failure_counts[FAILURE_BLOCKED] += 1
                    logger.warning(
                        "discovery_response_blocked",
                        category=FAILURE_BLOCKED,
                        marketplace=marketplace_name,
                        query=query_seed.query,
                        status_code=response.status_code,
                    )
                    continue

                raw_html_path.write_text(response.text, encoding="utf-8")
                page = adapter.create_page(
                    query_seed=query_seed,
                    html=response.text,
                    raw_html_path=raw_html_path,
                    status_code=response.status_code,
                )

                try:
                    parse_result = adapter.parse_search_results(page)
                except Exception as error:  # pragma: no cover - defensive logging
                    failure_counts[FAILURE_PARSE_FAILED] += 1
                    logger.exception(
                        "discovery_parse_exception",
                        category=FAILURE_PARSE_FAILED,
                        marketplace=marketplace_name,
                        query=query_seed.query,
                        error=str(error),
                    )
                    continue

                if not parse_result.candidates:
                    failure_counts[FAILURE_NO_RESULTS] += 1
                    logger.warning(
                        "discovery_no_results",
                        category=FAILURE_NO_RESULTS,
                        marketplace=marketplace_name,
                        query=query_seed.query,
                    )
                else:
                    logger.info(
                        "discovery_query_parsed",
                        marketplace=marketplace_name,
                        query=query_seed.query,
                        candidates=len(parse_result.candidates),
                    )

                raw_candidates.extend(parse_result.candidates)
                time.sleep(settings.discovery_request_delay_seconds)
    finally:
        http_client.close()

    deduped_candidates, duplicate_count = dedupe_candidates(raw_candidates)
    if duplicate_count:
        failure_counts[FAILURE_DUPLICATE_REMOVED] += duplicate_count
        logger.info(
            "discovery_duplicates_removed",
            category=FAILURE_DUPLICATE_REMOVED,
            duplicates=duplicate_count,
        )

    ranked_candidates = rank_candidates(deduped_candidates)
    limited_candidates = ranked_candidates[: settings.discovery_max_products]
    _write_candidates_jsonl(paths["candidates"], limited_candidates)

    manifest = DiscoveryManifest(
        config_path=str(config_path.resolve()),
        output_dir=str(resolved_output_dir.resolve()),
        candidate_queries_path=str(paths["candidate_queries"].resolve()),
        candidates_path=str(paths["candidates"].resolve()),
        raw_html_dir=str(paths["raw_html_dir"].resolve()),
        total_queries=sum(len(query.marketplaces or adapter_names) for query in config.queries),
        total_candidates_raw=len(raw_candidates),
        total_candidates_saved=len(limited_candidates),
        failure_counts=dict(failure_counts),
        marketplaces=adapter_names,
        notes=[
            "Results are deduplicated by canonical URL.",
            "Ranking prioritizes visible review count and product-page likelihood.",
        ],
    )
    paths["manifest"].write_text(
        manifest.model_dump_json(indent=2),
        encoding="utf-8",
    )

    if not artifacts_complete(resolved_output_dir):
        raise DiscoveryError(
            "Discovery did not complete successfully because required artifacts are missing."
        )

    return DiscoveryRunResult(
        manifest=manifest,
        candidates=limited_candidates,
        candidate_queries_path=paths["candidate_queries"],
        candidates_path=paths["candidates"],
        raw_html_dir=paths["raw_html_dir"],
    )


def dedupe_candidates(
    candidates: list[DiscoveryCandidate],
) -> tuple[list[DiscoveryCandidate], int]:
    """Deduplicate candidates by canonical URL while merging matched queries."""
    deduped: dict[str, DiscoveryCandidate] = {}
    duplicate_count = 0

    for candidate in candidates:
        key = canonicalize_url(str(candidate.canonical_url))
        if key in deduped:
            duplicate_count += 1
            existing = deduped[key]
            merged_queries = sorted(set(existing.matched_queries + candidate.matched_queries))
            if compute_candidate_score(candidate) > compute_candidate_score(existing):
                candidate.matched_queries = merged_queries
                deduped[key] = candidate
            else:
                existing.matched_queries = merged_queries
            continue
        deduped[key] = candidate

    return list(deduped.values()), duplicate_count


def rank_candidates(candidates: list[DiscoveryCandidate]) -> list[DiscoveryCandidate]:
    """Assign ranking scores and return candidates sorted best-first."""
    for candidate in candidates:
        candidate.ranking_score = compute_candidate_score(candidate)
    return sorted(candidates, key=lambda item: item.ranking_score, reverse=True)


def compute_candidate_score(candidate: DiscoveryCandidate) -> float:
    """Score candidates by review evidence and product-page relevance."""
    score = float(candidate.visible_review_count or 0)
    if candidate.is_product_page:
        score += 100.0
    if candidate.price is not None:
        score += 10.0
    if candidate.rating is not None:
        score += candidate.rating * 8.0

    query_tokens = {token for token in candidate.query.lower().split() if token}
    title_tokens = {token for token in candidate.title.lower().replace("-", " ").split() if token}
    overlap = len(query_tokens & title_tokens)
    score += overlap * 6.0
    return score


def _build_candidate_query_payload(config: DiscoveryConfig) -> dict[str, object]:
    """Serialize the planned marketplace queries before discovery runs."""
    return {
        "version": config.version,
        "marketplaces": _resolve_marketplaces(config),
        "queries": [query.model_dump(mode="json") for query in config.queries],
    }


def _resolve_marketplaces(config: DiscoveryConfig) -> list[str]:
    """Return the globally configured marketplace list."""
    if not config.marketplaces:
        raise DiscoveryError("At least one marketplace adapter must be configured.")
    return config.marketplaces


def _get_adapter(name: str) -> DiscoveryAdapter:
    """Instantiate a discovery adapter by name."""
    adapter_cls = ADAPTERS.get(name)
    if adapter_cls is None:
        available = ", ".join(sorted(ADAPTERS))
        raise DiscoveryError(f"Unknown discovery adapter '{name}'. Available: {available}")
    return adapter_cls()


def _can_fetch(
    adapter: DiscoveryAdapter,
    search_url: str,
    user_agent: str,
    timeout_seconds: int,
) -> bool:
    """Check robots.txt before making a discovery request."""
    robots_url = adapter.robots_url()
    parser = ROBOTS_CACHE.get(robots_url)
    if parser is None:
        parser = robotparser.RobotFileParser()
        try:
            response = httpx.get(
                robots_url,
                timeout=timeout_seconds,
                follow_redirects=True,
                headers=adapter.default_headers(user_agent),
            )
            response.raise_for_status()
            parser.parse(response.text.splitlines())
        except httpx.HTTPError:
            logger.warning("discovery_robots_unavailable", marketplace=adapter.marketplace)
            return True
        ROBOTS_CACHE[robots_url] = parser
    return parser.can_fetch(user_agent, search_url)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=5),
    retry=retry_if_exception_type(httpx.HTTPError),
    reraise=True,
)
def _fetch_with_retry(
    *,
    client: httpx.Client,
    url: str,
    headers: dict[str, str],
) -> httpx.Response:
    """Fetch a discovery page with retries and exponential backoff."""
    response = client.get(url, headers=headers)
    response.raise_for_status()
    return response


def _write_candidates_jsonl(path: Path, candidates: list[DiscoveryCandidate]) -> None:
    """Persist candidates as JSON Lines."""
    payload = "\n".join(candidate.model_dump_json() for candidate in candidates)
    path.write_text(payload + ("\n" if payload else ""), encoding="utf-8")
