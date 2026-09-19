"""Offline tests for the interview pipeline.

    python -m unittest discover tests -v

No network: the model provider is replaced by a stub and the embedding call is
disabled, so retrieval runs on its local fallback (BM25 + LSA). That makes these
fast and deterministic, and it means the degraded path -- the one that only runs
when something upstream is broken -- is the one that is always tested.

The agent tests run twice, once on real LangGraph/LangChain (when installed) and
once on the stdlib stand-ins, to hold the claim that the same graph definition
behaves the same on both.
"""

from __future__ import annotations

import operator
import os
import unittest
from typing import Annotated, TypedDict

from interview.compat import runnable as std_lcel
from interview.compat.stategraph import END, START, GraphRecursionError, StateGraph
from interview.corpus import build as corpus


class FakeProvider:
    name = "fake"
    label = "Fake"
    model = "fake-1"

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def complete(self, system, messages):
        self.calls.append((system, messages))
        return self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]


def _offline_index():
    from interview.retrieval import hybrid

    index = hybrid.load()
    if index.embedder:
        index.embedder.api_key = ""        # force the local fallback path
    hybrid.get_index = lambda: index
    return index


class CorpusTests(unittest.TestCase):
    def test_corpus_builds_and_every_entry_is_complete(self):
        doc = corpus.build()                   # raises on any malformed entry
        self.assertGreaterEqual(doc["stats"]["questions"], 150)
        self.assertGreaterEqual(doc["stats"]["pages"], 100)
        for q in doc["questions"]:
            self.assertTrue(q["grounded_in"], q["id"])

    def test_bold_lead_ins_stay_inside_the_answer(self):
        doc = corpus.build()
        behavioural = [q for q in doc["questions"] if q["part"] == 12]
        self.assertTrue(all("**Situation.**" in q["answer"] for q in behavioural[:9]))


class LcelTests(unittest.TestCase):
    def _chain(self, lcel):
        return (lcel.RunnablePassthrough.assign(double=lcel.RunnableLambda(lambda d: d["x"] * 2))
                | lcel.RunnableLambda(lambda d: {**d, "sum": d["x"] + d["double"]})
                | lcel.RunnableParallel(total=lcel.RunnableLambda(lambda d: d["sum"]),
                                        echo=lcel.RunnablePassthrough()))

    def test_stdlib_lcel(self):
        out = self._chain(std_lcel).invoke({"x": 3})
        self.assertEqual(out["total"], 9)
        self.assertEqual(out["echo"]["double"], 6)

    def test_stdlib_matches_langchain_core(self):
        try:
            import langchain_core.runnables as real
        except ImportError:
            self.skipTest("langchain_core not installed")
        for x in (0, 3, 11):
            self.assertEqual(self._chain(std_lcel).invoke({"x": x}), self._chain(real).invoke({"x": x}))


class StateGraphTests(unittest.TestCase):
    def test_reducers_conditional_edges_and_recursion_limit(self):
        class S(TypedDict, total=False):
            n: int
            log: Annotated[list, operator.add]

        g = StateGraph(S)
        g.add_node("inc", lambda s: {"n": s["n"] + 1, "log": [s["n"]]})
        g.add_edge(START, "inc")
        g.add_conditional_edges("inc", lambda s: "again" if s["n"] < 3 else "stop",
                                {"again": "inc", "stop": END})
        out = g.compile().invoke({"n": 0, "log": []})
        self.assertEqual(out["n"], 3)
        self.assertEqual(out["log"], [0, 1, 2])

        loop = StateGraph(S)
        loop.add_node("spin", lambda s: {"n": s["n"] + 1})
        loop.add_edge(START, "spin")
        loop.add_edge("spin", "spin")
        with self.assertRaises(GraphRecursionError):
            loop.compile().invoke({"n": 0}, {"recursion_limit": 5})


class RetrievalTests(unittest.TestCase):
    def test_dense_unavailable_falls_back_to_lsa(self):
        index = _offline_index()
        docs, trace = index.search("why does the venera chatbot use qwen")
        self.assertTrue(docs)
        self.assertTrue(trace["dense_fallback"])
        self.assertIn("lsa", trace["retrievers"])


class DatasetTests(unittest.TestCase):
    def test_refusals_disjoint_from_eval_and_gold_in_context(self):
        from interview.finetune import build_dataset
        from interview.retrieval import eval as retrieval_eval

        self.assertFalse(set(build_dataset.REFUSALS) & set(retrieval_eval.MUST_DECLINE))
        _offline_index()
        out = build_dataset.build()
        by_id = {d["id"]: d for d in corpus.build()["questions"]}
        for split in out["records"].values():
            for r in split:
                if r["kind"] == "answer":
                    self.assertIn(by_id[r["id"]]["question"], r["messages"][1]["content"])


