# Maintainer Guide - PR Publishing Infrastructure

This guide is for repository maintainers on how to use and manage the PR publishing infrastructure.

## Initial Setup (One-Time)

After merging this PR, complete these one-time setup tasks:

### 1. Verify Workflows Are Running

- [ ] Go to Actions tab in GitHub
- [ ] Check that workflows appear in the list
- [ ] Create a test branch and PR to verify automation
- [ ] Ensure all checks complete successfully

### 2. Configure Repository Settings

#### Branch Protection (Recommended)

For `main` branch:
- [ ] Go to Settings → Branches → Add rule
- [ ] Require status checks to pass:
  - [ ] test (Python 3.11 recommended minimum)
  - [ ] lint
  - [ ] security
- [ ] Require at least 1 approval
- [ ] Dismiss stale reviews when new commits are pushed
- [ ] Require linear history (optional)

#### Enable/Disable Workflows

All workflows are enabled by default. To disable:
- Go to Actions → Select workflow → ... → Disable workflow

### 3. Create Labels (Auto-created, but verify)

Required labels for auto-labeling:
- `bug`, `enhancement`, `documentation`, `testing`
- `performance`, `security`, `refactoring`, `question`
- `priority: high`, `stale`
- `size/XS`, `size/S`, `size/M`, `size/L`, `size/XL`, `size/XXL`
- `core`, `modules`, `sectors`, `memory`, `nlp`, `ops`, `messaging`
- `configuration`, `dependencies`, `ci/cd`, `scripts`

Most will be auto-created on first use.

### 4. Optional Integrations

#### Codecov (Optional)
```bash
# Get token from codecov.io
# Add as repository secret: CODECOV_TOKEN
```

#### Notifications
- Configure GitHub notifications for workflow failures
- Set up Slack/Discord webhook (if desired)

## Daily Operations

### Managing Pull Requests

#### 1. Initial PR Review

When a new PR arrives:
1. Check automated checks pass
2. Review PR description completeness
3. Verify all checklist items are checked
4. Check size label for complexity
5. Review code changes

#### 2. Requesting Changes

```markdown
Thank you for your contribution! Please address the following:

- [ ] Add tests for the new feature
- [ ] Update documentation in README.md
- [ ] Fix linting issues (see CI log)
- [ ] Resolve merge conflicts

Once addressed, I'll review again.
```

#### 3. Approving PRs

Before approving:
- [ ] All CI checks pass
- [ ] Code quality is acceptable
- [ ] Documentation is updated
- [ ] Tests are adequate
- [ ] Security scan passes
- [ ] At least one maintainer review

#### 4. Merging

We use **Squash and Merge** by default:
1. Click "Squash and merge"
2. Edit commit message if needed
3. Confirm merge
4. Delete branch (if not from fork)

For special cases:
- **Merge commit**: Feature branches with valuable history
- **Rebase**: Clean linear history preferred

### Managing Issues

#### New Issues

1. **Auto-labels** will be applied based on content
2. **Review** and add additional labels if needed
3. **Assign** to appropriate person
4. **Milestone** (if using milestones)
5. **Respond** within 2-3 business days

#### Stale Issues

- Bot will mark issues stale after 60 days
- Bot will close after 7 more days
- Remove `stale` label to keep open
- Add `pinned` label to prevent auto-close

### Managing Releases

#### Creating a Release

1. **Update Version**: Edit version strings if needed
2. **Create Tag**: 
   ```bash
   git tag -a v1.2.3 -m "Release version 1.2.3"
   git push origin v1.2.3
   ```
3. **Workflow Runs**: Automatically creates GitHub release
4. **Verify**: Check release notes and assets
5. **Announce**: Share release in appropriate channels

#### Version Numbering

