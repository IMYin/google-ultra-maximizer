# Contributing to Google AI Ultra Maximizer

Thanks for helping make every Google AI Ultra subscription pool transparent, measurable, and composable!

## Engineering Principles

This repository follows the core practices codified in `docs/MATTPOCOCK-SKILLS-PLAYBOOK.md` and `GLOSSARY.md`:
1. **Compose, don't reinvent**: Prefer integrating well-maintained open-source wheels (`t3code`, `agy-lens`, `agent-desktop`, `apprise`, `gflow-cli`) behind small probe/adapter seams rather than reimplementing protocols.
2. **Zero fake metrics**: Never emit placeholder or fabricated numbers. If a quota source is unconfigured or uncalibrated (such as GCP promotional credits without an explicit monthly cap), display its exact state honestly and link to calibration.
3. **Deep modules & clean seams**: Keep HTTP routing, HTML rendering, quota probing, and scheduling advice cleanly separated.
4. **Open-source hygiene**: Never commit personal paths, usernames, emails, tokens, or `*.sqlite` state. Every pull request must pass the hygiene test.

## Local Development & Verification

```bash
# Run unit & open-source hygiene tests
python3 -m unittest discover -s tests -v

# Syntax check bootstrap script
bash -n scripts/bootstrap.sh
```
