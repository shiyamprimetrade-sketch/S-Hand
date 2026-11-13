# Programming workflow

## Example: S builds a small Python application

1. S plans files and generates source text.
2. S-Hand receives a structured `write_file` action scoped to a user-selected workspace.
3. S-Hand writes the file atomically, returning bytes and path.
4. S requests a permitted IDE action (e.g. keyboard shortcut to open a file).
5. S-Eye observes the IDE and checks the expected file is visible.
6. A separately permissioned runner executes tests; S reads the output and decides next changes.
7. S-Hand applies edits; the loop repeats until tests pass.

## Why both typing and file writing?
Keyboard actions are useful in graphical apps, but direct file operations preserve indentation, Unicode and large code blocks. The action engine is not the model or compiler.

## Security model
- Local Windows bridge remains loopback-only.
- Use per-session bearer token, and do not share it.
- Workspace operations must stay inside an explicitly selected directory.
- Never interpret code text as shell commands.
- Human-enabled Accessibility Service is required on Android.
- Actions report dispatch success, not verified final application state.
- S-Eye verification is required before marking a task complete.

## Integration status
Workspace implementation and tests are present. HTTP endpoints for workspace actions, S planner connection, Android-to-PC pairing, and execution sandbox remain future integration tasks.
