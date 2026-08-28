# Third-party notices and provenance

## Bundled material

The current repository snapshot contains no declared third-party script, binary, font, image, analysis template, FCS/WSP file, or biological dataset. The bundled validator imports only the Python standard library. The JSON file in `examples/` is a synthetic contract fixture and does not contain acquired events or patient/sample data.

## External names and formats

- FlowJo and its WSP workspace format are referenced for interoperability and descriptive purposes. FlowJo is not bundled, and no affiliation or endorsement is implied.
- FCS and Gating-ML are referenced as flow-cytometry data/interchange formats. Their specifications are not copied into this repository.
- CytoPilot is the project whose output contract is described and validated here.

Names and trademarks remain the property of their respective owners.

## Provenance item requiring maintainer confirmation

An internal pre-release draft stated that an OpenScience `flow-cytometry-analysis` skill had been used as a capability checklist. That source was not available in the local audit, so textual independence could not be verified conclusively. The release snapshot does not bundle or quote that skill and removes the internal provenance instruction from `SKILL.md`.

Before the first public push, the maintainer should compare the final `SKILL.md` and `references/` against any OpenScience source actually consulted. If expressive text, thresholds, examples, or structure were adapted, either rewrite them independently or add the source, copyright holder, license, URL, and affected files here. Do not assume that publicly visible prompts are MIT-licensed.

## Future contributions

Do not add real FCS/WSP data, patient identifiers, proprietary gating templates, screenshots, vendor manuals, or copied prompts without explicit redistribution rights and documented attribution.
