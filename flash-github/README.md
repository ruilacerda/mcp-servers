# Flash-GitHub

A powerful MCP server tool for interacting with GitHub repositories directly from Claude.

## Overview

Flash-GitHub is a FastMCP server that enables AI assistants to interact with GitHub repositories on your behalf. It provides a seamless interface for performing common GitHub operations such as searching repositories, browsing content, pulling code, pushing changes, and comparing local directories with remote repositories.

## Features

- **Search GitHub repositories** - Find repositories based on keywords, topics, or other search criteria
- **Browse repositories** - Explore repository structure, view file contents, and access repository information
- **Pull from repositories** - Download files from a repository to a local directory
- **Push to repositories** - Upload local changes to a repository, with automatic repository creation if needed
- **Compare repositories** - Compare local directories with remote repositories to identify differences

## Installation

### Prerequisites

- Python 3.7 or higher
- GitHub personal access token with the appropriate permissions

### Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/flash-github.git
   cd flash-github
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root directory with your GitHub API token:
   ```
   GITHUB_API_TOKEN=your_github_token_here
   ```

   To generate a GitHub token, visit GitHub Settings > Developer Settings > Personal Access Tokens.

## Usage

Start the MCP server:

```bash
python flash-github.py
```

The server can be used with compatible AI assistants that support MCP protocol.

## Available Tools

### search_repositories

Search for repositories on GitHub based on a query.

```
search_repositories(query: str, limit: int = 10)
```

**Arguments:**
- `query`: Search query to find repositories
- `limit`: Maximum number of repositories to return (default: 10)

### browse_repository

Browse a GitHub repository - provides repository info, lists contents, and retrieves file content.

```
browse_repository(repo_path: str, path: str = "", branch: str = "", include_content: bool = False)
```

**Arguments:**
- `repo_path`: Repository path in format 'owner/repo'
- `path`: Path to the directory or file within the repository (default: root)
- `branch`: Branch to explore (default: repository's default branch)
- `include_content`: Whether to include file content when viewing a single file (default: False)

### pull_from_repository

Pull changes from a GitHub repository to a local directory.

```
pull_from_repository(repo_path: str, local_dir: str, branch: str = "")
```

**Arguments:**
- `repo_path`: Repository path in format 'owner/repo'
- `local_dir`: Path to the local directory
- `branch`: Branch to pull from (default: repository's default branch)

### push_to_repository

Push local changes to a GitHub repository.

```
push_to_repository(repo_path: str, local_dir: str, commit_message: str, branch: str = "")
```

**Arguments:**
- `repo_path`: Repository path in format 'owner/repo'
- `local_dir`: Path to the local directory
- `commit_message`: Commit message for the changes
- `branch`: Branch to push to (default: repository's default branch)

### compare_repository

Compare local directory with GitHub repository and show differences.

```
compare_repository(repo_path: str, local_dir: str, branch: str = "")
```

**Arguments:**
- `repo_path`: Repository path in format 'owner/repo'
- `local_dir`: Path to the local directory
- `branch`: Branch to compare with (default: repository's default branch)

## Example Workflows

### Clone a repository and make changes
```
# Search for a repository
search_repositories("tensorflow")

# Browse the repository
browse_repository("tensorflow/tensorflow")

# Pull the repository to a local directory
pull_from_repository("tensorflow/tensorflow", "./tensorflow-local")

# Make local changes to files...

# Push changes back to GitHub
push_to_repository("yourusername/tensorflow-fork", "./tensorflow-local", "Updated documentation")
```

### Exploring repository contents
```
# View repository information
browse_repository("microsoft/vscode")

# Browse a specific directory
browse_repository("microsoft/vscode", "src/vs/editor")

# View a specific file with its content
browse_repository("microsoft/vscode", "README.md", include_content=True)
```

### Compare local changes with remote repository
```
# Pull a repository
pull_from_repository("yourusername/myproject", "./local-project")

# Make local changes...

# Compare changes before pushing
compare_repository("yourusername/myproject", "./local-project")

# Push changes if everything looks good
push_to_repository("yourusername/myproject", "./local-project", "Updated features")
```

## Dependencies

- `github` - PyGithub for GitHub API access
- `mcp.server.fastmcp` - FastMCP for building MCP servers
- `dotenv` - Loading environment variables
- Standard libraries: os, pathlib, base64, fnmatch, traceback, datetime

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests.