from typing import Any, List, Optional, Dict
import os
import pathlib
import base64
import fnmatch
import traceback
from datetime import datetime
from github import Github, Auth
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Initialize FastMCP server
mcp = FastMCP("flash-github")

# Load environment variables from .env file
load_dotenv()

# Get the GitHub API token from environment variables
GITHUB_API_TOKEN = os.getenv("GITHUB_API_TOKEN")

# Check if the token was loaded successfully
if not GITHUB_API_TOKEN:
    print("Error: GITHUB_API_TOKEN not found in .env file")
    exit(1)

# Initialize GitHub API client
auth = Auth.Token(GITHUB_API_TOKEN)
g = Github(auth=auth)


@mcp.tool()
async def search_repositories(query: str, limit: int = 10) -> str:
    """
    Search for repositories on GitHub based on a query.

    Args:
        query: Search query to find repositories
        limit: Maximum number of repositories to return (default: 10)
    """
    try:
        repositories = g.search_repositories(query)
        results = []

        for i, repo in enumerate(repositories[:limit]):
            results.append(f"Repository {i + 1}:")
            results.append(f"  Name: {repo.name}")
            results.append(f"  Full Name: {repo.full_name}")
            results.append(f"  URL: {repo.html_url}")
            results.append(f"  Description: {repo.description}")
            results.append(f"  Stars: {repo.stargazers_count}")
            results.append(f"  Forks: {repo.forks_count}")
            results.append(f"  Last Updated: {repo.updated_at}")
            results.append("")

        if not results:
            return "No repositories found matching your query."

        return "\n".join(results)
    except Exception as e:
        error_details = traceback.format_exc()
        return f"Error searching repositories: {str(e)}\n\nDetails: {error_details}"


