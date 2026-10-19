# Assumptions: settled vs changed (Appendix A of the spec)
SETTLED by the owner after the spec file:
- Module that taps is named Tapper (NOT Stepper). Folders: readmap/ solver/ tapper/ connection/ ui/.
- ReadMap owns capturing; Connection only connects ADB, opens the game, handles interruptions.
- Tap gap: 150-200 ms random (spec 5.2). Appendix A item 2 (100-150?) NOT fully settled -> constants TAP_GAP_MIN_MS/TAP_GAP_MAX_MS in src/tapper/tapper.py, change in one place.
- Heart loss: ANY lost heart -> stop now, diagnostic captures, log case, switch to Way 2 (spec 5.3).
- No help-request channel (7.5). Full logs from day one in local logs/ (section 8).
- Update: public repo, plain small files only, NO zip. Update downloads only when the user presses the button. version.json at repo root is the single update-check file.
STILL UNVERIFIED on real hardware (must tune on a real phone/Windows PC):
- Exact pixel thresholds in ReadMap cell classification (black/blue/rainbow/grey-dot), right-strip width, grid geometry, heart-icon reading, and real stitching offsets. Clean heuristics informed by v1, not proven on a real board yet.
- Appendix A item 5 (log sharing route) and item 6 (whether Reset resets both clocks): Reset currently clears both clocks; log folder is a fixed local logs/ folder the user can send.
