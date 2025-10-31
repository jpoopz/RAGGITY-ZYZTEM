# Agent Memory (rolling log; newest at top)

## 2025-10-31 (Evening) - Garment Workshop System
- **Decision**: Replaced fragile CLO socket listener with file-based "Garment Workshop" system
- **Why**: Socket-based approach caused CLO crashes; new system generates CLO-ready files externally
- **Implementation**:
  - Created `modules/garment_generator.py` - generates .zprj files from templates
  - Created `modules/render_engine.py` - generates preview images without CLO
  - Created `modules/project_manager.py` - handles CLO integration and project tracking
  - Created `ui/tabs/workshop_tab.py` - full UI for design → preview → export workflow
  - Added 5 base templates (tshirt, pants, jacket, dress, shirt) in `templates/garments/`
  - Added API endpoints: `/generate_garment`, `/list_garments`, `/open_in_clo`
  - Integrated Workshop tab into main UI navigation
- **Risks**: Template files are placeholders; real CLO integration requires actual pattern data
- **Follow-ups**: 
  - Archive or remove `clo_bridge_listener.py` (marked deprecated)
  - Add real garment pattern generation (future enhancement)
  - Consider CLO CLI integration when available

## 2025-10-31 (Earlier)
- Bootstrapped external memory system: AGENT_MEMORY, ARCHITECTURE, CONTEXT_INDEX, Cursor rules.
- Enforced pre-commit hooks to refresh index and require memory updates on large diffs.
- Next: keep adding brief entries here for any significant change (5–10 lines max).
