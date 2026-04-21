"""
evaluate_ragas.py — RAGAS evaluation for Legal Document Assistant
Run: python evaluate_ragas.py
"""

import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from agent import (
    build_permanent_kb,
    build_graph,
    PERMANENT_DOCUMENTS
)
from langchain_groq import ChatGroq

load_dotenv()

# ============================================================
# Setup
# ============================================================
print("=" * 60)
print("RAGAS EVALUATION — Legal Document Assistant")
print("=" * 60)

print("\nInitializing agent...")
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
embedder, permanent_kb = build_permanent_kb()
app = build_graph(llm, embedder, permanent_kb, session_kb=None)

def ask(question: str, thread_id: str = "eval") -> dict:
    """Helper to run the agent and return the result."""
    config = {"configurable": {"thread_id": thread_id}}
    result = app.invoke({"question": question}, config=config)
    return result

# ============================================================
# Mode A — Permanent KB only (no upload)
# ============================================================
print("\n" + "=" * 60)
print("MODE A: Permanent KB Only")
print("=" * 60)

MODE_A_QUESTIONS = [
    {
        "question": "What are the elements of a valid contract?",
        "ground_truth": "Contract formation requires four elements: offer, acceptance, consideration, and intention to create legal relations."
    },
    {
        "question": "What is the burden of proof in criminal cases?",
        "ground_truth": "In criminal cases, the prosecution bears the burden and must prove guilt beyond reasonable doubt."
    },
    {
        "question": "How long does copyright protection last?",
        "ground_truth": "Copyright duration is typically the author's life plus 60-70 years depending on jurisdiction."
    }
]

print(f"\nRunning {len(MODE_A_QUESTIONS)} questions for Mode A...")
mode_a_dataset = []

for rq in MODE_A_QUESTIONS:
    print(f"  Processing: {rq['question'][:60]}...")
    
    # Get retrieval context
    q_emb = embedder.encode([rq["question"]]).tolist()
    results = permanent_kb.query(query_embeddings=q_emb, n_results=3)
    chunks = results["documents"][0]
    
    # Get agent answer
    result = ask(rq["question"], thread_id=f"modea-{rq['question'][:10]}")
    
    mode_a_dataset.append({
        "question": rq["question"],
        "answer": result.get("answer", ""),
        "contexts": [chunks[0]] if chunks else [""],
        "ground_truth": rq["ground_truth"]
    })

print(f"✅ Mode A dataset built: {len(mode_a_dataset)} rows")

# ============================================================
# Mode B — Session KB active (after upload)
# ============================================================
print("\n" + "=" * 60)
print("MODE B: Session KB (requires uploaded document)")
print("=" * 60)

# For Mode B, we'll use a sample document or skip if none available
# In real evaluation, you would upload an actual legal document here

print("\nNote: Mode B requires an uploaded document.")
print("Skipping Mode B for now — run this after uploading a document in the Streamlit UI.")

mode_b_dataset = []

# Example structure (uncomment when you have an uploaded document):
# MODE_B_QUESTIONS = [
#     {
#         "question": "What does clause 3 say about payment terms?",
#         "ground_truth": "[Expected answer from uploaded document]"
#     },
#     {
#         "question": "Who are the parties in this agreement?",
#         "ground_truth": "[Expected answer from uploaded document]"
#     }
# ]
# 
# session_kb = build_session_kb(uploaded_file, embedder)
# app_with_session = build_graph(llm, embedder, permanent_kb, session_kb=session_kb)
# 
# for rq in MODE_B_QUESTIONS:
#     result = app_with_session.invoke(
#         {"question": rq["question"]},
#         config={"configurable": {"thread_id": f"modeb-{rq['question'][:10]}"}}
#     )
#     mode_b_dataset.append({...})

# ============================================================
# Run RAGAS Evaluation
# ============================================================
print("\n" + "=" * 60)
print("RUNNING RAGAS EVALUATION")
print("=" * 60)

try:
    from ragas import evaluate
    from ragas.metrics import faithfulness, answer_relevancy, context_precision
    from datasets import Dataset
    
    # Mode A Evaluation
    print("\nMode A — Permanent KB Only:")
    print("-" * 60)
    
    ragas_data_a = Dataset.from_list(mode_a_dataset)
    print("Running RAGAS evaluation (1-2 minutes)...")
    
    ragas_result_a = evaluate(
        dataset=ragas_data_a,
        metrics=[faithfulness, answer_relevancy, context_precision],
    )
    
    df_a = ragas_result_a.to_pandas()
    print("\nMODE A RAGAS SCORES:")
    print(f"  Faithfulness:      {df_a['faithfulness'].mean():.3f}")
    print(f"  Answer Relevance:  {df_a['answer_relevancy'].mean():.3f}")
    print(f"  Context Precision: {df_a['context_precision'].mean():.3f}")
    
    # Mode B Evaluation (if available)
    if mode_b_dataset:
        print("\nMode B — Session KB:")
        print("-" * 60)
        
        ragas_data_b = Dataset.from_list(mode_b_dataset)
        ragas_result_b = evaluate(
            dataset=ragas_data_b,
            metrics=[faithfulness, answer_relevancy, context_precision],
        )
        
        df_b = ragas_result_b.to_pandas()
        print("\nMODE B RAGAS SCORES:")
        print(f"  Faithfulness:      {df_b['faithfulness'].mean():.3f}")
        print(f"  Answer Relevance:  {df_b['answer_relevancy'].mean():.3f}")
        print(f"  Context Precision: {df_b['context_precision'].mean():.3f}")
    
    print("\n⚠️  Record these baseline scores. Re-run after any improvements.")
    
except ImportError:
    print("\nRAGAS not installed — running manual faithfulness scoring")
    print("=" * 60)
    
    # Manual evaluation for Mode A
    faith_scores_a = []
    for row in mode_a_dataset:
        prompt = f"""Rate faithfulness 0.0-1.0. Reply with only a number.
Context: {row['contexts'][0][:300]}
Answer: {row['answer'][:200]}"""
        
        try:
            score = float(llm.invoke(prompt).content.strip().split()[0])
            score = max(0.0, min(1.0, score))
        except:
            score = 0.5
        
        faith_scores_a.append(score)
        print(f"  Q: {row['question'][:50]:50s} → {score:.2f}")
    
    avg_a = sum(faith_scores_a) / len(faith_scores_a)
    print(f"\nMODE A — Baseline faithfulness: {avg_a:.3f}")
    
    print("\nInstall RAGAS for full evaluation: pip install ragas datasets")

print("\n" + "=" * 60)
print("✅ EVALUATION COMPLETE")
print("=" * 60)