@mcp.tool()
async def browse_repository(repo_path: str, path: str = "", branch: str = "", include_content: bool = False) -> str:
    """
    Browse a GitHub repository - provides repository info, lists contents, and retrieves file content.

    Args:
        repo_path: Repository path in format 'owner/repo'
        path: Path to the directory or file within the repository (default: root)
        branch: Branch to explore (default: repository's default branch)
        include_content: Whether to include file content when viewing a single file (default: False)
    """
    try:
        # Validate the repository path format
        if '/' not in repo_path:
            return f"Error: Invalid repository path '{repo_path}'. Format should be 'owner/repo'."

        # Attempt to access the repository
        try:
            repo = g.get_repo(repo_path)
        except Exception as repo_error:
            # Add specific handling for repository not found
            return f"Error accessing repository '{repo_path}': {str(repo_error)}"

        # If branch is specified, use it, otherwise use default branch
        ref = branch if branch else repo.default_branch

        # Always include repository info at the beginning
        repo_info = []
        repo_info.append("📚 REPOSITORY INFORMATION")
        repo_info.append("=" * 50)
        repo_info.append(f"Repository: {repo.full_name}")
        repo_info.append(f"URL: {repo.html_url}")
        repo_info.append(f"Description: {repo.description or '(No description)'}")
        repo_info.append(f"Default Branch: {repo.default_branch}")
        repo_info.append(f"Current Branch: {ref}")
        repo_info.append(f"Primary Language: {repo.language or 'Not specified'}")

        # Add statistics in a compact format
        stats = []
        stats.append(f"⭐ Stars: {repo.stargazers_count:,}")
        stats.append(f"🍴 Forks: {repo.forks_count:,}")
        stats.append(f"⚠️ Issues: {repo.open_issues_count:,}")
        repo_info.append(" | ".join(stats))

        # Add dates in a compact format
        dates = []
        dates.append(f"Created: {repo.created_at.strftime('%Y-%m-%d')}")
        dates.append(f"Updated: {repo.updated_at.strftime('%Y-%m-%d')}")
        dates.append(f"Last Push: {repo.pushed_at.strftime('%Y-%m-%d')}")
        repo_info.append(" | ".join(dates))

        # Add license and visibility
        if repo.license:
            repo_info.append(f"License: {repo.license.name}")
        repo_info.append(f"Visibility: {'Private' if repo.private else 'Public'}")

        # Add clone URLs
        repo_info.append(f"Clone URL (HTTPS): {repo.clone_url}")
        repo_info.append(f"Clone URL (SSH): {repo.ssh_url}")
        repo_info.append("=" * 50)
        repo_info.append("")  # Empty line for separation

        # Try to get the contents at the specified path
        try:
            contents = repo.get_contents(path, ref=ref)
        except Exception as path_error:
            # If there's an error accessing the path, still return the repo info
            # but add the error message
            return "\n".join(repo_info) + f"\nError accessing path '{path}' in repository: {str(path_error)}"

        # Determine if we're looking at a file or directory
        if not isinstance(contents, list):
            # We have a single file
            file_info = []
            file_info.append("📄 FILE INFORMATION")
            file_info.append("-" * 50)
            file_info.append(f"File: {contents.path}")
            file_info.append(f"Size: {contents.size:,} bytes")
            file_info.append(f"SHA: {contents.sha}")

            # If it's a symlink, show the target
            if hasattr(contents, 'target') and contents.target:
                file_info.append(f"Symlink to: {contents.target}")

            # Add download URL
            file_info.append(f"Download URL: {contents.download_url}")
            file_info.append("-" * 50)

            # Include content if requested
            if include_content:
                file_info.append("")  # Empty line for separation
                file_info.append("FILE CONTENT")
                file_info.append("-" * 50)
                try:
                    file_content = contents.decoded_content.decode('utf-8')
                    file_info.append(file_content)
                except UnicodeDecodeError:
                    file_info.append("(Binary file - content not displayed)")
            else:
                file_info.append("")
                file_info.append("To view the file content, use include_content=True")

            # Combine repository info and file info
            return "\n".join(repo_info + file_info)

        # We have a directory listing
        dir_info = []
        path_display = path if path else "root"
        dir_info.append(f"📂 DIRECTORY CONTENTS: '{path_display}'")
        dir_info.append("-" * 50)

        # Sort contents - directories first, then files
        dirs = []
        files = []

        for item in contents:
            if item.type == "dir":
                dirs.append(item)
            else:
                files.append(item)

        # Add directories to results
        if dirs:
            for item in sorted(dirs, key=lambda x: x.path.lower()):
                dir_name = item.path.split('/')[-1]
                dir_info.append(f"📁 {dir_name}/")
        else:
            dir_info.append("(No subdirectories)")

        dir_info.append("")  # Empty line for separation

        # Add files to results
        if files:
            dir_info.append("FILES:")
            for item in sorted(files, key=lambda x: x.path.lower()):
                file_name = item.path.split('/')[-1]
                file_size = f"{item.size:,} bytes"
                dir_info.append(f"📄 {file_name} ({file_size})")
        else:
            dir_info.append("(No files)")

        # Add navigation tip
        dir_info.append("")
        dir_info.append("-" * 50)
        dir_info.append("To navigate to a subdirectory, specify its path.")
        dir_info.append("To view a file, specify its path and set include_content=True.")

        # Combine repository info and directory info
        return "\n".join(repo_info + dir_info)

    except Exception as e:
        # Add detailed error reporting
        import traceback
        error_details = traceback.format_exc()
        return f"Error browsing repository: {str(e)}\n\nDetails: {error_details}"


@mcp.tool()
async def pull_from_repository(repo_path: str, local_dir: str, branch: str = "") -> str:
    """
    Pull changes from a GitHub repository to a local directory.
    Creates the local directory if it doesn't exist.

    Args:
        repo_path: Repository path in format 'owner/repo'
        local_dir: Path to the local directory
        branch: Branch to pull from (default: repository's default branch)
    """
    try:
        # Validate repo_path format
        if '/' not in repo_path:
            return f"Error: Invalid repository path '{repo_path}'. Format should be 'owner/repo'."

        # Create local directory if it doesn't exist
        local_path = pathlib.Path(local_dir)
        local_path.mkdir(parents=True, exist_ok=True)

        # Get repository
        try:
            repo = g.get_repo(repo_path)
        except Exception as repo_error:
            return f"Error accessing repository '{repo_path}': {str(repo_error)}"

        # If branch is not specified, use default branch
        if not branch:
            branch = repo.default_branch

        # Load gitignore patterns if present
        ignore_patterns = _load_gitignore_patterns(local_path)

        # Get all files from the repository
        repo_files = _get_repository_files(repo, branch=branch)

        # Download and update local files
        updated_files = []
        errors = []

        for file_path, file_sha in repo_files.items():
            # Skip if file matches gitignore patterns
            if _should_ignore_file(file_path, ignore_patterns):
                continue

            # Get file content from GitHub
            try:
                file_content = repo.get_contents(file_path, ref=branch)
                content = file_content.decoded_content

                # Create local file path
                local_file_path = local_path / file_path

                # Create directory if it doesn't exist
                local_file_path.parent.mkdir(parents=True, exist_ok=True)

                # Write content to file
                with open(local_file_path, 'wb') as f:
                    f.write(content)

                updated_files.append(file_path)
            except Exception as file_error:
                errors.append(f"Error pulling file '{file_path}': {str(file_error)}")

        # Prepare result
        result = []

        if updated_files:
            result.append(f"Successfully pulled {len(updated_files)} files from repository to {local_dir}")

            # List first 10 files and then summarize if there are more
            if len(updated_files) <= 10:
                for file in updated_files:
                    result.append(f"  - {file}")
            else:
                for file in updated_files[:10]:
                    result.append(f"  - {file}")
                result.append(f"  ... and {len(updated_files) - 10} more files")
        else:
            result.append(
                "No files were pulled from the repository. Either the repository is empty or all files are being ignored.")

        # Add errors if any
        if errors:
            result.append("\nWarnings/Errors:")
            if len(errors) <= 5:
                result.extend(errors)
            else:
                result.extend(errors[:5])
                result.append(f"... and {len(errors) - 5} more errors")

        return "\n".join(result)

    except Exception as e:
        error_details = traceback.format_exc()
        return f"Error pulling from repository: {str(e)}\n\nDetails: {error_details}"


