# Vendor Test Pack

Use this folder as the fixed extraction/normalization regression corpus.

Files:
- `buyer_rfx_reference.xlsx` - buyer's reference RFx
- `rfx.json` - canonical RFx
- `vendor_a_packright_offer.xlsx` - 30/30; per-piece and per-100
- `vendor_b_corrpro_quote.pdf` - 30/30; USD/100; conditional footnote rebate
- `vendor_c_boxworks_offer.docx` - 27/30; carton/each; freight extra
- `vendor_d_alphapack_rate_card_photo.jpg` - angled photo; visual ambiguity; bundle units; FSC failure
- `vendor_e_greencarton_reply.eml` / `.txt` - INR/kg; prior-year references; percentage freight
- `demo_state.json` - full seeded truth
- `normalized_truth.csv` - flat expected comparison truth
- `manifest.json` - edge-case descriptions

Rules when testing:
1. Do not edit supplier files to make parsing easier.
2. Missing must remain missing.
3. Do not apply conditional discounts silently.
4. Never let the model perform the final normalization arithmetic.
5. Preserve source evidence for every extracted commercial fact.
