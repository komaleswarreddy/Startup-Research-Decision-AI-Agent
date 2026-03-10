import re

from app.agents.state import AgentState


class EvaluationAgent:
    def run(self, state: AgentState) -> AgentState:
        query = str(state.get("query", ""))
        retrieved = state.get("retrieved_context", [])
        retrieval_score = (
            sum(item.get("score", 0.0) for item in retrieved) / max(1, len(retrieved))
            if retrieved
            else 0.4
        )
        context_relevance = self._context_relevance(query, retrieved, retrieval_score)
        source_grounding = self._source_grounding(state.get("final_answer", ""), retrieved)
        answer_faithfulness = round(min(1.0, (source_grounding * 0.6) + (retrieval_score * 0.4)), 2)
        confidence = round((context_relevance + answer_faithfulness + source_grounding) / 3, 2)

        state["evaluation"] = {
            "context_relevance": round(context_relevance, 2),
            "answer_faithfulness": round(answer_faithfulness, 2),
            "source_grounding": round(source_grounding, 2),
            "retrieval_score": round(retrieval_score, 2),
            "confidence_score": confidence,
        }
        return state

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return set(re.findall(r"[a-zA-Z0-9]+", text.lower()))

    def _context_relevance(
        self, query: str, retrieved: list[dict[str, object]], retrieval_score: float
    ) -> float:
        if not retrieved:
            return min(1.0, retrieval_score + 0.15)
        q_tokens = self._tokens(query)
        if not q_tokens:
            return min(1.0, retrieval_score + 0.1)
        overlaps: list[float] = []
        for item in retrieved:
            doc_tokens = self._tokens(str(item.get("content", "")))
            overlap = len(q_tokens.intersection(doc_tokens)) / max(1, len(q_tokens))
            overlaps.append(overlap)
        avg_overlap = sum(overlaps) / max(1, len(overlaps))
        return round(min(1.0, 0.4 * retrieval_score + 0.6 * avg_overlap), 2)

    def _source_grounding(self, final_answer: str, retrieved: list[dict[str, object]]) -> float:
        if not retrieved:
            return 0.35
        corpus = " ".join(str(item.get("content", "")) for item in retrieved)
        corpus_tokens = self._tokens(corpus)
        if not corpus_tokens:
            return 0.35
        claims = [
            segment.strip()
            for segment in re.split(r"[.\n]+", final_answer)
            if segment.strip()
        ][:8]
        if not claims:
            return 0.5
        grounded = 0
        for claim in claims:
            tokens = self._tokens(claim)
            if not tokens:
                continue
            overlap = len(tokens.intersection(corpus_tokens)) / max(1, len(tokens))
            if overlap >= 0.3:
                grounded += 1
        return round(grounded / max(1, len(claims)), 2)
