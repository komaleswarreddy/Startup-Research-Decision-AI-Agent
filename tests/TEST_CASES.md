# Detailed Test Cases (Production Readiness Matrix)

This matrix defines verification coverage for API, graph orchestration, reliability, memory, tools, and edge conditions.

## 1) API Contract and Error Handling

- `test_health`: `/health` returns 200 and `status=ok`.
- `test_query_endpoint_contract`: `/query` returns all required fields.
- `test_query_validation_rejects_too_short_prompt`: invalid request returns standardized `validation_error`.
- `test_query_generates_session_id_when_missing`: backend creates `session-*` ID if absent.
- `test_query_uses_provided_session_id`: explicit session id is preserved.
- `test_query_failure_returns_standard_error_envelope`: runtime failures return structured `query_processing_failed`.

## 2) Agent Logic Coverage

- `test_planner_adds_compare_task`: compare queries include geography task.
- `test_coordinator_merges_long_term_context_and_history_marker`: follow-up context merge task and long-term recall.
- `test_market_analyzer_uses_extracted_numbers_for_cagr`: numeric extraction path.
- `test_market_analyzer_falls_back_when_no_numbers`: fallback CAGR path.
- `test_risk_analyzer_thresholds`: all risk branches (>=3, ==2, <2 sources).
- `test_evaluator_with_and_without_retrieval_context`: both retrieval/no-retrieval scoring paths.
- `test_research_agent_populates_context_and_sources`: search/scrape/retrieval state propagation.

## 3) Tool and RAG Coverage

- `test_cagr_and_projection_helpers`: CAGR/revenue helper correctness.
- `test_safe_python_executor_success_and_forbidden_constructs`: allowed and forbidden AST constructs.
- `test_safe_python_executor_runtime_error_is_captured`: runtime exception propagation.
- `test_safe_python_executor_rejects_forbidden_name_usage`: forbidden dynamic execution names (`eval`, etc.).
- `test_safe_python_executor_timeout`: infinite loop timeout protection.
- `test_retriever_scores_and_limits_results`: retrieval ordering and top-k limits.
- `test_retriever_returns_empty_when_no_overlap`: no lexical overlap behavior.
- `test_scraper_enrich_uses_fallback_content_without_url`: enrich fallback behavior.
- `test_charting_creates_output_file`: chart artifact generation.

## 4) Reliability and Resilience

- `test_search_tool_uses_fallback_after_retries`: retries + circuit-breaker fallback path.
- `test_llm_service_retries_transient_failures`: transient LLM failures recover under retry budget.

## 5) Memory and Persistence

- `test_sqlite_memory_persists_across_store_instances`: SQLite-backed memory durability across instances.

## 6) Graph and End-to-End Behavior

- `test_graph_follow_up_reuses_memory_context`: follow-up state continuity with same session thread.
- `test_graph_run_returns_required_state_keys`: graph output contract has all required state keys.
- `test_checkpointer_factory_returns_object`: checkpointer factory always returns usable object.
- `test_api_can_handle_parallel_requests`: parallel request handling for endpoint contract stability.

## 7) Execution Standard

- Run command:
  - `py -m pytest -q`
- Current acceptance threshold:
  - all tests must pass
  - no unhandled exception paths
  - standardized error responses for validation and runtime failures