Follow [Semantic Versioning](https://semver.org/):
- **v1.0.0 → v2.0.0**: Breaking changes
- **v1.0.0 → v1.1.0**: New features
- **v1.0.0 → v1.0.1**: Bug fixes

## Workflow Management

### CI Workflow

**When it runs**: Push to main/develop, all PRs

**What to check**:
- Test results across Python versions
- Code coverage trends
- Linting warnings
- Security alerts

**If it fails**:
1. Check logs in Actions tab
2. Identify failing job
3. Review error messages
4. Guide contributor to fix (or fix yourself for urgent issues)

### Release Workflow

**When it runs**: Version tags pushed

**What to check**:
- Tests pass before release created
- Changelog is accurate
- Release notes are clear
- Version number is correct

**If it fails**:
1. Delete the tag: `git tag -d vX.Y.Z && git push origin :refs/tags/vX.Y.Z`
2. Fix the issue
3. Re-create tag with fixed version

### PR Checklist Workflow

**What it does**:
- Validates PR description
- Adds size label
- Checks for required sections

**Manual overrides**:
- Edit PR to fix validation
- Manually add/remove size labels if needed

### Auto-label Workflow

**What it does**:
- Labels based on content
- Labels based on file paths

**Manual adjustments**:
- Review auto-applied labels
- Add/remove as needed
- Edit `.github/labeler.yml` to adjust rules

### Stale Bot

**Configuration**: `.github/workflows/stale.yml`

**Adjust timing**:
```yaml
days-before-issue-stale: 60  # Change as needed
days-before-issue-close: 7
days-before-pr-stale: 30
days-before-pr-close: 7
```

**Exempt items**:
- Add `pinned` label
- Add to `exempt-issue-labels` list

## Troubleshooting

### Workflow Not Running

1. Check workflow file syntax: Actions → Select workflow → View file
2. Verify triggers match event (push vs PR)
3. Check branch protection isn't blocking
4. Review path filters if used

### Workflow Failing

1. Check Actions tab for error details
2. Review specific job logs
3. Re-run failed jobs if transient
4. Update workflow if systematic issue

### Too Many Notifications

1. Adjust personal GitHub notification settings
2. Disable specific workflow notifications
3. Use GitHub's "Unwatch" with custom settings

### Labels Not Applied

1. Verify label exists in repository
2. Check auto-labeling rules in `.github/labeler.yml`
3. Manually apply if auto-labeling missed
4. Update labeler rules if pattern needed

## Best Practices

### For Maintainers

1. **Respond quickly**: Acknowledge PRs within 2-3 days
2. **Be constructive**: Provide helpful feedback
3. **Be consistent**: Apply standards uniformly
4. **Document decisions**: Explain non-obvious rejections
5. **Recognize contributors**: Thank and credit people
6. **Update documentation**: Keep guides current

### For Code Review

1. **Check logic**: Does it solve the problem correctly?
2. **Check tests**: Are tests comprehensive?
3. **Check docs**: Is documentation updated?
4. **Check style**: Does it follow conventions?
5. **Check security**: Are there vulnerabilities?
6. **Check performance**: Any performance impacts?

### For Merging

1. **Verify CI**: All checks must pass
2. **Squash commits**: Unless history is valuable
3. **Good commit messages**: Edit if needed
4. **Delete branches**: Clean up after merge
5. **Close issues**: Ensure linked issues close

## Monitoring

### Weekly Tasks

- [ ] Review open PRs and provide feedback
- [ ] Triage new issues
- [ ] Check CI success rates
- [ ] Review security scan results
- [ ] Update labels as needed

### Monthly Tasks

- [ ] Review stale issues/PRs
- [ ] Update workflow versions (actions/*)
- [ ] Check for dependency updates
- [ ] Review and adjust automation rules
- [ ] Update documentation if processes changed

### Quarterly Tasks

- [ ] Full workflow audit
- [ ] Review and update labels
- [ ] Update contribution guidelines
- [ ] Survey contributors for feedback
- [ ] Plan process improvements

## Metrics to Track

### PR Metrics
- Time to first response
- Time to merge
- PR acceptance rate
- Average PR size
- Review cycles needed

### Issue Metrics
- Time to triage
- Resolution time
- Stale issue rate
- Issue types distribution

### Workflow Metrics
- CI success rate
- Average CI duration
- Security alerts count
- Test coverage trends

## Getting Help

### Documentation
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [GitHub Flow](https://docs.github.com/en/get-started/quickstart/github-flow)
- Project docs: CONTRIBUTING.md, PR_PROCESS.md

### Support Channels
- GitHub Community Forum
- GitHub Support (for GitHub-specific issues)
- Project maintainers discussion

## Customization

### Adjusting Workflows

Edit `.github/workflows/*.yml` files:
- Change Python versions tested
- Adjust linting rules
- Modify notification settings
- Add new checks

### Adjusting Templates

Edit template files:
- `.github/pull_request_template.md`
- `.github/ISSUE_TEMPLATE/*.md`

### Adjusting Auto-labeling

Edit `.github/labeler.yml`:
- Add new labels
- Change path patterns
- Adjust matching rules

---

**Last Updated**: October 31, 2025
**Infrastructure Version**: 1.0.0

For questions about this infrastructure, create an issue with the `question` label.
