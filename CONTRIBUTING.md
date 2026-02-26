# Contributing to TALEWEAVERS

Thank you for your interest in helping build this world! To maintain the integrity of the mechanics and lore, please follow these guidelines.

## 🛠️ General Rules
- **No AC (Armor Class)**: This system does not use D&D-style Armor Class. Use the "Lead & Trail" and "Clash" mechanics defined in the documentation.
- **Fantasy Setting**: This project is strictly high fantasy. No sci-fi or modern technology unless explicitly part of the lore (e.g., Aetherium).
- **Stateless Engines**: All math-based modules (Skill, Clash, Character, Item) must remain stateless. They should accept JSON and return JSON without side effects.

## 📝 Code Style
- **Python**: Use PEP 8. All API endpoints must use Pydantic for request/response validation.
- **Types**: Use Python type hints and TypeScript for the frontend.
- **Comments**: Document the "Why", not the "What".

## 🚀 Development Workflow
1.  **Audits**: Before making major changes, check the `tech_debt_report.md` to see if your change aligns with the rectification plan.
2.  **Versioning**: Do not use `.bak` files. Rely on Git for versioning.
3.  **Testing**: Every new feature should include a `verify_app.py` or `test_api.py` script to validate functionality.

## 📂 Repository Structure
- `saga_*`: Individual microservices.
- `data/`: Core JSON datasets for the world.
- `raw_data/`: Blueprints and source documents.
