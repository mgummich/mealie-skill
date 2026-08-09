## What this changes

<!-- One or two sentences. Link an issue if there is one. -->

## Checklist

- [ ] Edited `skill/`, not the rendered files in `dist/` or the derived
      standalone prompts (`standalone/prompts/common.txt` is the one
      hand-maintained exception)
- [ ] `python3 test_build.py` passes
- [ ] `python3 build.py` renders all targets without leftover
      `${CONTENT_LANG}` placeholders
- [ ] No content language hardcoded into a prompt
- [ ] New write operation? Entry in `ORDER`, branch in `cmd_apply`, row in
      `skill/references/actions.md`, checked with `apply --dry-run`

## Verification

<!-- Commands you ran and their outcome. For anything touching writes,
     paste the relevant part of `apply --dry-run`. -->