@mcp.tool()
async def push_to_repository(repo_path: str, local_dir: str, commit_message: str, branch: str = "") -> str:
    """
    Push local changes to a GitHub repository.

    Args:
        repo_path: Repository path in format 'owner/repo'
        local_dir: Path to the local directory
        commit_message: Commit message for the changes
        branch: Branch to push to (default: repository's default branch)
    """
    try:
        # Validate repo_path format
        if '/' not in repo_path:
            return f"Error: Invalid repository path '{repo_path}'. Format should be 'owner/repo'."

        user = g.get_user()
        local_path = pathlib.Path(local_dir)

        # Check if local directory exists
        if not local_path.exists() or not local_path.is_dir():
            return f"Error: Local directory '{local_dir}' does not exist"

        # Load gitignore patterns
        ignore_patterns = _load_gitignore_patterns(local_path)

        # Scan local directory
        local_files = _scan_local_directory(local_path, ignore_patterns)

        if not local_files:
            return "Error: No files found in the local directory (empty or all files ignored)"

        # Check if repository exists
        repo_exists = True
        try:
            repo = g.get_repo(repo_path)
        except Exception:
            repo_exists = False

        # Create new repository if it doesn't exist
        if not repo_exists:
            # Extract owner and repo name from repo_path
            parts = repo_path.split('/')
            if len(parts) != 2:
                return "Error: Invalid repository path format. Use 'owner/repo' format."

            owner, repo_name = parts

            # Check if the authenticated user matches the target owner
            if owner.lower() != user.login.lower():
                return f"Error: You can only create repositories under your own account ({user.login}), not under '{owner}'"

            # Create the repository
            try:
                repo = user.create_repo(
                    name=repo_name,
                    description="",  # Default empty description
                    private=False,  # Default to public
                    has_issues=True,
                    has_wiki=True,
                    has_projects=True
                )
            except Exception as create_error:
                return f"Error creating repository: {str(create_error)}"

            result = [f"Repository created successfully!"]
            result.append(f"Name: {repo.name}")
            result.append(f"URL: {repo.html_url}")

            # Default branch for new GitHub repositories
            if not branch:
                branch = "main"

            # Initialize with README if it doesn't exist in local files
            readme_exists = any(rel_path.lower() == "readme.md" for rel_path in local_files)
            if not readme_exists:
                # Create a simple README.md
                readme_content = f"# {repo.name}\n"
                try:
                    repo.create_file(
                        "README.md",
                        "Initial commit: Add README",
                        readme_content,
                        branch=branch
                    )
                    result.append("Created README.md file.")
                except Exception as readme_error:
                    result.append(f"Warning: Failed to create README file: {str(readme_error)}")
        else:
            # Use existing repository
            result = [f"Pushing to existing repository: {repo.full_name}"]

            # If branch is not specified, use default branch
            if not branch:
                branch = repo.default_branch

        # Get existing repository files to compare
        repo_files = {}
        if repo_exists:
            repo_files = _get_repository_files(repo, branch=branch)

        # Add/update all local files
        files_added = 0
        files_updated = 0
        errors = []
        processed_files = []

        for file_path, local_file_path in local_files.items():
            try:
                # Read file content
                with open(local_file_path, 'rb') as f:
                    content = f.read()

                # Check if file exists in repository
                file_exists = file_path in repo_files

                if file_exists:
                    # Update existing file
                    file_content = repo.get_contents(file_path, ref=branch)
                    repo.update_file(
                        file_path,
                        f"{commit_message}: Update {file_path}",
                        content,
                        file_content.sha,
                        branch=branch
                    )
                    files_updated += 1
                    processed_files.append(f"Updated: {file_path}")
                else:
                    # Create new file
                    repo.create_file(
                        file_path,
                        f"{commit_message}: Add {file_path}",
                        content,
                        branch=branch
                    )
                    files_added += 1
                    processed_files.append(f"Added: {file_path}")
            except Exception as file_error:
                errors.append(f"Failed to process file {file_path}: {str(file_error)}")

        # Add summary of changes
        if files_added > 0:
            result.append(f"Added {files_added} new files.")
        if files_updated > 0:
            result.append(f"Updated {files_updated} existing files.")

        if files_added == 0 and files_updated == 0:
            result.append("No files were added or updated.")

        # Show up to 10 processed files
        if processed_files:
            result.append("\nProcessed files:")
            if len(processed_files) <= 10:
                result.extend([f"  - {file}" for file in processed_files])
            else:
                for file in processed_files[:10]:
                    result.append(f"  - {file}")
                result.append(f"  ... and {len(processed_files) - 10} more files")

        # Add errors if any
        if errors:
            result.append("\nWarnings/Errors:")
            if len(errors) <= 5:
                result.extend([f"  - {err}" for err in errors])
            else:
                for err in errors[:5]:
                    result.append(f"  - {err}")
                result.append(f"  ... and {len(errors) - 5} more errors")

        return "\n".join(result)

    except Exception as e:
        error_details = traceback.format_exc()
        return f"Error pushing to repository: {str(e)}\n\nDetails: {error_details}"


