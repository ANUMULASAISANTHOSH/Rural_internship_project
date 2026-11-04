# AQUILA — Academic Evaluation, Project Defense & Viva Package

**Project:** AQUILA — Urban Flood Intelligence, Infrastructure Monitoring and Emergency Response Platform  
**Target Pilot Area:** Manikonda, Hyderabad, Telangana, India  
**Target Audience:** Academic Project Defending Students, Faculty Advisors, and Technical Viva Examiners  
**Package Status:** Complete, Reconciled & Demonstration-Ready  

---

## 1. Package Purpose & Overview

This directory (`docs/evaluation/`) provides an end-to-end, scientifically defensible preparation suite for academic evaluations, project presentations, live demonstrations, and technical viva voce examinations of the AQUILA platform.

Every document in this package is strictly reconciled against the actual Python 3.13 codebase, the validated geospatial datasets, and the **57 passing automated Pytest tests**.

---

## 2. Document Directory & How to Use Each File

| Document Name | File Path | Primary Purpose & How to Use |
| :--- | :--- | :--- |
| **Academic Consistency Check** | [`academic_consistency_check.md`](file:///C:/AI/Rural_internship_project/docs/evaluation/academic_consistency_check.md) | **Start Here.** Contains canonical benchmarks (15.5 km², 22.4 km², 55.63 km², 51.72% built-up, 21 nalas, 24 lakes, 6,659 roads, 94.7% connectivity, 57 tests). Memorize these figures to avoid contradicting project documentation during your defense. |
| **Presentation Blueprint** | [`presentation_blueprint.md`](file:///C:/AI/Rural_internship_project/docs/evaluation/presentation_blueprint.md) | **15-Slide Presentation Deck.** Use this to structure your PowerPoint / Google Slides deck. For each slide, it provides the title, key bullet points, recommended visual/diagram, exact technical talking points, and estimated speaking duration (total ~15 mins). |
| **Technical Project Explanation** | [`technical_explanation.md`](file:///C:/AI/Rural_internship_project/docs/evaluation/technical_explanation.md) | **In-Depth Engineering Guide.** Explains 17 core concepts (why Manikonda was chosen, DEM processing, Horn's method vs numpy gradient, IDW, Chicago hyetograph, 5-factor risk engine, dynamic renormalization, FSM lifecycle, Haversine dispatch, why SWMM wasn't used, etc.) across 5 standard dimensions: Concept, Why Selected, Implementation, Example, and Limitations. |
| **Algorithms & Mathematical Defense** | [`algorithms_and_formulas.md`](file:///C:/AI/Rural_internship_project/docs/evaluation/algorithms_and_formulas.md) | **Mathematical Proofs & Formulas.** Detailed derivations for the risk formula ($0.40P + 0.20T + 0.20D + 0.10L + 0.10H$), IDW interpolation ($p=2$), Great-Circle Haversine distance, DEM slope calculation, NetworkX road graph connectivity, and a complete step-by-step worked numerical example. |
| **60 Viva Questions & Answers** | [`viva_questions.md`](file:///C:/AI/Rural_internship_project/docs/evaluation/viva_questions.md) | **Viva Voce Rehearsal.** 60 structured Q&As categorized into: Basic Project (10), Geospatial/GIS (10), Data Engineering (10), Risk Modeling (10), Backend/Database (10), Testing/Validation (5), and Limitations/Ethics (5). Ideal for peer mock vivas. |
| **Live Demo Defense Guide** | [`live_demo_defense.md`](file:///C:/AI/Rural_internship_project/docs/evaluation/live_demo_defense.md) | **5-Minute Live Demonstration Script.** Exact terminal commands to launch the FastAPI backend (`uvicorn`) and Streamlit command center (`streamlit run`). Provides a screen-by-screen walkthrough with talking points, expected UI outputs, scenario step advances, dispatching, and emergency recovery troubleshooting steps. |
| **Critical Evaluator Questions** | [`critical_questions.md`](file:///C:/AI/Rural_internship_project/docs/evaluation/critical_questions.md) | **Adversarial Defense Prep.** 20 challenging, skeptical questions from senior external examiners (challenging data reliability, 30m DEM limitations, unverified crowdsourced OSM data, straight-line distance dispatching, and lack of live sensor APIs). Provides honest technical answers, repo evidence links, and unverified disclosures. |

---

## 3. Recommended 3-Day Preparation Strategy

```
+----------------------------------------------------------------------------------------------------+
|                                    DEFENSE PREPARATION SCHEDULE                                    |
|                                                                                                    |
|  DAY 1: FACTUAL & MATHEMATICAL MASTERY                                                             |
|         - Review academic_consistency_check.md and memorize key figures and benchmarks.            |
|         - Study algorithms_and_formulas.md; practice writing the worked numerical example by hand. |
|         - Review technical_explanation.md to master the rationale behind design choices.           |
|                                                                                                    |
|  DAY 2: SLIDE DECK & LIVE DEMONSTRATION PRACTICE                                                   |
|         - Build slide deck following presentation_blueprint.md (15 slides, timed to 15 mins).      |
|         - Practice the live demonstration using live_demo_defense.md; rehearse starting servers    |
|           and executing the MANI-HEAVY-001 scenario under 5 minutes.                               |
|         - Verify automated tests run live on screen: pytest -v (57 tests passing in ~2.4s).        |
|                                                                                                    |
|  DAY 3: MOCK VIVA & ADVERSARIAL DEFENSE                                                            |
|         - Conduct a mock viva using the 60 questions in viva_questions.md.                         |
|         - Rehearse skeptical examiner responses using critical_questions.md.                      |
|         - Practice intellectual honesty: defend what the system DOES without exaggerating what it  |
|           does NOT do.                                                                             |
+----------------------------------------------------------------------------------------------------+
```

---

## 4. Golden Rules for the Defense

1. **Be Intellectually Honest:** Never claim the system predicts flood depth in meters. It calculates an empirical, dimensionless geographic risk score (0–100).
2. **Respect Data Provenance:** Openly state that critical facilities are `OSM_UNVERIFIED` and all emergency response units are `[DEMO SYNTHETIC]`.
3. **Clarify Distance Metrics:** State that dispatch ranking uses straight-line Great-Circle Haversine distance, and that road graph routing is designated for Phase 4.
4. **Disclaim Statutory Authority:** Clarify that AQUILA is an academic decision-support prototype that assists municipal operators, not a replacement for GHMC or IMD.
5. **Show Live Code and Tests:** If an examiner is skeptical, open the terminal and run `pytest -q`. A suite of 57 passing tests executing in 2.4 seconds is the strongest possible defense.

