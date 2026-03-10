from app.agents.state import AgentState
from app.memory.long_term_store import LongTermMemoryStore
from app.memory.short_term import ShortTermMemoryStore


class CoordinatorAgent:
    def __init__(
        self,
        short_term_memory: ShortTermMemoryStore,
        long_term_memory: LongTermMemoryStore,
    ) -> None:
        self.short_term_memory = short_term_memory
        self.long_term_memory = long_term_memory

    def pre_run(self, state: AgentState) -> AgentState:
        session_id = state.get("session_id", "default-session")
        query = state.get("query", "")
        history = self.short_term_memory.get_history(session_id)
        prior_summary = self.long_term_memory.get(session_id, "last_analysis", "")

        self.short_term_memory.add_message(session_id, "user", query)
        if prior_summary and "retrieved_context" not in state:
            state["retrieved_context"] = [
                {"content": str(prior_summary), "source": "long_term_memory", "score": 0.55}
            ]
            state["sources"] = list(set(state.get("sources", []) + ["long_term_memory"]))
        if history:
            state["tasks"] = list(dict.fromkeys(state.get("tasks", []) + ["follow_up_context_merge"]))
        return state

    def post_run(self, state: AgentState) -> AgentState:
        session_id = state.get("session_id", "default-session")
        final_answer = state.get("final_answer", "")

        self.short_term_memory.add_message(session_id, "assistant", final_answer)
        self.long_term_memory.upsert(session_id, "last_analysis", final_answer[:2000])
        self.long_term_memory.upsert(session_id, "last_recommendation", state.get("recommendation", ""))
        self.long_term_memory.upsert(session_id, "last_top_startup", state.get("top_startup", ""))
        return state
