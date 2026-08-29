# Public Repository Release Checklist

Use this checklist before sharing the repository publicly on LinkedIn, Naukri or a resume.

## Repository hygiene

- [ ] README is the first-stop document and explains value within 30 seconds.
- [ ] No secrets, private keys, credentials or environment files are tracked.
- [ ] Temporary backups/experiments are removed from the public tree or clearly isolated as documentation.
- [ ] Large model files are not committed unless intentionally managed outside Git.
- [ ] `.gitignore` covers local environments and generated artifacts.
- [ ] `git diff --check` passes.

## Engineering evidence

- [ ] CI workflow is visible and passes.
- [ ] Test command is documented.
- [ ] Architecture is documented.
- [ ] Deployment path is documented.
- [ ] Troubleshooting path is documented.
- [ ] Current limitations are explicit.
- [ ] Claims match what was actually validated.

## Recruiter experience

- [ ] Repository description contains LLMOps / GenAI / AI Platform keywords.
- [ ] GitHub Topics contain relevant search terms.
- [ ] README starts with a strong one-line value proposition.
- [ ] Architecture diagram is visible without reading code.
- [ ] Current milestone and roadmap are easy to find.
- [ ] Resume/LinkedIn link points directly to this repository.

## Security settings for a public GitHub repository

GitHub recommends enabling, where available for public repositories:

- Dependabot alerts
- Secret scanning
- Push protection
- Code scanning
- `SECURITY.md`

See GitHub repository best-practice guidance for the current security controls.
