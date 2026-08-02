# Athena dynamic repository context

For repository questions that require understanding or changing code, call `athena_context` exactly
once before opening files. Use its ranked evidence as the starting context. Do not repeat searches
or reopen the same files unless Athena reports low confidence or missing evidence. Keep responses
concise and stop after the requested change and verification. Do not call Athena for general
questions that do not require repository context.

When the user explicitly names a persona, pass that persona to `athena_context`. Otherwise allow
Athena's normal task router to choose. Do not silently switch to a specialized persona merely
because one is installed.
