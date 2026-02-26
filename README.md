# 🧶 TALEWEAVERS

**The Ultimate Storytelling & Game Master Orchestration Engine**

TALEWEAVERS is a suite of AI-driven microservices designed to facilitate deep, immersive tabletop roleplaying experiences. From procedural world architecture to dynamic encounter resolution and AI-narrated campaigns, TALEWEAVERS handles the "math and lore" so GMs and players can focus on the story.

---

## 🚀 The S.A.G.A. Ecosystem

The project is divided into several specialized "Saga" modules, each serving a distinct purpose in the game loop:

| Module | Name | Port | Description |
| :--- | :--- | :--- | :--- |
| **00** | **VTT Client** | 5173 | The visual interface for players and GMs (React/PixiJS). |
| **01** | **Lore Vault** | 8001 | Central repository for world facts, cultures, and history. |
| **02** | **World Architect** | 8002 | Prodecural map and physics/calendar simulator (C++ Engine). |
| **03** | **Character Engine** | 8003 | Survial pools, evolution, and loadout calculations. |
| **04** | **Encounter Engine** | 8004 | AI-driven threat generation and combat orchestration. |
| **05** | **Item Foundry** | 8005 | Economy, D-Dust math, and equipment effects. |
| **06** | **Skill Engine** | 8006 | Tactical triad calculations (Aggressive, Skirmish, etc.). |
| **07** | **Clash Engine** | 8007 | Margin-of-Victory resolution for combat actions. |
| **08** | **Chronos** | 9000 | Time-tracking and event scheduling. |
| **09** | **Game Master** | 8000 | The "Director" node using LangGraph to weave it all together. |
| **10** | **Campaign Weaver** | 8010 | Procedural quest and campaign roadmap generator. |

## 🛠️ Getting Started

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** (for VTT Client)
- **Local LLM** (Ollama recommended for Campaign Weaver/GM)

### Installation & Launch
The easiest way to start the entire ecosystem on Windows is using the provided batch script:

```bash
run_all.bat
```

This will launch all microservices in separate terminal windows and open the VTT client at `http://localhost:5173`.

## 📜 Mechanics Overview
TALEWEAVERS uses a custom "Lead & Trail" stat system. 
- **Lead Stat**: Determines the primary action modifier and costs resources (Stamina/Focus).
- **Trail Stat**: Determines the reactive defense modifier.
- **Assault/Resolve**: Combat is resolved via "Clashes" where margin-of-victory determines the severity of the outcome.

For a detailed breakdown of the 36 Tactical Skills, see [crucial.md](file:///c:/Users/krazy/Documents/GitHub/TALEWEAVERS/crucial.md).

## 🛡️ License
Proprietary. All rights reserved.
