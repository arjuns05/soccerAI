from __future__ import annotations
from openai import OpenAI
from sqlalchemy.orm import Session
from app.config import settings
from app.rag_store import top_k_similar 

client = OpenAI(api_key = settings.openai_api_key)
def embed_text(text: str) -> list[float]:
    resp = client.embeddings.create(
        model = settings.openai_embed_model, 
        input = text
    )
    return resp.data[0].embedding

def explain_prediction(session: Session, match_prompt:str, pred_probs: dict, k:int) -> tuple[str, list[dict]]:
    '''

    RAG: embded the prompt, get similar history, ask OpenAI to explain using that context

    '''

    q_emb = embed_text(match_prompt)
    docs = top_k_similar(session, q_emb, k=k)

    context = "\n\n".join(
        [f"- [doc_id={d.id}]] {d.text}" for d in docs]
    )
    prompt = f"""
    You are an explainable football prediction assistant.

    We have a live match summary:
    {match_prompt}

    Model probabilities:
    HOME_WIN={pred_probs["HOME_WIN"]:.3f}, DRAW={pred_probs["DRAW"]:.3f}, AWAY_WIN={pred_probs["AWAY_WIN"]:.3f}

    Here is retrieved historical context (most similar first):
    {context}

    Task:
    1) Explain *why* the model is leaning the way it is (tie it to features like goal diff, xG diff, shots, time).
    2) Use the retrieved historical context to justify the explanation.
    3) Provide 2-3 actionable fantasy angles (e.g., likely scorers, clean sheet odds, late-game volatility).
    Keep it concise but concrete.
    """

    resp = client.responses.create(
        model = settings.openai_text_model, 
        input = prompt
    )

    explanation = resp.output_text
    citations = [{"docs_id":d.id, "meta": d.meta} for d in docs]
    return explanation, citations