class AgentTests(unittest.TestCase):
    ENGINES = ("auto", "stdlib")

    def _run(self, engine_name, replies, question, history=None):
        os.environ["INTERVIEW_GRAPH_ENGINE"] = engine_name
        from interview.graph import agent, engine

        engine.load.cache_clear()
        agent._compiled = None
        _offline_index()
        fake = FakeProvider(replies)
        from interview.chains import pipeline

        pipeline.provider_chain = lambda: [fake]
        return agent.run(question, history), fake

    def tearDown(self):
        os.environ.pop("INTERVIEW_GRAPH_ENGINE", None)

    def test_answers_with_citation(self):
        for eng in self.ENGINES:
            with self.subTest(engine=eng):
                out, _ = self._run(eng, ["Because the product runs on-premise [1]."],
                                   "why does the venera chatbot run on qwen instead of an api")
                self.assertEqual(out["outcome"], "answered")
                self.assertEqual([s["node"] for s in out["trace"]],
                                 ["route", "retrieve", "grade", "generate", "verify"])
                self.assertTrue(out["citations"])

    def test_grouped_citation_is_not_read_as_a_number(self):
        # Regression: "[2, 3]" used to fail verification as invented numbers 2 and 3,
        # costing a regeneration and scoring citing prompts as ungrounded.
        from interview.graph.agent import check

        docs = [{"question": "q", "answer": "on-premise", "follow_up": ""}] * 3
        self.assertEqual(check("It runs on-premise [2, 3].", docs, "where does it run"), [])
        self.assertTrue(check("It runs on 7 servers [2, 3].", docs, "where does it run"))
        for eng in self.ENGINES:
            with self.subTest(engine=eng):
                out, fake = self._run(eng, ["Because the product runs on-premise [1, 2]."],
                                      "why does the venera chatbot run on qwen instead of an api")
                self.assertEqual(out["outcome"], "answered")
                self.assertEqual(len(fake.calls), 1)                   # no regeneration
                self.assertEqual(len(out["citations"]), 2)

    def _with_budget(self, seconds):
        from interview.graph import agent

        saved = agent.REGENERATE_WITHIN_S
        agent.REGENERATE_WITHIN_S = seconds
        self.addCleanup(setattr, agent, "REGENERATE_WITHIN_S", saved)

    def test_invented_number_is_regenerated_then_falls_back(self):
        self._with_budget(60)                                          # timing out of the picture
        for eng in self.ENGINES:
            with self.subTest(engine=eng):
                out, fake = self._run(eng, ["He wrote 9999 test scripts [1]."],
                                      "tell me about his automated test scripts")
                nodes = [s["node"] for s in out["trace"]]
                self.assertEqual(nodes.count("generate"), 2)          # one regeneration, no more
                self.assertEqual(nodes[-1], "fallback")
                self.assertNotIn("9999", out["answer"])
                self.assertIn("previous draft", fake.calls[-1][0])     # strict retry prompt

    def test_no_regeneration_once_the_time_budget_is_spent(self):
        self._with_budget(0)
        for eng in self.ENGINES:
            with self.subTest(engine=eng):
                out, fake = self._run(eng, ["He wrote 9999 test scripts [1]."],
                                      "tell me about his automated test scripts")
                nodes = [s["node"] for s in out["trace"]]
                self.assertEqual(len(fake.calls), 1)                   # quoted, not retried
                self.assertEqual(nodes[-1], "fallback")
                self.assertEqual(out["trace"][-2].get("note"), "no time left to regenerate")

    def test_empty_question_refuses_without_a_model_call(self):
        for eng in self.ENGINES:
            with self.subTest(engine=eng):
                out, fake = self._run(eng, ["unused"], "   ")
                self.assertEqual(out["outcome"], "declined_before_model")
                self.assertEqual(fake.calls, [])

    def test_model_decline_is_reported(self):
        from interview.prompting.registry import DECLINE

        # Offline, keyword + LSA already turn away "is he married" before the model.
        # This one gets past that gate (a shared word, "Noida"), so the model has to
        # decline it -- the case the retrieval eval showed similarity cannot catch.
        out, fake = self._run("stdlib", [DECLINE], "recommend a good pizza place in noida")
        self.assertEqual(out["outcome"], "declined_by_model")
        self.assertEqual(len(fake.calls), 1)

    def test_follow_up_is_rewritten_with_the_previous_question(self):
        history = [{"role": "user", "content": "tell me about the severity-1 incident he intercepted"},
                   {"role": "assistant", "content": "He caught a severity-1 503 before release."}]
        for eng in self.ENGINES:
            with self.subTest(engine=eng):
                out, _ = self._run(eng, ["It was fixed the same day [1]."], "and then?", history)
                nodes = [s["node"] for s in out["trace"]]
                self.assertEqual(nodes[:4], ["route", "retrieve", "grade", "rewrite"])
                rewritten = next(s for s in out["trace"] if s["node"] == "rewrite")["query"]
                self.assertIn("severity-1", rewritten)
                self.assertEqual(out["outcome"], "answered")

    def test_standalone_vague_question_is_not_rewritten(self):
        out, fake = self._run("stdlib", ["unused"], "and then?")
        self.assertNotIn("rewrite", [s["node"] for s in out["trace"]])
        self.assertEqual(out["outcome"], "declined_before_model")
        self.assertEqual(fake.calls, [])

    def test_both_engines_take_the_same_path(self):
        paths = {}
        for eng in self.ENGINES:
            out, _ = self._run(eng, ["He built it from scratch [1]."], "what did he build at venera")
            paths[eng] = [s["node"] for s in out["trace"]]
        self.assertEqual(paths["auto"], paths["stdlib"])


if __name__ == "__main__":
    unittest.main()
