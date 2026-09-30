# AirAware – System Architecture & UML Documentation

This directory contains the complete set of formal UML diagrams and architectural specifications for the **AirAware** PM2.5 Decision-Support System.

All diagrams are written in standard GitHub-flavored **Mermaid.js** syntax and render natively on GitHub, GitLab, VS Code, and Markdown previewers.

---

## Index of Diagrams

| Diagram | Document Link | Description | Primary Use in Thesis / FYP |
| :--- | :--- | :--- | :--- |
| **Use Case Diagram** | [use_case_diagram.md](./use_case_diagram.md) | Models system actors (Citizens, Schedulers, OpenAQ, Open-Meteo) and their interactions with core features. | **Chapter 3: Requirements Analysis** |
| **Class Diagram** | [class_diagram.md](./class_diagram.md) | Models the database ORM entities, attributes, primary/foreign keys, and data relationships. | **Chapter 4: System & Database Design** |
| **Entity Relationship Diagram (ERD)** | [entity_relationship_diagram.md](./entity_relationship_diagram.md) | Models physical PostgreSQL tables, foreign keys, cardinality, data types, and check constraints. | **Chapter 4: Physical Database Design** |
| **Sequence Diagrams** | [sequence_diagram.md](./sequence_diagram.md) | Details runtime message passing for (1) automated ingestion & ML forecasting, and (2) user activity planning. | **Chapter 4: Detailed Component Design** |
| **Deployment Diagram** | [deployment_diagram.md](./deployment_diagram.md) | Illustrates physical and container topology across Docker, Nginx, FastAPI, PostgreSQL, and external APIs. | **Chapter 5: Implementation & Deployment** |
| **Activity Diagrams** | [activity_diagram.md](./activity_diagram.md) | Details control flows and decision gates for staleness guards and the 168-lag ML pipeline. | **Chapter 4 & 5: Business Logic & Robustness** |

---

## Architectural Highlights
- **Decoupled 3-Tier Architecture**: Client-side React SPA, stateless FastAPI REST service, and relational PostgreSQL persistence.
- **Fail-Safe Operational Guardrails**: Enforces staleness checks ($\le 180$ minutes) and history completeness (168 hourly lags) before serving predictions.
- **Machine Learning Integration**: Combines deep learning (GRU) and gradient boosting (XGBoost) with conformal prediction bounds for calibrated uncertainty.
