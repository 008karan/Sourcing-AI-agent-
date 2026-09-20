# Final Submission Checklist

Aerchain requested:
- recorded walkthrough video (Loom or Google Drive)
- live link to build
- document/PPT explaining what was built
- hosted build link

## Product readiness
- [ ] All MUST acceptance criteria pass.
- [ ] `python verify_demo.py` passes.
- [ ] Run full demo twice from a fresh server start.
- [ ] Ensure no source file link 404s.
- [ ] Ensure all scenario demo questions return consistently.
- [ ] Ensure one ugly-edge exception is unresolved at start so trust UX is visible.
- [ ] Ensure buyer can resolve one exception live without breaking later demo steps.

## Hosting
- [ ] App is publicly reachable.
- [ ] Model/API keys are server-side only.
- [ ] Demo files are bundled/served correctly.
- [ ] Health endpoint works.
- [ ] Cold-start behavior is acceptable.

## Walkthrough structure (5-7 min)
- [ ] 30 sec - problem and thesis.
- [ ] 45 sec - RFx copilot + buyer approval.
- [ ] 60 sec - five messy supplier responses.
- [ ] 120 sec - comparison, ugly edges, evidence drawer.
- [ ] 60 sec - exception resolution / clarification.
- [ ] 90 sec - natural-language scenario + deterministic award.
- [ ] 30 sec - deliberate tradeoffs + next step.

## Document/PPT
Include:
- [ ] problem / why current spreadsheet workflow fails
- [ ] primary persona + supporting personas
- [ ] product flow
- [ ] architecture with AI vs deterministic boundaries
- [ ] evidence/provenance design
- [ ] edge cases demonstrated
- [ ] scenario engine
- [ ] deliberate exclusions
- [ ] what would be built next

## Final hygiene
- [ ] remove secrets, caches and local-only junk
- [ ] README has setup + demo instructions
- [ ] use fictional supplier/customer data only
- [ ] label any seeded/fallback model behavior clearly