@mcp.tool()
async def compare_repository(repo_path: str, local_dir: str, branch: str = "") -> str:
    """
    Compare local directory with GitHub repository and show differences.

    Args:
        repo_path: Repository path in format 'owner/repo'
        local_dir: Path to the local directory
        branch: Branch to compare with (default: repository's default branch)
    """
    try:
        # Validate repo_path format
        if '/' not in repo_path:
            return f"Error: Invalid repository path '{repo_path}'. Format should be 'owner/repo'."

        # Verify local directory exists
        local_path = pathlib.Path(local_dir)
        if not local_path.exists() or not local_path.is_dir():
            return f"Error: Local directory '{local_dir}' does not exist"

        # Get repository
        try:
            repo = g.get_repo(repo_path)
        except Exception as repo_error:
            return f"Error accessing repository '{repo_path}': {str(repo_error)}"

        # If branch is not specified, use default branch
        if not branch:
            branch = repo.default_branch

        # Load gitignore patterns if present
        ignore_patterns = _load_gitignore_patterns(local_path)

        # Get all files from the repository
        repo_files = _get_repository_files(repo, branch=branch)

        # Scan local directory
        local_files = _scan_local_directory(local_path, ignore_patterns)

        # Identify differences
        only_in_repo = []
        only_in_local = []
        modified = []
        identical = []
        comparison_errors = []

        # Files only in repo
        for repo_file in repo_files:
            if _should_ignore_file(repo_file, ignore_patterns):
                continue

            if repo_file not in local_files:
                only_in_repo.append(repo_file)

        # Files only in local or modified or identical
        for local_file, local_path_file in local_files.items():
            if _should_ignore_file(local_file, ignore_patterns):
                continue

            if local_file not in repo_files:
                only_in_local.append(local_file)
            else:
                # Check if content is different
                try:
                    with open(local_path_file, 'rb') as f:
                        local_content = f.read()

                    repo_content = repo.get_contents(local_file, ref=branch)
                    repo_bytes = base64.b64decode(repo_content.content)

                    if repo_bytes != local_content:
                        modified.append(local_file)
                    else:
                        identical.append(local_file)
                except Exception as compare_error:
                    comparison_errors.append(f"{local_file} (Error comparing: {str(compare_error)})")

        # Build result message
        result = []
        result.append(
            f"Comparison between local directory '{local_dir}' and repository '{repo_path}' (branch: {branch or repo.default_branch}):")
        result.append("")

        # Summary stats
        result.append("SUMMARY:")
        result.append(f"- Files only in repository: {len(only_in_repo)}")
        result.append(f"- Files only in local directory: {len(only_in_local)}")
        result.append(f"- Files modified locally: {len(modified)}")
        result.append(f"- Files identical: {len(identical)}")
        if comparison_errors:
            result.append(f"- Files with comparison errors: {len(comparison_errors)}")
        result.append("")

        # Details
        if only_in_repo:
            result.append("FILES ONLY IN REPOSITORY:")
            if len(only_in_repo) <= 10:
                for file in sorted(only_in_repo):
                    result.append(f"  - {file}")
            else:
                for file in sorted(only_in_repo)[:10]:
                    result.append(f"  - {file}")
                result.append(f"  ... and {len(only_in_repo) - 10} more files")
            result.append("")

        if only_in_local:
            result.append("FILES ONLY IN LOCAL DIRECTORY:")
            if len(only_in_local) <= 10:
                for file in sorted(only_in_local):
                    result.append(f"  - {file}")
            else:
                for file in sorted(only_in_local)[:10]:
                    result.append(f"  - {file}")
                result.append(f"  ... and {len(only_in_local) - 10} more files")
            result.append("")

        if modified:
            result.append("FILES MODIFIED LOCALLY:")
            if len(modified) <= 10:
                for file in sorted(modified):
                    result.append(f"  - {file}")
            else:
                for file in sorted(modified)[:10]:
                    result.append(f"  - {file}")
                result.append(f"  ... and {len(modified) - 10} more files")
            result.append("")

        if comparison_errors:
            result.append("FILES WITH COMPARISON ERRORS:")
            if len(comparison_errors) <= 10:
                for file in comparison_errors:
                    result.append(f"  - {file}")
            else:
                for file in comparison_errors[:10]:
                    result.append(f"  - {file}")
                result.append(f"  ... and {len(comparison_errors) - 10} more files")
            result.append("")

        if not only_in_repo and not only_in_local and not modified and not comparison_errors:
            result.append("Local directory and repository are in sync. All files are identical.")

        return "\n".join(result)

    except Exception as e:
        error_details = traceback.format_exc()
        return f"Error comparing repository: {str(e)}\n\nDetails: {error_details}"


