class BenchmarkRunner:
    def run(self, questions: list[dict], answer_fn) -> list[dict]:
        return [{'question':q['question'],'result':answer_fn(q['question'])} for q in questions]
