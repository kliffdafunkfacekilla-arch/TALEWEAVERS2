# TALEWEAVERS Technical Debt Report

Date: 2026-02-26
Status: INITIAL AUDIT COMPLETED

## Summary of Findings
The TALEWEAVERS project shows signs of rapid iterative development, resulting in a "loose" file structure and inconsistent naming conventions across microservices. While the core logic appears solid, the orchestration layer (scripts, directory structure) is fragile and prone to versioning confusion.

## Critical Issues

### 1. Inconsistent Directory Structure
**Findings:** The project root contains several `saga_` modules, but there is also a nested `TALEWEAVERS/TALEWEAVERS` directory containing the `saga_campaign_weaver` and `saga_vtt_client`.
**Impact:** High. This complicates build scripts (`run_all.bat` needs special paths) and makes the project difficult for new developers to navigate.
**Recommendation:** Flatten the structure. Move `saga_campaign_weaver` and `saga_vtt_client` to the root directory alongside other modules.

### 2. High Density of Redundant Backup Files
**Findings:** Almost every module contained `.bak` copies of source files (e.g., `server.py.bak`, `main.py.bak`).
**Impact:** Low (Maintenance). Clutters the workspace and can lead to accidental edits of the wrong file.
**Status:** **RESOLVED** (Backups removed and added to `.gitignore`).

### 3. Inconsistent Entry Point Naming
**Findings:** 
- `saga_gamemaster` uses `server.py`.
- `saga_lore_module`, `saga_architect`, `saga_character_engine`, etc., use `main.py`.
**Impact:** Medium (Developer Experience). Disconnects with standard FastAPI/uvicorn expectations for a uniform project.
**Recommendation:** Standardize all FastAPI services to use `main.py` as the entry point.

### 4. Fragmented Documentation
**Findings:** Multiple versions of `.docx` blueprints (e.g., `ok lets see it.docx`, `ok lets see it(1).docx`) and zip files are scattered in the root and subdirectories.
**Impact:** Medium (Correctness). Hard to know which document represents the current "Source of Truth" for mechanics.
**Recommendation:** Consolidate documentation into Markdown files within the repository (e.g., localized `README.md` or a central `docs/` folder).

## Low Priority / Polish

- **Schema Redundancy:** Multiple modules define similar Pydantic models (e.g., `VoronoiCell`, `Character`). Consider a shared `saga_common` package if logical overlap exceeds 40%.
- **Log Pollution:** Some directories contain `verification_output.txt` or `build_log.txt`. These should be ignored or routed to a central `logs/` directory.

## Next Steps for Rectification
1. Flatten the directory structure (Move Campaign Weaver and VTT Client to root).
2. Standardize all entry points to `main.py`.
3. Consolidate specific mechanics documentation from `.docx` to Markdown.
