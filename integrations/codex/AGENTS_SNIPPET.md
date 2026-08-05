## Athena repository context

For a vague repository target, call `repository_context` once with `request_kind="clarify"`. Ask
one focused question when it recommends `ask_user`; otherwise make one focused context call. For a
specific task, call with `request_kind="context"` before broad exploration and reuse its evidence.
Skip Athena for general questions or trivial edits in a file already provided. Use continuation
only when the initial context evidence is insufficient. Verify exact source before editing when
confidence is low.
