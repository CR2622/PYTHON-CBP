# CODESTORM

## Project Overview
This project uses Claude Code custom subagents for enhanced AI-assisted development workflows.

## Available Subagents

### 🔴 Critical Agents (Opus)
| Agent | Description | Usage |
|:------|:------------|:------|
| `code-reviewer` | Read-only code quality, security, and maintainability reviews | `Use the code-reviewer agent to review the auth module` |
| `debugger` | Systematic root cause analysis with fix capability | `@"debugger (agent)" fix the failing login test` |
| `optimizer` | Performance profiling and bottleneck elimination | `Have the optimizer agent analyze the API endpoints` |
| `security-auditor` | OWASP-based vulnerability scanning and security audit | `Use the security-auditor to scan for vulnerabilities` |
| `architect` | System design, architecture planning, and ADRs | `Use the architect agent to design the microservices` |
| `refactorer` | SOLID-based code restructuring without behavior change | `Use the refactorer to clean up the user module` |
| `api-builder` | REST/GraphQL/WebSocket endpoint design and implementation | `Use the api-builder to create the payments API` |
| `doc-writer` | Documentation generation (READMEs, API docs, guides) | `Use the doc-writer to document the API` |
| `devops` | CI/CD, Docker, cloud infrastructure, and deployment | `Use the devops agent to set up GitHub Actions` |
| `ui-designer` | Premium, responsive, accessible UI implementation | `Use the ui-designer to build the dashboard page` |

### 🟡 Support Agents (Sonnet)
| Agent | Description | Usage |
|:------|:------------|:------|
| `test-runner` | Fast test execution with concise failure reporting | `Use a subagent to run all tests and report failures` |
| `git-manager` | Branching, commits, conflicts, and PR management | `Use the git-manager to resolve the merge conflict` |
| `dependency-manager` | Package auditing, updates, and optimization | `Use the dependency-manager to audit packages` |

### 🔵 User-Level Agents (All Projects)
| Agent | Description | Usage |
|:------|:------------|:------|
| `data-scientist` | SQL & data analysis (Opus) | `Use the data-scientist to analyze the user data` |

## Hook Scripts
- `scripts/validate-readonly-query.sh` — Blocks SQL write operations for read-only agents
- `scripts/run-linter.sh` — Auto-detects and runs linter after file edits
