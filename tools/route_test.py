from app.config.router import route_question

import os

DATA_SOURCE = os.getenv("DATA_SOURCE",
                        "postgres",
                        ).strip().lower()


questions = [
    # "How was performance by segment for CMP-2026-003?",
    # "How was segment performance for CMP-2026-003?",
    "How is Marketing ROI calculated?",
    # "Compare churn vs growth for campaign CMP-2026-003",
    # "Compare churn vs growth segments for campaign CMP-2026-003 and CMP-2026-004",
    # "Which campaign performed better, CMP-2026-004 or CMP-2026-003?",
    "How did CMP-2026-004 perform?",
    # "Tell me what stands out about CMP-2026-004.",
    # "What are the key takeaways from CMP-2026-004 and CMP-2026-003?",
    # "Overall, which campaign had highest revenue?",
    # "Across all campaigns, which campaign had the highest conversion rate?",
    # "Overall, which segment had highest revenue?",
    # "Across all campaigns, which segment had the highest conversion rate?",
    # "How did CMP-2026-999 perform?",
    # "Tell me about CMP-2026-999."
]


for question in questions:
    route = route_question(question)
    print(question, "->", route)
