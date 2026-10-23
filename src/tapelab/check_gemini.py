"""One live call to confirm the key, model and quota work. Run: python -m tapelab.check_gemini"""
from .agents.gemini import GeminiLLM


def main() -> None:
    llm = GeminiLLM()
    score, reason = llm.score_fundamentals(["Revenue increased 12% with record operating profit."])
    print(f"model={llm.model} score={score} reason={reason}")


if __name__ == "__main__":
    main()
