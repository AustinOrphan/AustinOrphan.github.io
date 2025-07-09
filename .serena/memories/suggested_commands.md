# Suggested Commands

## System Commands (Darwin/macOS)
- `ls` - List directory contents
- `cd` - Change directory
- `grep` - Search text patterns
- `find` - Find files and directories
- `git` - Version control operations

## Development Commands
Since this is a static HTML/CSS website, there are no build tools or package managers configured.

## File Operations
- `open index.html` - Open the website in default browser
- `python -m http.server` - Simple local server for testing
- `python3 -m http.server` - Python 3 version of local server

## Git Operations
- `git add .` - Stage all changes
- `git commit -m "message"` - Commit changes
- `git push origin master` - Push to GitHub (auto-deploys to GitHub Pages)
- `git status` - Check repository status
- `git log` - View commit history

## Deployment
- **Automatic**: Any push to master branch auto-deploys to GitHub Pages
- **Custom Domain**: Configured via CNAME file (austinorphan.com)
- **No build process**: Direct file serving from repository