# Helper functions

def _load_gitignore_patterns(directory: pathlib.Path) -> List[str]:
    """Load gitignore patterns from the specified directory."""
    gitignore_path = directory / ".gitignore"
    patterns = []

    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    patterns.append(line)

    # Add default patterns to always ignore
    patterns.extend([
        ".git/",
        ".env",
        ".venv/",
        "__pycache__/",
        "*.pyc",
        "*.pyo"
    ])

    return patterns


def _should_ignore_file(file_path: str, ignore_patterns: List[str]) -> bool:
    """Check if a file should be ignored based on gitignore patterns."""
    for pattern in ignore_patterns:
        if pattern.endswith('/'):
            # Directory pattern
            pattern = pattern[:-1]
            if file_path.startswith(pattern + '/') or file_path == pattern:
                return True
        elif fnmatch.fnmatch(file_path, pattern):
            # File pattern
            return True
    return False


def _get_repository_files(repo, branch: str = "") -> Dict[str, str]:
    """Get all files from a GitHub repository recursively."""
    files = {}

    def get_contents(path: str = ""):
        try:
            contents = repo.get_contents(path, ref=branch)

            if not isinstance(contents, list):
                contents = [contents]

            for content in contents:
                if content.type == "dir":
                    get_contents(content.path)
                else:
                    files[content.path] = content.sha
        except Exception as e:
            # Log the exception for debugging purposes
            print(f"Warning: Error accessing {path}: {str(e)}")

    get_contents()
    return files


def _scan_local_directory(directory: pathlib.Path, ignore_patterns: List[str]) -> Dict[str, pathlib.Path]:
    """Scan local directory recursively and return relative paths."""
    files = {}

    for path in directory.glob('**/*'):
        if path.is_file():
            # Get path relative to directory
            rel_path = str(path.relative_to(directory))

            # Convert Windows paths to use forward slashes (for GitHub compatibility)
            rel_path = rel_path.replace('\\', '/')

            # Check if file should be ignored
            if not _should_ignore_file(rel_path, ignore_patterns):
                files[rel_path] = path

    return files


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')